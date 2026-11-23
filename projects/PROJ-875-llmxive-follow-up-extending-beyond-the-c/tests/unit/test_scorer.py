"""
Unit tests for code/scorer.py
Validates the Memory Gap calculation and Plan Override logic.
"""
import json
import os
import pytest
import numpy as np

# Add parent to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from scorer import (
    calculate_memory_gap_score,
    identify_missing_critical_items,
    calculate_semantic_similarity,
    PLAN_OVERRIDE_TAG
)
from logger import setup_logger

# Setup logger for tests
setup_logger(level="INFO")


@pytest.fixture
def mock_embedding_model(monkeypatch):
    """
    Mock the SentenceTransformer to avoid downloading weights during unit tests.
    We simulate a model that returns deterministic embeddings based on string length
    to ensure consistent similarity scores.
    """
    class MockModel:
        def encode(self, texts, convert_to_tensor=False):
            # Return a simple vector based on string length to simulate distinct embeddings
            # This ensures similarity is not always 1.0 or 0.0
            embeddings = []
            for t in texts:
                vec = np.array([float(len(t))])
                embeddings.append(vec)
            # Normalize to unit vectors for cosine similarity logic
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1
            return embeddings / norms

    monkeypatch.setattr("scorer.SentenceTransformer", lambda name: MockModel())
    return MockModel()


def test_identify_missing_critical_items(mock_embedding_model):
    """
    Test identification of missing critical items (keys/doors).
    """
    gt = {
        "items": [
            {"id": "key_1", "type": "key"},
            {"id": "door_1", "type": "door"},
            {"id": "chest_1", "type": "chest"}
        ]
    }
    
    # Agent sees key and chest, but misses door
    agent = {
        "items": [
            {"id": "key_1", "type": "key"},
            {"id": "chest_1", "type": "chest"}
        ]
    }
    
    missing, count = identify_missing_critical_items(gt, agent)
    
    assert count == 1
    assert "door_1" in missing
    assert "key_1" not in missing
    assert "chest_1" not in missing # Chest is not critical


def test_identify_missing_critical_items_none(mock_embedding_model):
    """
    Test when no critical items are missing.
    """
    gt = {
        "items": [
            {"id": "key_1", "type": "key"}
        ]
    }
    agent = {
        "items": [
            {"id": "key_1", "type": "key"}
        ]
    }
    
    missing, count = identify_missing_critical_items(gt, agent)
    assert count == 0
    assert len(missing) == 0


def test_memory_gap_score_calculation(mock_embedding_model):
    """
    Test the full memory gap score formula.
    """
    gt = {
        "masked_ground_truth": {
            "description": "I see a key and a door.",
            "items": [
                {"id": "key_1", "type": "key"},
                {"id": "door_1", "type": "door"}
            ]
        }
    }
    
    # Agent misses the door (critical)
    agent = {
        "mental_map": {
            "description": "I see a key.",
            "items": [
                {"id": "key_1", "type": "key"}
            ]
        }
    }
    
    result = calculate_memory_gap_score(agent, gt, penalty=1.0)
    
    assert "memory_gap_score" in result
    assert result["plan_override_tag"] == PLAN_OVERRIDE_TAG
    assert result["missing_count"] == 1
    assert result["penalty_applied"] == 1.0
    
    # Score should be > 0 due to missing item and potential semantic diff
    assert result["memory_gap_score"] > 0.0


def test_memory_gap_score_perfect_match(mock_embedding_model):
    """
    Test score when agent matches ground truth perfectly.
    """
    gt = {
        "masked_ground_truth": {
            "description": "I see a key.",
            "items": [{"id": "key_1", "type": "key"}]
        }
    }
    agent = {
        "mental_map": {
            "description": "I see a key.",
            "items": [{"id": "key_1", "type": "key"}]
        }
    }
    
    result = calculate_memory_gap_score(agent, gt, penalty=1.0)
    
    # With perfect match, missing_count = 0. 
    # Semantic similarity should be 1.0 (or very close) with identical strings.
    # Score = (1 - 1) + (1 * 0) = 0
    assert result["missing_count"] == 0
    assert result["penalty_applied"] == 0.0
    assert result["memory_gap_score"] == 0.0


def test_plan_override_tag_present(mock_embedding_model):
    """
    Verify that the Plan Override tag is explicitly included in results.
    """
    gt = {"masked_ground_truth": {"items": []}}
    agent = {"mental_map": {"items": []}}
    
    result = calculate_memory_gap_score(agent, gt)
    assert PLAN_OVERRIDE_TAG in result["plan_override_tag"]