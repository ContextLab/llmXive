"""
Integration test for T017: Output cleaned_data.csv with documentation.

Verifies:
  1. Script runs successfully
  2. Output file exists
  3. Required columns are present
  4. Data is standardized to 0-1 range
  5. Metadata file is created with correct structure
  6. Sample size meets minimum (>= 100)
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import pytest
import subprocess
import sys

# Get project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

@pytest.fixture(autouse=True)
def setup_t017_env():
    """Ensure preprocessed data exists before running T017 test."""
    # This assumes T014 has been run. If not, skip or create mock data.
    preprocessed_file = DATA_PROCESSED_DIR / "preprocessed_data.csv"
    
    if not preprocessed_file.exists():
        pytest.skip("T014 (preprocess.py) not run. Skipping T017 test.")
    
    # Ensure output directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def test_t017_script_execution():
    """Test that T017 script runs without errors."""
    script_path = PROJECT_ROOT / "code" / "preprocessing" / "output_cleaned_data.py"
    
    if not script_path.exists():
        pytest.skip("T017 script not found. Implementation pending.")
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"

def test_output_file_exists():
    """Test that cleaned_data.csv is created."""
    output_file = DATA_PROCESSED_DIR / "cleaned_data.csv"
    assert output_file.exists(), "cleaned_data.csv not created by T017"

def test_required_columns_present():
    """Test that all required columns exist in output."""
    output_file = DATA_PROCESSED_DIR / "cleaned_data.csv"
    if not output_file.exists():
        pytest.skip("Output file not created yet.")
    
    df = pd.read_csv(output_file)
    required_cols = ["participant_id", "latency", "smoothness", "lead_time", "agency_score"]
    
    missing_cols = [c for c in required_cols if c not in df.columns]
    assert len(missing_cols) == 0, f"Missing required columns: {missing_cols}"

def test_standardization_range():
    """Test that numeric features are standardized to 0-1 range."""
    output_file = DATA_PROCESSED_DIR / "cleaned_data.csv"
    if not output_file.exists():
        pytest.skip("Output file not created yet.")
    
    df = pd.read_csv(output_file)
    numeric_cols = ["latency", "smoothness", "lead_time", "agency_score"]
    
    for col in numeric_cols:
        if col in df.columns:
            min_val = df[col].min()
            max_val = df[col].max()
            
            # Allow small floating point tolerance
            assert min_val >= -1e-6, f"{col} min value {min_val} is below 0"
            assert max_val <= 1.0 + 1e-6, f"{col} max value {max_val} is above 1"

def test_metadata_file_created():
    """Test that metadata file is created with correct structure."""
    metadata_file = DATA_PROCESSED_DIR / "cleaned_data_metadata.json"
    assert metadata_file.exists(), "Metadata file not created by T017"
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    # Check required keys
    required_keys = ["file_path", "created_at", "n_samples", "scoring_method", "standardization"]
    missing_keys = [k for k in required_keys if k not in metadata]
    assert len(missing_keys) == 0, f"Metadata missing keys: {missing_keys}"
    
    # Check scoring method documentation
    assert "agency_score" in metadata["scoring_method"], "Agency score scoring method not documented"
    assert "standardization" in metadata["scoring_method"]["agency_score"], "Standardization not documented for agency_score"

def test_sample_size_minimum():
    """Test that sample size meets minimum requirement (>= 100)."""
    output_file = DATA_PROCESSED_DIR / "cleaned_data.csv"
    if not output_file.exists():
        pytest.skip("Output file not created yet.")
    
    df = pd.read_csv(output_file)
    n_samples = len(df)
    
    assert n_samples >= 100, f"Sample size {n_samples} is below minimum requirement of 100"

def test_data_integrity():
    """Test that no NaN values exist in required columns."""
    output_file = DATA_PROCESSED_DIR / "cleaned_data.csv"
    if not output_file.exists():
        pytest.skip("Output file not created yet.")
    
    df = pd.read_csv(output_file)
    required_cols = ["participant_id", "latency", "smoothness", "lead_time", "agency_score"]
    
    for col in required_cols:
        nan_count = df[col].isna().sum()
        assert nan_count == 0, f"Column {col} has {nan_count} NaN values"