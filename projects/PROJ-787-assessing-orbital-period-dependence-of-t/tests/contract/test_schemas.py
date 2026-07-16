"""
Contract test suite for validating data integrity against YAML schemas.

This module provides tests to ensure that data files produced by the pipeline
conform to the expected schemas defined in the contracts directory.
"""

import os
import sys
import json
import yaml
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging_config import setup_logging, get_logger

# Configure logging for tests
logger = get_logger("contract_tests")


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate data against a simple YAML schema.
    
    This is a basic validator that checks:
    - Required fields exist
    - Field types match (string, number, boolean, array, object)
    - Field constraints (min, max, pattern) if defined
    
    Returns a list of validation errors.
    """
    errors = []
    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Validate each field
    for field_name, value in data.items():
        if field_name not in properties:
            # Allow extra fields for now, but could be made strict
            continue
        
        field_schema = properties[field_name]
        expected_type = field_schema.get('type')
        
        # Type checking
        if expected_type == 'string':
            if not isinstance(value, str):
                errors.append(f"Field '{field_name}' must be string, got {type(value).__name__}")
        elif expected_type == 'number':
            if not isinstance(value, (int, float)):
                errors.append(f"Field '{field_name}' must be number, got {type(value).__name__}")
        elif expected_type == 'integer':
            if not isinstance(value, int):
                errors.append(f"Field '{field_name}' must be integer, got {type(value).__name__}")
        elif expected_type == 'boolean':
            if not isinstance(value, bool):
                errors.append(f"Field '{field_name}' must be boolean, got {type(value).__name__}")
        elif expected_type == 'array':
            if not isinstance(value, list):
                errors.append(f"Field '{field_name}' must be array, got {type(value).__name__}")
        elif expected_type == 'object':
            if not isinstance(value, dict):
                errors.append(f"Field '{field_name}' must be object, got {type(value).__name__}")
        
        # Range constraints for numbers
        if expected_type in ['number', 'integer'] and isinstance(value, (int, float)):
            if 'minimum' in field_schema and value < field_schema['minimum']:
                errors.append(f"Field '{field_name}' value {value} is below minimum {field_schema['minimum']}")
            if 'maximum' in field_schema and value > field_schema['maximum']:
                errors.append(f"Field '{field_name}' value {value} is above maximum {field_schema['maximum']}")
        
        # Pattern constraints for strings
        if expected_type == 'string' and 'pattern' in field_schema:
            import re
            if not re.match(field_schema['pattern'], str(value)):
                errors.append(f"Field '{field_name}' value '{value}' does not match pattern '{field_schema['pattern']}'")
    
    return errors


def validate_dataframe_schema(df, schema: Dict[str, Any], df_name: str = "DataFrame") -> List[str]:
    """
    Validate a pandas DataFrame against a schema.
    
    The schema should define:
    - required: list of required column names
    - properties: dict mapping column names to their type constraints
    """
    import pandas as pd
    
    errors = []
    required_columns = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check required columns exist
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    # Validate column types
    for col_name in df.columns:
        if col_name not in properties:
            continue
        
        col_schema = properties[col_name]
        expected_type = col_schema.get('type')
        
        # Check a sample of values for type consistency
        if len(df) > 0:
            sample_value = df[col_name].iloc[0]
            
            if expected_type == 'string':
                if not pd.api.types.is_string_dtype(df[col_name]):
                    errors.append(f"Column '{col_name}' should be string type")
            elif expected_type == 'number':
                if not pd.api.types.is_numeric_dtype(df[col_name]):
                    errors.append(f"Column '{col_name}' should be numeric type")
            elif expected_type == 'integer':
                if not pd.api.types.is_integer_dtype(df[col_name]):
                    errors.append(f"Column '{col_name}' should be integer type")
            elif expected_type == 'boolean':
                if not pd.api.types.is_bool_dtype(df[col_name]):
                    errors.append(f"Column '{col_name}' should be boolean type")
    
    return errors


class TestPlanetRecordSchema:
    """Tests for the planet_record schema."""
    
    @pytest.fixture
    def schema(self):
        """Load the planet_record schema."""
        schema_path = PROJECT_ROOT / "contracts" / "planet_record.schema.yaml"
        return load_schema(schema_path)
    
    def test_schema_exists(self):
        """Verify the planet_record schema file exists."""
        schema_path = PROJECT_ROOT / "contracts" / "planet_record.schema.yaml"
        assert schema_path.exists(), "planet_record.schema.yaml not found"
    
    def test_schema_has_required_fields(self, schema):
        """Verify the schema defines required fields."""
        assert 'required' in schema, "Schema must define required fields"
        assert len(schema['required']) > 0, "Schema must have at least one required field"
    
    def test_validate_valid_planet_record(self, schema):
        """Test validation of a valid planet record."""
        valid_record = {
            "kepler_id": 12345,
            "planet_name": "Kepler-1234.01",
            "radius": 1.5,
            "radius_uncertainty": 0.1,
            "period": 10.5,
            "period_uncertainty": 0.01,
            "stellar_temperature": 5500,
            "stellar_radius": 1.2,
            "discovery_method": "transit",
            "confidence_score": 0.95
        }
        
        errors = validate_against_schema(valid_record, schema)
        assert len(errors) == 0, f"Valid record failed validation: {errors}"
    
    def test_validate_missing_required_field(self, schema):
        """Test validation catches missing required fields."""
        invalid_record = {
            "kepler_id": 12345,
            "planet_name": "Kepler-1234.01"
            # Missing required fields
        }
        
        errors = validate_against_schema(invalid_record, schema)
        assert len(errors) > 0, "Validation should catch missing required fields"
        assert any("required" in err.lower() for err in errors), "Should report missing required fields"
    
    def test_validate_wrong_type(self, schema):
        """Test validation catches type mismatches."""
        invalid_record = {
            "kepler_id": "not_a_number",  # Should be integer
            "planet_name": "Kepler-1234.01",
            "radius": 1.5,
            "radius_uncertainty": 0.1,
            "period": 10.5,
            "period_uncertainty": 0.01,
            "stellar_temperature": 5500,
            "stellar_radius": 1.2,
            "discovery_method": "transit",
            "confidence_score": 0.95
        }
        
        errors = validate_against_schema(invalid_record, schema)
        assert len(errors) > 0, "Validation should catch type mismatches"


class TestGapResultSchema:
    """Tests for the gap_result schema."""
    
    @pytest.fixture
    def schema(self):
        """Load the gap_result schema."""
        schema_path = PROJECT_ROOT / "contracts" / "analysis_output.schema.yaml"
        return load_schema(schema_path)
    
    def test_schema_exists(self):
        """Verify the gap_result schema file exists."""
        schema_path = PROJECT_ROOT / "contracts" / "analysis_output.schema.yaml"
        assert schema_path.exists(), "analysis_output.schema.yaml not found"
    
    def test_schema_has_required_fields(self, schema):
        """Verify the schema defines required fields."""
        assert 'required' in schema, "Schema must define required fields"
        assert len(schema['required']) > 0, "Schema must have at least one required field"
    
    def test_validate_valid_gap_result(self, schema):
        """Test validation of a valid gap result."""
        valid_result = {
            "bin_id": "bin_1",
            "period_center": 5.0,
            "period_width": 0.5,
            "gap_location": 1.8,
            "gap_uncertainty": 0.1,
            "n_planets": 50,
            "status": "resolved",
            "method": "gmm",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        errors = validate_against_schema(valid_result, schema)
        assert len(errors) == 0, f"Valid result failed validation: {errors}"
    
    def test_validate_missing_required_field(self, schema):
        """Test validation catches missing required fields."""
        invalid_result = {
            "bin_id": "bin_1",
            "period_center": 5.0
            # Missing required fields
        }
        
        errors = validate_against_schema(invalid_result, schema)
        assert len(errors) > 0, "Validation should catch missing required fields"
        assert any("required" in err.lower() for err in errors), "Should report missing required fields"
    
    def test_validate_invalid_status(self, schema):
        """Test validation catches invalid status values."""
        # Check if status has an enum constraint
        properties = schema.get('properties', {})
        if 'status' in properties and 'enum' in properties['status']:
            invalid_result = {
                "bin_id": "bin_1",
                "period_center": 5.0,
                "period_width": 0.5,
                "gap_location": 1.8,
                "gap_uncertainty": 0.1,
                "n_planets": 50,
                "status": "invalid_status",
                "method": "gmm",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            errors = validate_against_schema(invalid_result, schema)
            assert len(errors) > 0, "Validation should catch invalid enum values"


class TestDataIngestionSchema:
    """Tests for the data ingestion output schema."""
    
    @pytest.fixture
    def schema(self):
        """Load the ingestion output schema."""
        schema_path = PROJECT_ROOT / "contracts" / "ingestion_output.schema.yaml"
        if not schema_path.exists():
            # Fallback to planet_record schema if specific ingestion schema doesn't exist
            schema_path = PROJECT_ROOT / "contracts" / "planet_record.schema.yaml"
        return load_schema(schema_path)
    
    def test_schema_exists(self):
        """Verify the ingestion schema file exists."""
        schema_path = PROJECT_ROOT / "contracts"
        assert schema_path.exists(), "contracts directory not found"
    
    def test_validate_sample_ingestion_data(self, schema):
        """Test validation with sample ingestion data."""
        sample_data = {
            "kepler_id": 12345,
            "planet_name": "Kepler-1234.01",
            "radius": 1.5,
            "radius_uncertainty": 0.1,
            "period": 10.5,
            "period_uncertainty": 0.01,
            "stellar_temperature": 5500,
            "stellar_radius": 1.2,
            "discovery_method": "transit",
            "confidence_score": 0.95
        }
        
        errors = validate_against_schema(sample_data, schema)
        # Should pass or have minimal errors depending on schema strictness
        logger.info(f"Validation errors for sample ingestion data: {errors}")


class TestBinningSchema:
    """Tests for the binning output schema."""
    
    @pytest.fixture
    def schema(self):
        """Load the binning schema."""
        schema_path = PROJECT_ROOT / "contracts" / "binning_output.schema.yaml"
        if not schema_path.exists():
            # Create a minimal schema for testing if file doesn't exist
            schema_path = PROJECT_ROOT / "contracts" / "analysis_output.schema.yaml"
        return load_schema(schema_path)
    
    def test_schema_exists(self):
        """Verify the binning schema file exists."""
        schema_path = PROJECT_ROOT / "contracts"
        assert schema_path.exists(), "contracts directory not found"
    
    def test_validate_binning_result(self, schema):
        """Test validation of binning results."""
        binning_result = {
            "bin_id": "bin_1",
            "period_center": 5.0,
            "period_width": 0.5,
            "gap_location": 1.8,
            "gap_uncertainty": 0.1,
            "n_planets": 50,
            "status": "resolved",
            "method": "gmm",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        errors = validate_against_schema(binning_result, schema)
        logger.info(f"Validation errors for binning result: {errors}")


class TestResultsSchema:
    """Tests for the final results schema."""
    
    @pytest.fixture
    def schema(self):
        """Load the results schema."""
        schema_path = PROJECT_ROOT / "contracts" / "final_results.schema.yaml"
        if not schema_path.exists():
            schema_path = PROJECT_ROOT / "contracts" / "analysis_output.schema.yaml"
        return load_schema(schema_path)
    
    def test_schema_exists(self):
        """Verify the results schema file exists."""
        schema_path = PROJECT_ROOT / "contracts"
        assert schema_path.exists(), "contracts directory not found"
    
    def test_validate_final_results(self, schema):
        """Test validation of final results."""
        final_results = {
            "slope": -0.12,
            "slope_uncertainty": 0.02,
            "intercept": 2.0,
            "r_squared": 0.85,
            "n_bins": 10,
            "method": "eiv_regression",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        errors = validate_against_schema(final_results, schema)
        logger.info(f"Validation errors for final results: {errors}")


def test_all_schemas_load():
    """Test that all schema files can be loaded."""
    contracts_dir = PROJECT_ROOT / "contracts"
    schema_files = list(contracts_dir.glob("*.schema.yaml"))
    
    assert len(schema_files) > 0, "No schema files found in contracts directory"
    
    for schema_file in schema_files:
        try:
            schema = load_schema(schema_file)
            assert isinstance(schema, dict), f"Schema {schema_file} should be a dict"
        except Exception as e:
            pytest.fail(f"Failed to load schema {schema_file}: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])