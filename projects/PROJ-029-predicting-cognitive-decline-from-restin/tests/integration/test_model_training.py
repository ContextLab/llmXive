"""Integration test ensuring the end‑to‑end training pipeline works."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code import _04_train_model as train_mod
from code.utils.io import ensure_dir, save_csv, save_json
import numpy as np
import pandas as pd

@pytest.fixture
def minimal_dataset(tmp_path):
    """Create minimal but realistic CSV files for the pipeline."""
    # Ensure directories exist
    data_processed = tmp_path / "data" / "processed"
    data_processed.mkdir(parents=True, exist_ok=True)

    # Graph metrics (10 subjects, 5 features)
    # Using the exact schema expected by the training script: subject_id + metric columns
    graph_df = pd.DataFrame({
        "subject_id": [f"sub-{i:03d}" for i in range(1, 11)],
        "node_degree": np.random.uniform(0.1, 0.9, 10),
        "global_efficiency": np.random.uniform(0.1, 0.8, 10),
        "clustering_coeff": np.random.uniform(0.1, 0.7, 10),
        "path_length": np.random.uniform(1.0, 5.0, 10),
        "local_efficiency": np.random.uniform(0.1, 0.8, 10)
    })
    graph_df.to_csv(data_processed / "graph_metrics.csv", index=False)

    # Eligible subjects with MMSE scores
    eligible_df = pd.DataFrame({
        "subject_id": [f"sub-{i:03d}" for i in range(1, 11)],
        "mmse_baseline": [30, 29, 28, 27, 30, 29, 28, 27, 30, 29],
        "mmse_followup": [27, 28, 25, 27, 26, 29, 24, 27, 29, 28]
    })
    eligible_df.to_csv(data_processed / "eligible_subjects.csv", index=False)

    return tmp_path

def test_end_to_end_training(minimal_dataset):
    """Run the full training script against the minimal dataset."""
    # Patch the Path resolution in the training module to use our temp directory
    # We need to patch the base path that the module constructs relative to
    original_main = train_mod.main

    def patched_main():
        # Override the base data path inside the function
        # The module likely uses a global or constructs paths; we patch the base
        # Since we can't easily inject a parameter, we patch the Path class or specific file access
        # A cleaner way for this specific test is to patch the specific file paths used
        # But since the module is complex, let's patch the base directory resolution
        # We'll assume the module uses `Path("data/processed/...")` relative to cwd
        # So we change cwd to our temp dir's parent
        original_cwd = os.getcwd()
        try:
            os.chdir(minimal_dataset)
            # Ensure the paths are relative to this new cwd
            result = original_main()
            return result
        finally:
            os.chdir(original_cwd)

    # Execute main; expect a clean exit
    # We need to handle the case where the script might fail due to data size or other constraints
    # but for a minimal test, we expect it to run through the logic
    try:
        # Run the script logic directly but with patched paths
        # We will simulate the environment by changing cwd
        original_cwd = os.getcwd()
        os.chdir(minimal_dataset)
        try:
            # Call the main function
            # If it returns an exit code, check it
            exit_code = train_mod.main()
            assert exit_code == 0, f"Training script exited with code {exit_code}"
        except Exception as e:
            # If it fails due to data issues (e.g., too few subjects), we might need to adjust
            # But for this test, we assume the minimal data is sufficient for the logic
            # to execute, even if the model doesn't train perfectly
            # If the error is about file not found, our patching failed
            raise e
        finally:
            os.chdir(original_cwd)

        # Check artefacts
        data_processed = minimal_dataset / "data" / "processed"
        model_file = data_processed / "model.pkl"
        report_file = data_processed / "performance_report.json"
        cv_results_file = data_processed / "cv_results.json"
        model_params_file = data_processed / "model_params.json"

        assert model_file.is_file(), f"model.pkl not found at {model_file}"
        assert report_file.is_file(), f"performance_report.json not found at {report_file}"
        assert cv_results_file.is_file(), f"cv_results.json not found at {cv_results_file}"
        assert model_params_file.is_file(), f"model_params.json not found at {model_params_file}"

        # Validate JSON structure
        with report_file.open() as f:
            data = json.load(f)
        assert "mean_roc_auc" in data, f"mean_roc_auc missing from {data}"
        assert "best_params" in data, f"best_params missing from {data}"

        # Validate cv_results structure
        with cv_results_file.open() as f:
            cv_data = json.load(f)
        assert isinstance(cv_data, list) or (isinstance(cv_data, dict) and "results" in cv_data), \
            f"cv_results.json has unexpected structure: {cv_data}"

    finally:
        os.chdir(original_cwd)