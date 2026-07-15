"""
Integration tests for the full pipeline execution.
Specifically validates T038: End-to-end execution time budget.
"""
import pytest
import os
import subprocess
import time
import logging
from pathlib import Path
import sys

# Ensure code/ is in path for imports if running directly, 
# though pytest usually handles this via conftest or setup.
CODE_ROOT = Path(__file__).parent.parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

logger = logging.getLogger(__name__)

def test_pipeline_execution():
    """
    T038: Run full pipeline integration test (main.py) to ensure 
    end-to-end execution ≤ 600s.
    
    This test executes the main entry point of the project and measures
    the total wall-clock time. It asserts that the process completes
    successfully and within the 600-second budget.
    """
    main_script = CODE_ROOT / "main.py"
    
    if not main_script.exists():
        pytest.fail(f"Main script not found at {main_script}")

    logger.info(f"Starting pipeline integration test at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Executing: python {main_script}")

    start_time = time.time()
    
    # Run the main script
    # We capture stdout/stderr to log it if the test fails
    try:
        result = subprocess.run(
            [sys.executable, str(main_script)],
            capture_output=True,
            text=True,
            timeout=600 + 60,  # Add 60s buffer for OS overhead
            cwd=CODE_ROOT
        )
    except subprocess.TimeoutExpired:
        end_time = time.time()
        elapsed = end_time - start_time
        pytest.fail(f"Pipeline execution timed out after {elapsed:.2f}s (Budget: 600s)")

    end_time = time.time()
    elapsed = end_time - start_time

    # Log the output for debugging if needed
    if result.stdout:
        logger.info("STDOUT:\n" + result.stdout[-2000:]) # Log last 2000 chars
    if result.stderr:
        logger.error("STDERR:\n" + result.stderr[-2000:])

    # Assert success
    assert result.returncode == 0, (
        f"Pipeline failed with return code {result.returncode}.\n"
        f"Time elapsed: {elapsed:.2f}s.\n"
        f"Error output: {result.stderr}"
    )

    # Assert time budget
    assert elapsed <= 600.0, (
        f"Pipeline execution took {elapsed:.2f}s, exceeding the 600s budget.\n"
        f"Return code: {result.returncode}"
    )

    logger.info(f"Pipeline execution completed successfully in {elapsed:.2f}s.")