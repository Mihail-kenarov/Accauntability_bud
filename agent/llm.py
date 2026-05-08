import os

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI


def _openrouter_headers() -> dict[str, str]:
    headers = {}
    site_url = os.getenv("OPENROUTER_SITE_URL")
    app_name = os.getenv("OPENROUTER_APP_NAME", "Accountability Bud")
    if site_url:
        headers["HTTP-Referer"] = site_url
    if app_name:
        headers["X-Title"] = app_name
    return headers


def build_chat_model(temperature: float = 0.3):
    provider = os.getenv("MODEL_PROVIDER", "openrouter").lower().strip()

    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "ministral-3:8b")
        return ChatOllama(model=model, temperature=temperature)

    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is missing. Add your OpenRouter key to .env."
            )

        return ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free"),
            api_key=api_key,
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            default_headers=_openrouter_headers(),
            temperature=temperature,
            max_retries=2,
        )

    raise ValueError(
        f"Unsupported MODEL_PROVIDER={provider!r}. Use 'openrouter' or 'ollama'."
    )
