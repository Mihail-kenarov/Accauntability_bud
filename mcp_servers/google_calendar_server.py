import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from fastmcp import FastMCP
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


mcp = FastMCP("Google Calendar")

_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def get_calendar_service():
    creds_path = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials/credentials.json"))
    token_path = Path(os.getenv("GOOGLE_TOKEN_PATH", "credentials/token.json"))

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                creds = None

        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), _SCOPES)
            creds = flow.run_local_server(port=0, prompt="consent")

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("calendar", "v3", credentials=creds)


def _calendar_id() -> str:
    return os.getenv("GOOGLE_CALENDAR_ID", "primary")


def _local_timezone() -> ZoneInfo:
    return ZoneInfo(os.getenv("APP_TIMEZONE", "Europe/Amsterdam"))


def _normalize_event_datetime(value: str) -> str:
    cleaned = value.strip().replace(" ", "T")
    if cleaned.endswith("Z"):
        cleaned = f"{cleaned[:-1]}+00:00"

    parsed = datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_local_timezone())

    return parsed.isoformat(timespec="seconds")


def _list_calendar_events(date: str) -> str:
    service = get_calendar_service()
    result = (
        service.events()
        .list(
            calendarId=_calendar_id(),
            timeMin=f"{date}T00:00:00Z",
            timeMax=f"{date}T23:59:59Z",
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = [
        {
            "event_id": event["id"],
            "title": event.get("summary", "Untitled"),
            "start": event["start"].get("dateTime", event["start"].get("date")),
            "end": event["end"].get("dateTime", event["end"].get("date")),
        }
        for event in result.get("items", [])
    ]
    return json.dumps(events) if events else "No events found"


def _create_calendar_event(
    title: str,
    start: str,
    end: str,
    description: str = "",
) -> str:
    service = get_calendar_service()
    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": _normalize_event_datetime(start)},
        "end": {"dateTime": _normalize_event_datetime(end)},
    }
    created = (
        service.events()
        .insert(calendarId=_calendar_id(), body=event)
        .execute()
    )
    return json.dumps(
        {
            "event_id": created["id"],
            "title": created.get("summary", title),
            "link": created.get("htmlLink", ""),
        }
    )


def _update_calendar_event(
    event_id: str,
    title: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    service = get_calendar_service()
    patch_body = {}
    if title is not None:
        patch_body["summary"] = title
    if description is not None:
        patch_body["description"] = description
    if start is not None:
        patch_body["start"] = {"dateTime": _normalize_event_datetime(start)}
    if end is not None:
        patch_body["end"] = {"dateTime": _normalize_event_datetime(end)}

    updated = (
        service.events()
        .patch(calendarId=_calendar_id(), eventId=event_id, body=patch_body)
        .execute()
    )
    return json.dumps(
        {
            "event_id": updated["id"],
            "title": updated.get("summary", title or ""),
        }
    )


def _delete_calendar_event(event_id: str) -> str:
    service = get_calendar_service()
    service.events().delete(calendarId=_calendar_id(), eventId=event_id).execute()
    return "deleted"


@mcp.tool()
def list_calendar_events(date: str) -> str:
    """List Google Calendar events for a date in YYYY-MM-DD format."""
    return _list_calendar_events(date)


@mcp.tool()
def create_calendar_event(
    title: str,
    start: str,
    end: str,
    description: str = "",
) -> str:
    """Create a Google Calendar event. Start/end may be ISO datetimes or YYYY-MM-DD HH:MM local time."""
    return _create_calendar_event(title, start, end, description)


@mcp.tool()
def update_calendar_event(
    event_id: str,
    title: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """Update an existing Google Calendar event by event_id. Start/end may be ISO datetimes or YYYY-MM-DD HH:MM local time."""
    return _update_calendar_event(event_id, title, start, end, description)


@mcp.tool()
def delete_calendar_event(event_id: str) -> str:
    """Delete a Google Calendar event by event_id after explicit confirmation."""
    return _delete_calendar_event(event_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
