import json
from unittest.mock import MagicMock, patch

from mcp_servers.google_calendar_server import (
    _create_calendar_event,
    _delete_calendar_event,
    _list_calendar_events,
    _update_calendar_event,
)


def _mock_service(events):
    service = MagicMock()
    service.events.return_value.list.return_value.execute.return_value = {"items": events}
    service.events.return_value.insert.return_value.execute.return_value = {
        "id": "new-event-1",
        "summary": "Training",
        "htmlLink": "https://calendar.google.com/event?eid=new-event-1",
    }
    service.events.return_value.patch.return_value.execute.return_value = {
        "id": "event-1",
        "summary": "Updated Training",
    }
    service.events.return_value.delete.return_value.execute.return_value = {}
    return service


def test_returns_events_as_json():
    events = [
        {
            "id": "event-1",
            "summary": "Lecture",
            "start": {"dateTime": "2026-04-30T09:00:00Z"},
            "end": {"dateTime": "2026-04-30T11:00:00Z"},
        }
    ]

    with patch(
        "mcp_servers.google_calendar_server.get_calendar_service",
        return_value=_mock_service(events),
    ):
        result = _list_calendar_events("2026-04-30")

    parsed = json.loads(result)
    assert parsed[0]["event_id"] == "event-1"
    assert parsed[0]["title"] == "Lecture"
    assert parsed[0]["start"] == "2026-04-30T09:00:00Z"


def test_returns_message_when_no_events():
    with patch(
        "mcp_servers.google_calendar_server.get_calendar_service",
        return_value=_mock_service([]),
    ):
        result = _list_calendar_events("2026-04-30")

    assert result == "No events found"


def test_create_event_returns_id_and_link():
    with patch(
        "mcp_servers.google_calendar_server.get_calendar_service",
        return_value=_mock_service([]),
    ):
        result = _create_calendar_event(
            title="Training",
            start="2026-04-30T15:00:00+02:00",
            end="2026-04-30T16:00:00+02:00",
            description="BJJ session",
        )

    parsed = json.loads(result)
    assert parsed["event_id"] == "new-event-1"
    assert parsed["title"] == "Training"
    assert "calendar.google.com" in parsed["link"]


def test_update_event_returns_updated_event():
    with patch(
        "mcp_servers.google_calendar_server.get_calendar_service",
        return_value=_mock_service([]),
    ):
        result = _update_calendar_event(
            event_id="event-1",
            title="Updated Training",
            start=None,
            end=None,
            description=None,
        )

    parsed = json.loads(result)
    assert parsed["event_id"] == "event-1"
    assert parsed["title"] == "Updated Training"


def test_delete_event_returns_deleted():
    with patch(
        "mcp_servers.google_calendar_server.get_calendar_service",
        return_value=_mock_service([]),
    ):
        result = _delete_calendar_event("event-1")

    assert result == "deleted"
