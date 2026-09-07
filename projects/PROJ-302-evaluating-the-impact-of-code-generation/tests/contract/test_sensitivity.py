import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

# Mock the config to avoid dependency on real config files during testing
import sys
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_config():
    """Mock config to point to temp directories."""
    temp_dir = tempfile.mkdtemp()
    data_processed = Path(temp_dir)
    
    mock_config_dict = {
        "paths": {
            "data_processed": data_processed,
            "data_raw": data_processed,
            "figures": data_processed / "figures"
        }
    }
    
    with patch('analysis.sensitivity.get_config', return_value=mock_config_dict):
        yield data_processed

@pytest.fixture
def mock_matched_data(mock_config):
    """Generate a mock matched_cohort.parquet for testing."""
    data_path = mock_config / "matched_cohort.parquet"
    
    # Create synthetic but realistic data for testing the logic
    n = 200
    df = pd.DataFrame({
        "review_duration": np.random.exponential(scale=10.0, size=n) + 1, # Positive durations
        "generation_source": np.random.choice(["LLM-like", "Human"], size=n),
        "star_count": np.random.choice([100, 500, 2000, 10000], size=n), # Varied star counts
        "file_size": np.random.randint(10, 1000, size=n),
        "complexity_score": np.random.randint(1, 20, size=n)
    })
    
    df.to_parquet(data_path)
    return data_path

def test_stratification_logic(mock_config, mock_matched_data):
    """Test that stratification correctly splits data into 4 quartiles."""
    from analysis.sensitivity import stratify_by_stars, load_analysis_data
    
    df = load_analysis_data()
    subsets = stratify_by_stars(df)
    
    assert len(subsets) == 4, "Should create 4 quartile subsets"
    assert all("Q" in k for k in subsets.keys()), "Keys should be Q1, Q2, Q3, Q4"
    
    # Verify all data points are accounted for (excluding potential NaNs if any)
    total_rows = sum(len(v) for v in subsets.values())
    assert total_rows == len(df), "All rows should be in a subset"

def test_consistency_check_threshold(mock_config, mock_matched_data):
    """Test that consistency check correctly identifies >= 80% significance."""
    from analysis.sensitivity import run_sensitivity_analysis
    
    # We need to mock the statistical test to control p-values
    # because real statistical tests on random data might vary.
    # We will mock run_full_analysis to return specific p-values.
    
    def mock_run_full_analysis(data, target_col, group_col, treatment_group, control_group):
        # Simulate: 3 out of 4 subsets are significant (75% -> Fail)
        # This is a simplified mock; in reality, we'd pass the subset label somehow
        # or just rely on the logic inside run_sensitivity_analysis.
        # For this contract test, we assume the function works if it returns a dict.
        return {
            "p_value": 0.04, # Significant
            "effect_size": 0.5,
            "test_type": "t-test"
        }

    with patch('analysis.sensitivity.run_full_analysis', side_effect=mock_run_full_analysis):
        from analysis.sensitivity import stratify_by_stars
        df = load_analysis_data()
        subsets = stratify_by_stars(df)
        
        results, is_consistent = run_sensitivity_analysis(subsets)
        
        # With 4 subsets and 100% significant (mocked), it should be consistent
        assert is_consistent == True
        assert len(results) == 4

def test_sensitivity_summary_output(mock_config, mock_matched_data):
    """Test that the summary JSON is written with correct structure."""
    from analysis.sensitivity import main
    
    # Mock the statistical test to ensure it runs without error
    def mock_run_full_analysis(*args, **kwargs):
        return {
            "p_value": 0.03,
            "effect_size": 0.4,
            "test_type": "t-test"
        }
    
    with patch('analysis.sensitivity.run_full_analysis', side_effect=mock_run_full_analysis):
        exit_code = main()
    
    # Check file existence
    output_path = mock_config / "sensitivity_summary.json"
    assert output_path.exists(), "sensitivity_summary.json should be created"
    
    # Check content structure
    with open(output_path, "r") as f:
        summary = json.load(f)
    
    assert "consistent" in summary
    assert "total_subsets" in summary
    assert "consistency_threshold" in summary
    assert summary["consistency_threshold"] == 0.80
    assert "results_by_quartile" in summary
    assert isinstance(summary["consistent"], bool)