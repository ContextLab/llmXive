"""
Unit tests for sensitivity analysis (T033b).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling import compute_sensitivity_analysis, run_sensitivity_analysis

@pytest.fixture
def sample_df():
    """Create a sample dataframe with required columns."""
    data = {
        'adherence_label': [1, 0, 1, 0, 1],
        'safety_refusal': [0, 0, 1, 0, 0],
        'pred_prob_adherent': [0.9, 0.1, 0.6, 0.4, 0.8]
    }
    return pd.DataFrame(data)

def test_compute_sensitivity_analysis_threshold_05(sample_df):
    """Test sensitivity analysis at threshold 0.5."""
    result = compute_sensitivity_analysis(sample_df, 0.5)
    
    assert result['threshold'] == 0.5
    # ASR: 3 adherent out of 5 -> 0.6
    assert np.isclose(result['asr'], 0.6)
    # Refusal: 1 refusal out of 5 -> 0.2
    assert np.isclose(result['refusal_rate'], 0.2)
    # Variance should be a float
    assert isinstance(result['variance'], float)

def test_compute_sensitivity_analysis_threshold_01(sample_df):
    """Test sensitivity analysis at threshold 0.1."""
    result = compute_sensitivity_analysis(sample_df, 0.1)
    
    assert result['threshold'] == 0.1
    # All predicted adherent since min prob is 0.1 (>= 0.1)
    # ASR is still based on actual labels: 3/5 = 0.6
    assert np.isclose(result['asr'], 0.6)
    assert np.isclose(result['refusal_rate'], 0.2)

def test_run_sensitivity_analysis(sample_df, tmp_path):
    """Test the full sensitivity analysis pipeline."""
    # Mock the global output path by changing the current working directory or passing a path
    # For this test, we just verify the function returns a dataframe
    df_result = run_sensitivity_analysis(sample_df)
    
    assert isinstance(df_result, pd.DataFrame)
    assert 'threshold' in df_result.columns
    assert 'asr' in df_result.columns
    assert 'refusal_rate' in df_result.columns
    assert 'variance' in df_result.columns
    assert len(df_result) == 3 # 3 thresholds

def test_missing_column_raises_error(sample_df):
    """Test that missing 'pred_prob_adherent' raises an error."""
    df_missing = sample_df.drop(columns=['pred_prob_adherent'])
    with pytest.raises(Exception): # DataAmbiguityError
        compute_sensitivity_analysis(df_missing, 0.5)