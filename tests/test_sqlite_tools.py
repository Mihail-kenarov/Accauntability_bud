import json
from unittest.mock import patch

import pytest


@pytest.fixture
def tmp_db(tmp_path):
    db_path = str(tmp_path / "habits.db")
    with patch("agent.tools.sqlite_tools.DB_PATH", db_path):
        from agent.tools.sqlite_tools import init_db

        init_db()
        yield db_path


def test_get_plan_when_none_exists(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import get_daily_plan

        assert get_daily_plan.invoke("2026-04-30") == "No plan found"


def test_save_and_get_plan(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import get_daily_plan, save_daily_plan

        result = save_daily_plan.invoke(
            {
                "date": "2026-04-30",
                "plan_text": "Morning: gym",
                "calendar_snapshot": "",
            }
        )

        assert result == "saved"
        assert "gym" in get_daily_plan.invoke("2026-04-30")


def test_save_plan_overwrites(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import get_daily_plan, save_daily_plan

        save_daily_plan.invoke(
            {
                "date": "2026-04-30",
                "plan_text": "old plan",
                "calendar_snapshot": "",
            }
        )
        save_daily_plan.invoke(
            {
                "date": "2026-04-30",
                "plan_text": "new plan",
                "calendar_snapshot": "",
            }
        )

        assert get_daily_plan.invoke("2026-04-30") == "new plan"


def test_save_and_get_daily_tasks(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import get_daily_plan, get_daily_tasks, save_daily_tasks

        result = save_daily_tasks.invoke(
            {
                "date": "2026-04-30",
                "tasks_json": json.dumps(
                    [
                        {
                            "title": "Study NLP assignment",
                            "subtasks": [
                                {"title": "Review lecture notes", "completed": False},
                                {"title": "Draft model comparison", "completed": True},
                            ],
                        }
                    ]
                ),
                "calendar_snapshot": "",
            }
        )
        tasks = json.loads(get_daily_tasks.invoke({"date": "2026-04-30"}))["tasks"]

        assert result == "saved"
        assert tasks[0]["title"] == "Study NLP assignment"
        assert tasks[0]["completed"] is False
        assert tasks[0]["subtasks"] == []
        assert tasks[1]["title"] == "Review lecture notes"
        assert tasks[1]["subtasks"] == []
        assert tasks[2]["title"] == "Draft model comparison"
        assert tasks[2]["completed"] is True
        assert "Draft model comparison" in get_daily_plan.invoke("2026-04-30")


def test_save_daily_tasks_overwrites_existing_structure(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import get_daily_tasks, save_daily_tasks

        save_daily_tasks.invoke(
            {
                "date": "2026-04-30",
                "tasks_json": json.dumps(
                    [{"title": "Old task", "subtasks": [{"title": "Old subtask"}]}]
                ),
            }
        )
        save_daily_tasks.invoke(
            {
                "date": "2026-04-30",
                "tasks_json": json.dumps(
                    [{"title": "New task", "subtasks": [{"title": "New subtask"}]}]
                ),
            }
        )
        tasks = json.loads(get_daily_tasks.invoke({"date": "2026-04-30"}))["tasks"]

        assert len(tasks) == 2
        assert tasks[0]["title"] == "New task"
        assert tasks[1]["title"] == "New subtask"
        assert tasks[1]["subtasks"] == []


def test_update_daily_task_completion(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import (
            get_daily_tasks,
            save_daily_tasks,
            set_daily_task_completion,
        )

        save_daily_tasks.invoke(
            {
                "date": "2026-04-30",
                "tasks_json": json.dumps(
                    [{"title": "Ship app"}, {"title": "Run tests"}]
                ),
            }
        )
        tasks = json.loads(get_daily_tasks.invoke({"date": "2026-04-30"}))["tasks"]
        task_id = tasks[0]["id"]

        assert set_daily_task_completion.invoke(
            {"task_id": task_id, "completed": True}
        ) == "updated"

        updated = json.loads(get_daily_tasks.invoke({"date": "2026-04-30"}))["tasks"]
        assert updated[0]["completed"] is True
        assert updated[1]["completed"] is False


def test_log_habit_and_update_streaks(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import (
            get_habit_streaks,
            log_habit,
            update_habit_streaks,
        )

        log_result = log_habit.invoke(
            {
                "date": "2026-04-30",
                "habit_name": "training",
                "completed": True,
                "notes": "",
            }
        )
        update_habit_streaks.invoke(json.dumps({"training": True}))
        streaks = json.loads(get_habit_streaks.invoke({}))

        assert log_result == "logged"
        assert streaks["training"]["current_streak"] == 1
        assert streaks["training"]["longest_streak"] == 1
        assert streaks["training"]["completion_rate"] == 1.0


def test_streak_resets_on_miss(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import (
            get_habit_streaks,
            log_habit,
            update_habit_streaks,
        )

        log_habit.invoke(
            {
                "date": "2026-04-29",
                "habit_name": "training",
                "completed": True,
                "notes": "",
            }
        )
        update_habit_streaks.invoke(json.dumps({"training": True}))
        log_habit.invoke(
            {
                "date": "2026-04-30",
                "habit_name": "training",
                "completed": False,
                "notes": "",
            }
        )
        update_habit_streaks.invoke(json.dumps({"training": False}))
        streaks = json.loads(get_habit_streaks.invoke({}))

        assert streaks["training"]["current_streak"] == 0
        assert streaks["training"]["longest_streak"] == 1
        assert streaks["training"]["total_completed"] == 1
        assert streaks["training"]["total_logged"] == 2


def test_get_streaks_empty(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import get_habit_streaks

        assert get_habit_streaks.invoke({}) == "No habits tracked yet."
