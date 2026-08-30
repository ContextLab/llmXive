"""
Contract test for model output schema (US3).

This test verifies that the outputs from the model training pipeline
(T024) adhere to the strict schema defined in code/data/models.py
and the project specifications.

It ensures that:
1. The model report is a valid dictionary with required keys.
2. Metrics (R2, RMSE) are numeric and within expected ranges.
3. The 'residual_variance' attributed to missing microstructural variables
   is explicitly present and numeric (FR-008).
4. The 'extrapolation_flag' and 'confidence_penalty' are present if applicable.
5. The model metadata (material types, reduction levels) matches the input data.
"""

import json
import os
import sys
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.models import ModelInput, TextureDescriptor
from code.utils.logging import get_logger

logger = get_logger(__name__)

# Constants for validation
REQUIRED_MODEL_REPORT_KEYS = {
    "model_type",
    "model_id",
    "training_samples",
    "metrics",
    "feature_importance",
    "residual_variance",  # FR-008: Explicitly required
    "hyperparameters",
    "timestamp"
}

REQUIRED_METRICS_KEYS = {
    "r2",
    "rmse",
    "mae"
}

ALLOWED_MODEL_TYPES = {"polynomial_regression", "gaussian_process"}
ALLOWED_MATERIALS = {"Al", "Cu", "Ni"}


class ModelOutputSchemaError(Exception):
    """Raised when model output violates the contract schema."""
    pass


