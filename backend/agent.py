import json
import re
from pathlib import Path

import requests

try:
    from .db import (
        get_all_students,
        get_student_by_name,
        search_vector_db,
        sync_students_to_vector_db,
    )
except ImportError:
    from db import (
        get_all_students,
        get_student_by_name,
        search_vector_db,
        sync_students_to_vector_db,
    )

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MEMORY_FILE = DATA_DIR / "memory.json"
VECTOR_INDEX_READY = False

SYSTEM_PROMPT = """
You are a student database assistant.

CRITICAL RULES:
- When a tool is required respond ONLY with tool call.
- No explanation.
- No greeting.
- No extra text.
- No punctuation.

Valid responses:

TOOL:get_student_by_name:NAME
TOOL:get_all_students

If unsure respond exactly:
I don't know
"""

def load_memory():
    if not MEMORY_FILE.exists():
        return {}
    with MEMORY_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(memory):
    DATA_DIR.mkdir(exist_ok=True)
    with MEMORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)


def get_session_history(session_id):
    memory = load_memory()

    if session_id not in memory:
        memory[session_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        save_memory(memory)

    return memory[session_id]


def update_session_history(session_id, history):
    memory = load_memory()
    memory[session_id] = history[-20:]   
    save_memory(memory)



def call_llm(messages):
    prompt = ""
    for msg in messages:
        prompt += f"{msg['role'].upper()}: {msg['content']}\n"

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=60
    )
    return response.json()["response"]


def ensure_vector_index():
    global VECTOR_INDEX_READY

    if VECTOR_INDEX_READY:
        return

    sync_students_to_vector_db()
    VECTOR_INDEX_READY = True


def build_rag_context(user_message: str):
    ensure_vector_index()
    matches = search_vector_db(user_message, top_k=3)

    if not matches:
        return None

    context_lines = []
    for match in matches:
        context_lines.append(
            f"- score={match['score']} | {match['content']}"
        )

    return "\n".join(context_lines)



def run_agent(user_message: str, session_id: str = "default"):

    history = get_session_history(session_id)

    history.append({"role": "user", "content": user_message})

    rag_context = build_rag_context(user_message)
    llm_input = list(history)

    if rag_context:
        llm_input.append({
            "role": "system",
            "content": (
                "Relevant vector search context for the latest user query:\n"
                f"{rag_context}\n"
                "Use this context when helpful, but use tools for exact database lookups."
            )
        })

    llm_reply = call_llm(llm_input)

    tool_line = None

    match = re.search(r"(?:TOOL:)?(get_student_by_name|get_all_students)(?::[^\n]+)?", llm_reply)

    if match:
        tool_line = match.group()

        tool_line = tool_line.replace("TOOL:", "")

        parts = tool_line.split(":")
        tool_name = parts[0]

        if tool_name == "get_student_by_name":
            name = parts[1]
            data = get_student_by_name(name)

        elif tool_name == "get_all_students":
            data = get_all_students()

        else:
            return "Unknown tool"

        tool_prompt = f"""
User asked: {user_message}
Tool result: {data}
Relevant retrieved context: {rag_context or "None"}
Explain clearly to user.
"""

        history.append({"role": "assistant", "content": str(data)})

        final_reply = call_llm(history + [
            {"role": "user", "content": tool_prompt}
        ])

        history.append({"role": "assistant", "content": final_reply})
        update_session_history(session_id, history)

        return final_reply

    history.append({"role": "assistant", "content": llm_reply})
    update_session_history(session_id, history)

    return llm_reply



def reset_memory(session_id: str):
    memory = load_memory()
    memory.pop(session_id, None)
    save_memory(memory)
