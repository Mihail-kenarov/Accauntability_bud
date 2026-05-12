# Accountability Bud

Accountability Bud is a Streamlit web app for daily planning and habit accountability.
It gives the user a private coaching chat that can look at Google Calendar events,
remember useful personal facts, save daily todo plans, and track habit streaks.

The main idea is simple: the assistant should not give generic productivity advice.
It should ground its answers in the user's actual calendar, saved plan, habit data,
and remembered context.

## What This Project Uses

- **Python** for the whole application.
- **Streamlit** for the web interface in `app.py`.
- **LangChain** for the tool-calling agent.
- **OpenRouter** or **Ollama** for the chat model.
- **FastMCP** for the Google Calendar MCP server.
- **Google Calendar API** for reading and editing calendar events.
- **SQLite** for daily plans, tasks, and habit streaks.
- **ChromaDB** for remembered user facts and conversation summaries.
- **Pytest** for automated tests.

## Requirements

You need:

- Python 3.10 or newer.
- Git.
- A browser.
- An LLM option:
  - an OpenRouter API key, or
  - Ollama installed locally with the model named in `.env`.
- Google Calendar OAuth credentials if you want calendar features to work.

The app creates its local database files automatically when it runs.

## Setup

Clone the repository and enter the project folder:

```bash
git clone https://github.com/Mihail-kenarov/Accauntability_bud.git
cd Accauntability_bud
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your local environment file:

```bash
cp .env.example .env
```

Then open `.env` and fill in the values you need.

## LLM Configuration

The default setup uses OpenRouter:

```env
MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-oss-120b:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

To use Ollama instead, install Ollama, pull the model you want, and set:

```env
MODEL_PROVIDER=ollama
OLLAMA_MODEL=ministral-3:8b
```

If you choose Ollama, make sure the local Ollama server is running before starting
the Streamlit app.

## Google Calendar Setup

Calendar support needs a Google OAuth client file.

1. Go to Google Cloud Console.
2. Create or select a project.
3. Enable the Google Calendar API.
4. Create OAuth client credentials for a desktop app.
5. Download the JSON file.
6. Save it as:

```text
credentials/credentials.json
```

The first time the app needs Calendar access, it will open a browser window for
Google login and consent. After login, it creates:

```text
credentials/token.json
```

Both files are local credentials and should not be committed.

## Run the App

Start Streamlit:

```bash
streamlit run app.py
```

Then open the local URL Streamlit prints, usually:

```text
http://localhost:8501
```

## How To Use It

- **Coach** is the main chat screen.
- **Plan** shows the saved todo plan for today.
- **Calendar** shows today's Google Calendar events.
- **Habits** is for accountability and evening reflection.
- **Notes** shows remembered user facts stored in ChromaDB.
- **Sources** shows which tools were used in recent assistant answers.
- **Settings** shows the important local configuration paths.

When asking the coach to plan your day, the agent can check the calendar, retrieve
stored facts, review recent conversation logs, and use habit data. It should only
save or change plans and calendar events after the user agrees.

## Run Tests

```bash
pytest
```

The tests cover the local tool logic and Google Calendar helper behavior using
mocks, so they should not need real Google credentials.

## Project Structure

```text
app.py                         Streamlit UI and app flow
agent/agent.py                 LangChain agent setup
agent/llm.py                   OpenRouter/Ollama model selection
agent/prompts.py               System prompt for the coach
agent/fact_extractor.py        Stores durable facts from chat messages
agent/tools/sqlite_tools.py    SQLite tools for plans, tasks, habits
agent/tools/chroma_tools.py    ChromaDB tools for memory and logs
mcp_servers/google_calendar_server.py
                               Google Calendar MCP tools
tests/                         Pytest test suite
requirements.txt               Python dependencies
.env.example                   Template for local environment variables
```

## Files You Should Not Push

These are intentionally ignored by Git:

- `.env`
- `.venv/`
- `credentials/credentials.json`
- `credentials/token.json`
- `db/`
- `__pycache__/`
- `.pytest_cache/`
- `*.pyc`

The ignored `db/` folder contains local SQLite and ChromaDB data. It may include
private plans, habits, memories, and conversation history.

## Troubleshooting

If the app says `OPENROUTER_API_KEY is missing`, add your OpenRouter key to `.env`
or switch `MODEL_PROVIDER` to `ollama`.

If Google Calendar fails, confirm that `credentials/credentials.json` exists and
that the Google Calendar API is enabled for your Google Cloud project.

If imports fail, make sure the virtual environment is active and dependencies were
installed with `pip install -r requirements.txt`.
