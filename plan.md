# Daily Life Coach Agent — Implementation Plan

**Goal:** Build a conversational life coach web agent that plans your day using Google Calendar, learns your habits via ChromaDB, tracks consistency via SQLite, and runs on a local Ollama LLM with a Streamlit UI.

**Architecture:** LangChain `create_tool_calling_agent` wraps a `ChatOllama` (ministral-3:8b) with tools from two sources: Google Calendar tools loaded from a local MCP server via `langchain-mcp-adapters`, and native LangChain tool calls for ChromaDB + SQLite. Streamlit renders the chat and a sidebar with today's streaks and plan. Fact extraction runs after every user message as a background step outside the agent loop.

**Tech Stack:** Python 3.11+, langchain + langchain-ollama, langchain-mcp-adapters, fastmcp, chromadb, sentence-transformers, google-api-python-client, sqlite3, streamlit, pytest

**Build order:** project setup → LangChain agent core → Google Calendar MCP server → ChromaDB tools → SQLite habit tracker → wire MCP + local tools into Streamlit UI

**Tool boundary decision:** Google Calendar is exposed through MCP because it is an external system integration that may later be reused by other agents/apps. ChromaDB and SQLite stay as native LangChain tool calls because they are local project-specific memory/state backends.

---

## Current Progress

**Last updated:** 2026-05-08

| Area | Status | Notes |
|---|---|---|
| GitHub repo | Done | Repo is connected and tracking `main` / `origin/main`. |
| Python environment | Done | `.venv` created with Python 3.12 and dependencies installed. `.venv/` is ignored by Git. |
| Project scaffolding | Done | Base package folders, env templates, ignore rules, and requirements are in place. |
| LangChain agent core | Done | `agent/agent.py` and `agent/prompts.py` exist. Live Ollama smoke test is still pending. |
| Google Calendar backend | Done | MCP server supports list/create/update/delete event operations. OAuth token exists and real Calendar read succeeded. |
| ChromaDB memory tools | Done | User facts and conversation logs can be stored/retrieved. Tests use isolated Chroma stores. |
| Fact extraction | Done | Best-effort LLM fact extraction module exists and is unit tested with mocked extraction. Live Ollama extraction test is pending. |
| SQLite habit tracker | Done | Daily plans, habit logs, and streak tracking are implemented and tested. |
| Streamlit web app | Not started | `app.py` still needs to be created. This is what will make the project runnable as a web app. |
| End-to-end agent wiring | Not started | Calendar MCP tools, Chroma tools, SQLite tools, prompt, and UI still need to be wired together. |
| Mobile/browser testing | Not started | Depends on Streamlit app implementation. |
| Deployment/demo | Not started | Optional later step for assignment demo. |

**Current test status:** `20 passed`

**Implementation note:** `sentence-transformers` was removed from `requirements.txt` because it pulled a very large CUDA/PyTorch dependency stack. ChromaDB remains usable with its lighter local ONNX embedding path.

---

## Prerequisites (do before Task 1)

