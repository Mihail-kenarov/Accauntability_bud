from unittest.mock import patch

from agent.fact_extractor import _parse_facts_json, extract_and_store_facts


def test_parse_facts_json_accepts_list():
    facts = _parse_facts_json(
        '[{"fact": "User trains BJJ", "fact_type": "habit", "confidence": 0.9}]'
    )

    assert facts == [
        {"fact": "User trains BJJ", "fact_type": "habit", "confidence": 0.9}
    ]


def test_parse_facts_json_accepts_wrapped_facts_key():
    facts = _parse_facts_json(
        '{"facts": [{"fact": "User studies at night", "fact_type": "schedule_pattern"}]}'
    )

    assert facts == [{"fact": "User studies at night", "fact_type": "schedule_pattern"}]


def test_extract_and_store_facts_invokes_store_tool():
    extracted = [
        {
            "fact": "User wants to train four times per week",
            "fact_type": "goal",
            "confidence": 0.91,
        }
    ]

    with (
        patch("agent.fact_extractor._extract_facts_with_llm", return_value=extracted),
        patch("agent.fact_extractor.store_user_fact") as store_user_fact,
    ):
        extract_and_store_facts("I want to train four times per week.")

    store_user_fact.invoke.assert_called_once_with(
        {
            "fact": "User wants to train four times per week",
            "fact_type": "goal",
            "confidence": 0.91,
            "source": "I want to train four times per week.",
        }
    )


def test_extract_and_store_facts_swallows_extraction_errors():
    with patch(
        "agent.fact_extractor._extract_facts_with_llm",
        side_effect=RuntimeError("ollama unavailable"),
    ):
        extract_and_store_facts("This should not raise.")
