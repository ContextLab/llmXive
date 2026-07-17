"""
Unit tests for T015: Holdout set creation.

Tests verify that:
1. The holdout set has exactly N=50 rows
2. Required columns are present
3. No duplicates exist
4. The sampling is deterministic with a fixed seed
"""
import pytest
import pandas as pd
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.annotate_holdout import (
    sample_holdout_set,
    prepare_holdout_dataframe,
    HOLDOUT_SIZE,
    RANDOM_SEED
)


@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    data = {
        'query': [f"Query {i}" for i in range(100)],
        'context': [f"Context {i}" for i in range(100)],
        'intent': ['simple' if i % 2 == 0 else 'complex' for i in range(100)],
        'complexity': [1 if i % 2 == 0 else 3 for i in range(100)],
    }
    return pd.DataFrame(data)


def test_sample_holdout_set_size(sample_dataframe):
    """Test that sampled dataframe has exactly N=50 rows."""
    sampled = sample_holdout_set(sample_dataframe, n=HOLDOUT_SIZE, seed=RANDOM_SEED)
    assert len(sampled) == HOLDOUT_SIZE, f"Expected {HOLDOUT_SIZE} rows, got {len(sampled)}"


def test_sample_holdout_set_no_duplicates(sample_dataframe):
    """Test that sampled dataframe has no duplicate indices."""
    sampled = sample_holdout_set(sample_dataframe, n=HOLDOUT_SIZE, seed=RANDOM_SEED)
    assert sampled.index.is_unique, "Sampled dataframe contains duplicate indices"


def test_sample_holdout_set_deterministic(sample_dataframe):
    """Test that sampling is deterministic with fixed seed."""
    sampled1 = sample_holdout_set(sample_dataframe, n=HOLDOUT_SIZE, seed=RANDOM_SEED)
    sampled2 = sample_holdout_set(sample_dataframe, n=HOLDOUT_SIZE, seed=RANDOM_SEED)
    
    # Reset indices for comparison
    sampled1_reset = sampled1.reset_index(drop=True)
    sampled2_reset = sampled2.reset_index(drop=True)
    
    pd.testing.assert_frame_equal(sampled1_reset, sampled2_reset)


def test_prepare_holdout_dataframe_columns(sample_dataframe):
    """Test that prepared dataframe has required annotation columns."""
    sampled = sample_holdout_set(sample_dataframe, n=HOLDOUT_SIZE, seed=RANDOM_SEED)
    prepared = prepare_holdout_dataframe(sampled)
    
    required_cols = ['annotation_id', 'ground_truth_label', 'complexity_score']
    for col in required_cols:
        assert col in prepared.columns, f"Missing required column: {col}"


def test_prepare_holdout_dataframe_annotation_id_format(sample_dataframe):
    """Test that annotation IDs follow the expected format."""
    sampled = sample_holdout_set(sample_dataframe, n=HOLDOUT_SIZE, seed=RANDOM_SEED)
    prepared = prepare_holdout_dataframe(sampled)
    
    # Check first ID format
    first_id = prepared.iloc[0]['annotation_id']
    assert first_id.startswith("HOLDOUT_"), f"Annotation ID should start with 'HOLDOUT_', got: {first_id}"
    assert len(first_id) == 11, f"Annotation ID should be 11 chars (HOLDOUT_XXX), got: {first_id}"


def test_prepare_holdout_dataframe_empty_labels(sample_dataframe):
    """Test that human annotation columns are empty initially."""
    sampled = sample_holdout_set(sample_dataframe, n=HOLDOUT_SIZE, seed=RANDOM_SEED)
    prepared = prepare_holdout_dataframe(sampled)
    
    # Check that label columns are empty strings
    assert all(prepared['ground_truth_label'] == ''), "ground_truth_label should be empty"
    assert all(prepared['complexity_score'] == ''), "complexity_score should be empty"


def test_sample_fails_if_dataset_too_small():
    """Test that sampling fails loudly if dataset has fewer rows than requested."""
    small_df = pd.DataFrame({'query': ['q1', 'q2', 'q3']})
    
    with pytest.raises(ValueError) as exc_info:
        sample_holdout_set(small_df, n=10, seed=42)
    
    assert "cannot sample" in str(exc_info.value).lower()