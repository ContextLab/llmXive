"""
Unit tests for T012b: Score Exclusion Task
"""
import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from task_t012b_score_exclusion import filter_by_score, update_exclusion_counts, load_age_filtered_dataset

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_age_filtered_df():
    """Create a sample dataframe simulating cleaned_age_filtered.csv."""
    data = {
        "participant_id": ["P1", "P2", "P3", "P4", "P5"],
        "stimulus_type": ["nostalgia", "control", "nostalgia", "control", "nostalgia"],
        "perseverative_errors": [5.0, 3.0, None, 2.0, 4.0],
        "categories_completed": [4.0, 5.0, 3.0, None, 5.0],
        "age": [65, 70, 72, 68, 80]
    }
    return pd.DataFrame(data)

def test_filter_by_score_removes_nulls(sample_age_filtered_df):
    """Test that filter_by_score removes rows with null perseverative_errors or categories_completed."""
    filtered_df, excluded_count = filter_by_score(sample_age_filtered_df)
    
    # Expected: P3 (missing errors) and P4 (missing categories) should be removed
    # Remaining: P1, P2, P5
    assert len(filtered_df) == 3
    assert excluded_count == 2
    
    # Verify no nulls in target columns
    assert filtered_df["perseverative_errors"].isna().sum() == 0
    assert filtered_df["categories_completed"].isna().sum() == 0

def test_filter_by_score_preserves_data(sample_age_filtered_df):
    """Test that valid rows are preserved correctly."""
    filtered_df, _ = filter_by_score(sample_age_filtered_df)
    
    # Check specific IDs
    assert "P1" in filtered_df["participant_id"].values
    assert "P2" in filtered_df["participant_id"].values
    assert "P5" in filtered_df["participant_id"].values
    
    # Check values are preserved
    p1_row = filtered_df[filtered_df["participant_id"] == "P1"].iloc[0]
    assert p1_row["perseverative_errors"] == 5.0
    assert p1_row["categories_completed"] == 4.0

def test_update_exclusion_counts(tmp_data_dir, sample_age_filtered_df):
    """Test that update_exclusion_counts correctly updates the JSON file."""
    # Setup temp paths
    counts_file = tmp_data_dir / "exclusion_counts.json"
    os.environ["DATA_PROCESSED_DIR"] = str(tmp_data_dir)
    
    # Mock the global constant for the test
    import task_t012b_score_exclusion as module
    original_file = module.EXCLUSION_COUNTS_FILE
    module.EXCLUSION_COUNTS_FILE = counts_file
    
    try:
        # Initial state
        excluded_count = 2
        update_exclusion_counts(excluded_count)
        
        # Verify file content
        with open(counts_file, "r") as f:
            counts = json.load(f)
        
        assert counts["ERR_MISSING_SCORE"] == 2
        assert "ERR_MISSING_AGE_FIELD" in counts
        assert "ERR_MMSE_IMPAIRED" in counts
    finally:
        # Restore original constant
        module.EXCLUSION_COUNTS_FILE = original_file
        if "DATA_PROCESSED_DIR" in os.environ:
            del os.environ["DATA_PROCESSED_DIR"]
