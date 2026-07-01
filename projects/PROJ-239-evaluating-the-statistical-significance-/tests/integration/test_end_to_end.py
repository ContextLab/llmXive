"""End-to-end integration test for the robust simulation pipeline."""
import os
import subprocess
import sys
import tempfile
import csv
import pandas as pd
import pytest

# Ensure code directory is in path for imports if running directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "derived")

@pytest.mark.integration
def test_end_to_end_reduced_iterations():
    """
    Runs the robust simulation script with reduced iterations (10) and asserts:
    1. The script exits with code 0.
    2. The output file 'data/derived/robust_results.csv' exists.
    3. The output file contains valid data (header + rows).
    4. The data contains plausible values for ICC, Alpha, Method, and error rates.
    """
    # Ensure output directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    output_file = os.path.join(DATA_DIR, "robust_results.csv")

    # Clean up previous output if it exists to ensure fresh run
    if os.path.exists(output_file):
        os.remove(output_file)

    # Construct command
    # We run the script using the python interpreter from sys.executable to ensure environment consistency
    script_path = os.path.join(CODE_DIR, "run_simulation_robust.py")
    
    if not os.path.exists(script_path):
        pytest.fail(f"Script not found: {script_path}. Ensure T021 is implemented.")

    cmd = [
        sys.executable,
        script_path,
        "--iterations", "10",
        "--icc", "0.1",  # Run for a single ICC to speed up test
        "--seed", "42"
    ]

    try:
        # Run the script
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout for the test
        )
    except subprocess.TimeoutExpired:
        pytest.fail("Simulation script timed out.")

    # Assert exit code
    if result.returncode != 0:
        error_msg = f"Script failed with return code {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        pytest.fail(error_msg)

    # Assert output file exists
    assert os.path.exists(output_file), f"Output file {output_file} was not created."

    # Assert file is not empty and contains data
    with open(output_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) > 0, "Output CSV contains no data rows."

    # Validate structure and plausible values
    required_columns = {'ICC', 'Alpha', 'Method', 'Empirical_Error_Rate', 'CI_Lower', 'CI_Upper'}
    assert required_columns.issubset(set(rows[0].keys())), f"Missing required columns. Found: {rows[0].keys()}"

    # Check plausible values
    for row in rows:
        # ICC should be 0.1 (or close if step logic varies, but we passed 0.1)
        assert float(row['ICC']) >= 0.0 and float(row['ICC']) <= 1.0, f"Invalid ICC: {row['ICC']}"
        
        # Alpha should be one of the standard levels
        alpha_val = float(row['Alpha'])
        assert alpha_val in [0.01, 0.05, 0.10], f"Unexpected Alpha: {alpha_val}"
        
        # Error rate should be between 0 and 1
        err_rate = float(row['Empirical_Error_Rate'])
        assert 0.0 <= err_rate <= 1.0, f"Invalid Error Rate: {err_rate}"
        
        # CI bounds should be valid
        ci_lower = float(row['CI_Lower'])
        ci_upper = float(row['CI_Upper'])
        assert 0.0 <= ci_lower <= 1.0, f"Invalid CI Lower: {ci_lower}"
        assert 0.0 <= ci_upper <= 1.0, f"Invalid CI Upper: {ci_upper}"
        assert ci_lower <= ci_upper, "CI Lower > CI Upper"
        
        # Method should be one of the expected methods
        assert row['Method'] in ['naive', 'cluster_robust', 'block_permutation'], f"Unknown Method: {row['Method']}"

    # Specific check: Since we ran with 10 iterations, we expect at least one row per method
    methods_found = set(row['Method'] for row in rows)
    expected_methods = {'naive', 'cluster_robust', 'block_permutation'}
    assert methods_found == expected_methods, f"Missing methods in output. Expected {expected_methods}, found {methods_found}"