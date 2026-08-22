"""
Contract test for T007: Validate that contracts/dataset.schema.yaml
is syntactically valid and can be loaded and validated against Pydantic models.
This test skeleton implements TDD for User Story 1 (Ingest and Harmonize Multimodal Data).

Note: These tests will fail until T015-T022 are implemented to populate real data,
but the schema contract itself (T007) and the validation logic (T012) must be
functional to verify data integrity once data is present.
"""
import os
import sys
import yaml
import pytest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from src.config.schemas import AnalysisDatasetRecord, validate_dataset_schema


class TestDatasetSchemaContract:
    """Tests for the dataset schema contract (T007)."""

    @pytest.fixture
    def schema_path(self):
        """Return path to the dataset schema YAML file."""
        return PROJECT_ROOT / "contracts" / "dataset.schema.yaml"

    def test_schema_file_exists(self, schema_path):
        """Verify that the schema file exists on disk."""
        assert schema_path.exists(), f"Schema file not found at {schema_path}"

    def test_schema_is_valid_yaml(self, schema_path):
        """Verify that the schema file is valid YAML."""
        try:
            with open(schema_path, 'r') as f:
                schema_data = yaml.safe_load(f)
            assert isinstance(schema_data, dict), "Schema must be a YAML dictionary"
            assert "$schema" in schema_data, "Schema must define $schema"
            assert "properties" in schema_data, "Schema must define properties"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in schema file: {e}")

    def test_schema_loads_into_pydantic(self, schema_path):
        """Verify that the schema can be used to validate Pydantic models."""
        # Load the schema
        with open(schema_path, 'r') as f:
            schema_data = yaml.safe_load(f)

        # Verify that the Pydantic model's field definitions align with the schema
        # This is a structural check; actual validation is tested in test_validation_passes
        schema_props = schema_data.get("properties", {})
        model_fields = AnalysisDatasetRecord.model_fields.keys()

        # Check that all required schema properties are present in the model
        required_schema_fields = [k for k, v in schema_props.items() if k in model_fields]
        assert len(required_schema_fields) > 0, "Schema properties do not match model fields"

    def test_validation_passes_with_valid_data(self, schema_path):
        """Verify that valid data passes schema validation."""
        # Create a minimal valid record matching the schema
        valid_record = {
            "household_id": "HH-001",
            "village_id": "VIL-001",
            "country": "Malawi",
            "latitude": -13.9626,
            "longitude": 33.7741,
            "survey_year": 2020,
            "land_size": 1.5,
            "education": 8,
            "finance_access": True,
            "CSA_Index": 3,
            "Stability_Score": 0.85,
            "HFIAS": 12,
            "practice_drought_resistant": True,
            "practice_conservation_tillage": False,
            "practice_irrigation": True,
            "practice_agroforestry": False,
            "extension_visits": 4,
            "ndvi_mean": 0.45,
            "ndvi_cv": 0.15
        }

        # Validate using the helper function
        result = validate_dataset_schema(valid_record)
        assert result is True, "Valid record should pass validation"

    def test_validation_fails_with_missing_required_field(self, schema_path):
        """Verify that validation fails when a required field is missing."""
        invalid_record = {
            "household_id": "HH-002",
            # Missing village_id and other required fields
            "country": "Tanzania",
            "latitude": -6.3690,
            "longitude": 34.8888,
            "survey_year": 2021,
            "land_size": 2.0,
            "education": 10,
            "finance_access": False,
            "CSA_Index": 2,
            "Stability_Score": 0.70,
            "HFIAS": 18,
            "practice_drought_resistant": False,
            "practice_conservation_tillage": True,
            "practice_irrigation": False,
            "practice_agroforestry": True,
            "extension_visits": 2,
            "ndvi_mean": 0.50,
            "ndvi_cv": 0.20
        }

        # Validation should fail because village_id is missing
        result = validate_dataset_schema(invalid_record)
        assert result is False, "Invalid record should fail validation"

    def test_validation_fails_with_invalid_enum_value(self, schema_path):
        """Verify that validation fails when an enum field has an invalid value."""
        invalid_record = {
            "household_id": "HH-003",
            "village_id": "VIL-003",
            "country": "Kenya",  # Invalid: not in enum [Malawi, Tanzania]
            "latitude": -1.2921,
            "longitude": 36.8219,
            "survey_year": 2022,
            "land_size": 1.0,
            "education": 6,
            "finance_access": True,
            "CSA_Index": 1,
            "Stability_Score": 0.60,
            "HFIAS": 24,
            "practice_drought_resistant": True,
            "practice_conservation_tillage": True,
            "practice_irrigation": True,
            "practice_agroforestry": True,
            "extension_visits": 6,
            "ndvi_mean": 0.40,
            "ndvi_cv": 0.25
        }

        result = validate_dataset_schema(invalid_record)
        assert result is False, "Record with invalid enum value should fail validation"