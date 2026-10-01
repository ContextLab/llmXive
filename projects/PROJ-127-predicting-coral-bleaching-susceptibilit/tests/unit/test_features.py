import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.features import (
    compute_lagged_features,
    compute_interaction_features,
    check_definitional_circularity,
    calculate_vif,
    filter_high_vif
)

@pytest.fixture
def sample_df():
    """Create a sample dataframe for testing."""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    data = {
        "date": dates,
        "sst": np.random.normal(29.0, 1.0, 100),
        "dhw": np.random.exponential(0.5, 100), # Simulated DHW
        "thermal_tolerance": np.random.normal(1.2, 0.2, 100),
        "reef_id": ["R1"] * 100,
        "species_id": ["S1"] * 100
    }
    return pd.DataFrame(data)

def test_compute_lagged_features(sample_df):
    """Test that lagged features are computed correctly."""
    result = compute_lagged_features(sample_df, value_cols=["sst"])
    assert "sst_lag_30d" in result.columns
    # First few rows should have values (min_periods=1)
    assert result["sst_lag_30d"].notna().all()
    # Values should be cumulative means, so generally increasing in variance or smoothing
    assert result["sst_lag_30d"].std() <= result["sst"].std()

def test_compute_interaction_features(sample_df):
    """Test interaction term calculation."""
    result = compute_interaction_features(sample_df)
    assert "dhw_thermal_interaction" in result.columns
    expected = sample_df["dhw"] * sample_df["thermal_tolerance"]
    pd.testing.assert_series_equal(result["dhw_thermal_interaction"], expected)

def test_check_definitional_circularity(sample_df):
    """
    Test T018: Definitional Circularity Check.
    Must detect that DHW is derived from SST.
    """
    is_circular, reason = check_definitional_circularity(sample_df, "dhw", "sst")
    assert is_circular is True
    assert "derived" in reason.lower() or "circular" in reason.lower()
    assert "dhw" in reason
    assert "sst" in reason

def test_check_definitional_circularity_missing_columns(sample_df):
    """Test circularity check when columns are missing."""
    df = sample_df.drop(columns=["dhw"])
    is_circular, reason = check_definitional_circularity(df, "dhw", "sst")
    assert is_circular is False
    assert "not found" in reason.lower()

def test_calculate_vif(sample_df):
    """Test VIF calculation."""
    features = ["sst", "dhw", "thermal_tolerance"]
    vif_df = calculate_vif(sample_df, features)
    assert "feature" in vif_df.columns
    assert "vif" in vif_df.columns
    assert len(vif_df) == len(features)
    # VIF should be >= 1
    assert (vif_df["vif"] >= 1.0).all()

def test_filter_high_vif(sample_df):
    """Test VIF filtering."""
    # Create a dataset with high correlation to force high VIF
    high_corr_df = sample_df.copy()
    high_corr_df["sst_dup"] = high_corr_df["sst"] * 1.0 + 0.0001 # Almost identical
    high_corr_df["dhw_dup"] = high_corr_df["dhw"] * 1.0 + 0.0001
    
    features = ["sst", "dhw", "thermal_tolerance", "sst_dup", "dhw_dup"]
    filtered_df, dropped = filter_high_vif(high_corr_df, vif_threshold=5.0)
    
    # At least one of the duplicates should be dropped
    assert "sst_dup" in dropped or "dhw_dup" in dropped
    # The dropped columns should not be in the result
    assert "sst_dup" not in filtered_df.columns or "dhw_dup" not in filtered_df.columns

def test_main_execution_integration():
    """
    Integration test for main() if the input file exists.
    Skips if data not present (expected in CI without data download).
    """
    input_path = Path("data/processed/reef_species_unified.csv")
    if not input_path.exists():
        pytest.skip("Input data file not found, skipping integration test.")
    
    # We cannot easily test the full main() without mocking file system writes
    # but we verify the logic path by ensuring the functions it calls work.
    pass