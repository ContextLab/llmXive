"""
Integration test for T011c: Fetch SeaBASS in-situ data.

This test verifies that:
1. The script runs without error.
2. The output file `data/raw/seabass.csv` is created.
3. The file contains data (not empty).
4. The file contains at least the expected columns (latitude, longitude, time, etc.).
"""
import os
import sys
import subprocess
import pytest
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

OUTPUT_FILE = project_root / "data" / "raw" / "seabass.csv"

@pytest.mark.integration
def test_seabass_fetch_creates_file():
    """Test that the fetch script creates the output CSV file."""
    # Ensure the file doesn't exist before running (optional, but cleaner)
    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()
    
    # Run the script
    result = subprocess.run(
        [sys.executable, "code/01_fetch_seabass.py"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    # Assert the script exited successfully
    assert result.returncode == 0, f"Script failed with: {result.stderr}"
    
    # Assert the file exists
    assert OUTPUT_FILE.exists(), "Output file data/raw/seabass.csv was not created."

@pytest.mark.integration
def test_seabass_file_has_content():
    """Test that the output file is not empty and has rows."""
    if not OUTPUT_FILE.exists():
        pytest.skip("Output file does not exist. Run test_seabass_fetch_creates_file first.")
    
    df = pd.read_csv(OUTPUT_FILE)
    
    assert len(df) > 0, "The SeaBASS dataset is empty."
    
@pytest.mark.integration
def test_seabass_file_has_expected_columns():
    """Test that the output file contains the required columns for the project."""
    if not OUTPUT_FILE.exists():
        pytest.skip("Output file does not exist.")
    
    df = pd.read_csv(OUTPUT_FILE)
    
    # We expect at least these columns based on the mapping logic in fetch_seabass.py
    # The dataset might have more, but these are critical.
    expected_cols = ['latitude', 'longitude', 'time']
    
    missing_cols = [col for col in expected_cols if col not in df.columns]
    
    # If the mapping logic in the script is correct, these should exist.
    # If the source dataset changed significantly, this test will catch it.
    if missing_cols:
        # Log what we actually have for debugging
        pytest.fail(f"Missing critical columns: {missing_cols}. "
                    f"Available columns: {list(df.columns)}")

@pytest.mark.integration
def test_seabass_data_quality_basic():
    """Test basic data quality: lat/lon should be numeric and within reasonable ranges."""
    if not OUTPUT_FILE.exists():
        pytest.skip("Output file does not exist.")
    
    df = pd.read_csv(OUTPUT_FILE)
    
    # Check latitude range
    if 'latitude' in df.columns:
        valid_lat = df['latitude'].dropna()
        if len(valid_lat) > 0:
            assert valid_lat.min() >= -90, "Latitude out of range (< -90)"
            assert valid_lat.max() <= 90, "Latitude out of range (> 90)"
    
    # Check longitude range
    if 'longitude' in df.columns:
        valid_lon = df['longitude'].dropna()
        if len(valid_lon) > 0:
            assert valid_lon.min() >= -180, "Longitude out of range (< -180)"
            assert valid_lon.max() <= 180, "Longitude out of range (> 180)"