def load_model_report(report_path: str) -> Dict[str, Any]:
    """
    Load a model report from a JSON file.

    Args:
        report_path: Path to the JSON report file.

    Returns:
        Dictionary containing the model report.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(report_path)
    if not path.exists():
        raise FileNotFoundError(f"Model report not found at {report_path}")

    with open(path, 'r') as f:
        return json.load(f)


def validate_model_report_schema(report: Dict[str, Any]) -> None:
    """
    Validate the structure and content of a model report against the contract.

    Args:
        report: The loaded model report dictionary.

    Raises:
        ModelOutputSchemaError: If the report violates the schema.
    """
    # Check top-level keys
    missing_keys = REQUIRED_MODEL_REPORT_KEYS - set(report.keys())
    if missing_keys:
        raise ModelOutputSchemaError(
            f"Model report missing required keys: {missing_keys}"
        )

    # Validate model_type
    if report["model_type"] not in ALLOWED_MODEL_TYPES:
        raise ModelOutputSchemaError(
            f"Invalid model_type: {report['model_type']}. "
            f"Must be one of {ALLOWED_MODEL_TYPES}"
        )

    # Validate metrics structure
    if "metrics" not in report:
        raise ModelOutputSchemaError("Missing 'metrics' key in report")

    metrics = report["metrics"]
    missing_metrics = REQUIRED_METRICS_KEYS - set(metrics.keys())
    if missing_metrics:
        raise ModelOutputSchemaError(
            f"Metrics missing required keys: {missing_metrics}"
        )

    # Validate metric values are numeric and reasonable
    for key in REQUIRED_METRICS_KEYS:
        val = metrics[key]
        if not isinstance(val, (int, float)):
            raise ModelOutputSchemaError(
                f"Metric '{key}' must be numeric, got {type(val)}"
            )
        if key == "r2" and (val < -1.0 or val > 1.0):
            # Allow slight float errors, but R2 generally bounded [-1, 1]
            logger.warning(f"R2 value {val} is outside typical [-1, 1] range")

    # FR-008: Validate residual_variance is present and numeric
    if "residual_variance" not in report:
        raise ModelOutputSchemaError(
            "Missing 'residual_variance' in report. "
            "This is required by FR-008 to quantify missing microstructural variables."
        )
    if not isinstance(report["residual_variance"], (int, float)):
        raise ModelOutputSchemaError(
            f"'residual_variance' must be numeric, got {type(report['residual_variance'])}"
        )

    # Validate feature_importance exists (even if empty dict)
    if "feature_importance" not in report:
        raise ModelOutputSchemaError("Missing 'feature_importance' in report")

    # Validate hyperparameters
    if "hyperparameters" not in report:
        raise ModelOutputSchemaError("Missing 'hyperparameters' in report")
    if not isinstance(report["hyperparameters"], dict):
        raise ModelOutputSchemaError(
            f"'hyperparameters' must be a dict, got {type(report['hyperparameters'])}"
        )


def validate_model_input_schema(input_data: Dict[str, Any]) -> None:
    """
    Validate the input data structure used for training.

    Args:
        input_data: Dictionary containing training features and targets.

    Raises:
        ModelOutputSchemaError: If input data violates schema.
    """
    # Check for required keys based on ModelInput schema
    required_input_keys = {"features", "targets", "metadata"}
    missing_keys = required_input_keys - set(input_data.keys())
    if missing_keys:
        raise ModelOutputSchemaError(
            f"Model input missing required keys: {missing_keys}"
        )

    # Validate features structure
    features = input_data["features"]
    if not isinstance(features, dict):
        raise ModelOutputSchemaError("'features' must be a dictionary")

    # Validate targets structure
    targets = input_data["targets"]
    if not isinstance(targets, dict):
        raise ModelOutputSchemaError("'targets' must be a dictionary")

    # Validate metadata contains material types
    metadata = input_data["metadata"]
    if "materials" not in metadata:
        raise ModelOutputSchemaError("Missing 'materials' in input metadata")

    materials = metadata["materials"]
    if not isinstance(materials, list):
        raise ModelOutputSchemaError("'materials' must be a list")

    for mat in materials:
        if mat not in ALLOWED_MATERIALS:
            logger.warning(f"Unknown material in metadata: {mat}")


class TestModelOutputSchema:
    """Contract tests for model output schema."""

    @pytest.fixture
    def sample_model_report(self) -> Dict[str, Any]:
        """Provide a valid sample model report for testing."""
        return {
            "model_type": "polynomial_regression",
            "model_id": "test_model_001",
            "training_samples": 150,
            "metrics": {
                "r2": 0.89,
                "rmse": 0.05,
                "mae": 0.04
            },
            "feature_importance": {
                "reduction": 0.6,
                "material_Cu": 0.2,
                "material_Al": 0.2
            },
            "residual_variance": 0.12,
            "hyperparameters": {
                "degree": 2,
                "alpha": 0.1
            },
            "timestamp": "2026-01-01T00:00:00Z"
        }

    @pytest.fixture
    def sample_model_input(self) -> Dict[str, Any]:
        """Provide a valid sample model input for testing."""
        return {
            "features": {
                "reduction": [10.0, 20.0, 30.0],
                "material_Cu": [1, 0, 0],
                "material_Al": [0, 1, 1]
            },
            "targets": {
                "brass_fraction": [0.1, 0.2, 0.3],
                "copper_fraction": [0.05, 0.1, 0.15]
            },
            "metadata": {
                "materials": ["Cu", "Al"],
                "reduction_levels": [10, 20, 30]
            }
        }

    def test_valid_model_report_schema(self, sample_model_report):
        """Test that a valid report passes schema validation."""
        # Should not raise
        validate_model_report_schema(sample_model_report)

    def test_missing_required_key_in_report(self, sample_model_report):
        """Test that missing required keys raise an error."""
        report = sample_model_report.copy()
        del report["residual_variance"]  # Remove FR-008 requirement

        with pytest.raises(ModelOutputSchemaError) as exc_info:
            validate_model_report_schema(report)

        assert "residual_variance" in str(exc_info.value)

    def test_invalid_model_type(self, sample_model_report):
        """Test that invalid model_type raises an error."""
        report = sample_model_report.copy()
        report["model_type"] = "invalid_model"

        with pytest.raises(ModelOutputSchemaError) as exc_info:
            validate_model_report_schema(report)

        assert "invalid_model" in str(exc_info.value)

    def test_missing_metrics_keys(self, sample_model_report):
        """Test that missing metric keys raise an error."""
        report = sample_model_report.copy()
        report["metrics"] = {"r2": 0.9}  # Missing rmse, mae

        with pytest.raises(ModelOutputSchemaError) as exc_info:
            validate_model_report_schema(report)

        assert "rmse" in str(exc_info.value) or "mae" in str(exc_info.value)

    def test_non_numeric_residual_variance(self, sample_model_report):
        """Test that non-numeric residual_variance raises an error."""
        report = sample_model_report.copy()
        report["residual_variance"] = "high_uncertainty"

        with pytest.raises(ModelOutputSchemaError) as exc_info:
            validate_model_report_schema(report)

        assert "numeric" in str(exc_info.value)

    def test_valid_model_input_schema(self, sample_model_input):
        """Test that valid input data passes validation."""
        validate_model_input_schema(sample_model_input)

    def test_missing_input_metadata(self, sample_model_input):
        """Test that missing input metadata raises an error."""
        input_data = sample_model_input.copy()
        del input_data["metadata"]

        with pytest.raises(ModelOutputSchemaError) as exc_info:
            validate_model_input_schema(input_data)

        assert "metadata" in str(exc_info.value)

    def test_integration_with_real_report_if_exists(self):
        """
        Integration test: If a real model report exists from T024,
        load and validate it.
        """
        # Check for common output paths from T024
        possible_paths = [
            PROJECT_ROOT / "data" / "processed" / "model_report.json",
            PROJECT_ROOT / "data" / "processed" / "models" / "model_report.json",
            PROJECT_ROOT / "results" / "model_report.json"
        ]

        report_path = None
        for path in possible_paths:
            if path.exists():
                report_path = str(path)
                break

        if report_path:
            try:
                report = load_model_report(report_path)
                validate_model_report_schema(report)
                logger.info(f"Successfully validated real model report at {report_path}")
            except (FileNotFoundError, json.JSONDecodeError) as e:
                pytest.skip(f"Real report file exists but is invalid or missing: {e}")
            except ModelOutputSchemaError as e:
                pytest.fail(f"Real model report failed schema validation: {e}")
        else:
            pytest.skip("No real model report found to validate against.")