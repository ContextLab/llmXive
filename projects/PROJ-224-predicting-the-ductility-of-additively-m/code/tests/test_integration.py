"""
Integration test for the full pipeline execution (T038).
Verifies end-to-end execution completes within the 600s budget.
"""
import pytest
import os
import subprocess
import time
import logging
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

logger = logging.getLogger(__name__)

BUDGET_SECONDS = 600
MAIN_SCRIPT = Path(__file__).parent.parent / "main.py"

def test_pipeline_execution():
    """
    Run the full pipeline via main.py and verify:
    1. Execution completes successfully (exit code 0).
    2. Total execution time is <= 600 seconds.
    3. Key output artifacts are generated.
    """
    if not MAIN_SCRIPT.exists():
        pytest.fail(f"Main script not found at {MAIN_SCRIPT}")

    logger.info(f"Starting full pipeline integration test with budget of {BUDGET_SECONDS}s...")
    start_time = time.time()

    # Run the main pipeline script
    # We use the current working directory as the project root
    try:
        result = subprocess.run(
            [sys.executable, str(MAIN_SCRIPT)],
            cwd=Path(__file__).parent.parent.parent, # Project root
            capture_output=True,
            text=True,
            timeout=BUDGET_SECONDS + 60 # Add buffer for timeout
        )
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        pytest.fail(f"Pipeline execution exceeded budget of {BUDGET_SECONDS}s (timed out at {elapsed:.1f}s)")

    elapsed = time.time() - start_time

    # Log output for debugging
    if result.stdout:
        logger.info("STDOUT:\n" + result.stdout)
    if result.stderr:
        logger.warning("STDERR:\n" + result.stderr)

    # Check execution time
    assert elapsed <= BUDGET_SECONDS, (
        f"Pipeline execution took {elapsed:.2f}s, exceeding budget of {BUDGET_SECONDS}s"
    )

    # Check exit code
    if result.returncode != 0:
        pytest.fail(
            f"Pipeline execution failed with exit code {result.returncode}. "
            f"See stderr: {result.stderr}"
        )

    # Verify key artifacts exist
    expected_artifacts = [
        Path("data/curated_builds.csv"),
        Path("artifacts/lme_results.json"),
        Path("artifacts/xgboost_model.pkl"),
        Path("artifacts/predictive_model_artifact.json"),
        Path("reports/final_report.md"),
    ]

    missing = []
    for artifact in expected_artifacts:
        full_path = Path.cwd() / artifact
        if not full_path.exists():
            missing.append(str(artifact))

    if missing:
        pytest.fail(f"Missing expected artifacts after pipeline run: {', '.join(missing)}")

    logger.info(f"Pipeline integration test passed. Total time: {elapsed:.2f}s")
    logger.info("All expected artifacts generated successfully.")
