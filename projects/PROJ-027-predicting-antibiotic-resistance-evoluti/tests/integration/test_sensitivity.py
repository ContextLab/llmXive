"""
Integration test for sensitivity sweep output (Task T029).

This test verifies that the sensitivity analysis script:
1. Runs successfully on the processed data.
2. Generates the expected output file: `data/processed/sensitivity_results.csv`.
3. Produces a valid CSV with the required columns.
4. Handles the case where no models exist by failing loudly (not faking data).

Prerequisites:
- T027 must be completed (models saved to `data/models/`).
- T023a/T023b/T023c must be completed (filtered matrix and splits available).
- T032 (sensitivity_analysis.py) must be implemented.
"""

import os
import sys
import subprocess
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path for imports if running directly
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging import get_logger

logger = get_logger(__name__)

# Constants matching the project structure
SENSITIVITY_SCRIPT = PROJECT_ROOT / "code" / "04_validate" / "sensitivity_analysis.py"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "sensitivity_results.csv"
MODELS_DIR = PROJECT_ROOT / "data" / "models"

@pytest.fixture(scope="module", autouse=True)
def ensure_output_dir():
    """Ensure the output directory exists before tests run."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    yield

def test_sensitivity_sweep_execution():
    """
    Integration test: Run the sensitivity analysis script and verify output.

    This test asserts that:
    1. The script file exists.
    2. The script runs without raising a non-zero exit code.
    3. The output file `data/processed/sensitivity_results.csv` is created.
    4. The output file contains the expected columns.
    """
    # 1. Verify script exists
    assert SENSITIVITY_SCRIPT.exists(), (
        f"Sensitivity analysis script not found at {SENSITIVITY_SCRIPT}. "
        "Ensure T032 (sensitivity_analysis.py) is implemented."
    )

    # 2. Verify models exist (prerequisite check)
    if not any(MODELS_DIR.glob("*.pkl")) and not any(MODELS_DIR.glob("*.json")):
        pytest.fail(
            f"No model artifacts found in {MODELS_DIR}. "
            "T027 (save_models.py) must be completed before running this test."
        )

    # 3. Run the script
    # We run it as a subprocess to ensure it executes the full pipeline logic
    # and writes to disk, rather than just importing functions.
    cmd = [sys.executable, str(SENSITIVITY_SCRIPT)]
    logger.info(f"Running sensitivity analysis: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout for integration test
        )
    except subprocess.TimeoutExpired:
        pytest.fail("Sensitivity analysis script timed out.")

    # Log output for debugging
    if result.stdout:
        logger.info("Script stdout:\n" + result.stdout)
    if result.stderr:
        logger.error("Script stderr:\n" + result.stderr)

    # 4. Assert success
    assert result.returncode == 0, (
        f"Script failed with exit code {result.returncode}.\n"
        f"Stderr: {result.stderr}\n"
        f"Stdout: {result.stdout}"
    )

    # 5. Verify output file exists
    assert OUTPUT_FILE.exists(), (
        f"Expected output file {OUTPUT_FILE} was not created. "
        "The script must write results to data/processed/sensitivity_results.csv."
    )

    # 6. Verify output content schema
    df = pd.read_csv(OUTPUT_FILE)

    required_columns = {
        "antibiotic_class",
        "threshold",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "false_positive_rate",
        "false_negative_rate"
    }

    missing_columns = required_columns - set(df.columns)
    assert not missing_columns, (
        f"Output CSV is missing required columns: {missing_columns}. "
        f"Found columns: {list(df.columns)}"
    )

    # 7. Verify data integrity (non-empty, valid ranges)
    assert len(df) > 0, "Output CSV is empty. No thresholds were swept."
    
    # Check that thresholds are numeric and within expected range (0.0 to 1.0)
    assert df["threshold"].between(0.0, 1.0).all(), "Threshold values must be between 0.0 and 1.0."
    
    # Check that metrics are numeric
    metric_cols = ["accuracy", "precision", "recall", "f1_score", "false_positive_rate", "false_negative_rate"]
    for col in metric_cols:
        assert pd.api.types.is_numeric_dtype(df[col]), f"Column {col} must be numeric."

    logger.info("Sensitivity sweep integration test passed.")