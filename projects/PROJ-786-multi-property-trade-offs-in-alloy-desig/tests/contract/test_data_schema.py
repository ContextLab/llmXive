"""
Contract test for data schema validation.

Verifies that the data ingestion script handles edge cases regarding
dataset size correctly:
1. Logs a specific warning when input has < 500 rows.
2. Exits with code 0 in both scenarios (small and large datasets).
"""
import os
import sys
import tempfile
import subprocess
import logging
import json
from pathlib import Path

import pytest
import pandas as pd

# Project root path (assuming tests/contract is 2 levels deep)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INGESTION_SCRIPT = PROJECT_ROOT / "code" / "data_ingestion.py"

def setup_module(module):
    """Ensure dependencies are available."""
    # Verify script exists
    if not INGESTION_SCRIPT.exists():
        pytest.fail(f"Data ingestion script not found at {INGESTION_SCRIPT}")

def test_small_dataset_logs_warning_and_exits_zero():
    """
    Assert that when input has < 500 rows (499 rows), the script logs
    the specific warning "Insufficient data for statistical analysis (N < 500)"
    and exits with code 0.
    """
    # Create a temporary directory for this test
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create a dummy CSV with 499 rows (plus header)
        dummy_csv = tmp_path / "small_input.csv"
        
        # Create a minimal valid dataframe structure matching expected schema
        # Based on data_ingestion.py requirements: bulk_modulus, shear_modulus, composition
        data = {
            "bulk_modulus": [100.0] * 499,
            "shear_modulus": [40.0] * 499,
            "composition": ["Fe50Ni50"] * 499,
            "formula": ["FeNi"] * 499
        }
        df = pd.DataFrame(data)
        df.to_csv(dummy_csv, index=False)
        
        # Create a temporary output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Run the ingestion script with the small dataset
        # We need to pass the input file path and output directory
        # Assuming the script accepts CLI args or we mock the input
        # Since we don't know exact CLI args from the API surface, we assume standard pattern:
        # python code/data_ingestion.py --input <path> --output <path>
        # If the script doesn't support CLI args, we might need to modify it, 
        # but for a contract test, we assume standard CLI usage or environment setup.
        
        # Let's assume the script reads from a default location or accepts args.
        # To be safe, we'll pass args. If the script fails due to args, we catch it.
        cmd = [
            sys.executable,
            str(INGESTION_SCRIPT),
            "--input", str(dummy_csv),
            "--output", str(output_dir),
            "--output-file", "encoded_alloys.csv"
        ]
        
        # Capture output
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        )
        
        # Check exit code
        assert result.returncode == 0, f"Script exited with code {result.returncode}. Stderr: {result.stderr}"
        
        # Check for the specific warning message in stdout or stderr
        output_combined = result.stdout + result.stderr
        expected_warning = "Insufficient data for statistical analysis (N < 500)"
        
        # The warning might be logged, so check logs
        # If logging is configured to stderr, it should be there
        assert expected_warning in output_combined, (
            f"Expected warning '{expected_warning}' not found in output.\n"
            f"Stdout: {result.stdout}\nStderr: {result.stderr}"
        )

def test_large_dataset_no_warning_and_exits_zero():
    """
    Assert that when input has >= 500 rows, no warning is logged and exit code is 0.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create a dummy CSV with 500 rows (plus header)
        dummy_csv = tmp_path / "large_input.csv"
        
        data = {
            "bulk_modulus": [100.0] * 500,
            "shear_modulus": [40.0] * 500,
            "composition": ["Fe50Ni50"] * 500,
            "formula": ["FeNi"] * 500
        }
        df = pd.DataFrame(data)
        df.to_csv(dummy_csv, index=False)
        
        # Create a temporary output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        cmd = [
            sys.executable,
            str(INGESTION_SCRIPT),
            "--input", str(dummy_csv),
            "--output", str(output_dir),
            "--output-file", "encoded_alloys.csv"
        ]
        
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        )
        
        # Check exit code
        assert result.returncode == 0, f"Script exited with code {result.returncode}. Stderr: {result.stderr}"
        
        # Check that the warning is NOT present
        output_combined = result.stdout + result.stderr
        expected_warning = "Insufficient data for statistical analysis (N < 500)"
        
        assert expected_warning not in output_combined, (
            f"Unexpected warning '{expected_warning}' found in output for large dataset.\n"
            f"Stdout: {result.stdout}\nStderr: {result.stderr}"
        )