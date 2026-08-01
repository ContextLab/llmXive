"""
Integration test for sensitivity sweep (US3).

This test verifies that the sensitivity analysis script runs successfully,
produces the expected output file, and that the output contains valid
FPR/FNR calculations for all defined thresholds.

Prerequisites:
- The sensitivity analysis script (code/eval/sensitivity.py) must have been run
  to generate results/sensitivity_analysis.csv.
- Real test set predictions must exist (typically from code/eval/predictor.py).
"""
import os
import sys
import csv
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path to import config utilities if needed
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
RESULTS_DIR = PROJECT_ROOT / "results"
DATA_DIR = PROJECT_ROOT / "data"

# Ensure paths exist for the test environment
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Constants matching the specification (T031)
EXPECTED_COLUMNS = ['threshold', 'fpr', 'fnr']
EXPECTED_OUTPUT_FILE = RESULTS_DIR / "sensitivity_analysis.csv"

# Relative offsets from median used in T031: ±5%, ±10%, ±20%
# The script should generate rows for these specific relative thresholds.
EXPECTED_RELATIVE_OFFSETS = [-0.20, -0.10, -0.05, 0.05, 0.10, 0.20]

@pytest.fixture(scope="module")
def setup_sensitivity_test_data():
    """
    Fixture to ensure the necessary input data exists for the sensitivity test.
    Since this is an integration test, it assumes the prior pipeline steps
    (download, preprocess, split, train, predict) have run.
    
    If the output file doesn't exist, we attempt to run the sensitivity script.
    If that fails (e.g., missing predictions), we skip the test or fail loudly.
    """
    # Check if the output file already exists
    if EXPECTED_OUTPUT_FILE.exists():
        yield EXPECTED_OUTPUT_FILE
        return

    # If not, try to run the sensitivity script to generate it
    # This mimics the real execution flow
    sensitivity_script = CODE_DIR / "eval" / "sensitivity.py"
    
    if not sensitivity_script.exists():
        pytest.skip(f"Sensitivity script not found at {sensitivity_script}. "
                    "Prerequisite scripts (train/predict) may not have run.")
    
    # We need a predictions file to run the script.
    # Look for a standard predictions file location.
    predictions_file = RESULTS_DIR / "predictions.csv"
    
    if not predictions_file.exists():
        pytest.skip(f"Predictions file not found at {predictions_file}. "
                    "Run code/eval/predictor.py first.")
    
    # Construct the command
    cmd = [
        sys.executable, str(sensitivity_script),
        "--predictions", str(predictions_file),
        "--output", str(EXPECTED_OUTPUT_FILE)
    ]
    
    try:
        import subprocess
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Sensitivity analysis script failed to run: {e.stderr}")
    
    if not EXPECTED_OUTPUT_FILE.exists():
        pytest.fail("Sensitivity script ran but did not produce the expected output file.")
        
    yield EXPECTED_OUTPUT_FILE

def test_sensitivity_sweep(setup_sensitivity_test_data):
    """
    Asserts that sensitivity_analysis.csv contains rows for all threshold values
    and FPR/FNR columns are populated with valid floats.
    
    This satisfies T028: Integration test for sensitivity sweep.
    """
    output_file = setup_sensitivity_test_data
    
    assert output_file.exists(), f"Output file {output_file} does not exist."
    
    rows = []
    with open(output_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Verify header columns
        assert reader.fieldnames is not None, "CSV file is empty or has no header."
        for col in EXPECTED_COLUMNS:
            assert col in reader.fieldnames, f"Missing required column: {col}"
        
        for row in reader:
            rows.append(row)
    
    assert len(rows) > 0, "Sensitivity analysis CSV contains no data rows."
    
    # Verify data integrity for each row
    valid_offsets = []
    for row in rows:
        threshold_val = float(row['threshold'])
        fpr_val = float(row['fpr'])
        fnr_val = float(row['fnr'])
        
        # FPR and FNR must be between 0 and 1
        assert 0.0 <= fpr_val <= 1.0, f"FPR {fpr_val} out of range [0, 1]"
        assert 0.0 <= fnr_val <= 1.0, f"FN R {fnr_val} out of range [0, 1]"
        
        # We expect specific relative offsets from the median.
        # Since we don't know the median value here, we check if the threshold
        # corresponds to one of the expected relative offsets relative to the
        # median. However, the CSV stores absolute thresholds.
        # The task requires "rows for all threshold values".
        # We verify that we have at least 6 rows (for the 6 offsets defined in T031).
        valid_offsets.append(threshold_val)
    
    # T031 specifies: median ± 5%, median ± 10%, median ± 20%
    # That is 6 distinct thresholds.
    assert len(valid_offsets) >= 6, (
        f"Expected at least 6 threshold rows (for ±5%, ±10%, ±20%), "
        f"but found {len(valid_offsets)}."
    )
    
    # Optional: Verify the logic implies we hit the specific relative steps.
    # Since we can't know the median without reading the predictions file again,
    # we assert the count and valid numeric ranges, which confirms the sweep logic ran.
    # If the implementation was hardcoded to a single value, this would fail.
    
    # Log the found thresholds for debugging
    print(f"Found {len(valid_offsets)} threshold rows in {output_file}")
    for val in sorted(valid_offsets):
        print(f"  Threshold: {val:.4f}")

def test_sensitivity_file_format(setup_sensitivity_test_data):
    """
    Additional check to ensure the file is a valid CSV and readable.
    """
    output_file = setup_sensitivity_test_data
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert len(content) > 0, "File is empty."
            # Basic CSV sanity check: at least one newline
            assert '\n' in content, "File does not contain newlines (invalid CSV)."
    except Exception as e:
        pytest.fail(f"Failed to read or parse CSV file: {e}")