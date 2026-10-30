"""
Unit tests for the Reddit Loneliness Longitudinal Dataset ingestion script.

These tests verify that:
1. The parquet file is created at the expected location.
2. The file contains at least 600 rows.
3. All required columns are present.
4. Each user has at least six distinct calendar months with non‑null scores.
"""

import os
from pathlib import Path

import pandas as pd
import pytest

# Import the main function from the script we just implemented.
from src.ingest.download_loneliness import main as download_main

# Helper to locate the generated parquet file.
def get_output_path() -> Path:
    # The script writes to the path defined in its config (default location).
    return Path("data/raw/loneliness_dataset.parquet")

@pytest.fixture(scope="module")
def run_download():
    """Run the download script once for the entire test module."""
    # Ensure a clean start – remove any existing artifact.
    out_path = get_output_path()
    if out_path.exists():
        out_path.unlink()
    # Execute the script – any exception will cause the fixture to fail.
    download_main()
    yield out_path
    # Cleanup after tests (optional).
    if out_path.exists():
        out_path.unlink()

def test_parquet_exists(run_download):
    """The parquet file must exist after the script runs."""
    out_path = run_download
    assert out_path.exists(), f"Expected parquet file at {out_path}"

def test_minimum_row_count(run_download):
    """The dataset must contain at least 600 rows."""
    df = pd.read_parquet(run_download)
    assert len(df) >= 600, f"Dataset contains {len(df)} rows; expected >= 600"

def test_required_columns(run_download):
    """All required columns must be present."""
    df = pd.read_parquet(run_download)
    required = {
        "username_hash",
        "UCLA_Loneliness_Score",
        "timestamp",
        "baseline_text",
        "age",
        "gender",
    }
    missing = required - set(df.columns)
    assert not missing, f"Missing required columns: {missing}"

def test_longitudinal_depth(run_download):
    """Each user must have ≥6 distinct months with non‑null scores."""
    df = pd.read_parquet(run_download)
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    # Drop rows without a score or timestamp
    df_valid = df.dropna(subset=["UCLA_Loneliness_Score", "timestamp"])
    df_valid["year_month"] = df_valid["timestamp"].dt.to_period("M")
    month_counts = (
        df_valid.groupby("username_hash")["year_month"]
        .nunique()
        .reset_index(name="month_count")
    )
    insufficient = month_counts[month_counts["month_count"] < 6]
    assert insufficient.empty, f"{len(insufficient)} users have <6 months of data"