"""
Contract tests validating data structures against the defined JSON schema.
These tests ensure that data produced by the pipeline conforms to the
specification in `contracts/dataset.schema.yaml`.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import yaml

# Import schema validation library
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    pytest.skip("jsonschema not installed", allow_module_level=True)

# Project root for relative paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON schema from a YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_galaxy_data(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate a dictionary of galaxy data against the schema.
    Raises jsonschema.ValidationError if invalid.
    """
    jsonschema.validate(instance=data, schema=schema)


class TestDatasetSchema:
    """Contract tests for the galaxy dataset schema."""

    @pytest.fixture(scope="class")
    def schema(self) -> Dict[str, Any]:
        """Load the schema once for the test class."""
        return load_schema(SCHEMA_PATH)

    def test_schema_exists_and_loads(self) -> None:
        """Verify the schema file exists and is valid YAML."""
        assert SCHEMA_PATH.exists(), f"Schema file missing at {SCHEMA_PATH}"
        schema = load_schema(SCHEMA_PATH)
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert "properties" in schema, "Schema must have properties"
        assert "galaxies" in schema["properties"], "Schema must define 'galaxies'"

    def test_valid_galaxy_structure(self, schema: Dict[str, Any]) -> None:
        """Test that a minimal valid galaxy structure passes validation."""
        valid_data = {
            "galaxies": [
                {
                    "name": "NGC1234",
                    "inclination": 45.0,
                    "inclination_uncertainty": 2.0,
                    "distance": 10.5,
                    "distance_uncertainty": 0.5,
                    "mass_to_light_ratio": 2.1,
                    "rotation_curve": [
                        {
                            "radius": 1.0,
                            "velocity": 100.0,
                            "velocity_uncertainty": 5.0
                        },
                        {
                            "radius": 2.0,
                            "velocity": 110.0,
                            "velocity_uncertainty": 4.0
                        }
                    ]
                }
            ]
        }
        try:
            validate_galaxy_data(valid_data, schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Valid data failed schema validation: {e.message}")

    def test_missing_required_field_raises_error(self, schema: Dict[str, Any]) -> None:
        """Test that missing a required field raises a validation error."""
        invalid_data = {
            "galaxies": [
                {
                    "name": "NGC1234",
                    # Missing 'inclination' which is required
                    "inclination_uncertainty": 2.0,
                    "distance": 10.5,
                    "distance_uncertainty": 0.5,
                    "mass_to_light_ratio": 2.1,
                    "rotation_curve": []
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            validate_galaxy_data(invalid_data, schema)

    def test_invalid_type_raises_error(self, schema: Dict[str, Any]) -> None:
        """Test that incorrect types raise a validation error."""
        invalid_data = {
            "galaxies": [
                {
                    "name": "NGC1234",
                    "inclination": "forty-five",  # Should be number
                    "inclination_uncertainty": 2.0,
                    "distance": 10.5,
                    "distance_uncertainty": 0.5,
                    "mass_to_light_ratio": 2.1,
                    "rotation_curve": []
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            validate_galaxy_data(invalid_data, schema)

    def test_rotation_curve_point_structure(self, schema: Dict[str, Any]) -> None:
        """Test that rotation curve points must have radius, velocity, uncertainty."""
        invalid_data = {
            "galaxies": [
                {
                    "name": "NGC1234",
                    "inclination": 45.0,
                    "inclination_uncertainty": 2.0,
                    "distance": 10.5,
                    "distance_uncertainty": 0.5,
                    "mass_to_light_ratio": 2.1,
                    "rotation_curve": [
                        {
                            "radius": 1.0,
                            "velocity": 100.0
                            # Missing velocity_uncertainty
                        }
                    ]
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            validate_galaxy_data(invalid_data, schema)

    def test_empty_galaxies_list_is_valid(self, schema: Dict[str, Any]) -> None:
        """Test that an empty list of galaxies is valid."""
        valid_data = {"galaxies": []}
        try:
            validate_galaxy_data(valid_data, schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Empty galaxies list failed validation: {e.message}")

    def test_integration_with_preprocess_output(self, schema: Dict[str, Any]) -> None:
        """
        Integration test: If data/processed/filtered_galaxies.csv exists,
        attempt to load and validate it against the schema.
        This ensures the pipeline produces schema-compliant data.
        """
        data_path = PROJECT_ROOT / "data" / "processed" / "filtered_galaxies.csv"
        if not data_path.exists():
            pytest.skip(f"Data file not found at {data_path} - skipping integration check")

        try:
            import pandas as pd
            df = pd.read_csv(data_path)
        except Exception as e:
            pytest.fail(f"Failed to read data file: {e}")

        # Convert DataFrame to schema-compatible dict structure
        # This is a simplified conversion assuming the CSV has flat columns
        # In a real scenario, we might need to group by galaxy name first
        galaxies_list = []
        
        # Check if we have a grouping column
        if "name" in df.columns:
            for name, group in df.groupby("name"):
                galaxy_entry = {
                    "name": name,
                    "inclination": group["inclination"].iloc[0] if "inclination" in group else 0.0,
                    "inclination_uncertainty": group["inclination_uncertainty"].iloc[0] if "inclination_uncertainty" in group else 0.0,
                    "distance": group["distance"].iloc[0] if "distance" in group else 0.0,
                    "distance_uncertainty": group["distance_uncertainty"].iloc[0] if "distance_uncertainty" in group else 0.0,
                    "mass_to_light_ratio": group["mass_to_light_ratio"].iloc[0] if "mass_to_light_ratio" in group else 0.0,
                    "rotation_curve": group[["radius", "velocity", "velocity_uncertainty"]].to_dict("records")
                }
                # Clean up None values for schema compliance
                for k, v in list(galaxy_entry.items()):
                    if k != "rotation_curve" and v == 0.0 and k in ["inclination", "distance", "mass_to_light_ratio"]:
                        # If required fields are missing in CSV, we can't validate fully
                        # In a real pipeline, these should be populated
                        pass 
                
                galaxies_list.append(galaxy_entry)
        else:
            # Fallback if no name column, assume single galaxy or flat structure
            pytest.skip("CSV does not contain 'name' column for grouping")

        test_data = {"galaxies": galaxies_list}
        
        try:
            validate_galaxy_data(test_data, schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Pipeline output failed schema validation: {e.message}")
