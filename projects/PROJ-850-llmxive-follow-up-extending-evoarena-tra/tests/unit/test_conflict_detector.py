import pytest
from src.heuristics.conflict_detector import ConflictDetector
from unittest.mock import MagicMock
import json

@pytest.fixture
def mock_model(mocker):
    mock_model = MagicMock()
    return mock_model

@pytest.fixture
def synthetic_pairs():
    return [
        {"patch_a": "This is a sentence.", "patch_b": "This is a sentence.", "is_contradiction": False},
        {"patch_a": "The sky is blue.", "patch_b": "The sky is red.", "is_contradiction": True},
        {"patch_a": "Cats are cute.", "patch_b": "Dogs are cute.", "is_contradiction": False},
        {"patch_a": "It is raining today.", "patch_b": "It is sunny today.", "is_contradiction": True}
    ]

def test_fallback_no_conflicts(mock_model, synthetic_pairs):
    """Tests the fallback behavior when no conflicts are detected."""
    detector = ConflictDetector(model=mock_model)
    mock_model.predict.return_value = [0] * len(synthetic_pairs)  # No conflicts
    
    retrieved_patches = detector.retrieve_patches(synthetic_pairs)

    # Expect the latest state plus the 2 most recent non-conflict patches
    expected_patches = synthetic_pairs[-2:]
    assert retrieved_patches == expected_patches