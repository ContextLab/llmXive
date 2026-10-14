"""
Unit tests for the ``link_dataframe`` function in ``code.utils.entity_linker``.
These tests cover the three logical branches required by task T102:
  1. Pre‑existing ``node_id``/``entity_id`` columns (skip linking).
  2. Fuzzy string matching path with confidence threshold handling.
  3. Embedding‑based path (executed only when ``sentence_transformers`` is available).
"""

import pandas as pd
import pytest

from utils.entity_linker import link_dataframe, EntityLinker


def test_preexisting_node_id_column():
    """If a ``node_id`` column exists the function should copy it and set confidence=1.0."""
    df = pd.DataFrame(
        {
            "question": ["What is X?", "What is Y?"],
            "node_id": ["nodeA", "nodeB"],
        }
    )
    graph = {"nodeA": set(), "nodeB": set()}
    out = link_dataframe(df, graph)

    assert "entity_node_id" in out.columns
    assert "confidence" in out.columns
    assert out["entity_node_id"].tolist() == ["nodeA", "nodeB"]
    assert (out["confidence"] == 1.0).all()


def test_fuzzy_matching_threshold_behavior():
    """When no ID columns exist, fuzzy matching should respect the confidence threshold."""
    # Graph contains two nodes; only one will match the question text.
    graph = {"Apple": set(), "Banana": set()}
    df = pd.DataFrame(
        {
            "question": [
                "I love apples",      # substring match -> confidence 0.8 (>0.5)
                "I love oranges",    # no match -> confidence 0.0
            ]
        }
    )
    out = link_dataframe(df, graph, threshold=0.5)

    # First row should link to "Apple" with confidence >= 0.5
    assert out.loc[0, "entity_node_id"] == "Apple"
    assert out.loc[0, "confidence"] >= 0.5

    # Second row should have no link
    assert out.loc[1, "entity_node_id"] is None
    assert out.loc[1, "confidence"] == 0.0


def test_embedding_path_when_available(monkeypatch):
    """If ``sentence_transformers`` is installed, the embedding path should be used."""
    # Skip the test if the real package cannot be imported.
    st = pytest.importorskip("sentence_transformers")

    # Create a tiny mock model that returns deterministic vectors.
    class DummyModel:
        def encode(self, texts):
            # Simple deterministic "embedding": length of the string as a vector.
            # This is sufficient to make similarity proportional to length.
            return [[len(t)] for t in texts]

    dummy_model = DummyModel()

    # Monkey‑patch the import inside the module to return our dummy model.
    monkeypatch.setattr(
        "utils.entity_linker.SentenceTransformer",  # type: ignore
        lambda *_args, **_kwargs: dummy_model,
        raising=False,
    )

    graph = {"Short": set(), "VeryLongNodeName": set()}
    df = pd.DataFrame(
        {
            "question": [
                "Short",          # exact match, higher similarity
                "UnrelatedText",  # no good match
            ]
        }
    )
    # Use a low threshold to ensure the exact match is accepted.
    out = link_dataframe(df, graph, threshold=0.1)

    # The first question should be linked to "Short".
    assert out.loc[0, "entity_node_id"] == "Short"
    assert out.loc[0, "confidence"] > 0.0

    # The second question has no reasonable match.
    assert out.loc[1, "entity_node_id"] is None
    assert out.loc[1, "confidence"] == 0.0