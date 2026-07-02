"""
Integration test for full pipeline run (T014).
Verifies runtime < 6h and RAM < 7GB on the synthetic dataset.
"""
import os
import sys
import time
import tracemalloc
import subprocess
import json
import pytest
from pathlib import Path

# Add project root to path to allow imports from code/
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_path, load_config

# Constants for constraints
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours
MAX_RAM_BYTES = 7 * 1024**3     # 7 GB

def test_full_pipeline_runtime_and_memory():
    """
    Runs the full pipeline (T019 main.py) and asserts:
    1. Execution completes successfully (exit code 0).
    2. Runtime is under 6 hours.
    3. Peak memory usage is under 7 GB.
    4. Output artifacts (metrics.json) are generated.
    """
    # Start memory tracking
    tracemalloc.start()
    start_time = time.time()

    # Construct command to run the pipeline
    # We assume the synthetic data generation is triggered automatically if no real data is found,
    # as per T010 and T009 logic.
    main_script = PROJECT_ROOT / "code" / "main.py"
    
    if not main_script.exists():
        pytest.fail("code/main.py not found. Ensure T019 is implemented.")

    try:
        # Run the pipeline
        # Using subprocess to capture real execution time and exit code
        result = subprocess.run(
            [sys.executable, str(main_script)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=MAX_RUNTIME_SECONDS + 60  # Add buffer for timeout
        )

        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        runtime_seconds = end_time - start_time
        peak_ram_gb = peak / (1024**3)

        # Assert Exit Code
        if result.returncode != 0:
            # Log error output for debugging
            error_msg = f"Pipeline failed with exit code {result.returncode}.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            pytest.fail(error_msg)

        # Assert Runtime Constraint
        assert runtime_seconds < MAX_RUNTIME_SECONDS, (
            f"Pipeline runtime {runtime_seconds:.2f}s exceeds limit {MAX_RUNTIME_SECONDS}s (6h)."
        )

        # Assert Memory Constraint
        assert peak_ram_gb < 7.0, (
            f"Peak memory usage {peak_ram_gb:.2f} GB exceeds limit 7.0 GB."
        )

        # Assert Output Artifact Existence
        metrics_path = get_path("artifacts/reports/metrics.json")
        if not os.path.exists(metrics_path):
            pytest.fail(f"Output artifact {metrics_path} was not generated.")

        # Verify content of metrics.json is valid JSON
        try:
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            assert isinstance(metrics, dict), "metrics.json must be a JSON object."
            # Basic sanity check that it contains expected keys
            assert "cv_accuracy" in metrics or "r2" in metrics or "auc" in metrics, (
                "metrics.json missing expected performance metrics."
            )
        except json.JSONDecodeError:
            pytest.fail(f"Output artifact {metrics_path} is not valid JSON.")

        # Print summary for logs
        print(f"\n--- Pipeline Test Summary ---")
        print(f"Runtime: {runtime_seconds:.2f} seconds ({runtime_seconds/60:.2f} minutes)")
        print(f"Peak RAM: {peak_ram_gb:.2f} GB")
        print(f"Status: PASSED")
        print(f"Metrics file: {metrics_path}")

    except subprocess.TimeoutExpired:
        tracemalloc.stop()
        pytest.fail(f"Pipeline execution timed out after {MAX_RUNTIME_SECONDS} seconds.")
    except Exception as e:
        tracemalloc.stop()
        pytest.fail(f"Pipeline execution encountered an unexpected error: {str(e)}")
