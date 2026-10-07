import os
import sys
import pytest
import yaml
from pathlib import Path

# Ensure we can import from the project root if needed, though this is a unit test
# relying on the file system existence of the schema.
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

@pytest.fixture
def schema_path():
    return CONTRACTS_DIR / "signal.schema.yaml"

@pytest.fixture
def valid_signal_data():
    """Returns a dictionary representing a valid signal row according to the schema."""
    return {
        "soc": "SOC100000",
        "ror": 2.5,
        "ror_ci_lower": 1.2,
        "ror_ci_upper": 4.1,
        "prr": 1.8,
        "prr_ci_lower": 1.1,
        "prr_ci_upper": 2.9,
        "ic": 0.5,
        "ic_ci_lower": 0.1,
        "ic_ci_upper": 0.9,
        "p_adj": 0.03,
        "signal_flag": True,
        "background_rate_status": "UNKNOWN"
    }

@pytest.fixture
def invalid_signal_data_missing_field():
    """Returns data missing a required field."""
    return {
        "soc": "SOC100000",
        "ror": 2.5,
        # Missing ror_ci_lower
        "ror_ci_upper": 4.1,
        "prr": 1.8,
        "prr_ci_lower": 1.1,
        "prr_ci_upper": 2.9,
        "ic": 0.5,
        "ic_ci_lower": 0.1,
        "ic_ci_upper": 0.9,
        "p_adj": 0.03,
        "signal_flag": True,
        "background_rate_status": "UNKNOWN"
    }

@pytest.fixture
def invalid_signal_data_wrong_type():
    """Returns data with a wrong type for a field."""
    return {
        "soc": "SOC100000",
        "ror": "not_a_number", # Should be float/int
        "ror_ci_lower": 1.2,
        "ror_ci_upper": 4.1,
        "prr": 1.8,
        "prr_ci_lower": 1.1,
        "prr_ci_upper": 2.9,
        "ic": 0.5,
        "ic_ci_lower": 0.1,
        "ic_ci_upper": 0.9,
        "p_adj": 0.03,
        "signal_flag": True,
        "background_rate_status": "UNKNOWN"
    }

@pytest.fixture
def invalid_signal_data_wrong_enum():
    """Returns data with an invalid enum value."""
    return {
        "soc": "SOC100000",
        "ror": 2.5,
        "ror_ci_lower": 1.2,
        "ror_ci_upper": 4.1,
        "prr": 1.8,
        "prr_ci_lower": 1.1,
        "prr_ci_upper": 2.9,
        "ic": 0.5,
        "ic_ci_lower": 0.1,
        "ic_ci_upper": 0.9,
        "p_adj": 0.03,
        "signal_flag": True,
        "background_rate_status": "CALCULATED" # Invalid, must be UNKNOWN or KNOWN
    }

class TestSignalSchema:
    def test_schema_file_exists(self, schema_path):
        """Verify the schema file exists."""
        assert schema_path.exists(), f"Schema file not found at {schema_path}"

    def test_schema_is_valid_yaml(self, schema_path):
        """Verify the schema file is valid YAML."""
        with open(schema_path, 'r') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in schema file: {e}")

    def test_schema_structure(self, schema_path):
        """Verify the schema has the expected top-level keys."""
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_required_fields_present(self, schema_path):
        """Verify all required fields are listed in the schema."""
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        required_fields = schema.get("required", [])
        expected_fields = [
            "soc", "ror", "ror_ci_lower", "ror_ci_upper",
            "prr", "prr_ci_lower", "prr_ci_upper",
            "ic", "ic_ci_lower", "ic_ci_upper",
            "p_adj", "signal_flag", "background_rate_status"
        ]
        
        for field in expected_fields:
            assert field in required_fields, f"Field '{field}' is missing from required list"

    def test_validate_valid_data(self, schema_path, valid_signal_data):
        """Test that valid data passes basic schema checks (structural)."""
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        # Basic structural validation without jsonschema library
        # Check all required keys exist
        for key in schema["required"]:
            assert key in valid_signal_data, f"Missing required key: {key}"
        
        # Check types
        assert isinstance(valid_signal_data["soc"], str)
        assert isinstance(valid_signal_data["ror"], (int, float))
        assert isinstance(valid_signal_data["signal_flag"], bool)
        assert valid_signal_data["background_rate_status"] in ["UNKNOWN", "KNOWN"]

    def test_reject_missing_field(self, schema_path, invalid_signal_data_missing_field):
        """Test that data missing a required field is rejected."""
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        missing = False
        for key in schema["required"]:
            if key not in invalid_signal_data_missing_field:
                missing = True
                break
        
        assert missing, "Validation failed: should have detected missing field"

    def test_reject_wrong_type(self, schema_path, invalid_signal_data_wrong_type):
        """Test that data with wrong types is rejected."""
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        # Check ror type
        if not isinstance(invalid_signal_data_wrong_type["ror"], (int, float)):
            pass # Expected to fail type check
        else:
            pytest.fail("Validation failed: should have detected wrong type for 'ror'")

    def test_reject_wrong_enum(self, schema_path, invalid_signal_data_wrong_enum):
        """Test that data with invalid enum value is rejected."""
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        valid_statuses = schema["properties"]["background_rate_status"]["enum"]
        status = invalid_signal_data_wrong_enum["background_rate_status"]
        
        assert status not in valid_statuses, "Validation failed: should have rejected invalid enum value"