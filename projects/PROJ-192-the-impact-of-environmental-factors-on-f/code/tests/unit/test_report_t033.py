import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from src.pipelines.report import run_threshold_sweep, load_permanova_results, apply_fdr_correction

@pytest.fixture
def sample_permanova_data():
    """
    Creates a realistic sample PERMANOVA dataframe for testing T033.
    """
    data = {
        "term": ["pH", "Nutrients", "Moisture", "Temperature", "Organic_Matter"],
        "R2": [0.15, 0.25, 0.08, 0.12, 0.20],
        "p-value": [0.001, 0.003, 0.15, 0.04, 0.02]
    }
    return pd.DataFrame(data)

def test_threshold_sweep_basic(sample_permanova_data):
    """
    Test T033: Basic sweep logic.
    Verifies that the function returns a DataFrame with correct structure
    and that filtering logic works.
    """
    # Run sweep
    results = run_threshold_sweep(
        sample_permanova_data,
        p_thresholds=[0.05],
        r2_thresholds=[0.10]
    )

    # Check structure
    assert "p_thresh" in results.columns
    assert "r2_thresh" in results.columns
    assert "top_driver" in results.columns
    assert "significant_terms_count" in results.columns

    # Check logic:
    # For p<=0.05 and R2>=0.10:
    # pH (0.001, 0.15) -> Keep
    # Nutrients (0.003, 0.25) -> Keep
    # Moisture (0.15, 0.08) -> Drop (p > 0.05)
    # Temperature (0.04, 0.12) -> Keep
    # Organic_Matter (0.02, 0.20) -> Keep
    # Top driver should be Nutrients (R2=0.25)
    
    row = results.iloc[0]
    assert row["p_thresh"] == 0.05
    assert row["r2_thresh"] == 0.10
    assert row["top_driver"] == "Nutrients"
    assert row["significant_terms_count"] == 4

def test_threshold_sweep_strict():
    """
    Test T033: Strict thresholds resulting in no significant terms.
    """
    data = {
        "term": ["pH", "Nutrients"],
        "R2": [0.05, 0.06],
        "p-value": [0.01, 0.01]
    }
    df = pd.DataFrame(data)
    
    results = run_threshold_sweep(
        df,
        p_thresholds=[0.05],
        r2_thresholds=[0.10] # Higher than any R2
    )
    
    row = results.iloc[0]
    assert row["top_driver"] == "None"
    assert row["significant_terms_count"] == 0

def test_threshold_sweep_multiple_thresholds(sample_permanova_data):
    """
    Test T033: Multiple thresholds produce multiple rows.
    """
    results = run_threshold_sweep(
        sample_permanova_data,
        p_thresholds=[0.05, 0.01],
        r2_thresholds=[0.10, 0.20]
    )
    
    # 2 p-thresh * 2 r2-thresh = 4 rows
    assert len(results) == 4

def test_threshold_sweep_with_fdr_correction(sample_permanova_data):
    """
    Test T033: Function handles raw p-values and applies FDR internally.
    """
    # Ensure no p-value_adj exists initially
    assert "p-value_adj" not in sample_permanova_data.columns
    
    # The run_threshold_sweep should handle this
    results = run_threshold_sweep(
        sample_permanova_data,
        p_thresholds=[0.1],
        r2_thresholds=[0.1]
    )
    
    assert len(results) > 0
    assert "top_driver" in results.columns

def test_threshold_sweep_empty_input():
    """
    Test T033: Handles empty DataFrame gracefully.
    """
    df = pd.DataFrame(columns=["term", "R2", "p-value"])
    results = run_threshold_sweep(df, p_thresholds=[0.05], r2_thresholds=[0.1])
    
    assert len(results) > 0 # Should still produce rows for thresholds, just empty results
    assert results["top_driver"].iloc[0] == "None"
    assert results["significant_terms_count"].iloc[0] == 0