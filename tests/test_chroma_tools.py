import hashlib
import json
import math
from unittest.mock import patch

import chromadb
import pytest


class HashEmbeddingFunction:
    def __call__(self, input):
        return [self._embed(text) for text in input]

    def _embed(self, text: str):
        dims = 32
        vector = [0.0] * dims
        for token in text.lower().split():
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            vector[int(digest, 16) % dims] += 1.0

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [value / magnitude for value in vector]


@pytest.fixture
def isolated_client(tmp_path):
    return chromadb.PersistentClient(path=str(tmp_path / "chroma"))


@pytest.fixture
def patched_chroma(isolated_client):
    with (
        patch("agent.tools.chroma_tools.get_chroma_client", return_value=isolated_client),
        patch(
            "agent.tools.chroma_tools.get_embedding_function",
            return_value=HashEmbeddingFunction(),
        ),
    ):
        yield


def test_store_user_fact(patched_chroma):
    from agent.tools.chroma_tools import store_user_fact

    result = store_user_fact.invoke(
        {
            "fact": "User trains BJJ on Tuesdays",
            "fact_type": "schedule_pattern",
            "confidence": 0.9,
            "source": "test message",
        }
    )

    assert result == "stored"


def test_store_fact_skips_low_confidence(patched_chroma):
    from agent.tools.chroma_tools import store_user_fact

    result = store_user_fact.invoke(
        {
            "fact": "User maybe likes coffee",
            "fact_type": "preference",
            "confidence": 0.5,
            "source": "test",
        }
    )

    assert result == "skipped_low_confidence"


def test_store_fact_skips_duplicate(patched_chroma):
    from agent.tools.chroma_tools import store_user_fact

    payload = {
        "fact": "User trains BJJ on Tuesdays",
        "fact_type": "schedule_pattern",
        "confidence": 0.9,
        "source": "test message",
    }

    assert store_user_fact.invoke(payload) == "stored"
    assert store_user_fact.invoke(payload) == "duplicate_skipped"


def test_retrieve_user_facts(patched_chroma):
    from agent.tools.chroma_tools import retrieve_user_facts, store_user_fact

    store_user_fact.invoke(
        {
            "fact": "User does BJJ on Tuesday evenings",
            "fact_type": "schedule_pattern",
            "confidence": 0.9,
            "source": "test",
        }
    )

    result = retrieve_user_facts.invoke({"query": "BJJ schedule", "k": 3})
    parsed = json.loads(result)

    assert "User does BJJ on Tuesday evenings" in parsed


def test_save_and_retrieve_conversation_log(patched_chroma):
    from agent.tools.chroma_tools import retrieve_past_logs, save_conversation_log

    save_result = save_conversation_log.invoke(
        {
            "session_type": "evening_reflection",
            "summary": "User trained BJJ but missed the calorie target.",
            "habits_mentioned": ["training", "calories_on_target"],
        }
    )

    result = retrieve_past_logs.invoke({"query": "training calorie reflection", "n_days": 7})
    parsed = json.loads(result)

    assert save_result == "saved"
    assert "User trained BJJ but missed the calorie target." in parsed
