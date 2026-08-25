"""
Integration test for Task T028: Sensitivity Density Sweep.

This test verifies that the sensitivity_density_sweep script:
1. Executes without errors for a small subset of parameters.
2. Produces the expected output CSV file.
3. Contains valid data structure (headers, non-empty rows).
"""
import os
import csv
import tempfile
import subprocess
import sys
import pytest
from pathlib import Path

# Add code directory to path for imports if running standalone
# But for integration test, we assume the script is run as a subprocess
# to ensure it works in the project environment.

@pytest.fixture
def temp_output_path(tmp_path):
    """Create a temporary output path for the test."""
    output_file = tmp_path / "sensitivity_test.csv"
    return str(output_file)

def test_t028_sweep_execution(temp_output_path):
    """
    Test that T028 script runs and produces a valid CSV with expected columns.
    
    We run with very small N and few seeds to keep execution time low.
    """
    # Prepare arguments for a minimal run
    cmd = [
        sys.executable,
        "code/analysis/sensitivity_density_sweep.py",
        "--densities", "0.1", "0.2",
        "--patterns", "diagonal",
        "--N", "100",  # Small matrix for speed
        "--theta", "2.5",
        "--rank", "1",
        "--num-seeds", "2",
        "--base-seed", "42",
        "--output", temp_output_path
    ]
    
    # Run the script
    result = subprocess.run(
        cmd,
        cwd=str(Path(__file__).parent.parent.parent), # Run from project root
        capture_output=True,
        text=True
    )
    
    # Assert script succeeded
    assert result.returncode == 0, f"Script failed with:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    
    # Assert output file exists
    assert os.path.exists(temp_output_path), f"Output file not created at {temp_output_path}"
    
    # Assert CSV is valid and has content
    with open(temp_output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) > 0, "CSV file is empty"
    
    # Check expected columns
    expected_columns = {
        "N", "density", "pattern_type", "theta", "rank", "seed",
        "execution_time_sec", "max_eigenvalue", "bbp_edge", "is_outlier"
    }
    actual_columns = set(rows[0].keys())
    
    assert expected_columns.issubset(actual_columns), f"Missing columns. Expected: {expected_columns}, Got: {actual_columns}"
    
    # Verify data types and basic sanity
    for row in rows:
        assert int(row["N"]) == 100
        assert float(row["theta"]) == 2.5
        assert float(row["rank"]) == 1
        # Density should be one of the tested values
        assert float(row["density"]) in [0.1, 0.2]
        # Pattern should be diagonal
        assert row["pattern_type"] == "diagonal"
        # Seed should be 42 or 43
        assert int(row["seed"]) in [42, 43]
        
        # Check that numerical fields are valid numbers or None
        if row["max_eigenvalue"] is not None:
            assert float(row["max_eigenvalue"]) > 0
        if row["bbp_edge"] is not None:
            assert float(row["bbp_edge"]) > 0

def test_t028_sweep_multiple_patterns(temp_output_path):
    """
    Test sweep with multiple pattern types to ensure all are processed.
    """
    cmd = [
        sys.executable,
        "code/analysis/sensitivity_density_sweep.py",
        "--densities", "0.1",
        "--patterns", "diagonal", "block-sparse", "random sparse",
        "--N", "50",
        "--theta", "2.0",
        "--rank", "1",
        "--num-seeds", "1",
        "--base-seed", "100",
        "--output", temp_output_path
    ]
    
    result = subprocess.run(
        cmd,
        cwd=str(Path(__file__).parent.parent.parent),
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed with:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    
    with open(temp_output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # We expect 3 patterns * 1 density * 1 seed = 3 rows
    assert len(rows) == 3, f"Expected 3 rows, got {len(rows)}"
    
    patterns_found = {row["pattern_type"] for row in rows}
    assert patterns_found == {"diagonal", "block-sparse", "random sparse"}