"""
Contract test for hybrid output schema (T028).

This test validates that the hybrid inference simulation produces an artifact
(`data/processed/hybrid_output.parquet`) that strictly adheres to the required schema
defined for User Story 3.

It verifies:
1. File existence.
2. Presence of all required columns:
   - frame_id (int)
   - timestamp (float)
   - audio_energy (float)
   - estimator_prediction_delta (float)
   - estimator_uncertainty (float)
   - fallback_triggered (bool)
   - final_frame_vector (float array / list)
   - latency_ms (float)
3. Data types are correct.
4. No null values in critical columns.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports if necessary
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "hybrid_output.parquet"

REQUIRED_COLUMNS = [
    "frame_id",
    "timestamp",
    "audio_energy",
    "estimator_prediction_delta",
    "estimator_uncertainty",
    "fallback_triggered",
    "final_frame_vector",
    "latency_ms",
]

CRITICAL_COLUMNS = [
    "frame_id",
    "timestamp",
    "estimator_prediction_delta",
    "estimator_uncertainty",
    "fallback_triggered",
    "latency_ms",
]

def test_hybrid_output_file_exists():
    """Contract Test: Verify the hybrid output artifact exists."""
    assert OUTPUT_PATH.exists(), f"Hybrid output artifact not found at {OUTPUT_PATH}. " \
                                 "Run code/inference/hybrid_sim.py first."

def test_hybrid_output_schema_columns():
    """Contract Test: Verify all required columns are present."""
    if not OUTPUT_PATH.exists():
        pytest.skip("Output file does not exist yet.")

    df = pd.read_parquet(OUTPUT_PATH)
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    assert not missing_cols, f"Missing required columns: {missing_cols}"

def test_hybrid_output_schema_types():
    """Contract Test: Verify data types of critical columns."""
    if not OUTPUT_PATH.exists():
        pytest.skip("Output file does not exist yet.")

    df = pd.read_parquet(OUTPUT_PATH)

    # Check integer type for frame_id
    assert pd.api.types.is_integer_dtype(df["frame_id"]), "frame_id must be integer"

    # Check float types for numeric metrics
    float_cols = ["timestamp", "audio_energy", "estimator_prediction_delta", "estimator_uncertainty", "latency_ms"]
    for col in float_cols:
        assert pd.api.types.is_float_dtype(df[col]), f"{col} must be float"

    # Check boolean type for fallback_triggered
    assert pd.api.types.is_bool_dtype(df["fallback_triggered"]), "fallback_triggered must be boolean"

    # Check that final_frame_vector is a list or array (object dtype in pandas usually)
    # Parquet might store this as a list, which appears as object or list type depending on engine
    assert df["final_frame_vector"].dtype == object or "list" in str(df["final_frame_vector"].dtype), \
        "final_frame_vector must be a list/array"

def test_hybrid_output_schema_no_nulls():
    """Contract Test: Verify no nulls in critical columns."""
    if not OUTPUT_PATH.exists():
        pytest.skip("Output file does not exist yet.")

    df = pd.read_parquet(OUTPUT_PATH)

    for col in CRITICAL_COLUMNS:
        null_count = df[col].isnull().sum()
        assert null_count == 0, f"Column '{col}' contains {null_count} null values."

def test_hybrid_output_schema_ranges():
    """Contract Test: Verify logical ranges for specific metrics."""
    if not OUTPUT_PATH.exists():
        pytest.skip("Output file does not exist yet.")

    df = pd.read_parquet(OUTPUT_PATH)

    # Uncertainty must be between 0.0 and 1.0
    assert (df["estimator_uncertainty"] >= 0.0).all() and (df["estimator_uncertainty"] <= 1.0).all(), \
        "estimator_uncertainty must be in range [0.0, 1.0]"

    # Latency must be non-negative
    assert (df["latency_ms"] >= 0).all(), "latency_ms must be non-negative"

    # Frame IDs should be unique if they represent a time series index
    # (Optional but good practice for this schema)
    # assert df["frame_id"].is_unique, "frame_id should be unique"

def test_hybrid_output_sample_size():
    """Contract Test: Verify we have a non-empty dataset."""
    if not OUTPUT_PATH.exists():
        pytest.skip("Output file does not exist yet.")

    df = pd.read_parquet(OUTPUT_PATH)
    assert len(df) > 0, "Hybrid output dataset is empty."