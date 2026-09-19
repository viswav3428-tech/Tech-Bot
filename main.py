import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras
from ai_agent import process_chat_message
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt
from dotenv import load_dotenv

load_dotenv()  # reads your .env file so DATABASE_URL is available below

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="TEACHBOT Backend")


def get_connection():
    # RealDictCursor makes query results come back as {"column": value}
    # dictionaries instead of plain tuples — much easier to read/return as JSON.
    if not DATABASE_URL:
        raise HTTPException(
            status_code=500,
            detail="DATABASE_URL is not set. Please configure DATABASE_URL in your .env file."
        )
    try:
        return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    except psycopg2.OperationalError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {e}"
        )

@app.get("/debug-db")
def debug_db():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        return {"status": "success", "message": "Database connection works!"}
    except Exception as e:
        return {"status": "error", "type": type(e).__name__, "detail": str(e)}

@app.get("/")
def root():
    return {"message": "TEACHBOT backend is running"}


# ============================================================
# FACULTY REGISTRATION & LOGIN
# ============================================================

class FacultyRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    department: Optional[str] = None


class FacultyLogin(BaseModel):
    email: EmailStr
    password: str


@app.post("/faculty/register")
def register_faculty(payload: FacultyRegister):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM faculty WHERE email = %s", (payload.email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = bcrypt.hash(payload.password)  # never store the raw password
    cur.execute(
        """
        INSERT INTO faculty (name, email, password_hash, phone, department)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, name, email
        """,
        (payload.name, payload.email, password_hash, payload.phone, payload.department),
    )
    new_faculty = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Faculty registered", "faculty": new_faculty}


