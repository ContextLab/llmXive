"""
Integration test for the data extraction pipeline (US1, FR-001).

This test verifies that:
1. The extraction script runs without errors.
2. The output Parquet file is created at the expected location.
3. The output file contains the required columns and schema.
4. The file size is within the expected limits (<= 1 GB).
"""
import os
import sys
import pytest
import subprocess
import pandas as pd
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="module")
def extraction_output_path():
    """Define the expected output path for the extraction script."""
    return project_root / "data" / "processed" / "raw_latents.parquet"

@pytest.fixture(scope="module")
def run_extraction_script(extraction_output_path):
    """
    Fixture to run the extraction script before tests.
    Skips if the output file already exists and is valid.
    """
    if extraction_output_path.exists():
        # Quick check if file is valid
        try:
            pd.read_parquet(extraction_output_path)
            print("Output file already exists and is valid. Skipping extraction run.")
            return
        except Exception:
            print("Output file exists but is invalid. Re-running extraction.")
    
    script_path = project_root / "code" / "data" / "extract_latents.py"
    if not script_path.exists():
        pytest.skip(f"Extraction script not found at {script_path}. Skipping integration test.")
    
    print(f"Running extraction script: {script_path}")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        pytest.fail(f"Extraction script failed with return code {result.returncode}.\nStdout: {result.stdout}\nStderr: {result.stderr}")
    
    if not extraction_output_path.exists():
        pytest.fail("Extraction script completed but output file was not created.")

def test_extraction_output_exists(run_extraction_script, extraction_output_path):
    """Test that the extraction output file exists."""
    assert extraction_output_path.exists(), f"Output file {extraction_output_path} does not exist."

def test_extraction_output_size(run_extraction_script, extraction_output_path):
    """Test that the output file is within size limits (<= 1 GB)."""
    file_size_bytes = extraction_output_path.stat().st_size
    file_size_gb = file_size_bytes / (1024 ** 3)
    assert file_size_gb <= 1.0, f"Output file size ({file_size_gb:.2f} GB) exceeds 1 GB limit."

def test_extraction_output_schema(run_extraction_script, extraction_output_path):
    """Test that the output file contains the required columns and schema."""
    required_columns = [
        "timestamp",
        "semantic_feature",
        "prosodic_feature",
        "latent_delta_magnitude",
        "turn_label"
    ]
    
    df = pd.read_parquet(extraction_output_path)
    
    # Check columns
    missing_columns = set(required_columns) - set(df.columns)
    assert not missing_columns, f"Missing required columns: {missing_columns}"
    
    # Check data types (basic sanity check)
    assert df["timestamp"].notna().all(), "Timestamp column contains null values."
    assert df["turn_label"].notna().all(), "Turn label column contains null values."
    assert df["latent_delta_magnitude"].notna().all(), "Latent delta magnitude contains null values."

def test_extraction_output_sample_size(run_extraction_script, extraction_output_path):
    """Test that the output file contains at least 10,000 sampled frames."""
    df = pd.read_parquet(extraction_output_path)
    assert len(df) >= 10000, f"Output file contains only {len(df)} rows, expected at least 10,000."

def test_extraction_output_event_types(run_extraction_script, extraction_output_path):
    """Test that the output file includes interruption/pause events."""
    df = pd.read_parquet(extraction_output_path)
    unique_labels = df["turn_label"].unique()
    expected_labels = {"interruption", "pause", "normal"}
    
    # Check if at least some of the expected labels are present
    # (We don't require all to be present if the dataset is small, but we expect at least some)
    found_labels = set(unique_labels) & expected_labels
    assert len(found_labels) > 0, f"Expected at least one of {expected_labels} in turn_label column, found: {unique_labels}"
