"""
Contract test suite to validate data integrity against YAML schemas.

This module ensures that data models (PlanetRecord, GapResult) and their
serialized forms strictly adhere to the defined JSON/YAML schemas.
It serves as a guardrail for data integrity across the pipeline.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.planet_record import PlanetRecord
from models.gap_result import GapResult
from utils.logging_config import setup_logging, get_logger

# Configure logger
logger = get_logger("tests.contract.test_schemas")


# ---------------------------------------------------------------------
# Schema Definitions (Mirroring contracts/*.yaml structure)
# ---------------------------------------------------------------------

PLANET_RECORD_SCHEMA = {
    "type": "object",
    "required": [
        "kepler_id",
        "planet_name",
        "radius_planet",
        "radius_planet_unc",
        "period",
        "period_unc",
        "teff",
        "teff_unc",
        "r_star",
        "r_star_unc",
    ],
    "properties": {
        "kepler_id": {"type": "integer"},
        "planet_name": {"type": "string"},
        "radius_planet": {"type": "number"},
        "radius_planet_unc": {"type": "number"},
        "period": {"type": "number"},
        "period_unc": {"type": "number"},
        "teff": {"type": "number"},
        "teff_unc": {"type": "number"},
        "r_star": {"type": "number"},
        "r_star_unc": {"type": "number"},
        "source": {"type": "string"},
        "processed_at": {"type": "string"},
    },
}

GAP_RESULT_SCHEMA = {
    "type": "object",
    "required": [
        "period_bin_center",
        "gap_location",
        "gap_uncertainty",
        "n_planets",
        "model_type",
        "status",
    ],
    "properties": {
        "period_bin_center": {"type": "number"},
        "gap_location": {"type": "number"},
        "gap_uncertainty": {"type": "number"},
        "n_planets": {"type": "integer"},
        "model_type": {"type": "string"},
        "status": {"type": "string"},
        "bootstrap_ci_lower": {"type": ["number", "null"]},
        "bootstrap_ci_upper": {"type": ["number", "null"]},
        "fitted_at": {"type": "string"},
    },
}

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate a dictionary against a JSON-schema-like structure.
    Raises ValueError if validation fails.
    """
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict, got {type(data)}")

    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Check types
    properties = schema.get("properties", {})
    for key, value in data.items():
        if key in properties:
            expected_type = properties[key].get("type")
            if expected_type == "integer":
                if not isinstance(value, int):
                    raise ValueError(f"Field '{key}' must be integer, got {type(value)}")
            elif expected_type == "number":
                if not isinstance(value, (int, float)):
                    raise ValueError(f"Field '{key}' must be number, got {type(value)}")
            elif expected_type == "string":
                if not isinstance(value, str):
                    raise ValueError(f"Field '{key}' must be string, got {type(value)}")
            elif expected_type == "null":
                if value is not None:
                    raise ValueError(f"Field '{key}' must be null, got {type(value)}")
            # Allow 'number' to accept int or float, 'null' to accept None
            # Handle unions like ["number", "null"]
            elif isinstance(expected_type, list):
                valid = False
                for t in expected_type:
                    if t == "number" and isinstance(value, (int, float)):
                        valid = True
                    elif t == "integer" and isinstance(value, int):
                        valid = True
                    elif t == "string" and isinstance(value, str):
                        valid = True
                    elif t == "null" and value is None:
                        valid = True
                if not valid:
                    raise ValueError(f"Field '{key}' must be one of {expected_type}, got {type(value)}")


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture
def valid_planet_record() -> PlanetRecord:
    """Create a valid PlanetRecord instance."""
    return PlanetRecord(
        kepler_id=12345,
        planet_name="Kepler-123.01",
        radius_planet=2.5,
        radius_planet_unc=0.1,
        period=10.5,
        period_unc=0.001,
        teff=5500.0,
        teff_unc=100.0,
        r_star=1.1,
        r_star_unc=0.05,
        source="DR25",
        processed_at="2023-10-27T10:00:00Z",
    )

@pytest.fixture
def valid_gap_result() -> GapResult:
    """Create a valid GapResult instance."""
    return GapResult(
        period_bin_center=10.5,
        gap_location=1.8,
        gap_uncertainty=0.05,
        n_planets=45,
        model_type="GMM",
        status="resolved",
        bootstrap_ci_lower=1.75,
        bootstrap_ci_upper=1.85,
        fitted_at="2023-10-27T11:00:00Z",
    )

# ---------------------------------------------------------------------
# Tests: Serialization and Schema Validation
# ---------------------------------------------------------------------

