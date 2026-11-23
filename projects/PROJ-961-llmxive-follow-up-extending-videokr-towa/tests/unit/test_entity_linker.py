"""
Unit tests for the deterministic entity linker (code.utils.entity_linker).
"""
import pandas as pd
import pytest

from utils.entity_linker import link_dataframe, EntityLinker, create_entity_linker

def test_preexisting_node_id_column():
    """If a ``node_id`` column exists it should be copied with confidence=1.0."""
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
    """If an ``entity_id`` column exists it should be copied with confidence=1.0."""
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


def test_exact_match():
    """Exact (case‑insensitive, punctuation‑insensitive) matches should succeed."""
    graph = {"Apple": set(), "Banana": set()}
    df = pd.DataFrame({"question": ["Apple", "apple!", "Banana"]})
    out = link_dataframe(df, graph)

    assert out.loc[0, "entity_node_id"] == "Apple"
    assert out.loc[0, "confidence"] == 1.0
    assert out.loc[1, "entity_node_id"] == "Apple"
    assert out.loc[1, "confidence"] == 1.0
    assert out.loc[2, "entity_node_id"] == "Banana"
    assert out.loc[2, "confidence"] == 1.0


def test_levenshtein_fallback():
    """Levenshtein distance ≤ 2 should be accepted with lower confidence."""
    graph = {"Apple": set(), "Banana": set()}
    df = pd.DataFrame({"question": ["Aple", "Bannna", "Oranges"]})
    out = link_dataframe(df, graph)

    # 'Aple' (distance 1) matches 'Apple' with confidence 0.5
    assert out.loc[0, "entity_node_id"] == "Apple"
    assert out.loc[0, "confidence"] == 0.5

    # 'Bannna' (distance 2) matches 'Banana' with confidence 0.5
    assert out.loc[1, "entity_node_id"] == "Banana"
    assert out.loc[1, "confidence"] == 0.5

    # No suitable match for 'Oranges'
    assert out.loc[2, "entity_node_id"] is None
    assert out.loc[2, "confidence"] == 0.0


def test_no_match():
    """When no exact or fuzzy match is possible, result should be None/0.0."""
    graph = {"Apple": set()}
    df = pd.DataFrame({"question": ["Orange"]})
    out = link_dataframe(df, graph)

    assert out.loc[0, "entity_node_id"] is None
    assert out.loc[0, "confidence"] == 0.0