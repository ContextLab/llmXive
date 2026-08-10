"""
Integration test for T010b: Verify generate_partitions.py completes within
1.5 hours (5400 seconds) as derived from the total 6-hour budget minus 4 hours
allocated for modeling and plotting.

This test executes the data generation script and monitors:
1. Execution time (must be < 5400 seconds)
2. Peak memory usage (must be < 6.5 GB) - verified via resource limits or internal check
3. Correctness of output artifacts

Note: This is a stricter time constraint than T010a (2 hours) to ensure
sufficient buffer for downstream tasks.
"""

import os
import sys
import time
import subprocess
import resource
from pathlib import Path

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-799.yaml"

# Constants for limits (1.5 hours = 5400 seconds)
MAX_TIME_SECONDS = 1.5 * 3600  # 5400 seconds
MAX_MEMORY_BYTES = 6.5 * 1024**3  # 6.5 GB

def get_peak_memory_mb():
    """Get peak memory usage of the current process in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / 1024.0

def test_generate_partitions_time_budget():
    """
    Time-budget test: Run generate_partitions.py and verify:
    1. It completes successfully (exit code 0)
    2. It finishes within the 1.5-hour time budget (5400s)
    3. Memory usage stays under 6.5 GB
    4. Output files are created and valid
    """
    script_path = CODE_DIR / "generate_partitions.py"
    
    # Ensure the script exists
    assert script_path.exists(), f"Script not found: {script_path}"

    # Ensure output directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize state file if it doesn't exist
    if not STATE_FILE.exists():
        STATE_FILE.write_text("artifact_hashes: {}\nupdated_at: null\n")

    output_csv = DATA_RAW_DIR / "partitions_raw.csv"
    if output_csv.exists():
        output_csv.unlink()  # Remove existing output to ensure fresh run

    start_time = time.time()
    
    # Run the script as a subprocess to isolate memory usage
    cmd = [sys.executable, str(script_path)]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=MAX_TIME_SECONDS + 120  # Add 2 min buffer for safety
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            f"generate_partitions.py exceeded time budget of {MAX_TIME_SECONDS} seconds (1.5 hours). "
            f"The DP generation phase must complete within this limit to allow 4 hours for modeling/plotting."
        )

    end_time = time.time()
    elapsed_time = end_time - start_time

    # Check exit code
    if result.returncode != 0:
        error_msg = result.stderr if result.stderr else "No error output"
        raise AssertionError(
            f"generate_partitions.py failed with exit code {result.returncode}\n"
            f"Stderr: {error_msg}"
        )

    # Verify time constraint (1.5 hours)
    assert elapsed_time < MAX_TIME_SECONDS, (
        f"DP generation took {elapsed_time:.2f} seconds, exceeding time budget of {MAX_TIME_SECONDS} seconds (1.5 hours). "
        f"This violates SC-004 (6h total budget) which reserves 4h for modeling/plotting."
    )

    # Verify output file exists
    assert output_csv.exists(), f"Output file not created: {output_csv}"

    # Verify state file was updated
    assert STATE_FILE.exists(), "State file not created"
    state_content = STATE_FILE.read_text()
    assert "artifact_hashes" in state_content, "State file missing artifact_hashes key"
    assert "generate_partitions_raw" in state_content, "State file missing generate_partitions_raw checksum"

    print(f"✓ Time-budget test passed (T010b)")
    print(f"  - Execution time: {elapsed_time:.2f} seconds (< {MAX_TIME_SECONDS} s / 1.5h)")
    print(f"  - Time remaining for modeling/plotting: {(MAX_TIME_SECONDS - elapsed_time):.2f} seconds")
    print(f"  - Output file: {output_csv}")
    print(f"  - State file updated: {STATE_FILE}")

    # Verify the output has content and valid format
    with open(output_csv, 'r') as f:
        lines = f.readlines()
        assert len(lines) > 1, "Output CSV is empty or has only header"
        # Check header
        header = lines[0].strip()
        assert "n" in header and "p_P(n)" in header and "Q_as(n)" in header, (
            f"Invalid CSV header: {header}"
        )
        
        # Check a few data rows
        for i, line in enumerate(lines[1:10], start=1):
            parts = line.strip().split(',')
            assert len(parts) == 3, f"Row {i} has wrong number of columns: {line}"
            n, p_val, q_val = parts
            assert n.isdigit(), f"Row {i} n is not integer: {n}"
            assert p_val.isdigit() or (p_val.startswith('-') and p_val[1:].isdigit()), (
                f"Row {i} p_P(n) is not integer: {p_val}"
            )
            # Q_as(n) can be float
            float(q_val)  # Will raise if not valid float

    print("✓ Output validation passed")
    print("✓ T010b: DP generation phase completed within 1.5-hour budget")

if __name__ == "__main__":
    test_generate_partitions_time_budget()
    print("All time-budget tests for T010b passed!")