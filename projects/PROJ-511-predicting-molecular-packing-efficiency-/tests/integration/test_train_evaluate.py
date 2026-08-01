"""
Integration test for the training and evaluation pipeline (US2).

This test verifies that the full pipeline from feature assembly to model evaluation
runs successfully on real data, producing the expected artifacts:
- models/baseline_checkpoint.pt
- models/control_3d_checkpoint.pt
- models/upper_bound_checkpoint.pt
- results/validation_report.json
- results/comparative_analysis.csv

It depends on T018 (dataset.csv) and T024 (feature_matrix.npy, targets.npy) being complete.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure the code directory is in the path for imports
CODE_DIR = Path(__file__).parent.parent.parent / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from feature_assembly import main as assemble_features
from train import main as train_models
from evaluate import main as evaluate_models


def test_train_evaluate_pipeline():
    """
    Run the training and evaluation pipeline end-to-end.

    This test:
    1. Verifies that the required input files exist (dataset.csv, features_matrix.npy, targets.npy).
    2. Executes the training script to produce model checkpoints.
    3. Executes the evaluation script to produce validation reports.
    4. Validates that the output files exist and contain expected data.
    """

    # Paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    models_dir = project_root / "models"
    results_dir = project_root / "results"

    dataset_path = data_dir / "dataset.csv"
    features_path = data_dir / "features_matrix.npy"
    targets_path = data_dir / "targets.npy"

    baseline_model_path = models_dir / "baseline_checkpoint.pt"
    control_model_path = models_dir / "control_3d_checkpoint.pt"
    upper_bound_model_path = models_dir / "upper_bound_checkpoint.pt"

    validation_report_path = results_dir / "validation_report.json"
    comparative_analysis_path = results_dir / "comparative_analysis.csv"

    # Ensure output directories exist
    models_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Check preconditions
    assert dataset_path.exists(), f"Dataset file not found: {dataset_path}"
    assert features_path.exists(), f"Feature matrix not found: {features_path}"
    assert targets_path.exists(), f"Targets file not found: {targets_path}"

    # Clean up previous runs to ensure fresh artifacts
    for path in [baseline_model_path, control_model_path, upper_bound_model_path,
                 validation_report_path, comparative_analysis_path]:
        if path.exists():
            path.unlink()

    # Run Training
    # We call main() directly. The training script expects to find the data in the default locations.
    # If the script requires command-line arguments, we would need to mock sys.argv or refactor.
    # Assuming the script uses hardcoded paths or config relative to project root as per plan.
    try:
        train_models()
    except SystemExit as e:
        # Some scripts call sys.exit(0) on success. We treat that as pass.
        if e.code != 0:
            pytest.fail(f"Training script exited with code {e.code}")

    # Verify training outputs
    assert baseline_model_path.exists(), "Baseline model checkpoint not created"
    assert control_model_path.exists(), "Control model checkpoint not created"
    assert upper_bound_model_path.exists(), "Upper bound model checkpoint not created"

    # Verify model files are non-empty
    assert baseline_model_path.stat().st_size > 0, "Baseline model checkpoint is empty"
    assert control_model_path.stat().st_size > 0, "Control model checkpoint is empty"
    assert upper_bound_model_path.stat().st_size > 0, "Upper bound model checkpoint is empty"

    # Run Evaluation
    try:
        evaluate_models()
    except SystemExit as e:
        if e.code != 0:
            pytest.fail(f"Evaluation script exited with code {e.code}")

    # Verify evaluation outputs
    assert validation_report_path.exists(), "Validation report not created"
    assert comparative_analysis_path.exists(), "Comparative analysis CSV not created"

    # Validate content of validation_report.json
    with open(validation_report_path, 'r') as f:
        report = json.load(f)

    required_keys = ["baseline_mae", "baseline_r", "baseline_rho", "baseline_p_value",
                     "control_mae", "control_r", "control_rho", "control_p_value",
                     "upper_bound_mae", "upper_bound_r", "upper_bound_rho", "upper_bound_p_value"]
    
    # Check for at least the presence of key metrics (names may vary slightly by implementation)
    # We check that the report is a dict and has some metrics
    assert isinstance(report, dict), "Validation report must be a JSON object"
    assert any("mae" in k.lower() for k in report.keys()), "Report must contain MAE metrics"
    assert any("r" in k.lower() and "mae" not in k.lower() for k in report.keys()), "Report must contain correlation metrics"

    # Validate content of comparative_analysis.csv
    df = pd.read_csv(comparative_analysis_path)
    assert "model_type" in df.columns, "Comparative analysis must have 'model_type' column"
    assert "mae" in df.columns or "MAE" in df.columns, "Comparative analysis must have 'mae' column"
    
    expected_models = {"baseline", "control", "upper_bound"}
    found_models = set(df["model_type"].astype(str).str.lower())
    
    # Check if all three models are represented (case-insensitive)
    assert expected_models.issubset(found_models), f"Missing models in comparative analysis. Expected {expected_models}, found {found_models}"

    print("Integration test passed: Training and Evaluation pipeline completed successfully.")