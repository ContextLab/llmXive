"""
Contract test for baseline model output schema (T019).

Verifies that the baseline model pipeline produces artifacts with the
required schema, including coefficients, metrics, and metadata,
consuming residuals and collinearity reports as expected.
"""

import os
import json
import pytest
from pathlib import Path

# Import the pipeline function from the correct location based on API surface
# API surface says: code/models/baseline.py -> from models.baseline import run_baseline_pipeline
from models.baseline import run_baseline_pipeline
from config import get_config


@pytest.fixture
def config():
    """Load project configuration."""
    return get_config()


@pytest.fixture
def preprocessed_data_path(config):
    """Return the path to the preprocessed data file."""
    # Assuming preprocessing output is at data/processed/preprocessed_data.csv
    # based on standard pipeline flow described in tasks.md
    return Path(config["paths"]["data_processed"]) / "preprocessed_data.csv"


@pytest.fixture
def collinearity_report_path(config):
    """Return the path to the collinearity report."""
    return Path(config["paths"]["data_artifacts"]) / "collinearity_report.json"


@pytest.fixture
def baseline_artifact_path(config):
    """Return the expected path for the baseline model artifact."""
    return Path(config["paths"]["data_artifacts"]) / "baseline_model.json"


def test_baseline_output_schema_exists(
    config, preprocessed_data_path, collinearity_report_path, baseline_artifact_path
):
    """
    Contract Test: Verify baseline model output schema.

    This test runs the baseline pipeline (which depends on preprocessed data
    and the collinearity report) and asserts that the resulting JSON artifact
    contains the required keys and structure as defined in the project specs.

    Schema Requirements:
    - 'model_type': str
    - 'metrics': dict containing 'r2', 'mae'
    - 'coefficients': dict (main effects + interactions)
    - 'metadata': dict containing 'feature_names'
    - 'collinearity_handling': str (describing how flagged pairs were treated)
    """

    # Ensure the pipeline runs and produces the artifact
    # Note: In a real CI, we assume T020-T024 have run successfully to generate
    # the input files. This test asserts the OUTPUT of T024.
    try:
        run_baseline_pipeline(
            data_path=str(preprocessed_data_path),
            collinearity_report_path=str(collinearity_report_path),
            output_path=str(baseline_artifact_path)
        )
    except FileNotFoundError as e:
        # If input data is missing, this is a dependency failure (T022/T023 not done),
        # but for the contract test of the OUTPUT schema, we assert the file exists
        # after the pipeline attempts to run. If the pipeline fails due to missing
        # inputs, the artifact won't exist, and the test fails (correctly).
        pytest.fail(f"Baseline pipeline failed to produce artifact: {e}")

    assert baseline_artifact_path.exists(), "Baseline model artifact file not found."

    with open(baseline_artifact_path, "r") as f:
        artifact = json.load(f)

    # 1. Verify top-level keys
    required_keys = ["model_type", "metrics", "coefficients", "metadata", "collinearity_handling"]
    for key in required_keys:
        assert key in artifact, f"Missing required key in baseline output: {key}"

    # 2. Verify model_type
    assert isinstance(artifact["model_type"], str), "model_type must be a string"
    assert artifact["model_type"] == "LinearRegression", "model_type must be 'LinearRegression'"

    # 3. Verify metrics schema
    assert isinstance(artifact["metrics"], dict), "metrics must be a dictionary"
    assert "r2" in artifact["metrics"], "metrics missing 'r2'"
    assert "mae" in artifact["metrics"], "metrics missing 'mae'"
    assert isinstance(artifact["metrics"]["r2"], (int, float)), "r2 must be numeric"
    assert isinstance(artifact["metrics"]["mae"], (int, float)), "mae must be numeric"

    # 4. Verify coefficients schema
    assert isinstance(artifact["coefficients"], dict), "coefficients must be a dictionary"
    # Ensure at least one coefficient exists (intercept is usually included)
    assert len(artifact["coefficients"]) > 0, "coefficients dictionary is empty"

    # 5. Verify metadata schema
    assert isinstance(artifact["metadata"], dict), "metadata must be a dictionary"
    assert "feature_names" in artifact["metadata"], "metadata missing 'feature_names'"
    assert isinstance(artifact["metadata"]["feature_names"], list), "feature_names must be a list"

    # 6. Verify collinearity_handling (T025 requirement)
    assert isinstance(artifact["collinearity_handling"], str), "collinearity_handling must be a string"
    # It should contain descriptive framing if collinearity was detected, or a statement of none.
    assert len(artifact["collinearity_handling"]) > 0, "collinearity_handling description is empty"


def test_baseline_output_coefficients_match_features(
    config, preprocessed_data_path, collinearity_report_path, baseline_artifact_path
):
    """
    Contract Test: Verify that reported coefficients correspond to the feature names.
    """
    # Run pipeline first
    try:
        run_baseline_pipeline(
            data_path=str(preprocessed_data_path),
            collinearity_report_path=str(collinearity_report_path),
            output_path=str(baseline_artifact_path)
        )
    except FileNotFoundError:
        pytest.skip("Input data missing (dependency not met)")

    with open(baseline_artifact_path, "r") as f:
        artifact = json.load(f)

    features = artifact["metadata"]["feature_names"]
    coeffs = artifact["coefficients"]

    # Every feature listed in metadata should have a coefficient
    for feature in features:
        assert feature in coeffs, f"Feature '{feature}' in metadata missing from coefficients"

    # Intercept is typically handled separately or as a specific key
    if "intercept" in coeffs or "Intercept" in coeffs:
        pass # Valid
    else:
        # If no intercept key, ensure all features are accounted for
        # (Some implementations might not output intercept in the dict)
        pass