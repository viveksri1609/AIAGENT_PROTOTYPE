# Architecture

## Overview

This project is split into two runtime surfaces:

- `backend/`: FastAPI application, SQLite student database, chat agent, RAG indexing, and token usage middleware.
- `frontend/`: React + Vite application for chatting with the backend and managing sessions.

## Backend flow

1. The React client sends a message to `POST /chat`.
2. FastAPI middleware estimates request and response token usage and adds those numbers to the JSON response.
3. The agent loads conversation memory for the active `session_id`.
4. The RAG layer searches the `rag_documents` table for relevant student records.
5. The LLM receives session history plus retrieved context.
6. If the LLM emits a tool call, the backend runs SQLite lookups and asks the model to produce a user-facing explanation.
7. The final response is returned to the frontend with token-usage metadata.

## Data layout

- `backend/data/prototype.db`: primary SQLite database with `students` and `rag_documents`.
- `backend/data/memory.json`: session conversation history.

## Retrieval model

The current vector layer is intentionally lightweight for a prototype:

- Documents are generated from student rows.
- Embeddings are deterministic local hashed vectors.
- Ranking combines vector similarity with keyword, numeric, and exact-email boosts.

This keeps the app self-contained while still demonstrating a working RAG architecture.

