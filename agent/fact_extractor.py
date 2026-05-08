import json
from typing import Any

from langchain_core.prompts import PromptTemplate

from agent.llm import build_chat_model
from agent.tools.chroma_tools import store_user_fact


_PROMPT = PromptTemplate.from_template(
    "Extract facts about the user's goals, habits, schedule, or preferences from this message.\n"
    'Return ONLY a JSON array. Each item: {"fact": str, "fact_type": '
    '"goal|preference|schedule_pattern|constraint|habit", "confidence": 0.0-1.0}\n'
    "Return [] if nothing should be stored.\n\n"
    "Message: {message}\n\n"
    "JSON:"
)


def _parse_facts_json(raw: str) -> list[dict[str, Any]]:
    parsed = json.loads(raw)
    if isinstance(parsed, dict):
        parsed = parsed.get("facts", [])
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict) and item.get("fact")]


def _extract_facts_with_llm(message: str) -> list[dict[str, Any]]:
    llm = build_chat_model(temperature=0)
    result = (_PROMPT | llm).invoke({"message": message})
    return _parse_facts_json(result.content)


def extract_and_store_facts(message: str) -> None:
    """Extract durable user facts from a message and store them silently."""
    try:
        facts = _extract_facts_with_llm(message)
        for fact in facts:
            store_user_fact.invoke(
                {
                    "fact": fact["fact"],
                    "fact_type": fact.get("fact_type", "preference"),
                    "confidence": float(fact.get("confidence", 0.8)),
                    "source": message[:200],
                }
            )
    except Exception:
        return