class TestPlanetRecordSchema:
    def test_to_dict_contains_required_fields(self, valid_planet_record):
        data = valid_planet_record.to_dict()
        validate_against_schema(data, PLANET_RECORD_SCHEMA)

    def test_to_json_validates_schema(self, valid_planet_record):
        json_str = valid_planet_record.to_json()
        data = json.loads(json_str)
        validate_against_schema(data, PLANET_RECORD_SCHEMA)

    def test_missing_required_field_raises(self):
        """Ensure that a record missing a required field fails validation."""
        # Manually construct a dict missing a field to test validator
        incomplete = {
            "kepler_id": 123,
            "planet_name": "Test",
            # missing radius_planet
        }
        with pytest.raises(ValueError, match="Missing required field"):
            validate_against_schema(incomplete, PLANET_RECORD_SCHEMA)

    def test_wrong_type_raises(self):
        """Ensure that a record with wrong type fails validation."""
        invalid = {
            "kepler_id": "not_an_int", # Should be int
            "planet_name": "Test",
            "radius_planet": 2.0,
            "radius_planet_unc": 0.1,
            "period": 10.0,
            "period_unc": 0.001,
            "teff": 5500.0,
            "teff_unc": 100.0,
            "r_star": 1.1,
            "r_star_unc": 0.05,
        }
        with pytest.raises(ValueError, match="must be integer"):
            validate_against_schema(invalid, PLANET_RECORD_SCHEMA)


class TestGapResultSchema:
    def test_to_dict_contains_required_fields(self, valid_gap_result):
        data = valid_gap_result.to_dict()
        validate_against_schema(data, GAP_RESULT_SCHEMA)

    def test_to_json_validates_schema(self, valid_gap_result):
        json_str = valid_gap_result.to_json()
        data = json.loads(json_str)
        validate_against_schema(data, GAP_RESULT_SCHEMA)

    def test_null_fields_handled_correctly(self):
        """Test that null fields (like bootstrap CI when unresolved) pass validation."""
        result = GapResult(
            period_bin_center=10.5,
            gap_location=1.8,
            gap_uncertainty=0.05,
            n_planets=15, # Low count, potentially unresolved
            model_type="GMM",
            status="unresolved",
            bootstrap_ci_lower=None,
            bootstrap_ci_upper=None,
            fitted_at="2023-10-27T11:00:00Z",
        )
        data = result.to_dict()
        validate_against_schema(data, GAP_RESULT_SCHEMA)

    def test_missing_required_field_raises(self):
        incomplete = {
            "period_bin_center": 10.5,
            "gap_location": 1.8,
            # missing gap_uncertainty
            "n_planets": 45,
            "model_type": "GMM",
            "status": "resolved",
        }
        with pytest.raises(ValueError, match="Missing required field"):
            validate_against_schema(incomplete, GAP_RESULT_SCHEMA)


class TestFileIOContract:
    """Tests that ensure file I/O operations respect the schema."""

    def test_planet_record_roundtrip(self, valid_planet_record, tmp_path):
        """Test writing to JSON and reading back."""
        output_file = tmp_path / "planet.json"
        valid_planet_record.to_json(output_file)

        # Read back
        with open(output_file, "r") as f:
            data = json.load(f)

        # Validate
        validate_against_schema(data, PLANET_RECORD_SCHEMA)

        # Verify data integrity
        assert data["kepler_id"] == valid_planet_record.kepler_id
        assert data["planet_name"] == valid_planet_record.planet_name

    def test_gap_result_roundtrip(self, valid_gap_result, tmp_path):
        """Test writing to JSON and reading back."""
        output_file = tmp_path / "gap.json"
        valid_gap_result.to_json(output_file)

        with open(output_file, "r") as f:
            data = json.load(f)

        validate_against_schema(data, GAP_RESULT_SCHEMA)

        assert data["period_bin_center"] == valid_gap_result.period_bin_center
        assert data["status"] == valid_gap_result.status

    def test_yaml_schema_validation(self, valid_planet_record, tmp_path):
        """Test that YAML output also adheres to schema."""
        output_file = tmp_path / "planet.yaml"
        
        # Serialize to YAML
        data = valid_planet_record.to_dict()
        with open(output_file, "w") as f:
            yaml.dump(data, f)

        # Read back
        with open(output_file, "r") as f:
            loaded_data = yaml.safe_load(f)

        # Validate
        validate_against_schema(loaded_data, PLANET_RECORD_SCHEMA)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
