import json
import os
import re
from typing import Any, Dict, List, Optional
import httpx


SYSTEM_PROMPT_TEMPLATE = """
You are TEACHBOT, an intelligent college campus service robot built for the Smart India Hackathon.
You assist faculty and students with autonomous following, point-to-point delivery, automated attendance, and projector presentations.

Available Campus Locations:
{locations_list}

Your Capabilities & Allowed Actions:
- 'goto': Navigate to a specific location (destination_id required).
- 'follow': Follow the user / faculty member safely.
- 'stop': Immediately halt all robot movements (emergency stop).
- 'dock': Return to the charging station / base dock.
- 'deliver': Carry an item to a destination location.

Available Touchscreen Animation Tags:
- 'explaining_ohms_law' (for Ohm's law questions)
- 'explaining_engineering' (for other science/engineering concepts)
- 'navigating' (when moving or going to a room)
- 'following' (when following someone)
- 'delivering' (when carrying items)
- 'speaking' (for general answers, greetings, facts)
- 'listening' (when prompt was conversational)
- 'idle' (default idle face)

IMPORTANT: You MUST reply in valid JSON with exactly these keys:
{{
  "reply_text": "<Clear, concise spoken response to user>",
  "animation": "<one of the animation tags above>",
  "action": null OR {{
      "task_type": "goto" | "follow" | "stop" | "dock" | "deliver",
      "destination_id": <int or null>,
      "destination_name": "<string or null>"
  }}
}}
"""


