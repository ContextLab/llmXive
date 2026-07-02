"""
Integration test for T012: 01_ingest_and_descriptors.py
Verifies that the script runs and produces the expected output file.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPT_PATH = PROJECT_ROOT / "code" / "01_ingest_and_descriptors.py"
OUTPUT_FILE = PROJECT_ROOT / "data" / "descriptors" / "raw_descriptors.csv"
SAMPLE_IDS_FILE = PROJECT_ROOT / "data" / "raw" / "cod_sample_ids.txt"

@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path):
    """Ensure required directories and sample IDs file exist for the test."""
    # Create necessary directories
    (PROJECT_ROOT / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "descriptors").mkdir(parents=True, exist_ok=True)

    # If sample IDs file doesn't exist, create a minimal one for testing
    # Note: In real execution, this should be populated by T004
    if not SAMPLE_IDS_FILE.exists():
        SAMPLE_IDS_FILE.write_text("1000001\n1000002\n")

def test_t012_script_execution():
    """Test that 01_ingest_and_descriptors.py runs and creates output."""
    # Run the script
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    # Log output for debugging
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    # Check exit code
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Check output file exists
    assert OUTPUT_FILE.exists(), "Output CSV file was not created"

    # Check file has content
    content = OUTPUT_FILE.read_text()
    lines = content.strip().split('\n')
    assert len(lines) >= 2, "Output file should have header + at least 1 data row"

    # Check columns
    header = lines[0].split(',')
    expected_cols = ['ID', 'Volume', 'SurfaceArea', 'Dipole', 'HBD', 'HBA', 'PSA', 'packing_coefficient']
    for col in expected_cols:
        assert col in header, f"Missing column: {col}"

def test_t012_output_format():
    """Test that the output CSV has valid numeric data."""
    if not OUTPUT_FILE.exists():
        pytest.skip("Output file not generated; run test_t012_script_execution first")

    import csv
    with open(OUTPUT_FILE, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        pytest.skip("No data rows in output")

    # Check that numeric columns are actually numeric
    for row in rows:
        assert row['ID']  # ID should be non-empty
        assert float(row['Volume']) > 0
        assert float(row['packing_coefficient']) >= 0
        assert float(row['packing_coefficient']) <= 1.5  # Allow some tolerance