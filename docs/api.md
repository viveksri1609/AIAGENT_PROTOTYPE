# API

## `GET /`

Returns a simple health payload describing the backend status.

## `POST /chat`

Request body:

```json
{
  "message": "Get me details of Student 42",
  "session_id": "default"
}
```

Response body:

```json
{
  "response": "Student 42 is ...",
  "token_usage": {
    "estimated_input_tokens": 18,
    "estimated_output_tokens": 42,
    "estimated_total_tokens": 60,
    "estimation_method": "approx_chars_div_4"
  }
}
```

## `POST /reset/{session_id}`

Clears stored conversation memory for the session.

## `POST /rag/reindex`

Rebuilds the SQLite-backed vector index from the `students` table.
