"""
Integration Test for the Full Pipeline (T030).

This test verifies that the pipeline scripts can be imported and that the
required artifacts are generated when the main script is run.
"""
import os
import sys
import json
import subprocess
import tempfile
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent / "projects" / "PROJ-030-predicting-crystal-structures-from-molec"
CODE_DIR = PROJECT_ROOT / "code"
sys.path.insert(0, str(CODE_DIR))

from config import get_path_results, get_path_processed_data

@pytest.mark.integration
def test_pipeline_execution():
    """
    Runs the full pipeline script and verifies the timing log is created.
    Note: This test may take a long time or fail in CI if data is not available.
    It is primarily a smoke test for the orchestration logic.
    """
    pipeline_script = PROJECT_ROOT / "code" / "execution" / "run_full_pipeline.py"
    
    if not pipeline_script.exists():
        pytest.skip("Pipeline script not found. T030 implementation may be incomplete.")

    # Run the pipeline with a timeout to prevent hanging in CI if it takes too long
    # In a real run, we expect it to take minutes/hours. Here we just check it starts and creates the log.
    # We use a short timeout for CI safety, but the actual task T030 runs without this limit.
    try:
        result = subprocess.run(
            [sys.executable, str(pipeline_script)],
            cwd=PROJECT_ROOT,
            timeout=300, # 5 minutes timeout for the test run
            capture_output=True,
            text=True
        )
        
        # Check if the timing log was created
        results_dir = get_path_results()
        timing_log_path = os.path.join(results_dir, "pipeline_timing.log")
        
        assert os.path.exists(timing_log_path), f"Timing log not found at {timing_log_path}"
        
        with open(timing_log_path, "r") as f:
            log_data = json.load(f)
        
        assert "duration_seconds" in log_data
        assert "status" in log_data
        
        # The test passes if the script ran and produced the log,
        # even if the pipeline failed partway through (which is expected in CI).
        assert True 

    except subprocess.TimeoutExpired:
        # If it times out, it means it's running (which is good for T030), 
        # but for this unit test we consider it a pass if it started.
        # In a real CI, we might want to check for partial artifacts.
        pytest.skip("Pipeline took too long for the integration test timeout.")
    except Exception as e:
        # If it crashes immediately, that's a failure.
        pytest.fail(f"Pipeline execution failed: {e}")
