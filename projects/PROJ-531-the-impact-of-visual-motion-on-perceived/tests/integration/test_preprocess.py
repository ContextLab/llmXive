"""
Integration test for the preprocessing pipeline (T014).

Verifies:
- VIF calculation logic
- Missing value handling
- Feature extraction correctness
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add project root to path if running from tests
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.preprocessing.preprocess import (
    extract_motion_features,
    aggregate_agency_scores,
    calculate_vif,
    run_preprocessing,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    INTERMEDIATE_FEATURES_PATH,
    VIF_REPORT_PATH
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    # Create expected subdirectories
    os.makedirs(os.path.join(temp_dir, "raw"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "processed"), exist_ok=True)
    
    # Override global paths for this test
    original_raw = DATA_RAW_DIR
    original_processed = DATA_PROCESSED_DIR
    
    # We cannot easily override global Path objects in the module,
    # so we will test the functions directly with dataframes instead of relying on file I/O.
    # This fixture is kept for potential future file-based tests.
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_extract_motion_features_latency():
    """Test latency extraction from different column configurations."""
    
    # Case 1: interaction_delay present
    df = pd.DataFrame({
        "interaction_delay": [100, 200, 300],
        "other_col": [1, 2, 3]
    })
    result = extract_motion_features(df)
    assert "latency" in result.columns
    assert result["latency"].tolist() == [100, 200, 300]
    
    # Case 2: user_trigger_time and system_response_time present
    df = pd.DataFrame({
        "user_trigger_time": [1000, 2000, 3000],
        "system_response_time": [1100, 2200, 3300],
        "other_col": [1, 2, 3]
    })
    result = extract_motion_features(df)
    assert "latency" in result.columns
    assert result["latency"].tolist() == [100, 200, 300]
    
    # Case 3: reaction_time present
    df = pd.DataFrame({
        "reaction_time": [150, 250, 350],
        "other_col": [1, 2, 3]
    })
    result = extract_motion_features(df)
    assert "latency" in result.columns
    assert result["latency"].tolist() == [150, 250, 350]

def test_extract_motion_features_smoothness():
    """Test smoothness extraction from velocity data."""
    
    # Case 1: smoothness already present
    df = pd.DataFrame({
        "smoothness": [0.8, 0.9, 0.7],
        "other_col": [1, 2, 3]
    })
    result = extract_motion_features(df)
    assert result["smoothness"].tolist() == [0.8, 0.9, 0.7]
    
    # Case 2: velocity list provided
    df = pd.DataFrame({
        "movement_velocity": [[1, 2, 3, 4, 5], [1, 1, 1, 1, 1], [1, 3, 6, 10, 15]],
        "other_col": [1, 2, 3]
    })
    result = extract_motion_features(df)
    assert "smoothness" in result.columns
    # Smoothness should be calculated (0-1 range)
    assert all(0 <= s <= 1 for s in result["smoothness"])

def test_extract_motion_features_lead_time():
    """Test lead_time extraction."""
    
    # Case 1: lead_time present
    df = pd.DataFrame({
        "lead_time": [50, 60, 70],
        "other_col": [1, 2, 3]
    })
    result = extract_motion_features(df)
    assert result["lead_time"].tolist() == [50, 60, 70]
    
    # Case 2: calculated from trigger/predicted
    df = pd.DataFrame({
        "user_trigger_time": [1000, 2000, 3000],
        "predicted_response_time": [1050, 2060, 3070],
        "other_col": [1, 2, 3]
    })
    result = extract_motion_features(df)
    assert result["lead_time"].tolist() == [50, 60, 70]
    
    # Case 3: no lead time data (should default to 0)
    df = pd.DataFrame({
        "other_col": [1, 2, 3]
    })
    # This case is tricky because extract_motion_features might raise if no latency/smoothness found.
    # We assume valid input for lead_time test (latency/smoothness must be present).
    df["latency"] = [10, 20, 30]
    df["smoothness"] = [0.5, 0.6, 0.7]
    result = extract_motion_features(df)
    assert result["lead_time"].tolist() == [0.0, 0.0, 0.0]

def test_aggregate_agency_scores_single():
    """Test aggregation when single agency score column exists."""
    df = pd.DataFrame({
        "agency_score": [0.5, 0.6, 0.7],
        "other": [1, 2, 3]
    })
    result = aggregate_agency_scores(df)
    assert result["agency_score"].tolist() == [0.5, 0.6, 0.7]

def test_aggregate_agency_scores_multiple():
    """Test aggregation when multiple rating columns exist."""
    df = pd.DataFrame({
        "agency_rating_1": [0.4, 0.5, 0.6],
        "agency_rating_2": [0.6, 0.7, 0.8],
        "other": [1, 2, 3]
    })
    result = aggregate_agency_scores(df)
    expected = [0.5, 0.6, 0.7] # Mean of (0.4, 0.6), (0.5, 0.7), (0.6, 0.8)
    assert result["agency_score"].tolist() == expected

def test_aggregate_agency_scores_normalize():
    """Test normalization of agency scores > 1."""
    df = pd.DataFrame({
        "agency_rating_1": [4, 5, 6],
        "agency_rating_2": [6, 7, 8],
        "other": [1, 2, 3]
    })
    result = aggregate_agency_scores(df)
    # Mean is [5, 6, 7], normalized to [0.5, 0.6, 0.7]
    expected = [0.5, 0.6, 0.7]
    assert result["agency_score"].tolist() == expected

def test_calculate_vif_no_collinearity():
    """Test VIF calculation with uncorrelated features."""
    # Create data with low correlation
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "latency": np.random.normal(100, 20, n),
        "smoothness": np.random.normal(0.5, 0.1, n),
        "lead_time": np.random.normal(50, 10, n)
    })
    
    vif_results = calculate_vif(df, ["latency", "smoothness", "lead_time"])
    
    assert "latency" in vif_results
    assert "smoothness" in vif_results
    assert "lead_time" in vif_results
    
    # With random data, VIF should be close to 1 (no collinearity)
    for vif_val in vif_results.values():
        assert 0.9 < vif_val < 5.0, f"Unexpected VIF value: {vif_val}"

def test_calculate_vif_high_collinearity():
    """Test VIF calculation with highly correlated features."""
    np.random.seed(42)
    n = 100
    x = np.random.normal(0, 1, n)
    df = pd.DataFrame({
        "latency": x,
        "smoothness": x * 2 + np.random.normal(0, 0.1, n), # Highly correlated
        "lead_time": np.random.normal(0, 1, n)
    })
    
    vif_results = calculate_vif(df, ["latency", "smoothness", "lead_time"])
    
    # latency and smoothness should have high VIF
    assert vif_results["latency"] >= 5.0 or vif_results["smoothness"] >= 5.0

def test_missing_value_handling_in_vif():
    """Test that VIF calculation handles missing values gracefully."""
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "latency": np.random.normal(100, 20, n),
        "smoothness": np.random.normal(0.5, 0.1, n),
        "lead_time": np.random.normal(50, 10, n)
    })
    
    # Introduce NaNs
    df.loc[0, "latency"] = np.nan
    df.loc[1, "smoothness"] = np.nan
    
    # Should not raise, should drop NaNs internally
    vif_results = calculate_vif(df, ["latency", "smoothness", "lead_time"])
    
    assert len(vif_results) == 3
    assert all(isinstance(v, float) for v in vif_results.values())