# Students AI Bot

A small full-stack AI agent prototype with:

- FastAPI backend
- SQLite student database
- lightweight RAG layer with a local vector table
- Ollama-powered LLM calls
- React frontend for chat, session control, and token visibility

## Folder structure

```text
aiagent_prototype/
├── backend/
│   ├── __init__.py
│   ├── agent.py
│   ├── db.py
│   ├── main.py
│   ├── requirements.txt
│   └── data/
│       ├── memory.json
│       └── prototype.db
├── docs/
│   ├── api.md
│   └── architecture.md
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── api/
│       ├── components/
│       ├── App.jsx
│       ├── main.jsx
│       └── styles.css
└── README.md
```

## Backend setup

Create or activate your Python environment, then install dependencies:

```bash
pip install -r backend/requirements.txt
```

Start the API:

```bash
uvicorn backend.main:app --reload
```

The backend runs on `http://127.0.0.1:8000`.

## Frontend setup

Install frontend dependencies:

```bash
cd frontend
npm install
```

Start the React app:

```bash
npm run dev
```

The frontend runs on `http://127.0.0.1:5173` and proxies API calls to the FastAPI server.

## Ollama requirement

The backend expects Ollama at:

```text
http://localhost:11434/api/generate
```

With the current model name:

```text
llama3
```

If you want a different local model, update `MODEL` in [backend/agent.py](/Users/vivek/projects/aiagent_prototype/backend/agent.py).

## Available backend endpoints

- `GET /`: health/status
- `POST /chat`: send a chat message
- `POST /reset/{session_id}`: clear conversation memory
- `POST /rag/reindex`: rebuild the vector index

## Frontend features

- Chat interface for the student agent
- Session ID switching
- Memory reset button
- RAG reindex button
- Token usage display from backend middleware
- Backend health visibility

## Notes

- Token counts are estimated using a lightweight character-based approximation.
- The current vector store is implemented inside SQLite for simplicity.
- The current embedding function is deterministic and local, which keeps the prototype easy to run but less capable than a dedicated embedding model.

More detail is available in [docs/architecture.md](/Users/vivek/projects/aiagent_prototype/docs/architecture.md) and [docs/api.md](/Users/vivek/projects/aiagent_prototype/docs/api.md).