@app.post("/faculty/login")
def login_faculty(payload: FacultyLogin):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email, password_hash FROM faculty WHERE email = %s",
        (payload.email,),
    )
    faculty = cur.fetchone()
    cur.close()
    conn.close()

    if not faculty or not bcrypt.verify(payload.password, faculty["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # NOTE: for a real app you'd return a JWT/session token here instead of
    # just the faculty_id. Fine for now while you're testing end-to-end flow.
    return {"message": "Login successful", "faculty_id": faculty["id"], "name": faculty["name"]}


# ============================================================
# LOCATIONS (the named map points: Lab 1, Faculty Office, etc.)
# ============================================================

@app.get("/locations")
def list_locations():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, map_x, map_y, floor FROM locations ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ============================================================
# ROBOT STATUS (battery, mode, position)
# ============================================================

class StatusUpdate(BaseModel):
    robot_id: int
    battery_percent: Optional[int] = None
    mode: Optional[str] = None
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None


@app.post("/status")
def report_status(payload: StatusUpdate):
    """The ROBOT calls this to report what it's currently doing."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO robot_status_log (robot_id, battery_percent, mode, pos_x, pos_y)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (payload.robot_id, payload.battery_percent, payload.mode, payload.pos_x, payload.pos_y),
    )
    cur.execute("UPDATE robots SET last_seen_at = now() WHERE id = %s", (payload.robot_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Status recorded"}


@app.get("/status/{robot_id}")
def get_latest_status(robot_id: int):
    """The APP/DASHBOARD calls this to see the robot's latest known state."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT battery_percent, mode, pos_x, pos_y, reported_at
        FROM robot_status_log
        WHERE robot_id = %s
        ORDER BY reported_at DESC
        LIMIT 1
        """,
        (robot_id,),
    )
    latest = cur.fetchone()
    cur.close()
    conn.close()

    if not latest:
        raise HTTPException(status_code=404, detail="No status reported yet for this robot")
    return latest


# ============================================================
# TASKS (follow / goto / deliver / stop / dock)
# ============================================================

class TaskCreate(BaseModel):
    robot_id: int
    faculty_id: Optional[int] = None
    task_type: str  # 'follow' | 'goto' | 'deliver' | 'stop' | 'dock'
    destination_id: Optional[int] = None
    requested_via: Optional[str] = "app"  # 'app' | 'touchscreen' | 'voice_agent' | 'dashboard'


VALID_TASK_TYPES = {"follow", "goto", "deliver", "stop", "dock"}


@app.post("/tasks")
def create_task(payload: TaskCreate):
    """
    Called by the APP, DASHBOARD, or AI AGENT — whichever one issues a command,
    it becomes one row here. This is the single funnel every control surface uses.
    """
    if payload.task_type not in VALID_TASK_TYPES:
        raise HTTPException(status_code=400, detail=f"task_type must be one of {VALID_TASK_TYPES}")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO tasks (robot_id, faculty_id, task_type, destination_id, requested_via)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, task_type, status, created_at
        """,
        (payload.robot_id, payload.faculty_id, payload.task_type, payload.destination_id, payload.requested_via),
    )
    new_task = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Task created", "task": new_task}


@app.get("/tasks/pending/{robot_id}")
def get_pending_tasks(robot_id: int):
    """The ROBOT calls this to check what it's been asked to do."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, task_type, destination_id, requested_via, created_at
        FROM tasks
        WHERE robot_id = %s AND status = 'pending'
        ORDER BY created_at ASC
        """,
        (robot_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


class TaskStatusUpdate(BaseModel):
    status: str  # 'in_progress' | 'completed' | 'failed' | 'cancelled'


VALID_TASK_STATUSES = {"in_progress", "completed", "failed", "cancelled"}


@app.patch("/tasks/{task_id}")
def update_task_status(task_id: int, payload: TaskStatusUpdate):
    """The ROBOT calls this as it works through (or fails/cancels) a task."""
    if payload.status not in VALID_TASK_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {VALID_TASK_STATUSES}")

    completed_at = datetime.utcnow() if payload.status == "completed" else None

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE tasks
        SET status = %s, completed_at = COALESCE(%s, completed_at)
        WHERE id = %s
        RETURNING id, status
        """,
        (payload.status, completed_at, task_id),
    )
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


# ============================================================
# CONVERSATIONAL AI AGENT (/chat, sessions & history)
# ============================================================

class ChatRequest(BaseModel):
    message: str
    robot_id: int
    faculty_id: Optional[int] = None
    student_id: Optional[int] = None
    session_id: Optional[int] = None


class ChatResponse(BaseModel):
    session_id: int
    reply_text: str
    animation: str
    task_created: Optional[Dict[str, Any]] = None


@app.post("/chat", response_model=ChatResponse)
def chat_with_agent(payload: ChatRequest):
    """
    Conversational AI Assistant endpoint.
    - Answers campus/engineering Q&A (e.g. Ohm's law, with animations).
    - Translates natural language commands ('go to Lab 1', 'follow', 'stop', 'dock')
      into tasks written directly to the central `tasks` table with requested_via='voice_agent'.
    - Stores full chat history in chat_sessions and chat_messages.
    - Runs reliably in both connected database mode and offline demo mode.
    """
    conn = None
    cur = None
    locations = [
        {"id": 1, "name": "Lab 1"},
        {"id": 2, "name": "Lab 2"},
        {"id": 3, "name": "Faculty Office"},
        {"id": 4, "name": "Charging Dock"},
    ]

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM locations")
        db_locations = cur.fetchall()
        if db_locations:
            locations = db_locations
    except HTTPException:
        # If DB is not configured or not yet running, use default campus locations
        conn = None

    # Process message with AI agent
    ai_result = process_chat_message(payload.message, locations)

    task_created = None
    task_id = None
    session_id = payload.session_id or 1

    if conn and cur:
        try:
            # 1. If a robot action was detected, insert into the central tasks table!
            if ai_result.get("action"):
                action = ai_result["action"]
                task_type = action.get("task_type")
                dest_id = action.get("destination_id")

                cur.execute(
                    """
                    INSERT INTO tasks (robot_id, faculty_id, task_type, destination_id, requested_via)
                    VALUES (%s, %s, %s, %s, 'voice_agent')
                    RETURNING id, task_type, destination_id, status, created_at
                    """,
                    (payload.robot_id, payload.faculty_id, task_type, dest_id),
                )
                task_created = cur.fetchone()
                if task_created:
                    task_id = task_created["id"]

            # 2. Manage session_id in chat_sessions
            if not payload.session_id:
                cur.execute(
                    """
                    INSERT INTO chat_sessions (faculty_id, student_id, started_at)
                    VALUES (%s, %s, now())
                    RETURNING id
                    """,
                    (payload.faculty_id, payload.student_id),
                )
                new_session = cur.fetchone()
                session_id = new_session["id"]

            # 3. Record user message and assistant reply in chat_messages
            cur.execute(
                """
                INSERT INTO chat_messages (session_id, sender, message_text, animation_key, triggered_task)
                VALUES (%s, 'user', %s, NULL, NULL)
                """,
                (session_id, payload.message),
            )
            cur.execute(
                """
                INSERT INTO chat_messages (session_id, sender, message_text, animation_key, triggered_task)
                VALUES (%s, 'agent', %s, %s, %s)
                """,
                (session_id, ai_result["reply_text"], ai_result["animation"], task_id),
            )
            conn.commit()
            cur.close()
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Database logging error: {e}")
        finally:
            conn.close()
    else:
        # Offline demo mode: construct virtual task object if an action was triggered
        if ai_result.get("action"):
            action = ai_result["action"]
            task_created = {
                "id": 0,
                "task_type": action.get("task_type"),
                "destination_id": action.get("destination_id"),
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
            }

    return {
        "session_id": session_id,
        "reply_text": ai_result["reply_text"],
        "animation": ai_result["animation"],
        "task_created": task_created,
    }


@app.get("/chat/sessions")
def list_chat_sessions():
    """Retrieve recent chat sessions."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, faculty_id, student_id, started_at, ended_at
            FROM chat_sessions
            ORDER BY started_at DESC
            LIMIT 20
            """
        )
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()


@app.get("/chat/sessions/{session_id}/messages")
def get_session_messages(session_id: int):
    """Retrieve full transcript of messages for a given chat session."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, session_id, sender, message_text AS message, animation_key AS animation, triggered_task AS task_id, created_at
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY created_at ASC
            """,
            (session_id,),
        )
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


