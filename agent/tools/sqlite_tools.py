import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from langchain_core.tools import tool


DB_PATH = os.getenv("DB_PATH", "db/habits.db")


def get_connection() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    connection = get_connection()
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS habit_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            habit_name  TEXT NOT NULL,
            completed   INTEGER NOT NULL,
            notes       TEXT,
            logged_at   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS daily_plans (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            date              TEXT NOT NULL UNIQUE,
            plan_text         TEXT NOT NULL,
            created_at        TEXT NOT NULL,
            calendar_snapshot TEXT
        );

        CREATE TABLE IF NOT EXISTS habit_streaks (
            habit_name      TEXT PRIMARY KEY,
            current_streak  INTEGER DEFAULT 0,
            longest_streak  INTEGER DEFAULT 0,
            total_completed INTEGER DEFAULT 0,
            total_logged    INTEGER DEFAULT 0,
            last_updated    TEXT
        );
        """
    )
    connection.commit()
    connection.close()


@tool
def get_daily_plan(date: str) -> str:
    """Get the saved daily plan for a date in YYYY-MM-DD format."""
    init_db()
    connection = get_connection()
    row = connection.execute(
        "SELECT plan_text FROM daily_plans WHERE date = ?",
        (date,),
    ).fetchone()
    connection.close()
    return row["plan_text"] if row else "No plan found"


@tool
def save_daily_plan(date: str, plan_text: str, calendar_snapshot: str = "") -> str:
    """Save or overwrite the daily plan for a date in YYYY-MM-DD format."""
    init_db()
    connection = get_connection()
    connection.execute(
        """
        INSERT INTO daily_plans (date, plan_text, created_at, calendar_snapshot)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            plan_text = excluded.plan_text,
            created_at = excluded.created_at,
            calendar_snapshot = excluded.calendar_snapshot
        """,
        (
            date,
            plan_text,
            datetime.now().isoformat(timespec="seconds"),
            calendar_snapshot,
        ),
    )
    connection.commit()
    connection.close()
    return "saved"


@tool
def log_habit(date: str, habit_name: str, completed: bool, notes: str = "") -> str:
    """Log whether a habit was completed on a date in YYYY-MM-DD format."""
    init_db()
    connection = get_connection()
    connection.execute(
        """
        INSERT INTO habit_logs (date, habit_name, completed, notes, logged_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            date,
            habit_name,
            1 if completed else 0,
            notes,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    connection.commit()
    connection.close()
    return "logged"


@tool
def get_habit_streaks() -> str:
    """Return all habit streaks as JSON."""
    init_db()
    connection = get_connection()
    rows = connection.execute("SELECT * FROM habit_streaks").fetchall()
    connection.close()
    if not rows:
        return "No habits tracked yet."

    result = {}
    for row in rows:
        total_logged = row["total_logged"]
        completion_rate = (
            round(row["total_completed"] / total_logged, 2) if total_logged else 0.0
        )
        result[row["habit_name"]] = {
            "current_streak": row["current_streak"],
            "longest_streak": row["longest_streak"],
            "total_completed": row["total_completed"],
            "total_logged": total_logged,
            "completion_rate": completion_rate,
        }
    return json.dumps(result)


@tool
def update_habit_streaks(completions_json: str) -> str:
    """Update streaks from a JSON object like {"training": true, "morning_read": false}."""
    init_db()
    completions = json.loads(completions_json)
    connection = get_connection()
    now = datetime.now().isoformat(timespec="seconds")
    result = {}

    for habit_name, completed in completions.items():
        completed = bool(completed)
        row = connection.execute(
            "SELECT * FROM habit_streaks WHERE habit_name = ?",
            (habit_name,),
        ).fetchone()

        if row:
            current_streak = row["current_streak"] + 1 if completed else 0
            longest_streak = max(row["longest_streak"], current_streak)
            total_completed = row["total_completed"] + (1 if completed else 0)
            total_logged = row["total_logged"] + 1
            connection.execute(
                """
                UPDATE habit_streaks
                SET current_streak = ?,
                    longest_streak = ?,
                    total_completed = ?,
                    total_logged = ?,
                    last_updated = ?
                WHERE habit_name = ?
                """,
                (
                    current_streak,
                    longest_streak,
                    total_completed,
                    total_logged,
                    now,
                    habit_name,
                ),
            )
        else:
            current_streak = 1 if completed else 0
            longest_streak = current_streak
            connection.execute(
                """
                INSERT INTO habit_streaks (
                    habit_name,
                    current_streak,
                    longest_streak,
                    total_completed,
                    total_logged,
                    last_updated
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    habit_name,
                    current_streak,
                    longest_streak,
                    1 if completed else 0,
                    1,
                    now,
                ),
            )

        result[habit_name] = current_streak

    connection.commit()
    connection.close()
    return json.dumps(result)
