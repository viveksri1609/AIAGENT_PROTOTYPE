import json
import math
import re
import sqlite3
from datetime import datetime
from hashlib import md5
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_NAME = DATA_DIR / "prototype.db"
EMBEDDING_DIMENSION = 128


def get_connection():
    DATA_DIR.mkdir(exist_ok=True)
    return sqlite3.connect(DB_NAME)


def init_vector_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rag_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL,
            metadata TEXT,
            updated_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def _tokenize(text: str):
    return re.findall(r"\w+", text.lower())


def _normalize(vector):
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]


def embed_text(text: str, dimension: int = EMBEDDING_DIMENSION):
    vector = [0.0] * dimension

    for token in _tokenize(text):
        bucket = int(md5(token.encode("utf-8")).hexdigest(), 16) % dimension
        vector[bucket] += 1.0

    return _normalize(vector)


def _cosine_similarity(vector_a, vector_b):
    if len(vector_a) != len(vector_b):
        return 0.0
    return sum(left * right for left, right in zip(vector_a, vector_b))


def _keyword_overlap_score(query: str, content: str):
    query_tokens = set(_tokenize(query))
    content_tokens = set(_tokenize(content))

    if not query_tokens:
        return 0.0

    overlap = len(query_tokens & content_tokens) / len(query_tokens)
    query_numbers = {token for token in query_tokens if token.isdigit()}
    content_numbers = {token for token in content_tokens if token.isdigit()}
    number_bonus = 0.35 if query_numbers & content_numbers else 0.0
    query_emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", query.lower())
    email_bonus = 0.5 if any(email in content.lower() for email in query_emails) else 0.0

    return overlap + number_bonus + email_bonus


def _student_to_document(student_row):
    student_id, name, age, email, course, marks = student_row
    return (
        f"Student ID: {student_id}. "
        f"Name: {name}. "
        f"Age: {age}. "
        f"Email: {email}. "
        f"Course: {course}. "
        f"Marks: {marks}."
    )


def upsert_vector_document(source_type: str, source_id: str, content: str, metadata=None):
    init_vector_db()

    conn = get_connection()
    cursor = conn.cursor()

    embedding = embed_text(content)
    payload = json.dumps(metadata or {})

    cursor.execute("""
        INSERT INTO rag_documents (source_type, source_id, content, embedding, metadata, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_id) DO UPDATE SET
            source_type = excluded.source_type,
            content = excluded.content,
            embedding = excluded.embedding,
            metadata = excluded.metadata,
            updated_at = excluded.updated_at
    """, (
        source_type,
        source_id,
        content,
        json.dumps(embedding),
        payload,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


def sync_students_to_vector_db():
    init_vector_db()
    students = get_all_students()

    for student in students:
        student_id, name, age, email, course, marks = student
        upsert_vector_document(
            source_type="student",
            source_id=f"student:{student_id}",
            content=_student_to_document(student),
            metadata={
                "student_id": student_id,
                "name": name,
                "age": age,
                "email": email,
                "course": course,
                "marks": marks
            }
        )

    return len(students)


def search_vector_db(query: str, top_k: int = 3, source_type: str = "student"):
    init_vector_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT source_id, content, embedding, metadata
        FROM rag_documents
        WHERE source_type = ?
    """, (source_type,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    query_embedding = embed_text(query)
    scored_rows = []

    for source_id, content, embedding_json, metadata_json in rows:
        vector_score = _cosine_similarity(query_embedding, json.loads(embedding_json))
        keyword_score = _keyword_overlap_score(query, content)
        similarity = (vector_score * 0.65) + (keyword_score * 0.35)
        scored_rows.append({
            "source_id": source_id,
            "content": content,
            "score": round(similarity, 4),
            "metadata": json.loads(metadata_json or "{}")
        })

    scored_rows.sort(key=lambda item: item["score"], reverse=True)
    return scored_rows[:top_k]


def get_student_by_name(name: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, age, email, course, marks
        FROM students
        WHERE name LIKE ?
    """, (f"%{name}%",))

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, age, email, course, marks
        FROM students
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows
