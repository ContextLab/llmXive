"""
Contract test for regression output schema (T026).

This test verifies that the regression analysis output file
`data/results/model_metrics.json` conforms to the expected schema.

Schema Requirements (derived from FR-005, FR-006, SC-003):
- Top-level keys: 'metrics', 'feature_importance', 'model_config'
- 'metrics' must contain: 'r2_score', 'rmse', 'cv_r2_mean', 'cv_r2_std'
- 'r2_score' must be > 0.5 (SC-003)
- 'feature_importance' must be a list of dicts with 'feature' and 'coefficient'
- 'model_config' must contain 'n_folds' and 'random_state'
"""
import pytest
import json
import os
from pathlib import Path
from typing import Dict, Any, List

# Define the expected schema structure
REGRESSION_OUTPUT_SCHEMA = {
    "metrics": {
        "r2_score": float,
        "rmse": float,
        "cv_r2_mean": float,
        "cv_r2_std": float
    },
    "feature_importance": list,  # List of dicts
    "model_config": {
        "n_folds": int,
        "random_state": int,
        "stratified": bool
    }
}

REQUIRED_METRIC_KEYS = ["r2_score", "rmse", "cv_r2_mean", "cv_r2_std"]
REQUIRED_CONFIG_KEYS = ["n_folds", "random_state", "stratified"]
R2_THRESHOLD = 0.5  # SC-003 requirement


class TestRegressionOutputSchema:
    """Contract tests for the regression analysis output schema."""

    @pytest.fixture
    def output_path(self) -> Path:
        """Locate the regression output file."""
        # Check both possible locations based on project structure
        possible_paths = [
            Path("data/results/model_metrics.json"),
            Path("results/model_metrics.json")
        ]
        for p in possible_paths:
            if p.exists():
                return p
        # If not found, return the default expected path (test will fail)
        return Path("data/results/model_metrics.json")

    def test_file_exists(self, output_path: Path):
        """Verify the output file exists."""
        assert output_path.exists(), f"Output file not found: {output_path}"

    def test_loads_valid_json(self, output_path: Path):
        """Verify the file contains valid JSON."""
        try:
            with open(output_path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in output file: {e}")

    def test_schema_structure(self, output_path: Path):
        """Verify the top-level schema structure matches requirements."""
        with open(output_path, 'r') as f:
            data = json.load(f)

        # Check top-level keys
        assert "metrics" in data, "Missing 'metrics' key in output"
        assert "feature_importance" in data, "Missing 'feature_importance' key in output"
        assert "model_config" in data, "Missing 'model_config' key in output"

        # Verify types
        assert isinstance(data["metrics"], dict), "'metrics' must be a dictionary"
        assert isinstance(data["feature_importance"], list), "'feature_importance' must be a list"
        assert isinstance(data["model_config"], dict), "'model_config' must be a dictionary"

    def test_required_metric_fields(self, output_path: Path):
        """Verify all required metric fields are present and correct type."""
        with open(output_path, 'r') as f:
            data = json.load(f)

        metrics = data["metrics"]
        for key in REQUIRED_METRIC_KEYS:
            assert key in metrics, f"Missing required metric: {key}"
            assert isinstance(metrics[key], (int, float)), f"Metric '{key}' must be numeric"

    def test_r2_threshold_compliance(self, output_path: Path):
        """Verify R² > 0.5 as per SC-003."""
        with open(output_path, 'r') as f:
            data = json.load(f)

        r2 = data["metrics"]["r2_score"]
        assert r2 > R2_THRESHOLD, f"R² score ({r2}) does not meet SC-003 threshold (> {R2_THRESHOLD})"

    def test_feature_importance_structure(self, output_path: Path):
        """Verify feature importance list structure."""
        with open(output_path, 'r') as f:
            data = json.load(f)

        features = data["feature_importance"]
        assert len(features) > 0, "Feature importance list cannot be empty"

        for i, item in enumerate(features):
            assert isinstance(item, dict), f"Feature item {i} must be a dictionary"
            assert "feature" in item, f"Feature item {i} missing 'feature' key"
            assert "coefficient" in item, f"Feature item {i} missing 'coefficient' key"
            assert isinstance(item["feature"], str), f"Feature name at index {i} must be string"
            assert isinstance(item["coefficient"], (int, float)), f"Coefficient at index {i} must be numeric"

    def test_model_config_structure(self, output_path: Path):
        """Verify model configuration fields."""
        with open(output_path, 'r') as f:
            data = json.load(f)

        config = data["model_config"]
        for key in REQUIRED_CONFIG_KEYS:
            assert key in config, f"Missing config key: {key}"

        assert isinstance(config["n_folds"], int), "n_folds must be an integer"
        assert isinstance(config["random_state"], int), "random_state must be an integer"
        assert isinstance(config["stratified"], bool), "stratified must be a boolean"

    def test_cv_metrics_reasonable(self, output_path: Path):
        """Verify cross-validation metrics are within reasonable bounds."""
        with open(output_path, 'r') as f:
            data = json.load(f)

        metrics = data["metrics"]
        cv_mean = metrics["cv_r2_mean"]
        cv_std = metrics["cv_r2_std"]

        # R² can be negative, but typically > -1 for valid models
        assert cv_mean > -1.0, f"CV mean R² ({cv_mean}) is unreasonably low"
        assert cv_std >= 0, f"CV std R² ({cv_std}) cannot be negative"
        
        # If mean is high, std should be relatively low
        if cv_mean > 0.5:
            assert cv_std < 0.5, f"High CV std ({cv_std}) relative to mean ({cv_mean}) indicates instability"

    def test_rmse_positive(self, output_path: Path):
        """Verify RMSE is a positive number."""
        with open(output_path, 'r') as f:
            data = json.load(f)

        rmse = data["metrics"]["rmse"]
        assert rmse > 0, f"RMSE must be positive, got {rmse}"