from pathlib import Path
import sys

from langchain_mcp_adapters.client import MultiServerMCPClient


def build_calendar_mcp_client() -> MultiServerMCPClient:
    server_path = (
        Path(__file__).resolve().parents[1]
        / "mcp_servers"
        / "google_calendar_server.py"
    )
    return MultiServerMCPClient(
        {
            "google_calendar": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(server_path)],
            }
        }
    )
