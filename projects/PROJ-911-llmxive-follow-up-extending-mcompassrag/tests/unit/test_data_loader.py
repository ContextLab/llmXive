"""
Unit tests for the data_loader module.
Verifies that sampling respects the MAX_DOCS constraint (N <= 360).
"""
import pytest
from unittest.mock import patch, MagicMock
from datasets import Dataset
import random

from code.data_loader import load_hotpotqa_sample, load_wikipedia_sample
from code.config import MAX_DOCS, RANDOM_SEED

@pytest.fixture(autouse=True)
def reset_seed():
    """Ensure random seed is reset before each test for determinism."""
    random.seed(RANDOM_SEED)

def test_load_hotpotqa_sample_capped_at_max():
    """
    Test that load_hotpotqa_sample never returns more than MAX_DOCS (360).
    """
    # Mock a dataset larger than MAX_DOCS
    mock_data = {"id": [str(i) for i in range(1000)], "text": ["doc" * 10 for _ in range(1000)]}
    mock_ds = Dataset.from_dict(mock_data)

    with patch("code.data_loader.load_dataset", return_value=mock_ds):
        samples = load_hotpotqa_sample(n=500)  # Request more than MAX_DOCS
        
        assert len(samples) == MAX_DOCS, f"Expected {MAX_DOCS} samples, got {len(samples)}"
        assert len(samples) <= 360, "Sample size must not exceed 360"

def test_load_hotpotqa_sample_small_dataset():
    """
    Test that load_hotpotqa_sample returns all data if dataset size < MAX_DOCS.
    """
    small_size = 50
    mock_data = {"id": [str(i) for i in range(small_size)], "text": ["doc" for _ in range(small_size)]}
    mock_ds = Dataset.from_dict(mock_data)

    with patch("code.data_loader.load_dataset", return_value=mock_ds):
        samples = load_hotpotqa_sample(n=100)
        
        assert len(samples) == small_size, "Should return all available samples when dataset is small"

def test_load_wikipedia_sample_capped_at_max():
    """
    Test that load_wikipedia_sample never returns more than MAX_DOCS (360).
    """
    mock_data = {"id": [str(i) for i in range(1000)], "title": ["Title" * 5 for _ in range(1000)], "text": ["Content" * 20 for _ in range(1000)]}
    mock_ds = Dataset.from_dict(mock_data)

    with patch("code.data_loader.load_dataset", return_value=mock_ds):
        samples = load_wikipedia_sample(n=500)
        
        assert len(samples) == MAX_DOCS, f"Expected {MAX_DOCS} samples, got {len(samples)}"
        assert len(samples) <= 360, "Sample size must not exceed 360"

def test_deterministic_sampling():
    """
    Test that sampling is deterministic given the fixed seed.
    """
    mock_data = {"id": [str(i) for i in range(100)], "text": ["doc" for _ in range(100)]}
    mock_ds = Dataset.from_dict(mock_data)

    with patch("code.data_loader.load_dataset", return_value=mock_ds):
        # Run twice
        samples1 = load_hotpotqa_sample(n=10)
        samples2 = load_hotpotqa_sample(n=10)
        
        # IDs should match exactly
        ids1 = [s["id"] for s in samples1]
        ids2 = [s["id"] for s in samples2]
        
        assert ids1 == ids2, "Sampling should be deterministic with fixed seed"