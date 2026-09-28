"""
db.py
-----
Database access layer for the Attendance Maker System.
Uses SQLite (built into Python's standard library) so no external
database server is required.

All functions in this module open a short-lived connection, perform
one unit of work, and close the connection again. This keeps the
module simple and safe to import from a CLI tool that runs one
command per process invocation.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "attendance.db")


def get_connection():
    """Return a new SQLite connection with foreign keys enabled."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they do not already exist. Safe to call every run."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            class_section TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('P', 'A', 'L')),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE(student_id, date)
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# Student operations
# ---------------------------------------------------------------------

def add_student(roll_no, name, class_section=None):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO students (roll_no, name, class_section) VALUES (?, ?, ?)",
            (roll_no, name, class_section),
        )
        conn.commit()
        return True, "Student added successfully."
    except sqlite3.IntegrityError:
        return False, f"A student with roll number '{roll_no}' already exists."
    finally:
        conn.close()


def remove_student(roll_no):
    conn = get_connection()
    cur = conn.execute("DELETE FROM students WHERE roll_no = ?", (roll_no,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    return deleted > 0


def list_students():
    conn = get_connection()
    rows = conn.execute(
        "SELECT roll_no, name, class_section FROM students ORDER BY roll_no"
    ).fetchall()
    conn.close()
    return rows


def get_student_by_roll(roll_no):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM students WHERE roll_no = ?", (roll_no,)
    ).fetchone()
    conn.close()
    return row


# ---------------------------------------------------------------------
# Attendance operations
# ---------------------------------------------------------------------

def mark_attendance(roll_no, date, status):
    """
    status must be one of 'P' (present), 'A' (absent), 'L' (late).
    If a record for this student+date already exists, it is updated
    (so re-marking attendance corrects mistakes instead of failing).
    """
    student = get_student_by_roll(roll_no)
    if student is None:
        return False, f"No student found with roll number '{roll_no}'."

    conn = get_connection()
    conn.execute(
        """
        INSERT INTO attendance (student_id, date, status)
        VALUES (?, ?, ?)
        ON CONFLICT(student_id, date)
        DO UPDATE SET status = excluded.status
        """,
        (student["id"], date, status),
    )
    conn.commit()
    conn.close()
    return True, "Attendance recorded."


def get_attendance_by_date(date):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT s.roll_no, s.name, s.class_section, a.status
        FROM students s
        LEFT JOIN attendance a ON a.student_id = s.id AND a.date = ?
        ORDER BY s.roll_no
        """,
        (date,),
    ).fetchall()
    conn.close()
    return rows


def get_attendance_by_student(roll_no):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT a.date, a.status
        FROM attendance a
        JOIN students s ON s.id = a.student_id
        WHERE s.roll_no = ?
        ORDER BY a.date
        """,
        (roll_no,),
    ).fetchall()
    conn.close()
    return rows


def get_all_dates():
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT date FROM attendance ORDER BY date").fetchall()
    conn.close()
    return [r["date"] for r in rows]


def get_summary_report():
    """
    Returns, for every student: total days marked, present count,
    absent count, late count, and attendance percentage
    (present + late counted as attended).
    """
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            s.roll_no,
            s.name,
            s.class_section,
            COUNT(a.id) AS total_marked,
            SUM(CASE WHEN a.status = 'P' THEN 1 ELSE 0 END) AS present_count,
            SUM(CASE WHEN a.status = 'A' THEN 1 ELSE 0 END) AS absent_count,
            SUM(CASE WHEN a.status = 'L' THEN 1 ELSE 0 END) AS late_count
        FROM students s
        LEFT JOIN attendance a ON a.student_id = s.id
        GROUP BY s.id
        ORDER BY s.roll_no
        """
    ).fetchall()
    conn.close()

    report = []
    for r in rows:
        total = r["total_marked"] or 0
        present = r["present_count"] or 0
        late = r["late_count"] or 0
        absent = r["absent_count"] or 0
        pct = round(((present + late) / total) * 100, 2) if total > 0 else 0.0
        report.append({
            "roll_no": r["roll_no"],
            "name": r["name"],
            "class_section": r["class_section"],
            "total_marked": total,
            "present": present,
            "absent": absent,
            "late": late,
            "percentage": pct,
        })
    return report
