import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

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

        CREATE TABLE IF NOT EXISTS daily_tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            title       TEXT NOT NULL,
            completed   INTEGER NOT NULL DEFAULT 0,
            sort_order  INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS daily_subtasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id     INTEGER NOT NULL,
            title       TEXT NOT NULL,
            completed   INTEGER NOT NULL DEFAULT 0,
            sort_order  INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL,
            FOREIGN KEY(task_id) REFERENCES daily_tasks(id) ON DELETE CASCADE
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
    _flatten_existing_subtasks(connection)
    connection.commit()
    connection.close()


def _flatten_existing_subtasks(connection: sqlite3.Connection) -> None:
    subtask_rows = connection.execute(
        """
        SELECT
            daily_subtasks.id,
            daily_subtasks.task_id,
            daily_subtasks.title,
            daily_subtasks.completed,
            daily_subtasks.sort_order,
            daily_subtasks.created_at,
            daily_tasks.date,
            daily_tasks.sort_order AS task_sort_order
        FROM daily_subtasks
        JOIN daily_tasks ON daily_tasks.id = daily_subtasks.task_id
        ORDER BY daily_tasks.date, daily_tasks.sort_order, daily_subtasks.sort_order
        """
    ).fetchall()
    if not subtask_rows:
        return

    parent_ids = sorted({row["task_id"] for row in subtask_rows})
    placeholders = ",".join("?" for _ in parent_ids)
    connection.execute(
        f"UPDATE daily_tasks SET sort_order = sort_order * 100 WHERE id IN ({placeholders})",
        parent_ids,
    )

    for row in subtask_rows:
        connection.execute(
            """
            INSERT INTO daily_tasks (date, title, completed, sort_order, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                row["date"],
                row["title"],
                row["completed"],
                (row["task_sort_order"] * 100) + row["sort_order"] + 1,
                row["created_at"],
            ),
        )

    connection.execute("DELETE FROM daily_subtasks")


def _normalize_daily_tasks(tasks_json: str) -> list[dict[str, Any]]:
    parsed = json.loads(tasks_json)
    if isinstance(parsed, dict):
        parsed = parsed.get("tasks", [])
    if not isinstance(parsed, list):
        raise ValueError("tasks_json must be a JSON list or an object with a tasks list.")

    tasks = []
    for task_index, raw_task in enumerate(parsed):
        if isinstance(raw_task, str):
            raw_task = {"title": raw_task, "subtasks": []}
        if not isinstance(raw_task, dict):
            continue

        title = str(raw_task.get("title", "")).strip()
        if not title:
            continue

        raw_subtasks = raw_task.get("subtasks", [])

        tasks.append(
            {
                "title": title,
                "completed": bool(raw_task.get("completed", False)),
                "sort_order": int(raw_task.get("sort_order", task_index * 100)),
                "subtasks": [],
            }
        )
        if isinstance(raw_subtasks, list):
            for subtask_index, raw_subtask in enumerate(raw_subtasks):
                if isinstance(raw_subtask, str):
                    raw_subtask = {"title": raw_subtask}
                if not isinstance(raw_subtask, dict):
                    continue

                subtask_title = str(raw_subtask.get("title", "")).strip()
                if not subtask_title:
                    continue
                tasks.append(
                    {
                        "title": subtask_title,
                        "completed": bool(raw_subtask.get("completed", False)),
                        "sort_order": (task_index * 100) + subtask_index + 1,
                        "subtasks": [],
                    }
                )
    return tasks


def _tasks_to_plan_text(tasks: list[dict[str, Any]]) -> str:
    lines = []
    for task in tasks:
        lines.append(str(task["title"]))
        for subtask in task.get("subtasks", []):
            lines.append(f"  - {subtask['title']}")
    return "\n".join(lines)


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
def get_daily_tasks(date: str) -> str:
    """Get structured daily tasks and subtasks for a date in YYYY-MM-DD format."""
    init_db()
    connection = get_connection()
    task_rows = connection.execute(
        """
        SELECT id, date, title, completed, sort_order
        FROM daily_tasks
        WHERE date = ?
        ORDER BY sort_order, id
        """,
        (date,),
    ).fetchall()
    if not task_rows:
        connection.close()
        return "No tasks found"

    task_ids = [row["id"] for row in task_rows]
    placeholders = ",".join("?" for _ in task_ids)
    subtask_rows = connection.execute(
        f"""
        SELECT id, task_id, title, completed, sort_order
        FROM daily_subtasks
        WHERE task_id IN ({placeholders})
        ORDER BY sort_order, id
        """,
        task_ids,
    ).fetchall()
    connection.close()

    subtasks_by_task: dict[int, list[dict[str, Any]]] = {}
    for row in subtask_rows:
        subtasks_by_task.setdefault(row["task_id"], []).append(
            {
                "id": row["id"],
                "title": row["title"],
                "completed": bool(row["completed"]),
                "sort_order": row["sort_order"],
            }
        )

    tasks = [
        {
            "id": row["id"],
            "date": row["date"],
            "title": row["title"],
            "completed": bool(row["completed"]),
            "sort_order": row["sort_order"],
            "subtasks": subtasks_by_task.get(row["id"], []),
        }
        for row in task_rows
    ]
    return json.dumps({"date": date, "tasks": tasks})


@tool
def save_daily_tasks(
    date: str,
    tasks_json: str,
    calendar_snapshot: str = "",
) -> str:
    """Save or overwrite structured daily tasks for a date.

    tasks_json should be JSON like:
    [{"title": "Study NLP", "completed": false}]
    If subtasks are provided, they are flattened into regular todo tasks.
    """
    init_db()
    tasks = _normalize_daily_tasks(tasks_json)
    now = datetime.now().isoformat(timespec="seconds")
    plan_text = _tasks_to_plan_text(tasks)

    connection = get_connection()
    old_task_rows = connection.execute(
        "SELECT id FROM daily_tasks WHERE date = ?",
        (date,),
    ).fetchall()
    old_task_ids = [row["id"] for row in old_task_rows]
    if old_task_ids:
        placeholders = ",".join("?" for _ in old_task_ids)
        connection.execute(
            f"DELETE FROM daily_subtasks WHERE task_id IN ({placeholders})",
            old_task_ids,
        )
    connection.execute("DELETE FROM daily_tasks WHERE date = ?", (date,))

    connection.execute(
        """
        INSERT INTO daily_plans (date, plan_text, created_at, calendar_snapshot)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            plan_text = excluded.plan_text,
            created_at = excluded.created_at,
            calendar_snapshot = excluded.calendar_snapshot
        """,
        (date, plan_text, now, calendar_snapshot),
    )

    for task in tasks:
        cursor = connection.execute(
            """
            INSERT INTO daily_tasks (date, title, completed, sort_order, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                date,
                task["title"],
                1 if task["completed"] else 0,
                task["sort_order"],
                now,
            ),
        )
        task_id = cursor.lastrowid
        for subtask in task["subtasks"]:
            connection.execute(
                """
                INSERT INTO daily_subtasks (
                    task_id,
                    title,
                    completed,
                    sort_order,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    subtask["title"],
                    1 if subtask["completed"] else 0,
                    subtask["sort_order"],
                    now,
                ),
            )

    connection.commit()
    connection.close()
    return "saved"


@tool
def set_daily_task_completion(task_id: int, completed: bool) -> str:
    """Set completion for one top-level daily task."""
    init_db()
    connection = get_connection()
    connection.execute(
        "UPDATE daily_tasks SET completed = ? WHERE id = ?",
        (1 if completed else 0, task_id),
    )
    connection.commit()
    connection.close()
    return "updated"


@tool
def set_daily_subtask_completion(subtask_id: int, completed: bool) -> str:
    """Set completion for one daily subtask."""
    init_db()
    connection = get_connection()
    connection.execute(
        "UPDATE daily_subtasks SET completed = ? WHERE id = ?",
        (1 if completed else 0, subtask_id),
    )
    connection.commit()
    connection.close()
    return "updated"


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
