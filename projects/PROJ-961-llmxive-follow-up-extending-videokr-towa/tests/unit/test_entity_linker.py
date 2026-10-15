"""
Unit tests for the ``link_dataframe`` function in ``code.utils.entity_linker``.
"""
import pandas as pd
import pytest
import numpy as np
from utils.entity_linker import link_dataframe

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

def test_preexisting_entity_id_column():
    """If an ``entity_id`` column exists the function should copy it and set confidence=1.0."""
    df = pd.DataFrame(
        {
            "question": ["What is X?", "What is Y?"],
            "entity_id": ["nodeC", "nodeD"],
        }
    )
    graph = {"nodeC": set(), "nodeD": set()}
    out = link_dataframe(df, graph)

    assert out["entity_node_id"].tolist() == ["nodeC", "nodeD"]
    assert (out["confidence"] == 1.0).all()

def test_fuzzy_matching_threshold_behavior(monkeypatch):
    """When no ID columns exist, fuzzy matching should respect the confidence threshold."""
    # Force SentenceTransformer to None to ensure fuzzy path is taken
    monkeypatch.setattr("utils.entity_linker.SentenceTransformer", None)
    
    graph = {"Apple": set(), "Banana": set()}
    df = pd.DataFrame(
        {
            "question": [
                "I love apples",      # substring match -> confidence 0.8
                "I love oranges",    # no match -> confidence 0.0
            ]
        }
    )
    # Threshold 0.5: Apple should be accepted, Orange should be None
    out = link_dataframe(df, graph, threshold=0.5)

    assert out.loc[0, "entity_node_id"] == "Apple"
    assert out.loc[0, "confidence"] >= 0.5

    assert out.loc[1, "entity_node_id"] is None
    assert out.loc[1, "confidence"] < 0.5

def test_embedding_path_when_available(monkeypatch):
    """If ``sentence_transformers`` is available, the embedding path should be used."""
    # Create a mock model that returns deterministic vectors
    class MockSentenceTransformer:
        def __init__(self, model_name):
            self.model_name = model_name
        def encode(self, texts):
            # Map each string to a unique simple vector based on length
            return np.array([[float(len(t))] * 384 for t in texts])

    # Patch SentenceTransformer at the module level
    monkeypatch.setattr("utils.entity_linker.SentenceTransformer", MockSentenceTransformer)

    graph = {"Short": set(), "VeryLongNodeName": set()}
    df = pd.DataFrame(
        {
            "question": [
                "Short",          # Exact length match with "Short" (5)
                "UnrelatedText",  # Different length (13)
            ]
        }
    )
    # Low threshold to allow match
    out = link_dataframe(df, graph, threshold=0.1)

    # "Short" should match "Short" (perfect cosine similarity since vectors are identical)
    assert out.loc[0, "entity_node_id"] == "Short"
    assert out.loc[0, "confidence"] == pytest.approx(1.0)

    # Verify that the embedding path was exercised (columns exist)
    assert "entity_node_id" in out.columns
    assert "confidence" in out.columns