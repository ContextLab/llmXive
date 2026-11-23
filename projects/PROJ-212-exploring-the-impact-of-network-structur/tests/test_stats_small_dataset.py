"""
Unit test for src/stats.py handling of small datasets (<10) with warning generation.

This test verifies that when the dataset size is less than 10, the regression
functions output descriptive statistics and generate a warning without attempting
full regression analysis, as per FR-004.
"""
import pytest
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from stats import run_regression
from config import load_config


def test_small_dataset_warning_generation():
    """
    Test that run_regression handles small datasets (N < 10) correctly:
    1. Outputs descriptive statistics
    2. Generates a warning about insufficient data
    3. Does NOT attempt full regression
    4. Returns a valid result object with appropriate flags
    """
    # Create a small dataset (N=8, which is < 10)
    small_data = pd.DataFrame({
        'degree': np.random.rand(8),
        'clustering': np.random.rand(8),
        'path_length': np.random.rand(8),
        'threshold': np.random.rand(8) * 5  # Random threshold values
    })

    # Load config for alpha parameter
    config = load_config()
    alpha = config.get('thresholds', {}).get('alpha', 0.05)

    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Run regression on small dataset
        result = run_regression(small_data, alpha=alpha)
        
        # Verify a warning was raised
        assert len(w) >= 1, "Expected at least one warning for small dataset"
        
        # Check that the warning message contains relevant information
        warning_messages = [str(warning.message) for warning in w]
        warning_text = " ".join(warning_messages)
        assert "small dataset" in warning_text.lower() or "insufficient" in warning_text.lower(), \
            f"Warning message should mention small dataset or insufficient data. Got: {warning_text}"
        assert "n=8" in warning_text or "8 samples" in warning_text, \
            f"Warning should mention sample size. Got: {warning_text}"

    # Verify result object structure
    assert result is not None, "run_regression should return a result object"
    assert hasattr(result, 'status'), "Result should have a status attribute"
    assert hasattr(result, 'warning'), "Result should have a warning attribute"
    
    # Verify the warning flag is set
    assert result.warning is not None, "Warning field should be populated"
    assert "small dataset" in result.warning.lower() or "insufficient" in result.warning.lower(), \
        f"Result warning should mention small dataset. Got: {result.warning}"
    
    # Verify regression was NOT performed (or marked as skipped)
    # The result should indicate that full regression was skipped
    assert result.skipped or result.status == "warning", \
        f"Regression should be skipped or marked as warning. Got status: {result.status}, skipped: {result.skipped}"
    
    # Verify descriptive statistics are present
    assert hasattr(result, 'descriptive_stats'), "Result should include descriptive statistics"
    assert result.descriptive_stats is not None, "Descriptive statistics should not be None"
    
    # Check that sample size is correctly reported
    assert result.descriptive_stats.get('n') == 8, \
        f"Descriptive stats should report n=8. Got: {result.descriptive_stats.get('n')}"

def test_dataset_size_boundary():
    """
    Test the boundary condition: N=9 should trigger warning, N=10 should not.
    """
    # Test N=9 (should trigger warning)
    data_9 = pd.DataFrame({
        'degree': np.random.rand(9),
        'clustering': np.random.rand(9),
        'path_length': np.random.rand(9),
        'threshold': np.random.rand(9) * 5
    })

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result_9 = run_regression(data_9)
        assert len(w) >= 1, "N=9 should trigger a warning"
        assert result_9.skipped or result_9.status == "warning", "N=9 should skip regression"

    # Test N=10 (should NOT trigger warning for small dataset)
    data_10 = pd.DataFrame({
        'degree': np.random.rand(10),
        'clustering': np.random.rand(10),
        'path_length': np.random.rand(10),
        'threshold': np.random.rand(10) * 5
    })

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result_10 = run_regression(data_10)
        # N=10 should proceed with regression (may still have other warnings, but not small dataset)
        small_ds_warnings = [
            warning for warning in w 
            if "small dataset" in str(warning.message).lower() or "insufficient" in str(warning.message).lower()
        ]
        assert len(small_ds_warnings) == 0, "N=10 should not trigger small dataset warning"
        # Regression should proceed (not skipped)
        assert not (result_10.skipped or result_10.status == "warning"), \
            "N=10 should proceed with regression"