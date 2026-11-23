"""
Contract tests for Model Output Schema (Task T020).

This module validates that the model training and evaluation outputs
conform to the schema defined in `specs/001-assess-ml-predictive-power/contracts/output.schema.yaml`.

It verifies:
1. The structure of the final report (JSON).
2. The presence of required keys (R², RMSE, MAE, model type, hyperparameters).
3. The data types of these values.
4. The schema of the best models directory contents (if artifacts are saved).

These tests are designed to fail if the modeling pipeline changes its output format
without updating the schema or the contract tests.
"""
import json
import os
import pytest
from pathlib import Path
from typing import Any, Dict

import pandas as pd

# Import config to get paths
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
import config


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the output schema YAML file."""
    import yaml
    if not schema_path.exists():
        pytest.fail(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def get_expected_report_path() -> Path:
    """Determine the expected path for the final report."""
    # Based on T034, the report is saved to data/results/final_report.json
    return config.PROJECT_ROOT / "data" / "results" / "final_report.json"


def get_expected_models_dir() -> Path:
    """Determine the expected directory for best models."""
    # Based on T028, models are saved to data/results/best_models/
    return config.PROJECT_ROOT / "data" / "results" / "best_models"


class TestModelOutputSchema:
    """Contract tests for model output artifacts."""

    @pytest.fixture(scope="class")
    def schema(self) -> Dict[str, Any]:
        """Load the output schema once for the class."""
        schema_path = config.PROJECT_ROOT / "specs" / "001-assess-ml-predictive-power" / "contracts" / "output.schema.yaml"
        return load_schema(schema_path)

    @pytest.fixture(scope="class")
    def report_exists(self) -> bool:
        """Check if the report file exists."""
        return get_expected_report_path().exists()

    def test_report_file_exists(self, report_exists):
        """Verify that the final_report.json file exists."""
        assert report_exists, "final_report.json does not exist. Has the evaluation pipeline (T034) been run?"

    def test_report_schema_structure(self, report_exists):
        """Verify the top-level structure of the final report matches the schema."""
        if not report_exists:
            pytest.skip("Report file does not exist.")

        report_path = get_expected_report_path()
        with open(report_path, "r") as f:
            report = json.load(f)

        schema = load_schema(
            config.PROJECT_ROOT / "specs" / "001-assess-ml-predictive-power" / "contracts" / "output.schema.yaml"
        )

        required_keys = schema.get("required", [])
        for key in required_keys:
            assert key in report, f"Missing required key in final_report.json: '{key}'"

    def test_report_metric_types(self, report_exists):
        """Verify that metric values are numeric."""
        if not report_exists:
            pytest.skip("Report file does not exist.")

        report_path = get_expected_report_path()
        with open(report_path, "r") as f:
            report = json.load(f)

        # Check standard regression metrics
        metrics_to_check = ["r2_score", "rmse", "mae"]
        for metric in metrics_to_check:
            if metric in report:
                val = report[metric]
                assert isinstance(val, (int, float)), f"Metric '{metric}' must be numeric, got {type(val)}"

    def test_report_model_details(self, report_exists):
        """Verify that model details are present and structured correctly."""
        if not report_exists:
            pytest.skip("Report file does not exist.")

        report_path = get_expected_report_path()
        with open(report_path, "r") as f:
            report = json.load(f)

        # Check for model specific sections if they exist
        if "best_rf_model" in report:
            rf = report["best_rf_model"]
            assert "hyperparameters" in rf, "Missing 'hyperparameters' in best_rf_model"
            assert isinstance(rf["hyperparameters"], dict), "Hyperparameters must be a dict"

        if "best_svm_model" in report:
            svm = report["best_svm_model"]
            assert "hyperparameters" in svm, "Missing 'hyperparameters' in best_svm_model"
            assert isinstance(svm["hyperparameters"], dict), "Hyperparameters must be a dict"

    def test_split_ratios(self, report_exists):
        """Verify split ratios are present and sum to 1.0 (or close)."""
        if not report_exists:
            pytest.skip("Report file does not exist.")

        report_path = get_expected_report_path()
        with open(report_path, "r") as f:
            report = json.load(f)

        if "split_ratios" in report:
            ratios = report["split_ratios"]
            # Expect train, val, test
            assert "train" in ratios, "Missing 'train' ratio"
            assert "test" in ratios, "Missing 'test' ratio"
            
            total = sum(ratios.values())
            # Allow small floating point error
            assert 0.99 <= total <= 1.01, f"Split ratios must sum to ~1.0, got {total}"

    def test_model_artifacts_directory(self, report_exists):
        """Verify that the best_models directory exists if models were saved."""
        models_dir = get_expected_models_dir()
        # We only assert existence if the report says models were saved
        if report_exists:
            with open(get_expected_report_path(), "r") as f:
                report = json.load(f)
            
            if report.get("models_saved", False):
                assert models_dir.exists(), "best_models directory does not exist, but report indicates models were saved."
                assert any(models_dir.iterdir()), "best_models directory is empty."