import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# Import the implementation under test
# Note: The project structure uses 'code' as the root in the provided API surface,
# but the task description and tasks.md refer to 'src/'.
# Based on the provided API surface list, we import from 'code/src'.
# However, to match the standard project layout described in tasks.md (src/),
# and assuming the 'code/' prefix in the API surface is an artifact of the environment,
# we will attempt to import from 'src' first. If the environment expects 'code/src',
# the import path would need adjustment. Given the explicit list:
# "code/src/interpret/partial_dependence.py" -> import as ...
# We will assume the project root is the current directory and the module is 'src'.
# If the runner expects 'code', we can adjust.
# Let's assume the standard 'src' layout as per tasks.md description.
# If the API surface provided 'code/src', it implies the root is 'code'.
# We will use 'src' relative to the project root as defined in tasks.md.
# To be safe and match the provided API surface exactly:
try:
    from src.interpret.partial_dependence import generate_partial_dependence_plots
    from src.interpret.feature_importance import export_feature_importance
except ImportError:
    # Fallback if the project root is actually 'code' as per the API surface hints
    from code.src.interpret.partial_dependence import generate_partial_dependence_plots
    from code.src.interpret.feature_importance import export_feature_importance


@pytest.fixture
def sample_model():
    """Create a simple trained Random Forest model for testing."""
    # Generate synthetic training data (for the model training only)
    # This is NOT the dataset used for the project's real analysis,
    # but a local fixture to ensure the plotting functions have a model to work with.
    np.random.seed(42)
    X = np.random.rand(100, 5)
    y = X[:, 0] + X[:, 1] * 2 + np.random.normal(0, 0.1, 100)
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X, y)
    return model


@pytest.fixture
def sample_feature_names():
    """Return the expected feature names based on the schema."""
    return [
        "milling_speed",
        "milling_time",
        "ball_to_powder_ratio",
        "youngs_modulus",
        "density",
        "process_duration"
    ]


@pytest.fixture
def sample_target():
    """Return the target variable name."""
    return "d50"


class TestPartialDependencePlots:
    """Unit tests for partial dependence plot generation."""

    def test_plots_generated_successfully(
        self, sample_model, sample_feature_names, sample_target, tmp_path
    ):
        """Test that partial dependence plots are generated without error."""
        output_dir = tmp_path / "plots"
        output_dir.mkdir()

        # Call the function
        generate_partial_dependence_plots(
            model=sample_model,
            feature_names=sample_feature_names,
            target_feature=sample_target,
            output_dir=str(output_dir),
            features_to_plot=["milling_speed", "milling_time", "ball_to_powder_ratio"]
        )

        # Verify files exist
        expected_files = [
            "partial_dependence_milling_speed.png",
            "partial_dependence_milling_time.png",
            "partial_dependence_ball_to_powder_ratio.png"
        ]

        for filename in expected_files:
            file_path = output_dir / filename
            assert file_path.exists(), f"Expected plot file {filename} was not created."
            assert file_path.stat().st_size > 0, f"Plot file {filename} is empty."

    def test_plot_size_constraint(self, sample_model, sample_feature_names, sample_target, tmp_path):
        """Test that generated plots do not exceed the 10MB limit."""
        output_dir = tmp_path / "plots"
        output_dir.mkdir()

        generate_partial_dependence_plots(
            model=sample_model,
            feature_names=sample_feature_names,
            target_feature=sample_target,
            output_dir=str(output_dir),
            features_to_plot=["milling_speed"]
        )

        plot_file = output_dir / "partial_dependence_milling_speed.png"
        file_size_mb = plot_file.stat().st_size / (1024 * 1024)
        assert file_size_mb <= 10.0, f"Plot size {file_size_mb}MB exceeds 10MB limit."

    def test_invalid_feature_name_handling(self, sample_model, sample_feature_names, sample_target, tmp_path):
        """Test handling of feature names not present in the model."""
        output_dir = tmp_path / "plots"
        output_dir.mkdir()

        # Try to plot a feature that doesn't exist in the model's training data
        # The function should either skip it or raise a clear error.
        # Assuming it skips or handles gracefully.
        with patch('src.interpret.partial_dependence.logging') as mock_log:
            generate_partial_dependence_plots(
                model=sample_model,
                feature_names=sample_feature_names,
                target_feature=sample_target,
                output_dir=str(output_dir),
                features_to_plot=["non_existent_feature"]
            )
            # If it logs a warning or error, that's acceptable behavior
            # If it raises, that's also acceptable if documented.
            # We just verify it doesn't crash the test suite unexpectedly.


class TestFeatureImportanceExport:
    """Unit tests for feature importance export."""

    def test_json_export_success(self, sample_model, sample_feature_names, tmp_path):
        """Test that feature importance is exported to JSON correctly."""
        output_file = tmp_path / "feature_importance.json"

        export_feature_importance(
            model=sample_model,
            feature_names=sample_feature_names,
            output_path=str(output_file)
        )

        assert output_file.exists(), "Feature importance JSON file was not created."
        assert output_file.stat().st_size > 0, "Feature importance JSON file is empty."

        # Verify JSON content structure
        import json
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert "features" in data, "JSON missing 'features' key."
        assert "model_type" in data, "JSON missing 'model_type' key."
        assert len(data["features"]) == len(sample_feature_names), "Feature count mismatch."

        # Check that features are sorted by importance (descending)
        importances = [f["importance"] for f in data["features"]]
        assert importances == sorted(importances, reverse=True), "Features not sorted by importance."

    def test_json_schema_compliance(self, sample_model, sample_feature_names, tmp_path):
        """Test that the exported JSON matches the expected schema."""
        output_file = tmp_path / "feature_importance.json"

        export_feature_importance(
            model=sample_model,
            feature_names=sample_feature_names,
            output_path=str(output_file)
        )

        import json
        with open(output_file, 'r') as f:
            data = json.load(f)

        required_keys = ["feature", "importance", "rank"]
        for item in data["features"]:
            for key in required_keys:
                assert key in item, f"Missing key '{key}' in feature item."

        assert data["model_type"] in ["RandomForest", "GaussianProcessRegressor", "LinearRegression"]