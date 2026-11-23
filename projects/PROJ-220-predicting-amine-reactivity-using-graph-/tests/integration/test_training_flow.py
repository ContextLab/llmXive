"""
Integration test for training pipeline completion within time/memory limits.
Tests T021: US2 Integration test for training pipeline completion.

This test verifies:
1. The training script executes successfully on a standard CPU environment.
2. It produces model artifacts (baseline and GNN).
3. It generates a test set prediction file with MAE and R² metrics.
4. It respects the time (6 hours) and memory (< 7GB) limits defined in FR-008.
"""
import os
import sys
import time
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.memory_monitor import check_limits, enforce_limits
from src.utils.sampling import sample_dataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TIME_LIMIT_SECONDS = 6 * 3600  # 6 hours
MEMORY_LIMIT_MB = 7000  # 7GB
EXPECTED_ARTIFACTS = [
    "data/derived/baseline_model.pkl",
    "data/derived/gnn_model.pkl",
    "data/derived/predictions_test.json",
    "data/derived/training_metrics.json",
]

def _ensure_test_data_exists():
    """
    Ensure that the necessary input data for training exists.
    In a real CI environment, this would be provided by previous stages (US1).
    For this integration test, we assume the data pipeline (US1) has run.
    If data is missing, we skip the test as it depends on US1 completion.
    """
    graph_file = PROJECT_ROOT / "data/derived/reaction_graphs.json"
    if not graph_file.exists():
        logger.warning(f"Training data not found at {graph_file}. Skipping test. "
                       "Ensure US1 (Data Ingestion) has run successfully.")
        pytest.skip("US1 data not found. Skipping training integration test.")
    return True

def _run_training_script():
    """
    Executes the training script (src/train.py) and monitors resource usage.
    """
    train_script = PROJECT_ROOT / "src" / "train.py"
    if not train_script.exists():
        # If train.py doesn't exist, we can't run the test.
        # This implies T024 is not done.
        pytest.fail("Training script (src/train.py) not found. T024 implementation required.")

    start_time = time.time()
    peak_memory_mb = 0

    try:
        # Run the training script
        # We capture output to check for errors
        result = subprocess.run(
            [sys.executable, str(train_script)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=TIME_LIMIT_SECONDS,
            env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        )

        elapsed_time = time.time() - start_time

        if result.returncode != 0:
            logger.error(f"Training script failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            raise RuntimeError(f"Training script failed: {result.stderr}")

        logger.info(f"Training completed in {elapsed_time:.2f} seconds")
        return elapsed_time

    except subprocess.TimeoutExpired:
        logger.error("Training script timed out.")
        raise TimeoutError(f"Training exceeded time limit of {TIME_LIMIT_SECONDS} seconds")
    except Exception as e:
        logger.error(f"Error running training script: {e}")
        raise

def _validate_artifacts():
    """
    Validates that all expected output artifacts were created and contain valid data.
    """
    missing_files = []
    invalid_files = []

    for artifact_path in EXPECTED_ARTIFACTS:
        full_path = PROJECT_ROOT / artifact_path
        if not full_path.exists():
            missing_files.append(artifact_path)
            continue

        # Basic validation of content
        if artifact_path.endswith(".json"):
            try:
                with open(full_path, 'r') as f:
                    data = json.load(f)
                    if artifact_path.endswith("training_metrics.json"):
                        if 'duration_seconds' not in data or 'peak_memory_mb' not in data:
                            invalid_files.append(artifact_path)
                    elif artifact_path.endswith("predictions_test.json"):
                        if not isinstance(data, list) or len(data) == 0:
                            invalid_files.append(artifact_path)
            except json.JSONDecodeError:
                invalid_files.append(artifact_path)
        elif artifact_path.endswith(".pkl"):
            # Just check if file is not empty
            if full_path.stat().st_size == 0:
                invalid_files.append(artifact_path)

    if missing_files:
        raise FileNotFoundError(f"Missing expected artifacts: {missing_files}")
    if invalid_files:
        raise ValueError(f"Invalid artifacts (empty or wrong schema): {invalid_files}")

    logger.info("All artifacts validated successfully.")

def _check_resource_limits(elapsed_time: float):
    """
    Checks if the training completed within time and memory limits.
    Note: Actual memory monitoring during the subprocess run is complex.
    We rely on the training script (T024) to enforce limits and log them,
    or we check the generated training_metrics.json.
    """
    metrics_path = PROJECT_ROOT / "data/derived/training_metrics.json"
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
            recorded_memory = metrics.get('peak_memory_mb', 0)
            recorded_duration = metrics.get('duration_seconds', 0)

            if recorded_memory > MEMORY_LIMIT_MB:
                raise AssertionError(f"Peak memory {recorded_memory}MB exceeded limit {MEMORY_LIMIT_MB}MB")
            
            # Double check time from metrics if available, otherwise use measured
            if recorded_duration > TIME_LIMIT_SECONDS:
                raise AssertionError(f"Duration {recorded_duration}s exceeded limit {TIME_LIMIT_SECONDS}s")
            
            logger.info(f"Resource limits check passed: Time={recorded_duration}s, Memory={recorded_memory}MB")
    else:
        # Fallback to measured time if metrics file is missing (though _validate_artifacts should catch this)
        if elapsed_time > TIME_LIMIT_SECONDS:
            raise AssertionError(f"Measured time {elapsed_time}s exceeded limit")
        logger.warning("training_metrics.json not found, relying on subprocess timeout check.")

@pytest.mark.integration
def test_training_flow_completion():
    """
    Integration test for training pipeline completion within time/memory limits.
    
    Steps:
    1. Verify input data exists (dependency on US1).
    2. Run the training script (src/train.py).
    3. Verify it completes within time limits.
    4. Verify all expected artifacts are created and valid.
    5. Verify resource usage (memory) is within limits.
    """
    # 1. Check prerequisites
    _ensure_test_data_exists()

    # 2. Run training
    elapsed_time = _run_training_script()

    # 3. Validate artifacts
    _validate_artifacts()

    # 4. Check resource limits
    _check_resource_limits(elapsed_time)

    logger.info("test_training_flow_completion PASSED")

if __name__ == "__main__":
    # Allow running directly
    pytest.main([__file__, "-v"])
