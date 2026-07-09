"""
Contract test for data schema validation (T009).

Validates earthquake.schema.yaml and pressure-anomaly.schema.yaml against sample data.
Asserts failure if required fields (magnitude, depth, lat, lon, timestamp) are missing.

Dependency: T008 (Schema definitions)
"""
import os
import sys
import json
import yaml
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

# Constants for validation
REQUIRED_EARTHQUAKE_FIELDS = ["magnitude", "depth", "lat", "lon", "timestamp"]
REQUIRED_PRESSURE_FIELDS = ["timestamp", "pressure_anomaly", "lat", "lon", "event_id"]

# Sample valid data
VALID_EARTHQUAKE_DATA = {
    "magnitude": 5.2,
    "depth": 15.4,
    "lat": 61.2,
    "lon": -149.9,
    "timestamp": "2018-01-01T12:00:00Z",
    "event_id": "us70001234"
}

INVALID_EARTHQUAKE_DATA_MISSING_FIELDS = {
    "magnitude": 5.2,
    # Missing: depth, lat, lon, timestamp
    "event_id": "us70001234"
}

VALID_PRESSURE_DATA = {
    "timestamp": "2018-01-01T12:00:00Z",
    "pressure_anomaly": -2.5,
    "lat": 61.2,
    "lon": -149.9,
    "event_id": "us70001234"
}

INVALID_PRESSURE_DATA_MISSING_FIELDS = {
    "timestamp": "2018-01-01T12:00:00Z",
    # Missing: pressure_anomaly, lat, lon, event_id
}

def load_schema(schema_name: str) -> dict:
    """Load a YAML schema from the contracts directory."""
    contracts_path = project_root / "contracts"
    schema_file = contracts_path / f"{schema_name}.yaml"
    
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    
    with open(schema_file, 'r') as f:
        return yaml.safe_load(f)

def validate_record_against_schema(record: dict, schema: dict, schema_name: str) -> bool:
    """
    Validate a record against a schema definition.
    Returns True if valid, False if missing required fields.
    """
    required_fields = schema.get("required", [])
    missing_fields = [field for field in required_fields if field not in record]
    
    if missing_fields:
        logger.warning(f"Validation failed for {schema_name}: Missing fields {missing_fields}")
        return False
    
    return True

class TestDataSchemaValidation:
    """Contract tests for data schema validation."""

    def test_load_earthquake_schema(self):
        """Test that earthquake schema can be loaded."""
        schema = load_schema("earthquake")
        assert schema is not None
        assert "required" in schema
        logger.info("Earthquake schema loaded successfully")

    def test_load_pressure_anomaly_schema(self):
        """Test that pressure-anomaly schema can be loaded."""
        schema = load_schema("pressure-anomaly")
        assert schema is not None
        assert "required" in schema
        logger.info("Pressure-anomaly schema loaded successfully")

    def test_earthquake_schema_validates_valid_data(self):
        """Test that valid earthquake data passes validation."""
        schema = load_schema("earthquake")
        is_valid = validate_record_against_schema(
            VALID_EARTHQUAKE_DATA, schema, "earthquake"
        )
        assert is_valid, "Valid earthquake data should pass validation"
        logger.info("Valid earthquake data passed schema validation")

    def test_earthquake_schema_rejects_missing_fields(self):
        """Test that earthquake data with missing required fields fails validation."""
        schema = load_schema("earthquake")
        is_valid = validate_record_against_schema(
            INVALID_EARTHQUAKE_DATA_MISSING_FIELDS, schema, "earthquake"
        )
        assert not is_valid, "Earthquake data with missing fields should fail validation"
        logger.info("Invalid earthquake data correctly rejected by schema")

    def test_pressure_anomaly_schema_validates_valid_data(self):
        """Test that valid pressure data passes validation."""
        schema = load_schema("pressure-anomaly")
        is_valid = validate_record_against_schema(
            VALID_PRESSURE_DATA, schema, "pressure-anomaly"
        )
        assert is_valid, "Valid pressure data should pass validation"
        logger.info("Valid pressure data passed schema validation")

    def test_pressure_anomaly_schema_rejects_missing_fields(self):
        """Test that pressure data with missing required fields fails validation."""
        schema = load_schema("pressure-anomaly")
        is_valid = validate_record_against_schema(
            INVALID_PRESSURE_DATA_MISSING_FIELDS, schema, "pressure-anomaly"
        )
        assert not is_valid, "Pressure data with missing fields should fail validation"
        logger.info("Invalid pressure data correctly rejected by schema")

    def test_required_fields_match_spec(self):
        """Verify that schema required fields match the specification."""
        earthquake_schema = load_schema("earthquake")
        pressure_schema = load_schema("pressure-anomaly")
        
        earthquake_required = set(earthquake_schema.get("required", []))
        expected_earthquake = set(REQUIRED_EARTHQUAKE_FIELDS)
        
        pressure_required = set(pressure_schema.get("required", []))
        expected_pressure = set(REQUIRED_PRESSURE_FIELDS)
        
        assert expected_earthquake.issubset(earthquake_required), \
            f"Earthquake schema missing required fields: {expected_earthquake - earthquake_required}"
        assert expected_pressure.issubset(pressure_required), \
            f"Pressure schema missing required fields: {expected_pressure - pressure_required}"
        
        logger.info("Schema required fields match specification")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])