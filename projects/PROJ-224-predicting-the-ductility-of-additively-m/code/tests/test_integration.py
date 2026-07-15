import pytest
import os
import subprocess
from pathlib import Path
import sys
import time
import logging

# Configure logging for the test
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
MAIN_SCRIPT = PROJECT_ROOT / "code" / "main.py"
BUDGET_SECONDS = 600

def test_pipeline_execution():
    """
    T038: Run full pipeline integration test (main.py) to ensure end-to-end execution ≤ 600s.
    
    This test executes the main pipeline script and verifies:
    1. The script exits with code 0 (success).
    2. The total execution time is within the 600-second budget.
    3. The expected output artifacts are generated.
    """
    logger.info(f"Starting full pipeline integration test for T038.")
    logger.info(f"Budget: {BUDGET_SECONDS} seconds.")
    logger.info(f"Script: {MAIN_SCRIPT}")

    if not MAIN_SCRIPT.exists():
        pytest.fail(f"Main script not found at {MAIN_SCRIPT}")

    start_time = time.time()
    
    try:
        # Run the main pipeline script
        # We use the current sys.executable to ensure we are running in the correct venv
        result = subprocess.run(
            [sys.executable, str(MAIN_SCRIPT)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=BUDGET_SECONDS + 10  # Add 10s buffer for cleanup
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time

        # Log output for debugging
        if result.stdout:
            logger.info("STDOUT:\n" + result.stdout)
        if result.stderr:
            logger.info("STDERR:\n" + result.stderr)

        # Check execution time
        assert elapsed_time <= BUDGET_SECONDS, (
            f"Pipeline execution took {elapsed_time:.2f}s, exceeding the {BUDGET_SECONDS}s budget."
        )
        logger.info(f"Pipeline executed successfully in {elapsed_time:.2f}s (within {BUDGET_SECONDS}s budget).")

        # Check exit code
        assert result.returncode == 0, (
            f"Pipeline failed with exit code {result.returncode}.\nSTDERR: {result.stderr}"
        )
        logger.info("Pipeline exited with code 0.")

        # Verify expected artifacts exist (based on previous tasks)
        expected_artifacts = [
            PROJECT_ROOT / "data" / "curated_builds.csv",
            PROJECT_ROOT / "artifacts" / "xgboost_model.pkl",
            PROJECT_ROOT / "artifacts" / "mixed_effects_results.json",
            PROJECT_ROOT / "artifacts" / "predictive_model_artifact.json",
            PROJECT_ROOT / "state" / "projects" / "PROJ-224-predicting-the-ductility-of-additively-m.yaml"
        ]

        missing_artifacts = [p for p in expected_artifacts if not p.exists()]
        if missing_artifacts:
            logger.warning(f"Missing expected artifacts: {missing_artifacts}")
            # Depending on strictness, this might be a warning or a fail.
            # For T038, the primary requirement is execution time and success.
            # However, if the pipeline claims success, artifacts should exist.
            # We will fail if critical data is missing.
            pytest.fail(f"Pipeline reported success but missing critical artifacts: {missing_artifacts}")
        
        logger.info("All expected artifacts verified.")

    except subprocess.TimeoutExpired:
        pytest.fail(f"Pipeline execution timed out after {BUDGET_SECONDS} seconds.")
    except Exception as e:
        pytest.fail(f"Pipeline execution failed with exception: {str(e)}")