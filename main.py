from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent, reset_memory

app = FastAPI(title="Students AI Bot")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@app.get("/")
def root():
    return {"status": "Students AI Bot runming"}


@app.post("/chat")
def chat(req: ChatRequest):
    reply = run_agent(req.message, req.session_id)
    return {"response": reply}


@app.post("/reset/{session_id}")
def clear_memory(session_id: str):
    reset_memory(session_id)
    return {"status": "memory cleared"}