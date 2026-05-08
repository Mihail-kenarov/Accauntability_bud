import json
import os
from datetime import date, datetime, timedelta
from uuid import uuid4

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from langchain_core.tools import tool


MIN_FACT_CONFIDENCE = 0.7
DUPLICATE_DISTANCE_THRESHOLD = 0.15


def get_chroma_client():
    chroma_path = os.getenv("CHROMA_PATH", "db/chroma")
    return chromadb.PersistentClient(path=chroma_path)


def get_embedding_function():
    return DefaultEmbeddingFunction()


def _get_collection(name: str):
    return get_chroma_client().get_or_create_collection(
        name=name,
        embedding_function=get_embedding_function(),
    )


def _first_result(result: dict, key: str):
    values = result.get(key) or [[]]
    return values[0] if values else []


def _is_duplicate_fact(collection, fact: str) -> bool:
    if collection.count() == 0:
        return False

    result = collection.query(query_texts=[fact], n_results=1)
    distances = _first_result(result, "distances")
    return bool(distances and distances[0] <= DUPLICATE_DISTANCE_THRESHOLD)


@tool
def store_user_fact(
    fact: str,
    fact_type: str,
    confidence: float,
    source: str,
) -> str:
    """Store a high-confidence fact about the user's goals, habits, schedule, or preferences."""
    if confidence < MIN_FACT_CONFIDENCE:
        return "skipped_low_confidence"

    collection = _get_collection("user_facts")
    if _is_duplicate_fact(collection, fact):
        return "duplicate_skipped"

    collection.add(
        ids=[f"user_fact_{uuid4()}"],
        documents=[fact],
        metadatas=[
            {
                "fact_type": fact_type,
                "source": source,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "confidence": confidence,
            }
        ],
    )
    return "stored"


@tool
def retrieve_user_facts(query: str, k: int = 5) -> str:
    """Retrieve stored user facts that are relevant to the query."""
    collection = _get_collection("user_facts")
    if collection.count() == 0:
        return "No facts found"

    result = collection.query(query_texts=[query], n_results=k)
    documents = _first_result(result, "documents")
    return json.dumps(documents) if documents else "No facts found"


@tool
def save_conversation_log(
    session_type: str,
    summary: str,
    habits_mentioned: list[str] | None = None,
) -> str:
    """Save a conversation summary for long-term recall."""
    habits = habits_mentioned or []
    collection = _get_collection("conversation_logs")
    now = datetime.now()
    collection.add(
        ids=[f"conversation_log_{uuid4()}"],
        documents=[summary],
        metadatas=[
            {
                "session_type": session_type,
                "date": now.date().isoformat(),
                "date_ordinal": now.date().toordinal(),
                "timestamp": now.isoformat(timespec="seconds"),
                "habits_mentioned": ",".join(habits),
            }
        ],
    )
    return "saved"


@tool
def retrieve_past_logs(query: str, n_days: int = 7, k: int = 5) -> str:
    """Retrieve relevant conversation summaries from the last n_days."""
    collection = _get_collection("conversation_logs")
    if collection.count() == 0:
        return "No logs found"

    cutoff = date.today() - timedelta(days=n_days)
    result = collection.query(
        query_texts=[query],
        n_results=k,
        where={"date_ordinal": {"$gte": cutoff.toordinal()}},
    )
    documents = _first_result(result, "documents")
    return json.dumps(documents) if documents else "No logs found"
