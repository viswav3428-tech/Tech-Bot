import json
import os
import re
from typing import Any, Dict, List, Optional
import httpx
from knowledge_base import lookup_academic_kb

SYSTEM_PROMPT_TEMPLATE = """
You are TECHBOT, an AI teaching assistant robot for college students, developed by the RoboCore team (PCB Masters), a second-year ECE team.

PRIMARY ROLE:
- Answer student and teacher questions.
- Explain engineering and academic concepts simply and step-by-step.
- Make difficult topics easy to understand.
- Use examples and visual/animation explanations when appropriate.

ROBOT ROLE:
- Navigate to locations.
- Follow users.
- Deliver items.
- Support attendance and presentations.
- Dock and stop when commanded.

Prioritize teaching and concept explanation. Execute robot commands when requested.

Locations:
{locations_list}

Actions:
goto, follow, stop, dock, deliver

Animations:
explaining_ohms_law, explaining_engineering, navigating, following, delivering, speaking, listening, idle

Return ONLY valid JSON:
{{
  "reply_text": "<response>",
  "animation": "<animation>",
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

    # 7. TECHBOT IDENTITY / TEAM QUESTIONS
    if any(phrase in cleaned for phrase in [
        "who are you", "what are you", "introduce yourself",
        "about yourself", "tell me about yourself", "what is your name",
        "whats your name", "your name"
    ]):
        return {
            "reply_text": "I'm TECHBOT, an AI-powered campus assistant robot developed by the RoboCore team, a team of second-year ECE students. I'm designed to assist with campus activities, robot navigation, faculty support, engineering questions, deliveries, and other smart-campus tasks.",
            "animation": "speaking",
            "action": None,
        }

    if any(phrase in cleaned for phrase in [
        "who made you", "who created you", "who developed you",
        "who built you", "who is your developer", "who are your developers"
    ]):
        return {
            "reply_text": "I was developed by the RoboCore team, a team of second-year ECE students.",
            "animation": "speaking",
            "action": None,
        }

    if any(phrase in cleaned for phrase in [
        "what is robocore", "who is robocore", "tell me about robocore",
        "what is your team", "who is your team"
    ]):
        return {
            "reply_text": "RoboCore is the team behind TECHBOT. We are a team of second-year ECE students developing this AI-powered campus assistant robot.",
            "animation": "speaking",
            "action": None,
        }

    if any(phrase in cleaned for phrase in [
        "who are your team members", "name your team members",
        "tell me your team members", "who is in your team",
        "team members", "team member names", "who made techbot"
    ]):
        return {
            "reply_text": "My RoboCore team members are Viswa, Aron, Radhkrishnan, Shelina, Rayha, and Nithya.",
            "animation": "speaking",
            "action": None,
        }

    if any(phrase in cleaned for phrase in [
        "what is pcb masters", "who are pcb masters", "what are pcb masters",
        "tell me about pcb masters", "what is your team nickname",
        "what is your team nick name", "what do you call your team",
        "team nickname", "team nick name"
    ]):
        return {
            "reply_text": "PCB Masters is the team nickname for our six-member RoboCore team: Viswa, Aron, Radhkrishnan, Shelina, Rayha, and Nithya.",
            "animation": "speaking",
            "action": None,
        }

    if any(phrase in cleaned for phrase in [
        "what can you do", "what are your capabilities",
        "your capabilities", "what do you do", "what is your purpose",
        "why were you made"
    ]):
        return {
            "reply_text": "I can assist with campus activities, robot navigation, faculty support, engineering questions, deliveries, and other smart-campus tasks.",
            "animation": "speaking",
            "action": None,
        }

    # Default general reply
    return {
        "reply_text": “I'm TECHBOT, an AI-powered assistive robot developed by RoboCore. I answer questions, explain concepts, support faculty, and assist with deliveries.”,
        "animation": "speaking",
        "action": None,
    }


def call_gemini_api(api_key: str, user_msg: str, locations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    loc_str = "\n".join([f"- ID {loc.get('id')}: {loc.get('name')}" for loc in locations])
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(locations_list=loc_str)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
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
        with httpx.Client(timeout=30.0) as client:
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
            else:
                print(f"[OpenAI HTTP Error] status={resp.status_code}, body={resp.text[:500]}")
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

    if not result and openai_key:
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
