"""
Unit tests for code/analysis/sensitivity.py

Verifies:
1. Outlier removal functions (IQR, Winsorization) work correctly.
2. The 3x2 matrix is generated correctly.
3. Stability threshold violation is raised when variation is high.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from analysis.sensitivity import remove_outliers_iqr, winsorize_data, run_single_regression, run_sensitivity_analysis
from utils.exceptions import StabilityThresholdViolationError
from utils.constants import get_stability_threshold

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    np.random.seed(42)
    n = 200
    df = pd.DataFrame({
        "perceived_social_validation": np.random.normal(50, 10, n),
        "self_perception_score": np.random.normal(50, 10, n),
        "age": np.random.randint(13, 19, n),
        "gender": np.random.choice(["M", "F"], n),
        "offline_relationships": np.random.normal(50, 10, n),
        "intrinsic_traits": np.random.normal(50, 10, n)
    })
    return df

@pytest.fixture
def df_with_outliers():
    """Create a DataFrame with obvious outliers."""
    df = pd.DataFrame({
        "perceived_social_validation": [10, 12, 11, 13, 12, 100, -50], # 100 and -50 are outliers
        "self_perception_score": [10, 12, 11, 13, 12, 100, -50],
        "age": [15, 16, 15, 16, 15, 15, 15],
        "gender": ["M", "F", "M", "F", "M", "M", "F"],
        "offline_relationships": [10, 12, 11, 13, 12, 100, -50],
        "intrinsic_traits": [10, 12, 11, 13, 12, 100, -50]
    })
    return df

def test_remove_outliers_iqr(df_with_outliers):
    """Test that IQR removal actually removes the outliers."""
    initial_len = len(df_with_outliers)
    cleaned_df = remove_outliers_iqr(df_with_outliers, "perceived_social_validation")
    
    # We expect 2 outliers to be removed (100 and -50)
    assert len(cleaned_df) == initial_len - 2
    # Verify the specific values are gone
    assert 100 not in cleaned_df["perceived_social_validation"].values
    assert -50 not in cleaned_df["perceived_social_validation"].values

def test_winsorize_data(df_with_outliers):
    """Test that winsorization reduces the extreme values."""
    original_max = df_with_outliers["perceived_social_validation"].max()
    original_min = df_with_outliers["perceived_social_validation"].min()
    
    winsorized_df = winsorize_data(df_with_outliers, "perceived_social_validation", limits=0.15)
    
    new_max = winsorized_df["perceived_social_validation"].max()
    new_min = winsorized_df["perceived_social_validation"].min()
    
    # Max should decrease, min should increase
    assert new_max < original_max
    assert new_min > original_min
    # Length should remain the same
    assert len(winsorized_df) == len(df_with_outliers)

def test_run_single_regression(sample_df):
    """Test that regression runs and returns expected structure."""
    coef, p_val, is_sig = run_single_regression(sample_df, include_confounders=True)
    
    assert isinstance(coef, float)
    assert isinstance(p_val, float)
    assert isinstance(is_sig, bool)
    assert 0 <= p_val <= 1

def test_run_sensitivity_analysis_matrix(sample_df, tmp_path):
    """Test that the full matrix is generated and saved."""
    output_file = tmp_path / "test_sensitivity.json"
    
    results = run_sensitivity_analysis(sample_df, str(output_file))
    
    assert "matrix" in results
    assert len(results["matrix"]) == 6 # 3 strategies * 2 confounder states
    
    # Check structure of one result
    first_run = results["matrix"][0]
    assert "run_id" in first_run
    assert "coefficient" in first_run
    assert "p_value" in first_run

def test_stability_threshold_violation(sample_df, tmp_path):
    """Test that a high variation triggers the error."""
    # Mock the data to have extremely high variation in coefficients
    # We do this by patching run_single_regression to return widely varying coefficients
    
    # Create a fake dataset where the relationship is noisy
    np.random.seed(123)
    noisy_df = pd.DataFrame({
        "perceived_social_validation": np.random.normal(0, 100, 50), # High variance
        "self_perception_score": np.random.normal(0, 100, 50), # No real correlation
        "age": np.random.randint(13, 19, 50),
        "gender": np.random.choice(["M", "F"], 50),
        "offline_relationships": np.random.normal(0, 100, 50),
        "intrinsic_traits": np.random.normal(0, 100, 50)
    })

    output_file = tmp_path / "test_violation.json"
    
    # The threshold is usually small (e.g., 0.1). With random noise, variation might be high.
    # However, to guarantee a failure in a unit test, we might need to mock the result calculation
    # or ensure the random seed produces high variance. 
    # For robustness, we will mock the threshold to be very low to force a failure if variation exists.
    
    with patch('analysis.sensitivity.get_stability_threshold', return_value=0.0001):
        with pytest.raises(StabilityThresholdViolationError):
            run_sensitivity_analysis(noisy_df, str(output_file))
            
    # Verify the file was not written or contains the failure state if the logic allows partial write
    # In our implementation, we raise before writing if the check fails at the end.
    # But if we want to ensure the file exists with status FAIL, we check the logic.
    # Our implementation raises AFTER calculating variation, so file might not be written if we raise before dump.
    # Actually, looking at the code: we calculate variation, check, then raise.
    # So the file might not exist if we raise before the dump. 
    # Let's adjust the test to expect the exception.
    
    # Re-run to ensure file is not created on failure (based on current code logic: raise before dump)
    # Wait, the code does:
    # results["primary_coefficient_variation"] = variation
    # if variation > threshold: raise ...
    # So file is NOT written on failure in the current implementation.
    # This is acceptable behavior for a "halt" scenario.
    assert not os.path.exists(output_file)