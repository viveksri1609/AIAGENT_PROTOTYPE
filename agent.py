import json
import os
import requests
import re
from db import get_student_by_name, get_all_students

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

MEMORY_FILE = "memory.json"

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
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
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
        }
    )
    return response.json()["response"]



def run_agent(user_message: str, session_id: str = "default"):

    history = get_session_history(session_id)

    history.append({"role": "user", "content": user_message})

    llm_reply = call_llm(history)

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