"""
Unit tests for the Reddit Loneliness Longitudinal Dataset ingestion script.
"""

import pytest
import pandas as pd
from pathlib import Path
from src.ingest.download_loneliness import main as download_main

def get_output_path() -> Path:
    return Path("data/raw/loneliness_dataset.parquet")

@pytest.fixture(scope="module")
def run_ingestion():
    """
    Run the download script. 
    Note: In a real environment, this will attempt to hit Zenodo.
    If the DOI is a placeholder, this test will fail, which is the correct
    behavior for 'Real Data Only'.
    """
    out_path = get_output_path()
    if out_path.exists():
        out_path.unlink()
    
    try:
        download_main()
    except Exception as e:
        pytest.fail(f"Ingestion script failed: {e}")
        
    yield out_path

def test_parquet_exists(run_ingestion):
    assert run_ingestion.exists(), f"Expected parquet file at {run_ingestion}"

def test_minimum_row_count(run_ingestion):
    df = pd.read_parquet(run_ingestion)
    assert len(df) >= 600, f"Dataset contains {len(df)} rows; expected >= 600"

def test_required_columns(run_ingestion):
    df = pd.read_parquet(run_ingestion)
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

def test_longitudinal_depth(run_ingestion):
    df = pd.read_parquet(run_ingestion)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df_valid = df.dropna(subset=["UCLA_Loneliness_Score", "timestamp"])
    df_valid["year_month"] = df_valid["timestamp"].dt.to_period("M")
    
    month_counts = (
        df_valid.groupby("username_hash")["year_month"]
        .nunique()
    )
    
    insufficient = month_counts[month_counts < 6]
    assert insufficient.empty, f"{len(insufficient)} users have < 6 distinct months of data"