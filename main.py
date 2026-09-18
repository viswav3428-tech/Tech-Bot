import os
from datetime import datetime
from typing import Optional

import psycopg2
import psycopg2.extras
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
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


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
