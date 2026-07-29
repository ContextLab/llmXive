import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from main import run_data_pipeline, run_analysis_pipeline, log_quality_warnings
from data.lag import calculate_physics_lag

RESULTS_DIR = project_root / "results"
DATA_PROCESSED_DIR = project_root / "data" / "processed"
REPORT_PATH = RESULTS_DIR / "us1_correlation.json"

@pytest.fixture(scope="module")
def pipeline_results():
    """Run the full pipeline once to generate the report for T025 verification."""
    # Ensure directories exist
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Run data pipeline (ingest + clean)
    # Using a short, recent range to minimize API load and execution time
    # Note: If network fails, this test will fail loudly as per constraints.
    try:
        df_sw, df_ey = run_data_pipeline(
            start_date="2023-01-01",
            end_date="2023-01-03"
        )
    except Exception as e:
        pytest.fail(f"Data pipeline execution failed: {e}")

    # Run analysis pipeline
    try:
        results = run_analysis_pipeline(df_sw, df_ey)
    except Exception as e:
        pytest.fail(f"Analysis pipeline execution failed: {e}")

    # Save results to the expected JSON path
    with open(REPORT_PATH, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    # Log quality warnings (required deliverable)
    log_quality_warnings(df_sw, df_ey)

    return results

def test_t025_lag_difference_exists(pipeline_results):
    """
    T025 Verification: Check that the pipeline calculates and reports |L* - L_phys|.
    This verifies SC-002 requirement.
    """
    assert "lag_difference" in pipeline_results, (
        "Missing 'lag_difference' key in pipeline results. "
        "SC-002 calculation (|L* - L_phys|) was not performed or reported."
    )

    lag_diff = pipeline_results["lag_difference"]
    assert isinstance(lag_diff, (int, float, np.floating)), (
        f"'lag_difference' must be numeric, got {type(lag_diff)}"
    )
    assert not np.isnan(lag_diff), (
        "lag_difference is NaN. Ensure both L* and L_phys were valid numbers."
    )

def test_t025_report_file_contents(pipeline_results):
    """
    T025 Verification: Ensure the JSON file on disk contains the lag_difference key.
    """
    assert REPORT_PATH.exists(), f"Report file {REPORT_PATH} was not created."

    with open(REPORT_PATH, 'r') as f:
        saved_results = json.load(f)

    assert "lag_difference" in saved_results, (
        f"'lag_difference' key missing from {REPORT_PATH}. "
        "The pipeline must write this value to the JSON report."
    )

def test_t025_quality_log_exists():
    """
    T025 Verification: Ensure data/processed/quality_log.json exists as a side effect.
    """
    log_path = DATA_PROCESSED_DIR / "quality_log.json"
    assert log_path.exists(), (
        f"Missing required deliverable: {log_path}. "
        "The pipeline must log data-quality warnings to this file."
    )

    with open(log_path, 'r') as f:
        content = json.load(f)
    assert isinstance(content, list), "quality_log.json must contain a list of warnings."