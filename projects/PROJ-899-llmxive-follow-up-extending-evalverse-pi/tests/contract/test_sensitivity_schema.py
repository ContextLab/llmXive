import pytest
import pandas as pd
import numpy as np
import os
from pathlib import Path
from src.config import get_data_root

def test_sensitivity_sweep_raw_schema():
    """
    Contract test for T026 output schema.
    Verifies data/sensitivity_sweep_raw.csv has correct columns and types.
    """
    data_root = get_data_root()
    input_path = os.path.join(data_root, "sensitivity_sweep_raw.csv")

    if not os.path.exists(input_path):
        pytest.skip("sensitivity_sweep_raw.csv not found - T026 may not have run yet")

    df = pd.read_csv(input_path)

    # Check required columns
    required_cols = ["dimension", "threshold", "status"]
    assert all(col in df.columns for col in required_cols), f"Missing columns: {set(required_cols) - set(df.columns)}"

    # Check column types
    assert df["dimension"].dtype == object, "dimension should be string"
    assert df["threshold"].dtype in [np.float64, np.float32, int], "threshold should be numeric"
    assert df["status"].dtype == object, "status should be string"

    # Check status values
    valid_statuses = {"feature-sufficient", "vlm-required", "ambiguous"}
    assert set(df["status"].unique()).issubset(valid_statuses), f"Invalid statuses: {set(df['status'].unique()) - valid_statuses}"

    # Check thresholds
    expected_thresholds = {0.80, 0.85, 0.90}
    assert set(df["threshold"].unique()).issubset(expected_thresholds), f"Invalid thresholds: {set(df['threshold'].unique()) - expected_thresholds}"

def test_sensitivity_analysis_schema():
    """
    Contract test for T027 output schema.
    Verifies data/sensitivity_analysis.csv has correct columns.
    """
    data_root = get_data_root()
    input_path = os.path.join(data_root, "sensitivity_analysis.csv")

    if not os.path.exists(input_path):
        pytest.skip("sensitivity_analysis.csv not found - T027 may not have run yet")

    df = pd.read_csv(input_path)

    # Check required columns
    required_cols = ["dimension", "threshold", "status", "flip_rate"]
    assert all(col in df.columns for col in required_cols), f"Missing columns: {set(required_cols) - set(df.columns)}"

    # Check flip_rate range
    assert df["flip_rate"].between(0.0, 1.0).all(), "flip_rate should be between 0 and 1"

def test_sensitivity_matrix_full_schema():
    """
    Contract test for T028 output schema.
    Verifies data/sensitivity_matrix_full.csv is a valid pivot table.
    """
    data_root = get_data_root()
    input_path = os.path.join(data_root, "sensitivity_matrix_full.csv")

    if not os.path.exists(input_path):
        pytest.skip("sensitivity_matrix_full.csv not found - T028 may not have run yet")

    df = pd.read_csv(input_path)

    # First column should be dimension
    assert "dimension" in df.columns, "Missing 'dimension' column"

    # Other columns should be thresholds
    threshold_cols = [c for c in df.columns if c != "dimension"]
    expected_thresholds = {"0.8", "0.85", "0.9"}  # CSV may have string representation
    actual_thresholds = set(str(t) for t in threshold_cols)
    assert actual_thresholds.issubset(expected_thresholds), f"Unexpected threshold columns: {actual_thresholds - expected_thresholds}"