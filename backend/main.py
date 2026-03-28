import json

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

try:
    from .agent import reset_memory, run_agent
    from .db import sync_students_to_vector_db
except ImportError:
    from agent import reset_memory, run_agent
    from db import sync_students_to_vector_db

app = FastAPI(title="Students AI Bot")


def estimate_tokens(text: str) -> int:
    if not text:
        return 0

    # Lightweight approximation for local visibility without model-specific tokenizers.
    return max(1, round(len(text) / 4))


class TokenUsageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path != "/chat" or request.method.upper() != "POST":
            return await call_next(request)

        raw_body = await request.body()
        request_text = raw_body.decode("utf-8", errors="ignore")
        request_tokens = estimate_tokens(request_text)

        async def receive():
            return {
                "type": "http.request",
                "body": raw_body,
                "more_body": False,
            }

        request = Request(request.scope, receive)
        response = await call_next(request)

        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        response_text = response_body.decode("utf-8", errors="ignore")
        response_tokens = estimate_tokens(response_text)
        total_tokens = request_tokens + response_tokens

        response_headers = dict(response.headers)
        response_headers.pop("content-length", None)
        response_headers.pop("Content-Length", None)
        response_headers["X-Estimated-Input-Tokens"] = str(request_tokens)
        response_headers["X-Estimated-Output-Tokens"] = str(response_tokens)
        response_headers["X-Estimated-Total-Tokens"] = str(total_tokens)

        if "application/json" in response_headers.get("content-type", "") and response_text:
            try:
                payload = json.loads(response_text)
                payload["token_usage"] = {
                    "estimated_input_tokens": request_tokens,
                    "estimated_output_tokens": response_tokens,
                    "estimated_total_tokens": total_tokens,
                    "estimation_method": "approx_chars_div_4",
                }
                return JSONResponse(
                    content=payload,
                    status_code=response.status_code,
                    headers=response_headers,
                )
            except json.JSONDecodeError:
                pass

        return response


app.add_middleware(TokenUsageMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@app.get("/")
def root():
    return {
        "status": "Students AI Bot running",
        "frontend": "Start the React app from the frontend folder",
        "docs": "See README.md for setup details",
    }


@app.post("/chat")
def chat(req: ChatRequest):
    reply = run_agent(req.message, req.session_id)
    return {"response": reply}


@app.post("/reset/{session_id}")
def clear_memory(session_id: str):
    reset_memory(session_id)
    return {"status": "memory cleared"}


@app.post("/rag/reindex")
def rebuild_rag_index():
    count = sync_students_to_vector_db()
    return {"status": "rag index rebuilt", "documents_indexed": count}
