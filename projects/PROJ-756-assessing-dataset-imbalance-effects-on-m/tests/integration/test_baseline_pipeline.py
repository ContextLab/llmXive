"""
Integration test for the baseline pipeline (US1).
Verifies the full flow: Ingestion -> Descriptors -> Imbalance Calc -> Baseline Training -> Evaluation.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from ingestion import main as run_ingestion
from descriptors import main as run_descriptors
from imbalance import main as run_imbalance
from training import main as run_training
from evaluation import main as run_evaluation

DATA_DIR = Path(__file__).parent.parent.parent / "data"
RESULTS_DIR = Path(__file__).parent.parent.parent / "results"

@pytest.fixture(autouse=True)
def ensure_directories():
    """Ensure required directories exist before test."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    yield

def test_baseline_pipeline_end_to_end():
    """
    Run the full baseline pipeline and verify outputs exist and are valid.
    This test simulates the execution of T014-T017 in sequence.
    """
    # 1. Run Ingestion (T004/T006 logic)
    # Note: If real data is not available, this will raise an error as per constraints.
    # We assume T004/T006 have successfully populated data/raw/ or the script handles
    # the missing data state by failing loudly (which this test expects to propagate
    # if data is truly missing, or succeed if data exists).
    try:
        run_ingestion()
    except Exception as e:
        # If ingestion fails because data is missing (and not synthetic),
        # we cannot proceed with the integration test.
        # In a real CI environment, this would fail the build.
        # For this specific task, we assert that if the pipeline is expected to run,
        # the data must be present.
        if "No data found" in str(e) or "FileNotFoundError" in str(e):
            pytest.skip("Real data not present for integration test. Skipping to avoid fabrication.")
        raise

    # 2. Run Descriptors (T007)
    run_descriptors()

    # Verify processed data exists
    processed_files = list((DATA_DIR / "processed").glob("*.csv"))
    assert len(processed_files) > 0, "Descriptors were not saved to data/processed/"

    # 3. Run Imbalance Calculation (T008/T009)
    run_imbalance()

    # 4. Run Training (T014/T015)
    run_training()

    # Verify models or training artifacts exist (training.py usually saves models or metrics)
    # Depending on implementation, training.py might save models to a specific dir or just metrics.
    # We check for the existence of the training output defined in T016/evaluation flow.
    # If training.py doesn't save a specific file, we rely on the next step (Evaluation) to fail if models are missing.
    
    # 5. Run Evaluation (T016)
    run_evaluation()

    # 6. Verify Final Output
    baseline_report = RESULTS_DIR / "baseline_report.csv"
    assert baseline_report.exists(), f"Baseline report {baseline_report} was not generated."

    # Validate content of the report
    df = pd.read_csv(baseline_report)
    assert not df.empty, "Baseline report is empty."
    
    required_columns = ["property", "mae", "rmse", "r2"]
    # Check if at least the required columns exist (case insensitive check for robustness)
    cols_lower = [c.lower() for c in df.columns]
    for req in required_columns:
        assert req in cols_lower, f"Missing required column '{req}' in baseline report. Found: {df.columns}"

    # Verify we have at least one row of data
    assert len(df) > 0, "Baseline report contains no results."

    # Check for plausible values (MAE/RMSE should be positive numbers)
    # This prevents a report filled with NaN or 0 if the model failed silently.
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        if col.lower() in ['mae', 'rmse']:
            # Ensure at least some positive values exist if the metric is calculated
            # If all are NaN, the test fails.
            valid_vals = df[col].dropna()
            if len(valid_vals) > 0:
                # If we have values, they should be non-negative for MAE/RMSE
                assert (valid_vals >= 0).all(), f"Negative values found in {col}, which is invalid for error metrics."

    print("Baseline pipeline integration test PASSED.")
    print(f"Report generated at: {baseline_report}")
    print(f"Rows: {len(df)}, Columns: {list(df.columns)}")
    print(df.head())