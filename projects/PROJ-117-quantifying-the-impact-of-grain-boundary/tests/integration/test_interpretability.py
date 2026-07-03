"""
Integration test for User Story 3: Feature Interpretability & Sensitivity Analysis.

Verifies that:
1. The interpretability script runs without error.
2. SHAP plots are generated in artifacts/figures/.
3. The sensitivity table (threshold-variation-table.csv) is generated in artifacts/reports/.
4. The generated artifacts are non-empty and contain expected columns/structures.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import pandas as pd

# Project root relative to this test file (assumes tests/integration/ structure)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
FIGURES_DIR = ARTIFACTS_DIR / "figures"
REPORTS_DIR = ARTIFACTS_DIR / "reports"
MODEL_PATH = PROJECT_ROOT / "models" / "best_model.json"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_dataset.parquet"

# Expected outputs based on T021 specification
EXPECTED_SHAP_SUMMARY_PLOT = FIGURES_DIR / "shap_summary.png"
EXPECTED_FEATURE_IMPORTANCE_PLOT = FIGURES_DIR / "shap_feature_importance.png"
EXPECTED_SENSITIVITY_TABLE = REPORTS_DIR / "threshold-variation-table.csv"
EXPECTED_SENSITIVITY_REPORT = REPORTS_DIR / "sensitivity_analysis.json"

@pytest.fixture(autouse=True)
def setup_environment():
    """Ensure required directories exist before test."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    # Clean up any previous test artifacts to ensure fresh generation
    for f in [EXPECTED_SHAP_SUMMARY_PLOT, EXPECTED_FEATURE_IMPORTANCE_PLOT, 
              EXPECTED_SENSITIVITY_TABLE, EXPECTED_SENSITIVITY_REPORT]:
        if f.exists():
            f.unlink()

