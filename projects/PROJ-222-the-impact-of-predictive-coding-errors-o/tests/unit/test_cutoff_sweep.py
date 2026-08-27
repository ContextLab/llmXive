import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json

from config import get_data_dir
from analysis import run_cutoff_sweeping_analysis, run_analysis_pipeline_full

def test_cutoff_sweeping_logic():
    """Test that cutoff sweeping produces expected structure."""
    # Create a mock result dict
    mock_results = {
        "pval": 0.03,
        "coef": 0.5
    }
    
    # Create a mock dataframe
    df = pd.DataFrame({
        "duration_estimate": [10, 20, 30],
        "surprisal": [1, 2, 3],
        "participant_id": [1, 2, 3]
    })
    
    result = run_cutoff_sweeping_analysis(df, mock_results)
    
    assert "p_value_sweep" in result
    assert "effect_size_sweep" in result
    assert len(result["p_value_sweep"]) == 10
    assert result["p_value_sweep"][0]["cutoff"] == 0.01
    
    # Check logic: at 0.01 cutoff, 0.03 is not significant
    assert result["p_value_sweep"][0]["is_significant"] == False
    # At 0.10 cutoff, 0.03 is significant
    assert result["p_value_sweep"][-1]["is_significant"] == True

def test_cutoff_sweeping_missing_data():
    """Test behavior when p-value is missing."""
    mock_results = {
        "pval": None,
        "coef": 0.5
    }
    df = pd.DataFrame({"a": [1]})
    
    result = run_cutoff_sweeping_analysis(df, mock_results)
    
    assert result["status"] == "skipped"
    assert "missing data" in result["reason"]

def test_full_pipeline_integration():
    """Test that the full pipeline runs and includes cutoff sensitivity."""
    # This might fail if data is not present, but tests the structure
    # We assume T017 has run and data exists
    try:
        results = run_analysis_pipeline_full()
        assert "cutoff_sensitivity" in results
        assert "p_value_sweep" in results["cutoff_sensitivity"]
    except FileNotFoundError:
        # Expected if data not downloaded yet
        pytest.skip("Data not available for integration test")
