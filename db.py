import sqlite3

DB_NAME = "prototype.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def get_student_by_name(name: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, age, email, course, marks
        FROM students
        WHERE name LIKE ?
    """, (f"%{name}%",))

    rows = cursor.fetchall()
    print(rows)
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
    print(rows)
    conn.close()

    return rows