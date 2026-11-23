import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Import functions to test
from task_t012e_mmse_exclusion import (
    load_score_filtered_dataset,
    load_mmse_flag,
    filter_mmse,
    update_exclusion_counts,
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_filter_mmse_with_column(temp_dir):
    """Test filtering by MMSE when column exists."""
    data = {
        "participant_id": ["P1", "P2", "P3", "P4"],
        "MMSE": [28, 22, 25, 19],
        "score": [1, 2, 3, 4]
    }
    df = pd.DataFrame(data)
    df_path = temp_dir / "test.csv"
    df.to_csv(df_path, index=False)

    loaded_df = load_score_filtered_dataset(df_path)
    filtered_df = filter_mmse(loaded_df, 24)

    assert len(filtered_df) == 2
    assert all(filtered_df["MMSE"] >= 24)
    assert set(filtered_df["participant_id"]) == {"P1", "P3"}

def test_filter_mmse_missing_column(temp_dir):
    """Test filtering when MMSE column is missing."""
    data = {
        "participant_id": ["P1", "P2"],
        "score": [1, 2]
    }
    df = pd.DataFrame(data)
    df_path = temp_dir / "test.csv"
    df.to_csv(df_path, index=False)

    loaded_df = load_score_filtered_dataset(df_path)
    filtered_df = filter_mmse(loaded_df, 24)

    # Should return the full dataset if column is missing
    assert len(filtered_df) == len(loaded_df)

def test_update_exclusion_counts_with_mmse(temp_dir):
    """Test updating exclusion counts when MMSE exclusions exist."""
    counts = {"ERR_MISSING_AGE_FIELD": 5}
    updated = update_exclusion_counts(counts, mmse_excluded_count=3)
    
    assert updated["ERR_MISSING_AGE_FIELD"] == 5
    assert updated["ERR_MMSE_IMPAIRED"] == 3

def test_update_exclusion_counts_no_mmse(temp_dir):
    """Test updating exclusion counts when no MMSE exclusions exist."""
    counts = {"ERR_MISSING_AGE_FIELD": 5}
    updated = update_exclusion_counts(counts, mmse_excluded_count=0)
    
    assert updated["ERR_MISSING_AGE_FIELD"] == 5
    assert updated["ERR_MMSE_IMPAIRED"] == 0

def test_load_mmse_flag_true(temp_dir):
    """Test loading MMSE flag when true."""
    flag_path = temp_dir / "mmse_flag.json"
    with open(flag_path, 'w') as f:
        json.dump({"has_mmse": True}, f)
    
    result = load_mmse_flag(flag_path)
    assert result is True

def test_load_mmse_flag_false(temp_dir):
    """Test loading MMSE flag when false."""
    flag_path = temp_dir / "mmse_flag.json"
    with open(flag_path, 'w') as f:
        json.dump({"has_mmse": False}, f)
    
    result = load_mmse_flag(flag_path)
    assert result is False

def test_load_mmse_flag_default(temp_dir):
    """Test loading MMSE flag with missing key (defaults to False)."""
    flag_path = temp_dir / "mmse_flag.json"
    with open(flag_path, 'w') as f:
        json.dump({}, f)
    
    result = load_mmse_flag(flag_path)
    assert result is False
