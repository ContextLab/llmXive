import os
import tempfile
import pandas as pd
import pytest
from code.data.behavioral_validator import (
    load_behavioral_scores,
    identify_missing_scores,
    log_missing_score_exclusions,
    filter_missing_scores,
    run_behavioral_validation_pipeline
)
from code.utils.logging import get_exclusion_log_path

@pytest.fixture
def sample_merged_data():
    """Create a sample merged DataFrame for testing."""
    data = {
        "Subject_ID": ["1001", "1002", "1003", "1004", "1005"],
        "Variability_Metric": [0.5, 0.6, 0.7, 0.8, 0.9],
        "Flexibility_Score": [20.0, None, 25.0, None, 30.0],
        "Age": [20, 21, 22, 23, 24],
        "Sex": ["M", "F", "M", "F", "M"]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_exclusion_log():
    """Create a temporary directory for exclusion log testing."""
    # We mock the path function to return a temp file for this test
    # In real execution, this would be in data/processed/
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_path = os.path.join(tmpdir, "exclusion_log.csv")
        # We need to patch the function temporarily, but since we can't easily
        # patch in a simple pytest fixture without monkeypatch, we'll just
        # test the logic that writes to the path returned by get_exclusion_log_path
        # and assume the environment is set up correctly.
        yield mock_path

def test_identify_missing_scores(sample_merged_data):
    """Test identification of subjects with missing flexibility scores."""
    missing = identify_missing_scores(sample_merged_data, "Flexibility_Score")
    assert set(missing) == {"1002", "1004"}
    assert len(missing) == 2

def test_filter_missing_scores(sample_merged_data):
    """Test filtering of subjects with missing flexibility scores."""
    filtered_df, excluded = filter_missing_scores(sample_merged_data, "Flexibility_Score")
    
    assert len(filtered_df) == 3
    assert set(filtered_df["Subject_ID"]) == {"1001", "1003", "1005"}
    assert set(excluded) == {"1002", "1004"}
    assert filtered_df["Flexibility_Score"].isna().sum() == 0

def test_log_missing_score_exclusions(sample_merged_data, monkeypatch, tmp_path):
    """Test that missing score exclusions are logged to CSV."""
    # Create a temporary directory and set it as the processed path
    import code.data.paths as paths
    original_get_processed_path = paths.get_processed_path
    
    # Monkeypatch to use our temp directory
    paths.get_processed_path = lambda: str(tmp_path)
    
    try:
        missing_subjects = ["1002", "1004"]
        all_subjects = ["1001", "1002", "1003", "1004", "1005"]
        
        log_missing_score_exclusions(missing_subjects, all_subjects)
        
        exclusion_log_path = get_exclusion_log_path()
        assert os.path.exists(exclusion_log_path)
        
        log_df = pd.read_csv(exclusion_log_path)
        assert "Subject_ID" in log_df.columns
        assert "Exclusion_Reason" in log_df.columns
        assert "Mean_FD" in log_df.columns
        
        # Check that the correct subjects were logged
        logged_subjects = set(log_df["Subject_ID"])
        assert logged_subjects == {"1002", "1004"}
        
        # Check exclusion reason
        reasons = log_df["Exclusion_Reason"].tolist()
        assert all(r == "Missing_Behavioral_Score" for r in reasons)
    finally:
        paths.get_processed_path = original_get_processed_path

def test_run_behavioral_validation_pipeline(sample_merged_data, monkeypatch, tmp_path):
    """Test the full pipeline."""
    import code.data.paths as paths
    original_get_processed_path = paths.get_processed_path
    paths.get_processed_path = lambda: str(tmp_path)
    
    try:
        result_df = run_behavioral_validation_pipeline(sample_merged_data, "Flexibility_Score")
        assert len(result_df) == 3
        assert result_df["Flexibility_Score"].isna().sum() == 0
        
        # Verify exclusion log was created
        exclusion_log_path = get_exclusion_log_path()
        assert os.path.exists(exclusion_log_path)
        log_df = pd.read_csv(exclusion_log_path)
        assert len(log_df) == 2
    finally:
        paths.get_processed_path = original_get_processed_path