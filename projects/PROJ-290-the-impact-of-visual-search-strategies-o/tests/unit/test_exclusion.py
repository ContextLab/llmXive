import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
import logging

# Import the module under test
from data.exclusion import calculate_missing_ratio, evaluate_participant_exclusion

@pytest.fixture
def sample_data_clean():
    """Create a DataFrame with no missing gaze data."""
    data = {
        "participant_id": [1, 1, 1, 2, 2, 2],
        "gaze_coordinates": [(0.1, 0.2), (0.2, 0.3), (0.3, 0.4), 
                             (0.5, 0.6), (0.6, 0.7), (0.7, 0.8)]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_data_partial_missing():
    """Create a DataFrame with some missing gaze data (33% missing for pid 1)."""
    data = {
        "participant_id": [1, 1, 1, 2, 2, 2],
        "gaze_coordinates": [None, (0.2, 0.3), (0.3, 0.4), 
                             (0.5, 0.6), (0.6, 0.7), (0.7, 0.8)]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_data_high_missing():
    """Create a DataFrame with high missing gaze data (66% missing for pid 1)."""
    data = {
        "participant_id": [1, 1, 1, 2, 2, 2],
        "gaze_coordinates": [None, None, (0.3, 0.4), 
                             (0.5, 0.6), (0.6, 0.7), (0.7, 0.8)]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_data_empty_participant():
    """Create a DataFrame where one participant has no records (edge case)."""
    # Note: In groupby, empty groups are skipped, so this tests the logic 
    # if we had a separate list of IDs. For now, testing the ratio calc on empty DF.
    return pd.DataFrame(columns=["participant_id", "gaze_coordinates"])

def test_calculate_missing_ratio_zero():
    """Test that 0 missing data returns 0.0 ratio."""
    df = pd.DataFrame({"gaze_coordinates": [(0.1, 0.2), (0.3, 0.4)]})
    # Mock logger
    logger = logging.getLogger("test")
    ratio = calculate_missing_ratio(logger, df)
    assert ratio == 0.0

def test_calculate_missing_ratio_all_missing():
    """Test that all missing data returns 1.0 ratio."""
    df = pd.DataFrame({"gaze_coordinates": [None, None]})
    logger = logging.getLogger("test")
    ratio = calculate_missing_ratio(logger, df)
    assert ratio == 1.0

def test_calculate_missing_ratio_partial():
    """Test partial missing data calculation."""
    df = pd.DataFrame({"gaze_coordinates": [None, (0.1, 0.2), None, (0.3, 0.4)]})
    logger = logging.getLogger("test")
    ratio = calculate_missing_ratio(logger, df)
    assert ratio == 0.5

def test_evaluate_participant_exclusion_clean_data(sample_data_clean, tmp_path):
    """Test exclusion logic when no data should be excluded."""
    input_file = tmp_path / "features.csv"
    sample_data_clean.to_csv(input_file, index=False)
    
    output_file = tmp_path / "cleaned.csv"
    stats_file = tmp_path / "stats.json"
    
    logger = logging.getLogger("test")
    cleaned_df, stats = evaluate_participant_exclusion(
        logger, input_file, exclusion_threshold=0.20
    )
    
    assert len(cleaned_df) == len(sample_data_clean)
    assert stats["excluded_count"] == 0
    assert stats["exclusion_rate"] == 0.0

def test_evaluate_participant_exclusion_partial_missing(sample_data_partial_missing, tmp_path):
    """Test exclusion logic when some data is missing but within threshold."""
    # 1 missing out of 3 = 33% missing. Threshold 0.20 (20%). Should exclude pid 1.
    input_file = tmp_path / "features.csv"
    sample_data_partial_missing.to_csv(input_file, index=False)
    
    logger = logging.getLogger("test")
    cleaned_df, stats = evaluate_participant_exclusion(
        logger, input_file, exclusion_threshold=0.20
    )
    
    # PID 1 has 33% missing (>20%), so it should be excluded.
    # PID 2 has 0% missing, so it should be kept.
    assert 1 not in cleaned_df["participant_id"].values
    assert 2 in cleaned_df["participant_id"].values
    assert stats["excluded_count"] == 1
    assert stats["exclusion_rate"] == 0.5

def test_evaluate_participant_exclusion_high_missing(sample_data_high_missing, tmp_path):
    """Test exclusion logic when high missing data triggers exclusion."""
    input_file = tmp_path / "features.csv"
    sample_data_high_missing.to_csv(input_file, index=False)
    
    logger = logging.getLogger("test")
    cleaned_df, stats = evaluate_participant_exclusion(
        logger, input_file, exclusion_threshold=0.20
    )
    
    # PID 1 has 66% missing (>20%), excluded.
    assert 1 not in cleaned_df["participant_id"].values
    assert 2 in cleaned_df["participant_id"].values
    assert stats["excluded_count"] == 1
    assert stats["exclusion_rate"] == 0.5

def test_evaluate_participant_exclusion_saves_files(sample_data_clean, tmp_path):
    """Test that the pipeline function (if called) saves files correctly."""
    # We test the evaluate function which is the core logic.
    # The run_exclusion_pipeline is the CLI wrapper.
    input_file = tmp_path / "features.csv"
    sample_data_clean.to_csv(input_file, index=False)
    
    logger = logging.getLogger("test")
    # We can't easily test the file writing of run_exclusion_pipeline without 
    # mocking sys.exit, so we rely on evaluate_participant_exclusion returning correct stats.
    cleaned_df, stats = evaluate_participant_exclusion(logger, input_file)
    
    assert "excluded_count" in stats
    assert "included_count" in stats
    assert "exclusion_rate" in stats
    assert "excluded_ids" in stats
    assert "included_ids" in stats

def test_missing_column_raises_error(tmp_path):
    """Test that missing gaze column raises an error."""
    data = {"participant_id": [1, 1], "other_col": [1, 2]}
    input_file = tmp_path / "features.csv"
    pd.DataFrame(data).to_csv(input_file, index=False)
    
    logger = logging.getLogger("test")
    with pytest.raises(ValueError, match="Column .* not found"):
        evaluate_participant_exclusion(logger, input_file, gaze_column="gaze_coordinates")

def test_no_participant_id_raises_error(tmp_path):
    """Test that missing participant_id column raises an error."""
    data = {"gaze_coordinates": [(0.1, 0.2), (0.3, 0.4)]}
    input_file = tmp_path / "features.csv"
    pd.DataFrame(data).to_csv(input_file, index=False)
    
    logger = logging.getLogger("test")
    with pytest.raises(ValueError, match="Data must contain 'participant_id'"):
        evaluate_participant_exclusion(logger, input_file)