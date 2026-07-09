"""
Integration test for the download pipeline (T010).

This test verifies that the download script successfully fetches the 
2018 Alaska subset of earthquakes and produces the expected number of rows.
"""
import os
import sys
import subprocess
import json
from pathlib import Path
import csv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_data_path, get_processed_path, get_test_event_count

def test_download_pipeline_execution():
    """
    Runs the download script and asserts it exits with code 0.
    """
    script_path = Path(__file__).parent.parent.parent / "code" / "download.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=300 # 5 minutes timeout
    )
    
    assert result.returncode == 0, f"Download script failed with code {result.returncode}. Stderr: {result.stderr}"

def test_output_row_count():
    """
    Verifies the output CSV row count matches the expected count (N=12) within 1% tolerance.
    """
    # Ensure the script has run (or run it if not)
    script_path = Path(__file__).parent.parent.parent / "code" / "download.py"
    processed_path = Path(get_processed_path()) / "master_dataset.csv"
    
    if not processed_path.exists():
        # Run the script first
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300
        )
        assert result.returncode == 0, f"Pre-run of download script failed: {result.stderr}"
    
    assert processed_path.exists(), f"Processed file not found at {processed_path}"
    
    with open(processed_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # Header is the first row
    data_rows = rows[1:]
    count = len(data_rows)
    expected_count = get_test_event_count() # Should be 12
    
    tolerance = 0.01 * expected_count
    lower_bound = expected_count - tolerance
    upper_bound = expected_count + tolerance
    
    assert lower_bound <= count <= upper_bound, (
        f"Row count {count} is outside expected range [{lower_bound}, {upper_bound}] "
        f"for target {expected_count}."
    )

def test_output_fields_present():
    """
    Verifies that the output CSV contains all required fields.
    """
    processed_path = Path(get_processed_path()) / "master_dataset.csv"
    script_path = Path(__file__).parent.parent.parent / "code" / "download.py"
    
    if not processed_path.exists():
        subprocess.run([sys.executable, str(script_path)], capture_output=True, timeout=300)
    
    with open(processed_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
    
    required_fields = {"id", "time", "latitude", "longitude", "depth", "magnitude", "place"}
    header_set = set(header)
    
    missing = required_fields - header_set
    assert not missing, f"Missing required fields in CSV header: {missing}"

def test_raw_data_integrity():
    """
    Verifies that the raw GeoJSON file was created and is valid JSON.
    """
    raw_path = Path(get_data_path()) / "raw" / "usgs_2018_alaska.geojson"
    script_path = Path(__file__).parent.parent.parent / "code" / "download.py"
    
    if not raw_path.exists():
        subprocess.run([sys.executable, str(script_path)], capture_output=True, timeout=300)
    
    assert raw_path.exists(), f"Raw data file not found at {raw_path}"
    
    with open(raw_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            assert False, "Raw data file is not valid JSON"
    
    assert "features" in data, "Raw data missing 'features' key"
    assert len(data["features"]) > 0, "Raw data has no features"