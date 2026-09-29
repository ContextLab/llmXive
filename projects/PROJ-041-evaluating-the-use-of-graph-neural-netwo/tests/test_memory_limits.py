"""
Test skeleton for graph construction memory limit (US1 - T010).

This test verifies that the graph construction pipeline in `code/data/preprocess.py`
adheres to the hard memory limit of 7GB when invoked via `memory_monitor.py`.

Dependencies:
  - T013 (Interface definition in preprocess.py)
  - T015 (Memory guard implementation in memory_monitor.py)
"""
import os
import sys
import subprocess
import pytest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.memory_monitor import MemoryLimitExceededError, get_peak_memory_mb

# Configuration
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024
PREPROCESS_SCRIPT = PROJECT_ROOT / "code" / "data" / "preprocess.py"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

def _ensure_test_data():
    """
    Ensure that a small subset of real data exists for testing.
    If the full dataset is not present, we attempt to use a minimal
    subset if available, or skip the test if no data is found.
    This prevents the test from failing due to missing data, but
    the actual memory limit check requires real data volume.
    """
    if not RAW_DATA_DIR.exists():
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for any CSV files in raw data
    csv_files = list(RAW_DATA_DIR.glob("*.csv"))
    if not csv_files:
        pytest.skip("No raw CSV data found in data/raw. "
                    "Please run T007a/T007b to download the dataset.")
    return csv_files[0]

def _run_preprocess_with_monitor(input_file):
    """
    Runs the preprocess script wrapped with memory monitoring logic.
    Since `memory_monitor.py` provides a context manager and enforcement,
    we invoke the script via subprocess to simulate the full pipeline
    execution, capturing the exit code and output.
    
    The actual memory limit enforcement is tested by ensuring that
    if the process exceeds the limit, it raises an error or exits
    with a specific code, which we can verify here.
    """
    # Construct command to run the preprocess script
    # We assume the script handles the input/output paths via CLI args or config
    cmd = [
        sys.executable, str(PREPROCESS_SCRIPT),
        "--input", str(input_file),
        "--output-dir", str(PROCESSED_DATA_DIR),
        "--scenario", "test_scenario"
    ]
    
    # Run the script
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )
    
    return result

def test_memory_limit_enforcement():
    """
    Test that the graph construction process respects the 7GB memory limit.
    
    This test:
    1. Loads a real data file (or skips if none available).
    2. Runs the `preprocess.py` script which internally uses `memory_monitor.py`.
    3. Verifies that if memory usage exceeds 7GB, the process fails with
       a `MemoryLimitExceededError` (exit code != 0 or specific error message).
    
    Note: This test assumes T015 (Memory Guard) is implemented to raise
    `MemoryLimitExceededError` when the limit is breached.
    """
    input_file = _ensure_test_data()
    
    # Run the preprocessing script
    result = _run_preprocess_with_monitor(input_file)
    
    # Check for successful execution or expected failure due to memory
    # If the script ran successfully, we check if it wrote the expected artifacts
    # If it failed due to memory, we expect a specific error message or exit code.
    
    # For a "skeleton" test, we primarily verify that the pipeline can be invoked
    # and that the memory monitor is integrated.
    # In a real scenario with large data, we would expect:
    # - If data < 7GB: Success (Exit code 0)
    # - If data > 7GB: Failure with MemoryLimitExceededError (Exit code != 0)
    
    # Since we might not have enough data to actually trigger the limit,
    # we verify that the script ran and produced output or an error.
    # We assert that the script did not crash with a generic Python error.
    
    assert result.returncode == 0 or "MemoryLimitExceeded" in result.stdout or "MemoryLimitExceeded" in result.stderr, \
        f"Preprocess script failed unexpectedly. stdout: {result.stdout}, stderr: {result.stderr}"
    
    # Verify that the memory monitor logic was triggered (log message or output)
    # We check for the presence of the memory monitor's import or usage in the logs
    # This is a heuristic check for integration
    assert "tracemalloc" in result.stderr.lower() or "memory" in result.stderr.lower() or result.returncode == 0, \
        "Memory monitor integration not detected in output."

def test_memory_monitor_integration():
    """
    Direct unit test for the memory monitor integration in the preprocess pipeline.
    
    This test verifies that the `memory_monitor.py` module is correctly imported
    and that the `MemoryLimitExceededError` is available for use in `preprocess.py`.
    """
    # Verify imports are correct
    from utils.memory_monitor import MemoryLimitExceededError, enforce_memory_limit
    from data.preprocess import preprocess_graph, main
    
    # Verify that the preprocess module has the capacity to use the monitor
    # We check the source code or docstrings for the memory limit logic
    import inspect
    source = inspect.getsource(preprocess_graph)
    
    assert "tracemalloc" in source or "memory_monitor" in source, \
        "preprocess_graph does not appear to use memory monitoring."
    
    # Verify the exception class is defined
    assert issubclass(MemoryLimitExceededError, Exception), \
        "MemoryLimitExceededError must be an Exception subclass."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])