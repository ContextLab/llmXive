"""
Integration test for T014: Save raw downloaded data with checksum verification.

This test verifies that:
1. The script code/save_raw_data.py runs without errors
2. It produces data/raw/raw_dataset.csv
3. It produces data/raw/raw_dataset.csv.sha256
4. The checksum in the .sha256 file matches the actual file checksum
5. The CSV has at least 10 rows of data
"""
import os
import hashlib
import subprocess
import sys
import pytest
from pathlib import Path

@pytest.fixture
def setup_test_environment():
    """Ensure we start with a clean state for this test."""
    # Remove existing files if they exist
    csv_path = Path("data/raw/raw_dataset.csv")
    checksum_path = Path("data/raw/raw_dataset.csv.sha256")
    
    if csv_path.exists():
        csv_path.unlink()
    if checksum_path.exists():
        checksum_path.unlink()
    
    yield
    
    # Cleanup after test (optional, comment out for debugging)
    # if csv_path.exists():
    #     csv_path.unlink()
    # if checksum_path.exists():
    #     checksum_path.unlink()

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def test_save_raw_data_script_runs(setup_test_environment):
    """Test that the save_raw_data script runs successfully."""
    result = subprocess.run(
        [sys.executable, "code/save_raw_data.py"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    assert "completed successfully" in result.stdout.lower() or "completed successfully" in result.stderr.lower()

def test_csv_file_created(setup_test_environment):
    """Test that the CSV file is created."""
    csv_path = Path("data/raw/raw_dataset.csv")
    assert csv_path.exists(), "raw_dataset.csv was not created"
    assert csv_path.stat().st_size > 0, "raw_dataset.csv is empty"

def test_checksum_file_created(setup_test_environment):
    """Test that the checksum file is created."""
    checksum_path = Path("data/raw/raw_dataset.csv.sha256")
    assert checksum_path.exists(), "raw_dataset.csv.sha256 was not created"
    assert checksum_path.stat().st_size > 0, "raw_dataset.csv.sha256 is empty"

def test_checksum_verification(setup_test_environment):
    """Test that the checksum matches the actual file."""
    csv_path = Path("data/raw/raw_dataset.csv")
    checksum_path = Path("data/raw/raw_dataset.csv.sha256")
    
    # Ensure files exist first
    if not csv_path.exists() or not checksum_path.exists():
        # Run the script first
        subprocess.run(
            [sys.executable, "code/save_raw_data.py"],
            check=True,
            capture_output=True
        )
    
    # Compute actual checksum
    actual_checksum = compute_sha256(str(csv_path))
    
    # Read stored checksum
    with open(checksum_path, 'r') as f:
        stored_checksum = f.read().strip()
    
    assert actual_checksum == stored_checksum, (
        f"Checksum mismatch: actual={actual_checksum}, stored={stored_checksum}"
    )

def test_csv_has_minimum_rows(setup_test_environment):
    """Test that the CSV has at least 10 rows of data."""
    import pandas as pd
    
    csv_path = Path("data/raw/raw_dataset.csv")
    
    if not csv_path.exists():
        subprocess.run(
            [sys.executable, "code/save_raw_data.py"],
            check=True,
            capture_output=True
        )
    
    df = pd.read_csv(csv_path)
    assert len(df) >= 10, f"CSV has only {len(df)} rows, expected at least 10"

def test_csv_has_required_columns(setup_test_environment):
    """Test that the CSV has the required columns per the schema."""
    import pandas as pd
    
    csv_path = Path("data/raw/raw_dataset.csv")
    
    if not csv_path.exists():
        subprocess.run(
            [sys.executable, "code/save_raw_data.py"],
            check=True,
            capture_output=True
        )
    
    df = pd.read_csv(csv_path)
    required_columns = ['sample_id', 'genotype_id', 'resistance']
    
    for col in required_columns:
        assert col in df.columns, f"Required column '{col}' is missing from CSV"
        assert not df[col].isna().all(), f"Column '{col}' is entirely NaN"