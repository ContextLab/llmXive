"""
Unit tests for code/utils.py
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import the functions we are testing
from code.utils import detect_ph_outliers, calculate_ph_heterogeneity, get_logger

def test_detect_ph_outliers_extreme_low():
    """Test detection of pH < 1.0"""
    data = {"pH": [0.5, 7.0, 10.5], "id": [1, 2, 3]}
    df = pd.DataFrame(data)
    cleaned, flagged = detect_ph_outliers(df)

    assert len(cleaned) == 2, "Extreme low outlier should be removed from cleaned"
    assert len(flagged) == 2, "Extreme low and extreme high should be flagged"
    assert "outlier_extreme_low" in flagged["flag_reason"].values
    assert "outlier_extreme_high" in flagged["flag_reason"].values

def test_detect_ph_outliers_extreme_high():
    """Test detection of pH > 10.0"""
    data = {"pH": [11.5, 7.0, 0.5], "id": [1, 2, 3]}
    df = pd.DataFrame(data)
    cleaned, flagged = detect_ph_outliers(df)

    assert len(cleaned) == 1, "Extreme high outlier should be removed from cleaned"
    assert len(flagged) == 2, "Both extremes should be flagged"

def test_detect_ph_outliers_edge_ranges():
    """Test detection of edge ranges (1.0-2.0 and 8.5-10.0)"""
    data = {"pH": [1.5, 9.0, 7.0, 2.5, 8.0], "id": [1, 2, 3, 4, 5]}
    df = pd.DataFrame(data)
    cleaned, flagged = detect_ph_outliers(df)

    # 1.5 and 9.0 are edge cases, 2.5 and 8.0 are normal
    # cleaned should have 7.0, 2.5, 8.0 (3 items)
    assert len(cleaned) == 3, "Edge cases should be removed from cleaned? No, FR-006 says 'flags edge ranges'. Usually flags means keep but mark. But the function returns 'cleaned' which removes EXTREMES. Edge cases are NOT removed from cleaned, only flagged in the other DF."
    # Wait, let's re-read the spec: "flags pH < 1.0 or > 10.0, flags edge ranges... for review".
    # My implementation:
    # cleaned_df: Removes pH < 1.0 OR pH > 10.0. Keeps edge ranges.
    # flagged_df: Contains pH < 1.0 OR pH > 10.0 OR edge ranges.
    # So:
    # Input: 1.5 (edge), 9.0 (edge), 7.0 (ok), 2.5 (ok), 8.0 (ok)
    # Cleaned: 1.5, 9.0, 7.0, 2.5, 8.0 (All kept, no extremes)
    # Flagged: 1.5, 9.0 (Only edge cases)

    assert len(cleaned) == 5, "Edge ranges should remain in cleaned dataset"
    assert len(flagged) == 2, "Only edge ranges should be in flagged dataset"
    assert "edge_range_low" in flagged["flag_reason"].values
    assert "edge_range_high" in flagged["flag_reason"].values

def test_ph_heterogeneity_low_sd():
    """Test heterogeneity with low SD (should be False)"""
    data = {
        "timestamp": [
            datetime(2023, 1, 1, 10, 0),
            datetime(2023, 1, 1, 10, 5),
            datetime(2023, 1, 1, 10, 10),
        ],
        "pH": [7.0, 7.01, 7.02]
    }
    df = pd.DataFrame(data)
    result = calculate_ph_heterogeneity(df, window_minutes=15, threshold_sd=0.2)

    # SD is very low, should be False
    assert all(~result["pH_heterogeneous"]), "Low SD should result in False for heterogeneous"

def test_ph_heterogeneity_high_sd():
    """Test heterogeneity with high SD (should be True)"""
    data = {
        "timestamp": [
            datetime(2023, 1, 1, 10, 0),
            datetime(2023, 1, 1, 10, 5),
            datetime(2023, 1, 1, 10, 10),
        ],
        "pH": [7.0, 8.0, 6.0] # SD approx 0.816
    }
    df = pd.DataFrame(data)
    result = calculate_ph_heterogeneity(df, window_minutes=15, threshold_sd=0.2)

    # SD is high, should be True
    assert any(result["pH_heterogeneous"]), "High SD should result in True for heterogeneous"

def test_logger_singleton():
    """Test that get_logger returns the same instance"""
    logger1 = get_logger("test_singleton")
    logger2 = get_logger("test_singleton")
    assert logger1 is logger2, "Logger should be a singleton"

def test_logger_handlers():
    """Test that logger has handlers"""
    logger = get_logger("test_handlers")
    assert len(logger.handlers) > 0, "Logger should have at least one handler"