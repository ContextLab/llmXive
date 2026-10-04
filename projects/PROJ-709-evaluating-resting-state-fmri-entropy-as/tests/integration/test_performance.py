"""
Integration test for performance and runtime constraints (US3).

This test verifies that the pipeline can process a subset of subjects
within the specified time budget (6 hours).
"""
import os
import sys
import subprocess
import time
import json
from pathlib import Path

import pytest

# Ensure code directory is in path for imports if needed, 
# though we are primarily running the script via subprocess.
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
RUNTIME_LOG_PATH = DATA_DERIVED_DIR / "runtime_log.txt"

# Ensure the directory exists
DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)

@pytest.mark.integration
@pytest.mark.performance
def test_pipeline_runtime_subset():
    """
    Run code/main.py with --subset=50 and assert runtime < 6 hours.
    
    This test:
    1. Executes the main pipeline with a subset of 50 subjects.
    2. Measures the total wall-clock time.
    3. Asserts the time is less than 6 hours (21600 seconds).
    4. Writes the runtime result to data/derived/runtime_log.txt.
    """
    # Define the timeout threshold: 6 hours in seconds
    TIME_LIMIT_SECONDS = 6 * 60 * 60  # 21600 seconds
    
    # Prepare the command
    # We use the system python to ensure we run in the environment 
    # where the project dependencies are installed.
    cmd = [
        sys.executable,
        str(CODE_DIR / "main.py"),
        "--subset", "50"
    ]
    
    start_time = time.time()
    exit_code = None
    stdout = None
    stderr = None

    try:
        # Run the script with a timeout to prevent hanging indefinitely,
        # though the assertion below is the primary check.
        # We capture output to log in case of failure.
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=TIME_LIMIT_SECONDS + 300  # Add 5 min buffer for cleanup
        )
        exit_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired:
        # If the process exceeds the timeout, we fail the test immediately
        # but we still want to log the fact that it timed out.
        elapsed = time.time() - start_time
        log_entry = {
            "test": "test_pipeline_runtime_subset",
            "subset_size": 50,
            "elapsed_seconds": elapsed,
            "time_limit_seconds": TIME_LIMIT_SECONDS,
            "status": "TIMEOUT",
            "message": "Pipeline execution exceeded the 6-hour time limit."
        }
        _write_runtime_log(log_entry)
        pytest.fail(f"Pipeline execution timed out after {TIME_LIMIT_SECONDS} seconds.")
    
    end_time = time.time()
    elapsed_seconds = end_time - start_time

    # Construct log entry
    log_entry = {
        "test": "test_pipeline_runtime_subset",
        "subset_size": 50,
        "elapsed_seconds": round(elapsed_seconds, 2),
        "time_limit_seconds": TIME_LIMIT_SECONDS,
        "status": "PASSED" if exit_code == 0 and elapsed_seconds < TIME_LIMIT_SECONDS else "FAILED",
        "exit_code": exit_code
    }

    if exit_code != 0:
        log_entry["error_details"] = stderr[:1000] if stderr else "No stderr output"
        pytest.fail(f"Pipeline execution failed with exit code {exit_code}. Stderr: {stderr}")

    # Assert runtime constraint
    assert elapsed_seconds < TIME_LIMIT_SECONDS, (
        f"Pipeline runtime ({elapsed_seconds:.2f}s) exceeded limit ({TIME_LIMIT_SECONDS}s). "
        f"This indicates a performance regression."
    )

    # Write to runtime log
    _write_runtime_log(log_entry)

    # Verify the log file was written
    assert RUNTIME_LOG_PATH.exists(), "Runtime log file was not created."

def _write_runtime_log(entry: dict):
    """Appends a JSON line to the runtime log file."""
    with open(RUNTIME_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    # Allow running directly via pytest or python
    pytest.main([__file__, "-v"])