def test_interpretability_pipeline_execution():
    """
    Test that the interpret.py script runs successfully end-to-end.
    
    This test assumes:
    1. T012 (Training) has completed and produced models/best_model.json
    2. T011 (Preprocessing) has completed and produced data/processed/cleaned_dataset.parquet
    
    If these prerequisites are missing, the test will fail, which is expected behavior
    for an integration test in a sequential pipeline.
    """
    # Verify prerequisites exist before running the script
    if not MODEL_PATH.exists():
        pytest.skip(f"Model artifact not found at {MODEL_PATH}. "
                   "Prerequisite T012 (Training) must be completed first.")
    
    if not PROCESSED_DATA_PATH.exists():
        pytest.skip(f"Cleaned dataset not found at {PROCESSED_DATA_PATH}. "
                   "Prerequisite T011 (Preprocessing) must be completed first.")

    # Run the interpretability script
    result = subprocess.run(
        [sys.executable, str(CODE_DIR / "interpret.py")],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )

    # Assert script execution was successful
    assert result.returncode == 0, (
        f"interpret.py failed with exit code {result.returncode}\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

def test_shap_plots_generated():
    """
    Verify that SHAP plots are generated and are non-empty.
    """
    # Run the script first to ensure artifacts are created
    subprocess.run(
        [sys.executable, str(CODE_DIR / "interpret.py")],
        cwd=str(PROJECT_ROOT),
        check=True,
        capture_output=True
    )

    # Check SHAP summary plot
    assert EXPECTED_SHAP_SUMMARY_PLOT.exists(), (
        f"SHAP summary plot not found at {EXPECTED_SHAP_SUMMARY_PLOT}"
    )
    assert EXPECTED_SHAP_SUMMARY_PLOT.stat().st_size > 0, (
        f"SHAP summary plot at {EXPECTED_SHAP_SUMMARY_PLOT} is empty"
    )

    # Check feature importance plot
    assert EXPECTED_FEATURE_IMPORTANCE_PLOT.exists(), (
        f"Feature importance plot not found at {EXPECTED_FEATURE_IMPORTANCE_PLOT}"
    )
    assert EXPECTED_FEATURE_IMPORTANCE_PLOT.stat().st_size > 0, (
        f"Feature importance plot at {EXPECTED_FEATURE_IMPORTANCE_PLOT} is empty"
    )

def test_sensitivity_table_generated():
    """
    Verify that the sensitivity table is generated with correct structure.
    """
    # Run the script first to ensure artifacts are created
    subprocess.run(
        [sys.executable, str(CODE_DIR / "interpret.py")],
        cwd=str(PROJECT_ROOT),
        check=True,
        capture_output=True
    )

    # Check sensitivity table exists
    assert EXPECTED_SENSITIVITY_TABLE.exists(), (
        f"Sensitivity table not found at {EXPECTED_SENSITIVITY_TABLE}"
    )
    
    # Load and validate the table structure
    df = pd.read_csv(EXPECTED_SENSITIVITY_TABLE)
    
    # Verify required columns exist (based on T021 specification)
    required_columns = ["threshold", "pass_rate", "num_pass", "num_total"]
    for col in required_columns:
        assert col in df.columns, (
            f"Required column '{col}' not found in sensitivity table. "
            f"Found columns: {list(df.columns)}"
        )
    
    # Verify data types and values are reasonable
    assert df["threshold"].dtype in ["float64", "int64", "float32"], (
        f"Threshold column should be numeric, got {df['threshold'].dtype}"
    )
    assert df["pass_rate"].between(0, 1).all(), (
        "Pass rate values should be between 0 and 1"
    )
    assert len(df) > 0, "Sensitivity table should contain at least one row"

def test_sensitivity_report_generated():
    """
    Verify that the sensitivity analysis report is generated and contains 
    the R² threshold justification.
    """
    # Run the script first to ensure artifacts are created
    subprocess.run(
        [sys.executable, str(CODE_DIR / "interpret.py")],
        cwd=str(PROJECT_ROOT),
        check=True,
        capture_output=True
    )

    # Check report exists
    assert EXPECTED_SENSITIVITY_REPORT.exists(), (
        f"Sensitivity report not found at {EXPECTED_SENSITIVITY_REPORT}"
    )

    # Load and validate the report
    with open(EXPECTED_SENSITIVITY_REPORT, 'r') as f:
        report = json.load(f)
    
    # Verify required fields exist
    assert "threshold_justification" in report, (
        "Report must contain 'threshold_justification' field as per T021 specification"
    )
    assert "summary_metrics" in report, (
        "Report must contain 'summary_metrics' field"
    )
    
    # Verify justification is a non-empty string
    assert isinstance(report["threshold_justification"], str), (
        "Threshold justification should be a string"
    )
    assert len(report["threshold_justification"]) > 0, (
        "Threshold justification should not be empty"
    )
    
    # Verify the justification references community standards or documentation
    justification_lower = report["threshold_justification"].lower()
    assert any(term in justification_lower for term in ["community", "standard", "benchmark", "literature", "reference"]), (
        f"Threshold justification should reference community standards or literature. "
        f"Got: {report['threshold_justification']}"
    )

def test_artifacts_directory_structure():
    """
    Verify that all expected artifacts are in the correct directory structure.
    """
    # Run the script first
    subprocess.run(
        [sys.executable, str(CODE_DIR / "interpret.py")],
        cwd=str(PROJECT_ROOT),
        check=True,
        capture_output=True
    )

    # Verify directory structure
    assert FIGURES_DIR.exists(), "figures directory should exist"
    assert REPORTS_DIR.exists(), "reports directory should exist"
    
    # Count generated artifacts
    figure_files = list(FIGURES_DIR.glob("*.png"))
    report_files = list(REPORTS_DIR.glob("*.csv")) + list(REPORTS_DIR.glob("*.json"))
    
    assert len(figure_files) >= 2, (
        f"At least 2 SHAP plots should be generated. Found: {len(figure_files)}"
    )
    assert len(report_files) >= 2, (
        f"At least 2 report files (CSV + JSON) should be generated. Found: {len(report_files)}"
    )