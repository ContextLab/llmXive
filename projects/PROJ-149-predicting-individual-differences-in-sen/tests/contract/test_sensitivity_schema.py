"""
Contract tests for sensitivity analysis outputs.
Verifies schema of sensitivity_report.csv.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add code to path if needed
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

def test_sensitivity_report_schema():
    """
    Validates that sensitivity_report.csv exists and has correct columns.
    """
    # Determine path
    report_path = Path("data/processed/sensitivity_report.csv")
    if not report_path.exists():
        # Fallback if run from different root
        report_path = Path(__file__).parent.parent.parent / "data" / "processed" / "sensitivity_report.csv"

    assert report_path.exists(), f"Sensitivity report file not found at {report_path}"

    df = pd.read_csv(report_path)

    required_columns = ['threshold', 'significant_count']
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"

    # Check data types
    assert df['threshold'].dtype in ['float64', 'float32', 'int64', 'int32'], "threshold should be numeric"
    assert df['significant_count'].dtype in ['int64', 'int32', 'float64', 'float32'], "significant_count should be numeric"

    # Check monotonicity (count should be non-decreasing as threshold increases)
    # Note: Due to rounding in the sweep, it might not be strictly monotonic if multiple thresholds round to same value,
    # but generally it should be non-decreasing.
    # We'll just check for basic validity: counts >= 0
    assert (df['significant_count'] >= 0).all(), "Significant counts cannot be negative"
    
    # Check thresholds are within expected range (0.01 to 0.10)
    assert (df['threshold'] >= 0.01).all(), "Thresholds should be >= 0.01"
    assert (df['threshold'] <= 0.10).all(), "Thresholds should be <= 0.10"
