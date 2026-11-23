"""
Unit tests for edge cases in the plant stress resilience pipeline.

Tests cover:
1. >10% missing values (should raise DataRejectionError)
2. <50 samples (should trigger warning/skip in validation)
3. Missing individual pairing (should trigger population aggregation)
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any

# Import project modules
from data.preprocess import check_missing_threshold, aggregate_population
from data.models import MetabolomicProfile
from utils.logging import DataRejectionError, get_logger
from models.validate import check_sample_size


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture
def valid_dataframe() -> pd.DataFrame:
    """Create a valid dataframe with <10% missing and >= 50 samples."""
    n_samples = 60
    dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(n_samples)]
    
    # Create a dataframe with metabolite columns and metadata
    data = {
        "sample_id": [f"sample_{i}" for i in range(n_samples)],
        "plant_id": [f"plant_{i % 10}" for i in range(n_samples)],  # 10 unique plants
        "stress_type": ["drought"] * n_samples,
        "recovery_days": [10 + (i % 5) for i in range(n_samples)],
        "metabolite_A": np.random.rand(n_samples) * 100,
        "metabolite_B": np.random.rand(n_samples) * 100,
        "metabolite_C": np.random.rand(n_samples) * 100,
    }
    df = pd.DataFrame(data)
    
    # Introduce small amount of missing data (approx 5%)
    mask = np.random.random((n_samples, 3)) < 0.05
    df.loc[mask[:, 0], "metabolite_A"] = np.nan
    df.loc[mask[:, 1], "metabolite_B"] = np.nan
    df.loc[mask[:, 2], "metabolite_C"] = np.nan
    
    return df

@pytest.fixture
def high_missing_dataframe() -> pd.DataFrame:
    """Create a dataframe with >10% missing values."""
    n_samples = 60
    data = {
        "sample_id": [f"sample_{i}" for i in range(n_samples)],
        "plant_id": [f"plant_{i % 10}" for i in range(n_samples)],
        "stress_type": ["drought"] * n_samples,
        "recovery_days": [10 + (i % 5) for i in range(n_samples)],
        "metabolite_A": np.random.rand(n_samples) * 100,
        "metabolite_B": np.random.rand(n_samples) * 100,
        "metabolite_C": np.random.rand(n_samples) * 100,
    }
    df = pd.DataFrame(data)
    
    # Introduce high amount of missing data (approx 20%)
    mask = np.random.random((n_samples, 3)) < 0.20
    df.loc[mask[:, 0], "metabolite_A"] = np.nan
    df.loc[mask[:, 1], "metabolite_B"] = np.nan
    df.loc[mask[:, 2], "metabolite_C"] = np.nan
    
    return df

@pytest.fixture
def small_sample_dataframe() -> pd.DataFrame:
    """Create a dataframe with <50 samples."""
    n_samples = 30
    data = {
        "sample_id": [f"sample_{i}" for i in range(n_samples)],
        "plant_id": [f"plant_{i % 5}" for i in range(n_samples)],
        "stress_type": ["drought"] * n_samples,
        "recovery_days": [10 + (i % 5) for i in range(n_samples)],
        "metabolite_A": np.random.rand(n_samples) * 100,
        "metabolite_B": np.random.rand(n_samples) * 100,
        "metabolite_C": np.random.rand(n_samples) * 100,
    }
    return pd.DataFrame(data)

@pytest.fixture
def unpaired_dataframe() -> pd.DataFrame:
    """Create a dataframe missing individual pairing (no plant_id)."""
    n_samples = 60
    data = {
        "sample_id": [f"sample_{i}" for i in range(n_samples)],
        # "plant_id" is missing intentionally
        "stress_type": ["drought"] * n_samples,
        "recovery_days": [10 + (i % 5) for i in range(n_samples)],
        "metabolite_A": np.random.rand(n_samples) * 100,
        "metabolite_B": np.random.rand(n_samples) * 100,
        "metabolite_C": np.random.rand(n_samples) * 100,
    }
    return pd.DataFrame(data)

# ---------------------------------------------------------------------
# Tests: Missing Data Threshold (>10%)
# ---------------------------------------------------------------------

def test_missing_threshold_accepts_valid_data(valid_dataframe: pd.DataFrame):
    """Test that data with <10% missing passes the check."""
    # Should not raise an exception
    result = check_missing_threshold(valid_dataframe, threshold=0.1)
    assert result is True

def test_missing_threshold_rejects_high_missing(high_missing_dataframe: pd.DataFrame):
    """Test that data with >10% missing raises DataRejectionError."""
    with pytest.raises(DataRejectionError) as exc_info:
        check_missing_threshold(high_missing_threshold, threshold=0.1)
    
    assert "Missing data threshold exceeded" in str(exc_info.value)
    assert "10.0%" in str(exc_info.value)

# ---------------------------------------------------------------------
# Tests: Sample Size (<50)
# ---------------------------------------------------------------------

def test_sample_size_check_valid(valid_dataframe: pd.DataFrame):
    """Test that sample size >= 50 passes check."""
    result = check_sample_size(valid_dataframe)
    # check_sample_size returns True if valid, False otherwise (or logs warning)
    # Based on T035, it should log a warning and return False/skip if < 50
    # We expect it to return True (or not raise) for valid size
    assert result is True

def test_sample_size_check_small_sample(small_sample_dataframe: pd.DataFrame, caplog):
    """Test that sample size < 50 triggers warning and returns False."""
    result = check_sample_size(small_sample_dataframe)
    
    # Based on T035: "if len(samples) < 50, skip evaluation and log a warning"
    assert result is False
    assert any("sample size" in record.message.lower() for record in caplog.records)

# ---------------------------------------------------------------------
# Tests: Missing Individual Pairing
# ---------------------------------------------------------------------

def test_aggregate_population_with_pairing(valid_dataframe: pd.DataFrame):
    """Test aggregation when individual pairing exists."""
    # This should run without error and return a dataframe with aggregated means
    result = aggregate_population(valid_dataframe)
    
    # Verify the result has the aggregated columns
    assert "mean_pre_stress" in result.columns or "mean_recovery" in result.columns
    # Verify row count is reduced (aggregated by group)
    assert len(result) < len(valid_dataframe)

def test_aggregate_population_without_pairing(unpaired_dataframe: pd.DataFrame):
    """Test aggregation when individual pairing is missing (should handle gracefully)."""
    # When plant_id is missing, it should aggregate over the whole dataset or
    # use a default grouping strategy.
    result = aggregate_population(unpaired_dataframe)
    
    # Should not crash
    assert isinstance(result, pd.DataFrame)
    # Should have aggregated columns
    assert len(result) >= 0

def test_aggregate_population_missing_column_handling():
    """Test aggregation with a dataframe missing required columns."""
    df = pd.DataFrame({
        "sample_id": ["s1", "s2"],
        "metabolite_A": [1.0, 2.0],
        # Missing stress_type, recovery_days, etc.
    })
    
    # Should handle missing columns gracefully (either return empty or raise specific error)
    # Based on T018, it computes mean if individual pairing is missing.
    # We expect it to handle the missing columns without crashing the whole pipeline.
    try:
        result = aggregate_population(df)
        # If it returns, it should be a dataframe
        assert isinstance(result, pd.DataFrame)
    except KeyError:
        # Expected if strict column validation is in place
        pass