1. Install [Ollama](https://ollama.com) and pull the model:
   ```bash
   ollama pull ministral-3:8b
   ```
2. Create a Google Cloud project, enable the Google Calendar API, create an OAuth 2.0 Desktop credential, and download `credentials.json` — place it at `credentials/credentials.json`. [Guide](https://developers.google.com/calendar/api/quickstart/python)
3. Because this project creates and edits events, use a writable Calendar scope (`https://www.googleapis.com/auth/calendar.events`) and delete any old `credentials/token.json` created with read-only scopes before retesting OAuth.

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `agent/__init__.py`
- Create: `agent/tools/__init__.py`
- Create: `mcp_servers/__init__.py`
- Create: `tests/__init__.py`
- Create: `credentials/.gitignore`

- [ ] **Step 1: Create folder structure**

```bash
mkdir -p agent/tools mcp_servers tests db credentials
touch agent/__init__.py agent/tools/__init__.py mcp_servers/__init__.py tests/__init__.py
```

- [ ] **Step 2: Write requirements.txt**

```
langchain==0.3.25
langchain-community==0.3.23
langchain-ollama==0.3.2
langchain-mcp-adapters==0.1.7
fastmcp==2.3.4
chromadb==0.6.3
sentence-transformers==4.1.0
google-api-python-client==2.169.0
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.2.1
streamlit==1.45.0
python-dotenv==1.1.0
pydantic==2.11.4
pytest==8.3.5
pytest-mock==3.14.0
```

- [ ] **Step 3: Write .env.example**

```
OLLAMA_MODEL=ministral-3:8b
GOOGLE_CREDENTIALS_PATH=credentials/credentials.json
GOOGLE_TOKEN_PATH=credentials/token.json
GOOGLE_CALENDAR_ID=primary
DB_PATH=db/habits.db
CHROMA_PATH=db/chroma
```

- [ ] **Step 4: Write .gitignore**

```
.env
credentials/credentials.json
credentials/token.json
db/
__pycache__/
.pytest_cache/
*.pyc
```

- [ ] **Step 5: Write credentials/.gitignore (keeps the folder but ignores secrets)**

```
credentials.json
token.json
```

- [ ] **Step 6: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without errors.

- [ ] **Step 7: Commit**

```bash
git init
git add requirements.txt .env.example .gitignore credentials/.gitignore agent/__init__.py agent/tools/__init__.py mcp_servers/__init__.py tests/__init__.py
git commit -m "feat: project scaffolding"
```

---

## Task 2: LangChain Agent Core (Ollama + System Prompt)

**Files:**
- Create: `agent/prompts.py`
- Create: `agent/agent.py`

### 2a — Prompts module

- [ ] **Step 1: Write agent/prompts.py**

```python
# agent/prompts.py
from datetime import datetime

def build_system_prompt() -> str:
    now = datetime.now()
    return (
        f"You are a personal life coach for a busy student. "
        f"You are direct, warm, and hold the user accountable without lecturing.\n\n"
        f"Today is {now.strftime('%Y-%m-%d')}. Current time: {now.strftime('%H:%M')}.\n\n"
        "You have MCP tools to read, create, update, and delete Google Calendar events. "
        "You also have local tools to create and edit daily plans, store and retrieve facts "
        "you learn about the user, log habits, and track streaks. "
        "Always use tools to ground your responses — never guess at the schedule or streaks.\n\n"
        "For day planning requests: list_calendar_events → retrieve_user_facts → retrieve_past_logs → get_habit_streaks → generate plan → save_daily_plan.\n"
        "For calendar writes: first propose the exact event changes; only call create_calendar_event, update_calendar_event, or delete_calendar_event after the user confirms.\n"
        "For check-ins or plan edits: get_daily_plan → list_calendar_events → retrieve_user_facts → respond or adjust.\n"
        "For evening reflections: get_daily_plan → get_habit_streaks → log_habit → update_habit_streaks → save_conversation_log → respond.\n"
        "For general conversation: respond helpfully; use tools when they give a grounded answer.\n\n"
        "Tone: direct, encouraging, honest. If the user is slipping on goals, say so clearly but kindly. "
        "End with one concrete suggestion."
    )
```

### 2b — Agent builder

- [ ] **Step 2: Write agent/agent.py**

```python
# agent/agent.py
import os
from langchain_ollama import ChatOllama
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

def build_agent(tools: list) -> AgentExecutor:
    model = os.getenv("OLLAMA_MODEL", "ministral-3:8b")
    llm = ChatOllama(model=model, temperature=0.3)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=8)
```

- [ ] **Step 3: Smoke-test the LLM connection**

```bash
python -c "
from langchain_ollama import ChatOllama
llm = ChatOllama(model='ministral-3:8b')
print(llm.invoke('Say hello in one word.').content)
"
```

Expected: a single word response like `Hello`.

- [ ] **Step 4: Commit**

```bash
git add agent/prompts.py agent/agent.py
git commit -m "feat: langchain agent core with system prompt"
```

---

## Task 3: Google Calendar MCP Server

**Files:**
- Create: `mcp_servers/google_calendar_server.py`
- Create: `agent/calendar_mcp.py`
- Create: `tests/test_google_calendar_mcp.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_google_calendar_mcp.py
import json
from unittest.mock import patch, MagicMock
from mcp_servers.google_calendar_server import (
    _list_calendar_events,
    _create_calendar_event,
    _update_calendar_event,
    _delete_calendar_event,
)

def _mock_service(events):
    svc = MagicMock()
    svc.events.return_value.list.return_value.execute.return_value = {"items": events}
    svc.events.return_value.insert.return_value.execute.return_value = {
        "id": "new-event-1",
        "summary": "Training",
        "htmlLink": "https://calendar.google.com/event?eid=new-event-1",
    }
    svc.events.return_value.patch.return_value.execute.return_value = {
        "id": "event-1",
        "summary": "Updated Training",
    }
    svc.events.return_value.delete.return_value.execute.return_value = {}
    return svc

def test_returns_events_as_json():
    events = [{
        "id": "event-1",
        "summary": "Lecture",
        "start": {"dateTime": "2026-04-30T09:00:00Z"},
        "end":   {"dateTime": "2026-04-30T11:00:00Z"},
    }]
    with patch("mcp_servers.google_calendar_server.get_calendar_service", return_value=_mock_service(events)):
        result = _list_calendar_events("2026-04-30")
    parsed = json.loads(result)
    assert parsed[0]["event_id"] == "event-1"
    assert parsed[0]["title"] == "Lecture"
    assert parsed[0]["start"] == "2026-04-30T09:00:00Z"

def test_returns_message_when_no_events():
    with patch("mcp_servers.google_calendar_server.get_calendar_service", return_value=_mock_service([])):
        result = _list_calendar_events("2026-04-30")
    assert result == "No events found"

def test_create_event_returns_id_and_link():
    with patch("mcp_servers.google_calendar_server.get_calendar_service", return_value=_mock_service([])):
        result = _create_calendar_event(
            title="Training",
            start="2026-04-30T15:00:00+02:00",
            end="2026-04-30T16:00:00+02:00",
            description="BJJ session",
        )
    parsed = json.loads(result)
    assert parsed["event_id"] == "new-event-1"
    assert "calendar.google.com" in parsed["link"]

def test_update_event_returns_updated_event():
    with patch("mcp_servers.google_calendar_server.get_calendar_service", return_value=_mock_service([])):
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
    with patch("mcp_servers.google_calendar_server.get_calendar_service", return_value=_mock_service([])):
        result = _delete_calendar_event("event-1")
    assert result == "deleted"
```

- [ ] **Step 2: Run test — verify it fails**

```bash
pytest tests/test_google_calendar_mcp.py -v
```

Expected: `ModuleNotFoundError: No module named 'mcp_servers.google_calendar_server'`

- [ ] **Step 3: Write mcp_servers/google_calendar_server.py**

```python
# mcp_servers/google_calendar_server.py
import json, os
from pathlib import Path
from typing import Optional
from fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
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
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), _SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return build("calendar", "v3", credentials=creds)

def _calendar_id() -> str:
    return os.getenv("GOOGLE_CALENDAR_ID", "primary")

def _list_calendar_events(date: str) -> str:
    service = get_calendar_service()
    result = service.events().list(
        calendarId=_calendar_id(),
        timeMin=f"{date}T00:00:00Z",
        timeMax=f"{date}T23:59:59Z",
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = [
        {
            "event_id": e["id"],
            "title": e.get("summary", "Untitled"),
            "start": e["start"].get("dateTime", e["start"].get("date")),
            "end":   e["end"].get("dateTime",   e["end"].get("date")),
        }
        for e in result.get("items", [])
    ]
    return json.dumps(events) if events else "No events found"

def _create_calendar_event(title: str, start: str, end: str, description: str = "") -> str:
    service = get_calendar_service()
    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start},
        "end": {"dateTime": end},
    }
    created = service.events().insert(calendarId=_calendar_id(), body=event).execute()
    return json.dumps({
        "event_id": created["id"],
        "title": created.get("summary", title),
        "link": created.get("htmlLink", ""),
    })

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
        patch_body["start"] = {"dateTime": start}
    if end is not None:
        patch_body["end"] = {"dateTime": end}
    updated = service.events().patch(
        calendarId=_calendar_id(),
        eventId=event_id,
        body=patch_body,
    ).execute()
    return json.dumps({
        "event_id": updated["id"],
        "title": updated.get("summary", title or ""),
    })

def _delete_calendar_event(event_id: str) -> str:
    service = get_calendar_service()
    service.events().delete(calendarId=_calendar_id(), eventId=event_id).execute()
    return "deleted"

@mcp.tool()
def list_calendar_events(date: str) -> str:
    """List Google Calendar events for a date in YYYY-MM-DD format. Returns JSON with event_id, title, start, and end."""
    return _list_calendar_events(date)

@mcp.tool()
def create_calendar_event(title: str, start: str, end: str, description: str = "") -> str:
    """Create a Google Calendar event. start and end must be ISO datetimes with timezone."""
    return _create_calendar_event(title, start, end, description)

@mcp.tool()
def update_calendar_event(
    event_id: str,
    title: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """Update an existing Google Calendar event by event_id. Only provided fields are changed."""
    return _update_calendar_event(event_id, title, start, end, description)

@mcp.tool()
def delete_calendar_event(event_id: str) -> str:
    """Delete a Google Calendar event by event_id. Use only after explicit user confirmation."""
    return _delete_calendar_event(event_id)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

- [ ] **Step 4: Write agent/calendar_mcp.py**

```python
# agent/calendar_mcp.py
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient

def build_calendar_mcp_client() -> MultiServerMCPClient:
    server_path = Path(__file__).resolve().parents[1] / "mcp_servers" / "google_calendar_server.py"
    return MultiServerMCPClient({
        "google_calendar": {
            "transport": "stdio",
            "command": "python",
            "args": [str(server_path)],
        }
    })
```

- [ ] **Step 5: Run test — verify it passes**

```bash
pytest tests/test_google_calendar_mcp.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Test OAuth flow manually (requires credentials.json)**

```bash
python -c "
from dotenv import load_dotenv; load_dotenv()
from mcp_servers.google_calendar_server import _list_calendar_events
from datetime import date
print(_list_calendar_events(date.today().isoformat()))
"
```

Expected: browser opens for auth on first run, then JSON list of today's events.

- [ ] **Step 7: Commit**

```bash
git add mcp_servers/google_calendar_server.py agent/calendar_mcp.py tests/test_google_calendar_mcp.py
git commit -m "feat: google calendar mcp server"
```

---

## Task 4: ChromaDB Tools

**Files:**
- Create: `agent/tools/chroma_tools.py`
- Create: `agent/fact_extractor.py`
- Create: `tests/test_chroma_tools.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_chroma_tools.py
import chromadb
import pytest
from unittest.mock import patch

@pytest.fixture
def ephemeral_client():
    return chromadb.EphemeralClient()

def test_store_user_fact(ephemeral_client):
    with patch("agent.tools.chroma_tools.get_chroma_client", return_value=ephemeral_client):
        from agent.tools.chroma_tools import store_user_fact
        result = store_user_fact.invoke({
            "fact": "User trains BJJ on Tuesdays",
            "fact_type": "schedule_pattern",
            "confidence": 0.9,
            "source": "test message"
        })
    assert result == "stored"

def test_store_fact_skips_low_confidence(ephemeral_client):
    with patch("agent.tools.chroma_tools.get_chroma_client", return_value=ephemeral_client):
        from agent.tools.chroma_tools import store_user_fact
        result = store_user_fact.invoke({
            "fact": "User maybe likes coffee",
            "fact_type": "preference",
            "confidence": 0.5,
            "source": "test"
        })
    assert result == "skipped_low_confidence"

def test_retrieve_user_facts(ephemeral_client):
    with patch("agent.tools.chroma_tools.get_chroma_client", return_value=ephemeral_client):
        from agent.tools.chroma_tools import store_user_fact, retrieve_user_facts
        store_user_fact.invoke({
            "fact": "User does BJJ on Tuesday evenings",
            "fact_type": "schedule_pattern",
            "confidence": 0.9,
            "source": "test"
        })
        result = retrieve_user_facts.invoke({"query": "training schedule", "k": 3})
    assert "BJJ" in result

def test_retrieve_facts_empty_collection(ephemeral_client):
    with patch("agent.tools.chroma_tools.get_chroma_client", return_value=ephemeral_client):
        from agent.tools.chroma_tools import retrieve_user_facts
        result = retrieve_user_facts.invoke({"query": "anything", "k": 3})
    assert result == "No facts stored yet."

def test_save_and_retrieve_conversation_log(ephemeral_client):
    with patch("agent.tools.chroma_tools.get_chroma_client", return_value=ephemeral_client):
        from agent.tools.chroma_tools import save_conversation_log, retrieve_past_logs
        save_conversation_log.invoke({
            "session_type": "evening_reflection",
            "summary": "User skipped training, ate 1800 kcal.",
            "habits_mentioned": ["training", "calories_on_target"]
        })
        result = retrieve_past_logs.invoke({"query": "skipped training", "n_days": 7})
    assert "skipped" in result
```

- [ ] **Step 2: Run test — verify it fails**

```bash
pytest tests/test_chroma_tools.py -v
```

Expected: `ModuleNotFoundError: No module named 'agent.tools.chroma_tools'`

- [ ] **Step 3: Write agent/tools/chroma_tools.py**

```python
# agent/tools/chroma_tools.py
import os, uuid, json
from datetime import datetime, timedelta
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from langchain_core.tools import tool

def get_chroma_client():
    path = os.getenv("CHROMA_PATH", "db/chroma")
    Path(path).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=path)

def _ef():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

def _col(client, name: str):
    return client.get_or_create_collection(name, embedding_function=_ef())

@tool
def store_user_fact(fact: str, fact_type: str, confidence: float, source: str) -> str:
    """Store a fact learned about the user. fact_type: goal/preference/schedule_pattern/constraint/habit"""
    if confidence < 0.7:
        return "skipped_low_confidence"

    client = get_chroma_client()
    col = _col(client, "user_facts")

    if col.count() > 0:
        existing = col.query(query_texts=[fact], n_results=1)
        if existing["distances"] and existing["distances"][0] and existing["distances"][0][0] < 0.15:
            return "duplicate_skipped"

    col.add(
        documents=[fact],
        metadatas=[{
            "fact_type": fact_type,
            "source": source[:200],
            "timestamp": datetime.now().isoformat(),
            "confidence": str(confidence),
        }],
        ids=[str(uuid.uuid4())],
    )
    return "stored"

@tool
def retrieve_user_facts(query: str, k: int = 5) -> str:
    """Retrieve facts about the user relevant to the query."""
    client = get_chroma_client()
    col = _col(client, "user_facts")
    if col.count() == 0:
        return "No facts stored yet."
    n = min(k, col.count())
    results = col.query(query_texts=[query], n_results=n)
    docs = results.get("documents", [[]])[0]
    return "\n".join(docs) if docs else "No relevant facts found."

@tool
def save_conversation_log(session_type: str, summary: str, habits_mentioned: list[str]) -> str:
    """Save a conversation session summary to long-term memory."""
    client = get_chroma_client()
    col = _col(client, "conversation_logs")
    col.add(
        documents=[summary],
        metadatas=[{
            "session_type": session_type,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "habits_mentioned": ",".join(habits_mentioned),
        }],
        ids=[str(uuid.uuid4())],
    )
    return "saved"

@tool
def retrieve_past_logs(query: str, n_days: int = 7) -> str:
    """Retrieve past conversation logs relevant to the query, within the last n_days."""
    client = get_chroma_client()
    col = _col(client, "conversation_logs")
    if col.count() == 0:
        return "No past logs found."

    cutoff = (datetime.now() - timedelta(days=n_days)).strftime("%Y-%m-%d")
    results = col.query(
        query_texts=[query],
        n_results=min(5, col.count()),
        where={"date": {"$gte": cutoff}},
    )
    docs = results.get("documents", [[]])[0]
    return "\n---\n".join(docs) if docs else "No relevant logs found."
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_chroma_tools.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Write agent/fact_extractor.py**

```python
# agent/fact_extractor.py
import json, os
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from agent.tools.chroma_tools import store_user_fact

_PROMPT = PromptTemplate.from_template(
    "Extract facts about the user's goals, habits, schedule, or preferences from this message.\n"
    "Return ONLY a JSON array. Each item: {{\"fact\": str, \"fact_type\": \"goal|preference|schedule_pattern|constraint|habit\", \"confidence\": 0.0-1.0}}\n"
    "Return [] if nothing to extract.\n\n"
    "Message: {message}\n\nJSON:"
)

def extract_and_store_facts(message: str) -> None:
    """Run after every user message. Extracts and stores facts silently."""
    model = os.getenv("OLLAMA_MODEL", "ministral-3:8b")
    llm = ChatOllama(model=model, temperature=0, format="json")
    try:
        result = (_PROMPT | llm).invoke({"message": message})
        facts = json.loads(result.content)
        for f in facts:
            if isinstance(f, dict) and "fact" in f:
                store_user_fact.invoke({
                    "fact": f["fact"],
                    "fact_type": f.get("fact_type", "preference"),
                    "confidence": float(f.get("confidence", 0.8)),
                    "source": message[:200],
                })
    except Exception:
        pass  # best-effort, never block the main flow
```

- [ ] **Step 6: Commit**

```bash
git add agent/tools/chroma_tools.py agent/fact_extractor.py tests/test_chroma_tools.py
git commit -m "feat: chromadb tools and fact extractor"
```

---

## Task 5: SQLite Habit Tracker

**Files:**
- Create: `agent/tools/sqlite_tools.py`
- Create: `tests/test_sqlite_tools.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_sqlite_tools.py
import pytest
from unittest.mock import patch

@pytest.fixture
def tmp_db(tmp_path):
    db = str(tmp_path / "test.db")
    with patch("agent.tools.sqlite_tools.DB_PATH", db):
        from agent.tools.sqlite_tools import init_db
        init_db()
        yield db

def test_get_plan_when_none_exists(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import get_daily_plan
        assert get_daily_plan.invoke("2026-04-30") == "No plan found"

def test_save_and_get_plan(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import save_daily_plan, get_daily_plan
        save_daily_plan.invoke({"date": "2026-04-30", "plan_text": "Morning: gym", "calendar_snapshot": ""})
        assert "gym" in get_daily_plan.invoke("2026-04-30")

def test_save_plan_overwrites(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import save_daily_plan, get_daily_plan
        save_daily_plan.invoke({"date": "2026-04-30", "plan_text": "old plan", "calendar_snapshot": ""})
        save_daily_plan.invoke({"date": "2026-04-30", "plan_text": "new plan", "calendar_snapshot": ""})
        assert get_daily_plan.invoke("2026-04-30") == "new plan"

def test_log_habit_and_update_streaks(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import log_habit, update_habit_streaks, get_habit_streaks
        import json
        log_habit.invoke({"date": "2026-04-30", "habit_name": "training", "completed": True, "notes": ""})
        update_habit_streaks.invoke(json.dumps({"training": True}))
        streaks = json.loads(get_habit_streaks.invoke({}))
        assert streaks["training"]["current_streak"] == 1

def test_streak_resets_on_miss(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import log_habit, update_habit_streaks, get_habit_streaks
        import json
        log_habit.invoke({"date": "2026-04-29", "habit_name": "training", "completed": True, "notes": ""})
        update_habit_streaks.invoke(json.dumps({"training": True}))
        log_habit.invoke({"date": "2026-04-30", "habit_name": "training", "completed": False, "notes": ""})
        update_habit_streaks.invoke(json.dumps({"training": False}))
        streaks = json.loads(get_habit_streaks.invoke({}))
        assert streaks["training"]["current_streak"] == 0
        assert streaks["training"]["longest_streak"] == 1

def test_get_streaks_empty(tmp_db):
    with patch("agent.tools.sqlite_tools.DB_PATH", tmp_db):
        from agent.tools.sqlite_tools import get_habit_streaks
        assert get_habit_streaks.invoke({}) == "No habits tracked yet."
```

- [ ] **Step 2: Run test — verify it fails**

```bash
pytest tests/test_sqlite_tools.py -v
```

Expected: `ModuleNotFoundError: No module named 'agent.tools.sqlite_tools'`

- [ ] **Step 3: Write agent/tools/sqlite_tools.py**

```python
# agent/tools/sqlite_tools.py
import sqlite3, json, os
from datetime import datetime
from pathlib import Path
from langchain_core.tools import tool

DB_PATH = os.getenv("DB_PATH", "db/habits.db")

def get_connection() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS habit_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            habit_name  TEXT NOT NULL,
            completed   INTEGER NOT NULL,
            notes       TEXT,
            logged_at   TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS daily_plans (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT NOT NULL UNIQUE,
            plan_text       TEXT NOT NULL,
            created_at      TEXT NOT NULL,
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
    """)
    conn.commit()
    conn.close()

@tool
def get_daily_plan(date: str) -> str:
    """Get the daily plan for a given date (YYYY-MM-DD). Returns plan text or 'No plan found'."""
    conn = get_connection()
    row = conn.execute("SELECT plan_text FROM daily_plans WHERE date = ?", (date,)).fetchone()
    conn.close()
    return row["plan_text"] if row else "No plan found"

@tool
def save_daily_plan(date: str, plan_text: str, calendar_snapshot: str = "") -> str:
    """Save or update (upsert) the daily plan for a given date."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO daily_plans (date, plan_text, created_at, calendar_snapshot) VALUES (?,?,?,?) "
        "ON CONFLICT(date) DO UPDATE SET plan_text=excluded.plan_text, created_at=excluded.created_at, calendar_snapshot=excluded.calendar_snapshot",
        (date, plan_text, datetime.now().isoformat(), calendar_snapshot),
    )
    conn.commit()
    conn.close()
    return "saved"

@tool
def log_habit(date: str, habit_name: str, completed: bool, notes: str = "") -> str:
    """Log a habit completion for a given date. habit_name: training / morning_read / calories_on_target"""
    conn = get_connection()
    conn.execute(
        "INSERT INTO habit_logs (date, habit_name, completed, notes, logged_at) VALUES (?,?,?,?,?)",
        (date, habit_name, 1 if completed else 0, notes, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return "logged"

@tool
def get_habit_streaks(dummy: dict = {}) -> str:
    """Get current streaks for all tracked habits as a JSON string."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM habit_streaks").fetchall()
    conn.close()
    if not rows:
        return "No habits tracked yet."
    result = {}
    for row in rows:
        total = row["total_logged"]
        result[row["habit_name"]] = {
            "current_streak": row["current_streak"],
            "longest_streak": row["longest_streak"],
            "completion_rate": round(row["total_completed"] / total, 2) if total else 0.0,
        }
    return json.dumps(result)

@tool
def update_habit_streaks(completions_json: str) -> str:
    """Update habit streaks. Pass JSON string: '{\"training\": true, \"morning_read\": false}'"""
    completions = json.loads(completions_json)
    conn = get_connection()
    now = datetime.now().isoformat()
    result = {}
    for habit, completed in completions.items():
        row = conn.execute("SELECT * FROM habit_streaks WHERE habit_name = ?", (habit,)).fetchone()
        if row:
            current = (row["current_streak"] + 1) if completed else 0
            longest = max(row["longest_streak"], current)
            conn.execute(
                "UPDATE habit_streaks SET current_streak=?, longest_streak=?, total_completed=?, total_logged=?, last_updated=? WHERE habit_name=?",
                (current, longest, row["total_completed"] + (1 if completed else 0), row["total_logged"] + 1, now, habit),
            )
        else:
            current = 1 if completed else 0
            conn.execute(
                "INSERT INTO habit_streaks (habit_name, current_streak, longest_streak, total_completed, total_logged, last_updated) VALUES (?,?,?,?,?,?)",
                (habit, current, current, 1 if completed else 0, 1, now),
            )
        result[habit] = current
    conn.commit()
    conn.close()
    return json.dumps(result)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_sqlite_tools.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add agent/tools/sqlite_tools.py tests/test_sqlite_tools.py
git commit -m "feat: sqlite habit tracker — plans, habit logs, streaks"
```

---

## Task 6: Wire Everything + Streamlit Frontend

**Files:**
- Create: `app.py`
- Modify: (no existing files changed — app.py is new)

- [ ] **Step 1: Run the full test suite before wiring**

```bash
pytest tests/ -v
```

Expected: all tests pass. Fix any failures before proceeding.

- [ ] **Step 2: Write app.py**

```python
# app.py
import asyncio
import json
from datetime import date
from dotenv import load_dotenv

load_dotenv()

import streamlit as st
from agent.agent import build_agent
from agent.calendar_mcp import build_calendar_mcp_client
from agent.prompts import build_system_prompt
from agent.fact_extractor import extract_and_store_facts
from agent.tools.chroma_tools import store_user_fact, retrieve_user_facts, save_conversation_log, retrieve_past_logs
from agent.tools.sqlite_tools import (
    init_db, get_daily_plan, save_daily_plan,
    log_habit, get_habit_streaks, update_habit_streaks,
)

init_db()

st.set_page_config(page_title="Life Coach", layout="centered")

@st.cache_resource
def get_agent():
    calendar_client = build_calendar_mcp_client()
    calendar_tools = asyncio.run(calendar_client.get_tools())
    local_tools = [
        get_daily_plan, save_daily_plan,
        log_habit, get_habit_streaks, update_habit_streaks,
        store_user_fact, retrieve_user_facts,
        save_conversation_log, retrieve_past_logs,
    ]
    return build_agent(calendar_tools + local_tools)

agent = get_agent()

# Sidebar — streaks and today's plan
with st.sidebar:
    st.title("Today")
    today = date.today().isoformat()

    plan = get_daily_plan.invoke(today)
    if plan != "No plan found":
        st.subheader("Plan")
        st.text(plan)

    streaks_raw = get_habit_streaks.invoke({})
    if streaks_raw != "No habits tracked yet.":
        st.subheader("Streaks")
        for habit, data in json.loads(streaks_raw).items():
            st.metric(
                label=habit.replace("_", " ").title(),
                value=f"{data['current_streak']} days",
                delta=f"{int(data['completion_rate'] * 100)}% completion rate",
            )

# Chat interface
st.title("Life Coach")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if user_input := st.chat_input("What's on your mind?"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Background fact extraction (silent)
    extract_and_store_facts(user_input)

    system_prompt = build_system_prompt()

    # Chat history for agent context (exclude current message)
    history = [
        ("human" if m["role"] == "user" else "ai", m["content"])
        for m in st.session_state.messages[:-1]
    ]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = agent.invoke({
                "input": user_input,
                "system_prompt": system_prompt,
                "chat_history": history,
            })
        reply = response["output"]
        st.write(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
```

- [ ] **Step 3: Run the app**

```bash
streamlit run app.py
```

Expected: browser opens at `http://localhost:8501`. Sidebar shows "Today". Chat input is visible.

- [ ] **Step 4: Morning plan smoke test**

Type in the chat: `Plan my day for today`

Expected:
- Agent calls MCP tool `list_calendar_events`, plus `retrieve_user_facts` and `get_habit_streaks`
- Returns a time-blocked plan
- Plan appears in the sidebar after page refresh

- [ ] **Step 5: Evening reflection smoke test**

Type in the chat: `I trained today and read in the morning but went over on calories`

Expected:
- Agent calls `log_habit` three times
- Agent calls `update_habit_streaks`
- Sidebar streaks update
- Response includes what went well and one suggestion

- [ ] **Step 6: Fact extraction smoke test**

Type: `I usually go to BJJ on Tuesdays and Thursdays`

Then type: `What do you know about my schedule?`

Expected: second response references BJJ on Tuesdays/Thursdays (retrieved from ChromaDB).

- [ ] **Step 7: Calendar write smoke test**

Type: `Put my BJJ training tomorrow from 18:00 to 19:30 on my calendar`

Expected:
- Agent proposes the exact event title, date, start, and end time
- Agent asks for confirmation before writing
- After the user confirms, agent calls MCP tool `create_calendar_event`
- New event appears in Google Calendar

Then type: `Move that training event to 19:00`

Expected:
- Agent uses the saved/returned `event_id` or lists calendar events to find the correct event
- Agent asks for confirmation before editing
- After confirmation, agent calls MCP tool `update_calendar_event`

- [ ] **Step 8: Final commit**

```bash
git add app.py
git commit -m "feat: streamlit ui with mcp calendar and local memory tools"
```

---

## Self-Review Notes

**Spec coverage check:**
- ✅ Morning planning workflow — Task 6, Step 4
- ✅ Fact extraction workflow — Task 4 (fact_extractor.py) + Task 6 (called in app.py)
- ✅ Mid-day check-in — agent uses get_daily_plan when user checks in
- ✅ Evening reflection — Task 6, Step 5; log_habit + update_habit_streaks in agent
- ✅ Accountability injection — handled via single system prompt in prompts.py
- ✅ Google Calendar MCP tools — Task 3 (`list_calendar_events`, `create_calendar_event`, `update_calendar_event`, `delete_calendar_event`)
- ✅ Native LangChain tool calls — Tasks 4 and 5 (ChromaDB + SQLite)
- ✅ ChromaDB user_facts + conversation_logs — Task 4
- ✅ SQLite daily_plans + habit_logs + habit_streaks — Task 5
- ✅ Google Calendar read/write integration — Task 3
- ✅ Streamlit UI with sidebar — Task 6
- ✅ Validation (structured output via tool calls, calendar as ground truth, confirmation before calendar writes) — embedded in tool design

**Type consistency check:**
- `get_habit_streaks` takes `dummy: dict = {}` to satisfy LangChain tool requirement for no-arg tools — consistent across sqlite_tools.py and app.py
- `update_habit_streaks` takes `completions_json: str` (JSON string) — consistent in tests and prompts guidance
- `retrieve_user_facts` takes `query: str, k: int = 5` — consistent in tests and prompts.py addendum
