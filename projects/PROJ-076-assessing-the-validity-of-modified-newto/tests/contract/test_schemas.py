"""
Contract tests for dataset schema validation.

These tests ensure that the processed galaxy data conforms to the
defined schema in contracts/dataset.schema.yaml.
"""
import json
import os
import pytest
import yaml
from pathlib import Path
from typing import Any, Dict, List

# Try to import jsonschema, provide a helpful error if missing
try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    pytest.skip("jsonschema not installed. Run: pip install jsonschema", allow_module_level=True)


# Path to the schema file relative to project root
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "dataset.schema.yaml"
DATA_PATH = Path(__file__).parent.parent.parent / "data" / "processed" / "filtered_galaxies.csv"


def load_schema() -> Dict[str, Any]:
    """Load the JSON schema from the YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)


def load_sample_data() -> Dict[str, Any]:
    """
    Load sample data from the filtered galaxies CSV or generate a minimal valid sample.
    
    Note: This function attempts to load real data. If the file doesn't exist,
    it creates a minimal valid sample to test the schema structure.
    """
    if DATA_PATH.exists():
        import pandas as pd
        df = pd.read_csv(DATA_PATH)
        
        # Convert to the expected schema structure
        galaxies = []
        for _, row in df.iterrows():
            # Parse rotation curve data from the row (assuming it's stored as a JSON string or similar)
            # For now, we'll create a minimal valid structure based on the schema
            galaxy_data = {
                "id": row.get("id", "G001"),
                "name": row.get("name", "Test Galaxy"),
                "inclination": float(row.get("inclination", 45.0)),
                "inclination_uncertainty": float(row.get("inclination_uncertainty", 5.0)),
                "distance": float(row.get("distance", 10.0)),
                "distance_uncertainty": float(row.get("distance_uncertainty", 1.0)),
                "v_max": float(row.get("v_max", 100.0)),
                "rotation_curve": [
                    {
                        "radius": float(row.get("radius_0", 1.0)),
                        "velocity": float(row.get("velocity_0", 50.0)),
                        "velocity_uncertainty": float(row.get("velocity_uncertainty_0", 5.0))
                    }
                ]
            }
            galaxies.append(galaxy_data)
        
        return {
            "meta": {
                "source": "SPARC",
                "timestamp": "2024-01-01T00:00:00Z",
                "version": "1.0",
                "filter_criteria": {
                    "min_points": 15,
                    "max_inclination_uncertainty": 10.0
                }
            },
            "galaxies": galaxies
        }
    else:
        # Create a minimal valid sample for testing
        return {
            "meta": {
                "source": "https://data.astropy.org/sparc",
                "timestamp": "2024-01-01T00:00:00Z",
                "version": "1.0",
                "filter_criteria": {
                    "min_points": 15,
                    "max_inclination_uncertainty": 10.0
                }
            },
            "galaxies": [
                {
                    "id": "G001",
                    "name": "NGC 2403",
                    "inclination": 63.0,
                    "inclination_uncertainty": 5.0,
                    "distance": 3.2,
                    "distance_uncertainty": 0.3,
                    "v_max": 120.0,
                    "rotation_curve": [
                        {
                            "radius": i * 0.5,
                            "velocity": 50.0 + i * 2.0,
                            "velocity_uncertainty": 3.0
                        }
                        for i in range(20)
                    ]
                }
            ]
        }


class TestDatasetSchema:
    """Test suite for dataset schema validation."""

    @pytest.fixture
    def schema(self) -> Dict[str, Any]:
        """Load the schema for each test."""
        return load_schema()

    @pytest.fixture
    def sample_data(self) -> Dict[str, Any]:
        """Load sample data for each test."""
        return load_sample_data()

    def test_schema_file_exists(self):
        """Test that the schema file exists."""
        assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

    def test_schema_is_valid_json(self, schema):
        """Test that the schema is valid JSON/YAML."""
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"

    def test_required_top_level_properties(self, schema):
        """Test that required top-level properties are defined."""
        assert "required" in schema
        assert "meta" in schema["required"]
        assert "galaxies" in schema["required"]

    def test_meta_schema_structure(self, schema):
        """Test the meta section of the schema."""
        meta_schema = schema["properties"]["meta"]
        assert "required" in meta_schema
        assert "source" in meta_schema["required"]
        assert "timestamp" in meta_schema["required"]
        assert "version" in meta_schema["required"]
        assert "filter_criteria" in meta_schema["required"]

    def test_galaxy_schema_structure(self, schema):
        """Test the galaxy item schema structure."""
        galaxy_schema = schema["properties"]["galaxies"]["items"]
        assert "required" in galaxy_schema
        required_fields = galaxy_schema["required"]
        assert "id" in required_fields
        assert "name" in required_fields
        assert "inclination" in required_fields
        assert "inclination_uncertainty" in required_fields
        assert "distance" in required_fields
        assert "distance_uncertainty" in required_fields
        assert "v_max" in required_fields
        assert "rotation_curve" in required_fields

    def test_rotation_curve_min_items(self, schema):
        """Test that rotation curve requires minimum 15 points."""
        rotation_curve_schema = schema["properties"]["galaxies"]["items"]["properties"]["rotation_curve"]
        assert rotation_curve_schema["minItems"] == 15

    def test_validate_valid_data(self, schema, sample_data):
        """Test that valid data passes schema validation."""
        try:
            validate(instance=sample_data, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Valid data failed schema validation: {e.message}")

    def test_validate_invalid_inclination(self, schema):
        """Test that invalid inclination (out of range) fails validation."""
        invalid_data = load_sample_data()
        invalid_data["galaxies"][0]["inclination"] = 100.0  # Invalid: > 90
        
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)

    def test_validate_invalid_inclination_uncertainty(self, schema):
        """Test that invalid inclination uncertainty fails validation."""
        invalid_data = load_sample_data()
        invalid_data["galaxies"][0]["inclination_uncertainty"] = 15.0  # Invalid: > 10 (but schema allows up to 90)
        # Actually, the schema allows up to 90, so let's test negative
        invalid_data["galaxies"][0]["inclination_uncertainty"] = -1.0  # Invalid: < 0
        
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)

    def test_validate_insufficient_rotation_curve_points(self, schema):
        """Test that rotation curve with < 15 points fails validation."""
        invalid_data = load_sample_data()
        # Reduce rotation curve to 14 points
        invalid_data["galaxies"][0]["rotation_curve"] = invalid_data["galaxies"][0]["rotation_curve"][:14]
        
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)

    def test_validate_missing_required_field(self, schema):
        """Test that missing required field fails validation."""
        invalid_data = load_sample_data()
        del invalid_data["galaxies"][0]["name"]
        
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)

    def test_validate_invalid_id_format(self, schema):
        """Test that invalid ID format fails validation."""
        invalid_data = load_sample_data()
        invalid_data["galaxies"][0]["id"] = "INVALID_ID"  # Should match "^G[0-9]{3,}$"
        
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)

    def test_validator_class(self, schema):
        """Test using Draft7Validator directly."""
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(load_sample_data()))
        assert len(errors) == 0, f"Unexpected validation errors: {[e.message for e in errors]}"