def clean_text(text: str) -> str:
    """Normalize text for offline regex/keyword matching."""
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def match_location(user_msg: str, locations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Match destination name from the available locations list."""
    cleaned = clean_text(user_msg)
    for loc in locations:
        loc_name = loc.get("name", "").lower()
        if loc_name and loc_name in cleaned:
            return loc
    return None


def offline_rule_parser(user_msg: str, locations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Intelligent offline fallback intent parser.
    Guarantees that TEACHBOT can execute robot commands and answer
    core engineering questions even without an internet connection or LLM API key.
    """
    cleaned = clean_text(user_msg)

    # 1. STOP / EMERGENCY HALT
    if any(word in cleaned for word in ["stop", "halt", "freeze", "brake", "pause", "shut down"]):
        return {
            "reply_text": "Emergency stop activated! Halting all robot movements immediately.",
            "animation": "idle",
            "action": {"task_type": "stop", "destination_id": None, "destination_name": None},
        }

    # 2. DOCK / CHARGING
    if any(phrase in cleaned for phrase in ["dock", "charge", "charging", "base station", "go home", "return home"]):
        dock_loc = next((loc for loc in locations if "dock" in loc.get("name", "").lower()), None)
        return {
            "reply_text": "Heading back to the charging dock now.",
            "animation": "navigating",
            "action": {
                "task_type": "dock",
                "destination_id": dock_loc["id"] if dock_loc else None,
                "destination_name": dock_loc["name"] if dock_loc else "Charging Dock",
            },
        }

    # 3. FOLLOW FACULTY / USER
    if any(phrase in cleaned for phrase in ["follow me", "follow", "track me", "come with me"]):
        return {
            "reply_text": "I am now following you! Maintaining safe distance.",
            "animation": "following",
            "action": {"task_type": "follow", "destination_id": None, "destination_name": None},
        }

    # 4. DELIVERY
    if any(word in cleaned for word in ["deliver", "delivery", "bring this to", "take this package"]):
        matched_loc = match_location(user_msg, locations)
        if matched_loc:
            return {
                "reply_text": f"Starting delivery to {matched_loc['name']}. Please place the item in my storage compartment.",
                "animation": "delivering",
                "action": {
                    "task_type": "deliver",
                    "destination_id": matched_loc["id"],
                    "destination_name": matched_loc["name"],
                },
            }
        return {
            "reply_text": "I can deliver items. Please specify the destination, for example: 'Deliver this to Lab 1'.",
            "animation": "speaking",
            "action": None,
        }

    # 5. GOTO / NAVIGATION
    if any(phrase in cleaned for phrase in ["go to", "goto", "navigate to", "take me to", "head to", "move to", "drive to"]):
        matched_loc = match_location(user_msg, locations)
        if matched_loc:
            return {
                "reply_text": f"Navigating to {matched_loc['name']} now. Please clear the path.",
                "animation": "navigating",
                "action": {
                    "task_type": "goto",
                    "destination_id": matched_loc["id"],
                    "destination_name": matched_loc["name"],
                },
            }
        loc_names = ", ".join(loc["name"] for loc in locations) if locations else "Lab 1, Lab 2, Faculty Office"
        return {
            "reply_text": f"Which location would you like me to go to? Available rooms are: {loc_names}.",
            "animation": "speaking",
            "action": None,
        }

    # Check if user simply mentioned a known location by name (e.g. "Lab 1")
    matched_loc = match_location(user_msg, locations)
    if matched_loc and len(cleaned.split()) <= 4:
        return {
            "reply_text": f"Setting destination to {matched_loc['name']}.",
            "animation": "navigating",
            "action": {
                "task_type": "goto",
                "destination_id": matched_loc["id"],
                "destination_name": matched_loc["name"],
            },
        }

    # 6. CORE ACADEMIC Q&A DEMOS (With dedicated touchscreen animations)
    if "ohm" in cleaned and "law" in cleaned:
        return {
            "reply_text": "Ohm's Law states that the current through a conductor between two points is directly proportional to the voltage across the two points, represented as V = I * R (Voltage = Current times Resistance).",
            "animation": "explaining_ohms_law",
            "action": None,
        }

    if any(phrase in cleaned for phrase in ["kirchhoff", "kcl", "kvl"]):
        return {
            "reply_text": "Kirchhoff's Laws: KCL states total current entering a junction equals total current leaving. KVL states the algebraic sum of voltages around any closed loop is zero.",
            "animation": "explaining_engineering",
            "action": None,
        }

    if "capacit" in cleaned:
        return {
            "reply_text": "Capacitance is the ratio of electric charge on each conductor to the potential difference between them: C = Q / V, measured in Farads.",
            "animation": "explaining_engineering",
            "action": None,
        }

    if any(phrase in cleaned for phrase in ["who are you", "what are you", "introduce yourself", "about yourself"]):
        return {
            "reply_text": "Hello! I am TEACHBOT, an autonomous campus service robot developed by 2nd-year ECE students for Smart India Hackathon. I assist faculty with following, lab deliveries, face-recognition attendance, and slide presentations.",
            "animation": "speaking",
            "action": None,
        }

    # Default general reply
    return {
        "reply_text": "I'm TEACHBOT! You can ask me engineering questions or give me commands like 'Go to Lab 1', 'Follow me', or 'Stop'.",
        "animation": "speaking",
        "action": None,
    }


def call_gemini_api(api_key: str, user_msg: str, locations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    loc_str = "\n".join([f"- ID {loc.get('id')}: {loc.get('name')}" for loc in locations])
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(locations_list=loc_str)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{system_prompt}\n\nUser: {user_msg}"}]}
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.2,
        },
    }

    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text_out = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_out)
            else:
                print(f"[Gemini HTTP Error] status={resp.status_code}, body={resp.text[:500]}")
    except Exception as e:
        print(f"[Gemini API Exception] {e}")
    return None


def call_openai_api(api_key: str, user_msg: str, locations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Query OpenAI API with JSON output format."""
    loc_str = "\n".join([f"- ID {loc.get('id')}: {loc.get('name')}" for loc in locations])
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(locations_list=loc_str)

    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }

    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
    except Exception as e:
        print(f"[OpenAI API Exception] {e}")
    return None


def process_chat_message(user_msg: str, locations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main entrypoint for the Conversational AI Agent.
    Prioritizes Gemini / OpenAI if configured in .env, with instant
    fallback to the robust offline rule parser.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    print(f"[DEBUG] Gemini key present: {bool(gemini_key)}, OpenAI key present: {bool(openai_key)}")

    result = None
    if gemini_key:
        result = call_gemini_api(gemini_key, user_msg, locations)
    elif openai_key:
        result = call_openai_api(openai_key, user_msg, locations)

    # If LLM didn't return or isn't configured, use rule-based offline parser
    if not result or not isinstance(result, dict) or "reply_text" not in result:
        result = offline_rule_parser(user_msg, locations)

    # Sanitize and ensure standard structure
    return {
        "reply_text": result.get("reply_text", "I am listening."),
        "animation": result.get("animation", "speaking"),
        "action": result.get("action"),
    }
