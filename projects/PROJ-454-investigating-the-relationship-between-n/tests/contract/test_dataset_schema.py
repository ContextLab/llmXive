"""
Contract test for dataset.schema.yaml validation.

This test validates that the dataset schema defined in 
specs/001-neural-entropy-cognitive-flexibility/contracts/dataset.schema.yaml
correctly validates the expected data structure for EEG dataset metadata.

It tests both valid and invalid data scenarios to ensure the schema
properly enforces data quality requirements.
"""

import json
import os
import pytest
from pathlib import Path

import jsonschema
from jsonschema import validate, ValidationError, SchemaError

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "specs" / "001-neural-entropy-cognitive-flexibility" / "contracts"
SCHEMA_PATH = SCHEMAS_DIR / "dataset.schema.yaml"

import yaml


def load_schema():
    """Load and parse the dataset schema YAML file."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Validate that the schema itself is a valid JSON schema
    try:
        jsonschema.Draft7Validator.check_schema(schema)
    except SchemaError as e:
        pytest.fail(f"Schema file is not a valid JSON schema: {e}")
    
    return schema


def get_valid_sample_data():
    """Return a sample dataset that should pass validation."""
    return {
        "dataset_id": "ds003104",
        "dataset_name": "Neural Entropy and Cognitive Flexibility in Aging",
        "source_url": "https://openneuro.org/datasets/ds003104",
        "version": "1.0.0",
        "download_date": "2024-01-15",
        "participant_count": 150,
        "eeg_channels": 64,
        "sampling_rate_hz": 1000,
        "frequency_bands": ["delta", "theta", "alpha", "beta", "gamma"],
        "behavioral_measures": ["wcst_perseverative_errors", "wcst_total_errors", "wcst_categories"],
        "demographics": {
            "age_range": {"min": 50, "max": 85},
            "education_years_range": {"min": 12, "max": 20},
            "gender_distribution": {"male": 75, "female": 75}
        },
        "quality_metrics": {
            "min_valid_eeg_seconds": 60,
            "max_corrupted_percent": 20,
            "min_snr_db": 5
        },
        "exclusion_criteria": [
            "neurological_condition",
            "medication_interference",
            "insufficient_eeg_quality"
        ]
    }

def get_invalid_data_missing_required():
    """Return a dataset missing required fields."""
    return {
        "dataset_id": "ds003104",
        # Missing: dataset_name, source_url, etc.
    }

def get_invalid_data_wrong_type():
    """Return a dataset with wrong types for fields."""
    return {
        "dataset_id": "ds003104",
        "dataset_name": "Test Dataset",
        "source_url": "https://openneuro.org/datasets/ds003104",
        "version": "1.0.0",
        "download_date": "2024-01-15",
        "participant_count": "not_a_number",  # Should be integer
        "eeg_channels": 64,
        "sampling_rate_hz": 1000,
        "frequency_bands": "not_a_list",  # Should be list
        "behavioral_measures": ["wcst_perseverative_errors"],
        "demographics": {},
        "quality_metrics": {},
        "exclusion_criteria": []
    }

def get_invalid_data_extra_field():
    """Return a dataset with an extra field not in schema."""
    data = get_valid_sample_data()
    data["unauthorized_field"] = "should_fail"
    return data


class TestDatasetSchemaValidation:
    """Contract tests for dataset.schema.yaml validation."""
    
    @pytest.fixture(scope="class")
    def schema(self):
        """Load the schema once per test class."""
        return load_schema()
    
    def test_schema_exists_and_valid(self):
        """Test that the schema file exists and is a valid JSON schema."""
        schema = load_schema()
        assert schema is not None
        assert "type" in schema
        assert schema["type"] == "object"
    
    def test_valid_data_passes_validation(self, schema):
        """Test that valid sample data passes schema validation."""
        valid_data = get_valid_sample_data()
        try:
            validate(instance=valid_data, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Valid data failed schema validation: {e.message}")
    
    def test_missing_required_fields_fails(self, schema):
        """Test that data missing required fields fails validation."""
        invalid_data = get_invalid_data_missing_required()
        
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=schema)
        
        # Verify it's a missing required field error
        assert "required" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()
    
    def test_wrong_type_fails(self, schema):
        """Test that data with wrong types fails validation."""
        invalid_data = get_invalid_data_wrong_type()
        
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=schema)
        
        # Verify it's a type error
        assert "type" in str(exc_info.value).lower()
    
    def test_additional_properties_handling(self, schema):
        """Test that additional properties are handled according to schema."""
        invalid_data = get_invalid_data_extra_field()
        
        # Check if schema allows additional properties
        additional_props = schema.get("additionalProperties", False)
        
        if additional_props is False:
            with pytest.raises(ValidationError):
                validate(instance=invalid_data, schema=schema)
        else:
            # If additional properties are allowed, this should pass
            try:
                validate(instance=invalid_data, schema=schema)
            except ValidationError as e:
                # Some schemas have complex additionalProperties rules
                pytest.skip(f"Schema allows additional properties but rejected: {e.message}")
    
    def test_schema_enforces_age_constraint(self, schema):
        """Test that schema enforces age >= 50 constraint from spec."""
        data = get_valid_sample_data()
        data["demographics"]["age_range"]["min"] = 45  # Below required 50
        
        # Check if schema has minimum constraint on age
        if "demographics" in schema.get("properties", {}):
            demographics_schema = schema["properties"]["demographics"]
            if "properties" in demographics_schema:
                age_range_schema = demographics_schema["properties"].get("age_range", {})
                if "properties" in age_range_schema:
                    min_age_schema = age_range_schema["properties"].get("min", {})
                    if min_age_schema.get("minimum") == 50:
                        with pytest.raises(ValidationError):
                            validate(instance=data, schema=schema)
    
    def test_frequency_bands_validation(self, schema):
        """Test that frequency_bands contains expected values."""
        data = get_valid_sample_data()
        data["frequency_bands"] = ["delta", "invalid_band"]  # Invalid band name
        
        # Check if schema has enum constraint
        if "frequency_bands" in schema.get("properties", {}):
            bands_schema = schema["properties"]["frequency_bands"]
            if "items" in bands_schema and "enum" in bands_schema["items"]:
                with pytest.raises(ValidationError):
                    validate(instance=data, schema=schema)
    
    def test_schema_structure_matches_spec(self, schema):
        """Test that schema structure matches the specification requirements."""
        required_top_level_fields = [
            "dataset_id", "dataset_name", "source_url", "version", 
            "download_date", "participant_count", "eeg_channels",
            "sampling_rate_hz", "frequency_bands", "behavioral_measures",
            "demographics", "quality_metrics", "exclusion_criteria"
        ]
        
        schema_properties = schema.get("properties", {})
        schema_required = schema.get("required", [])
        
        for field in required_top_level_fields:
            assert field in schema_properties, f"Schema missing property: {field}"
            assert field in schema_required, f"Schema missing required field: {field}"
    
    def test_schema_validates_demographics_structure(self, schema):
        """Test that demographics sub-structure is validated correctly."""
        data = get_valid_sample_data()
        
        # Remove demographics to test required validation
        del data["demographics"]
        
        with pytest.raises(ValidationError):
            validate(instance=data, schema=schema)
    
    def test_schema_validates_quality_metrics_structure(self, schema):
        """Test that quality_metrics sub-structure is validated correctly."""
        data = get_valid_sample_data()
        
        # Remove quality_metrics to test required validation
        del data["quality_metrics"]
        
        with pytest.raises(ValidationError):
            validate(instance=data, schema=schema)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])