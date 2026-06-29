"""
Contract tests for User Story 2: aDDM Parameter Output Schema.

This module verifies that the aDDM fitting pipeline produces outputs
conforming to the expected schema defined in code/data_models.py (ModelParameters).
"""
import pytest
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_models import ModelParameters, Scenario
from pydantic import ValidationError


class TestParamsOutputSchema:
    """Contract tests ensuring aDDM parameter outputs match the defined schema."""

    @pytest.fixture
    def valid_params_dict(self) -> Dict[str, Any]:
        """Fixture providing a valid dictionary representation of ModelParameters."""
        return {
            "salience_weight": 0.5,
            "drift_rate": 0.1,
            "threshold": 1.0,
            "non_decision_time": 0.2,
            "log_likelihood": -150.5,
            "converged": True,
            "iteration_count": 45,
            "cross_validation_fold": 1
        }

    @pytest.fixture
    def invalid_params_dict_missing_field(self) -> Dict[str, Any]:
        """Fixture providing a dictionary missing a required field."""
        return {
            "salience_weight": 0.5,
            # Missing "drift_rate"
            "threshold": 1.0,
            "non_decision_time": 0.2,
            "log_likelihood": -150.5,
            "converged": True,
            "iteration_count": 45,
            "cross_validation_fold": 1
        }

    @pytest.fixture
    def invalid_params_dict_wrong_type(self) -> Dict[str, Any]:
        """Fixture providing a dictionary with a wrong type for a field."""
        return {
            "salience_weight": "0.5",  # Should be float
            "drift_rate": 0.1,
            "threshold": 1.0,
            "non_decision_time": 0.2,
            "log_likelihood": -150.5,
            "converged": True,
            "iteration_count": 45,
            "cross_validation_fold": 1
        }

    def test_params_output_schema(self, valid_params_dict: Dict[str, Any]):
        """
        Contract test: Verify that the output dictionary from the fitting process
        validates against the ModelParameters Pydantic schema.

        This ensures that any code consuming these parameters (e.g., analysis,
        reporting) can rely on the structure and types defined in data_models.py.
        """
        try:
            params = ModelParameters(**valid_params_dict)
            assert params is not None
            assert isinstance(params.salience_weight, float)
            assert isinstance(params.drift_rate, float)
            assert isinstance(params.threshold, float)
            assert isinstance(params.converged, bool)
        except ValidationError as e:
            pytest.fail(f"Valid params dictionary failed schema validation: {e}")

    def test_params_schema_rejects_missing_fields(self, invalid_params_dict_missing_field: Dict[str, Any]):
        """
        Contract test: Verify that the schema rejects dictionaries missing required fields.
        """
        with pytest.raises(ValidationError):
            ModelParameters(**invalid_params_dict_missing_field)

    def test_params_schema_rejects_wrong_types(self, invalid_params_dict_wrong_type: Dict[str, Any]):
        """
        Contract test: Verify that the schema rejects dictionaries with incorrect types.
        """
        with pytest.raises(ValidationError):
            ModelParameters(**invalid_params_dict_wrong_type)

    def test_params_schema_serialization(self, valid_params_dict: Dict[str, Any]):
        """
        Contract test: Verify that ModelParameters can be serialized to JSON
        and deserialized back without loss of structural integrity.
        """
        # Create instance
        params = ModelParameters(**valid_params_dict)

        # Serialize to JSON
        json_str = params.model_dump_json()
        parsed_dict = json.loads(json_str)

        # Verify keys are preserved
        assert set(parsed_dict.keys()) == set(valid_params_dict.keys())

        # Verify types in JSON (numbers remain numbers)
        assert isinstance(parsed_dict["salience_weight"], (int, float))
        assert isinstance(parsed_dict["converged"], bool)

    def test_params_schema_validation_ranges(self):
        """
        Contract test: Verify that the schema enforces logical ranges where defined
        (e.g., salience_weight between 0 and 1).
        """
        # Valid range
        valid_range = {
            "salience_weight": 0.0,
            "drift_rate": 0.1,
            "threshold": 1.0,
            "non_decision_time": 0.2,
            "log_likelihood": -150.5,
            "converged": True,
            "iteration_count": 45,
            "cross_validation_fold": 1
        }
        try:
            ModelParameters(**valid_range)
        except ValidationError:
            pytest.fail("Valid range (0.0) failed validation")

        # Invalid range (negative salience weight)
        invalid_range = {
            "salience_weight": -0.1,
            "drift_rate": 0.1,
            "threshold": 1.0,
            "non_decision_time": 0.2,
            "log_likelihood": -150.5,
            "converged": True,
            "iteration_count": 45,
            "cross_validation_fold": 1
        }
        with pytest.raises(ValidationError):
            ModelParameters(**invalid_range)

        # Invalid range (salience > 1)
        invalid_range_high = {
            "salience_weight": 1.1,
            "drift_rate": 0.1,
            "threshold": 1.0,
            "non_decision_time": 0.2,
            "log_likelihood": -150.5,
            "converged": True,
            "iteration_count": 45,
            "cross_validation_fold": 1
        }
        with pytest.raises(ValidationError):
            ModelParameters(**invalid_range_high)