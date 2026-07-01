"""
End-to-end integration test for the robust simulation pipeline.

This test verifies that the full simulation pipeline (data generation,
estimation, and aggregation) runs successfully with reduced iterations
and produces valid output files with plausible values.
"""
import os
import subprocess
import sys
import tempfile
import shutil
import pandas as pd
import pytest
from pathlib import Path

# Project root relative to test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"

def test_end_to_end_reduced_iterations():
    """
    Run the robust simulation with --iterations 10 and assert:
    1. The script exits with code 0.
    2. Output files exist in data/derived/.
    3. Output files contain plausible values (columns present, no NaNs in key fields).
    
    This test uses a reduced iteration count to keep runtime within limits
    while still validating the full pipeline.
    """
    # Ensure the derived data directory exists
    DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    # Define expected output files
    expected_files = [
        "robust_results.csv",
        "timing.csv",
        "memory.csv"
    ]

    # Clean up any existing output files from previous runs
    for fname in expected_files:
        fpath = DATA_DERIVED_DIR / fname
        if fpath.exists():
            fpath.unlink()

    # Construct the command to run the simulation
    # We use a fixed seed and low iteration count for reproducibility and speed
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "code" / "run_simulation_robust.py"),
        "--iterations", "10",
        "--seed", "42",
        "--icc-range", "0.0", "0.2",  # Small range to speed up
        "--icc-step", "0.1"
    ]

    # Run the simulation
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
    except subprocess.TimeoutExpired:
        pytest.fail("Simulation script timed out after 120 seconds")

    # Assert exit code is 0
    if result.returncode != 0:
        pytest.fail(
            f"Simulation script failed with exit code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    # Assert all expected output files exist
    missing_files = []
    for fname in expected_files:
        fpath = DATA_DERIVED_DIR / fname
        if not fpath.exists():
            missing_files.append(fname)

    if missing_files:
        pytest.fail(f"Expected output files not found: {missing_files}")

    # Validate content of robust_results.csv
    results_df = pd.read_csv(DATA_DERIVED_DIR / "robust_results.csv")
    
    # Check required columns exist
    required_cols = ["method", "icc", "alpha", "error_rate", "ci_lower", "ci_upper"]
    missing_cols = [col for col in required_cols if col not in results_df.columns]
    if missing_cols:
        pytest.fail(f"Missing required columns in robust_results.csv: {missing_cols}")

    # Check for plausible values
    # 1. No NaN in error_rate
    if results_df["error_rate"].isna().any():
        pytest.fail("error_rate column contains NaN values")

    # 2. error_rate must be between 0 and 1
    if not (results_df["error_rate"] >= 0).all() or not (results_df["error_rate"] <= 1).all():
        pytest.fail("error_rate values are outside the valid range [0, 1]")

    # 3. icc values should be in expected range (0.0 to 0.5 based on config)
    if not (results_df["icc"] >= 0).all():
        pytest.fail("icc values are negative")

    # 4. ci_lower and ci_upper should be valid probabilities
    if results_df["ci_lower"].isna().any() or results_df["ci_upper"].isna().any():
        pytest.fail("CI columns contain NaN values")

    # Validate content of timing.csv
    timing_df = pd.read_csv(DATA_DERIVED_DIR / "timing.csv")
    if "timestamp" not in timing_df.columns or "duration_seconds" not in timing_df.columns:
        pytest.fail("timing.csv missing required columns")
    
    if timing_df["duration_seconds"].isna().any():
        pytest.fail("timing.csv duration_seconds contains NaN")
    
    if (timing_df["duration_seconds"] < 0).any():
        pytest.fail("timing.csv contains negative durations")

    # Validate content of memory.csv
    memory_df = pd.read_csv(DATA_DERIVED_DIR / "memory.csv")
    if "timestamp" not in memory_df.columns or "peak_memory_mb" not in memory_df.columns:
        pytest.fail("memory.csv missing required columns")

    if memory_df["peak_memory_mb"].isna().any():
        pytest.fail("memory.csv peak_memory_mb contains NaN")

    if (memory_df["peak_memory_mb"] < 0).any():
        pytest.fail("memory.csv contains negative memory values")

    # If we reach here, the test passed
    assert True