"""
Contract test for dataset schema validation (US1).

This test verifies that the dataset schema defined in contracts/dataset.schema.yaml
matches the expected structure for the nostalgia-cognitive flexibility study.

Dependencies:
  - T020a: contracts/dataset.schema.yaml must exist
  - T004: utils.py for logging helpers
"""
import os
import json
import yaml
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import project utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils import log_info, log_error, compute_sha256

# Constants for schema validation
REQUIRED_FIELDS = [
    "participant_id",
    "age",
    "stimulus_type",
    "perseverative_errors",
    "categories_completed"
]

OPTIONAL_FIELDS = [
    "MMSE",
    "reaction_time",
    "accuracy",
    "trial_count"
]

REQUIRED_TYPES = {
    "participant_id": ["string", "integer"],
    "age": ["integer", "number"],
    "stimulus_type": ["string"],
    "perseverative_errors": ["integer", "number"],
    "categories_completed": ["integer", "number"]
}

VALID_STIMULUS_TYPES = ["nostalgia", "control", "neutral"]

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
SCHEMA_FILE = CONTRACTS_DIR / "dataset.schema.yaml"
METADATA_FILE = PROJECT_ROOT / "data" / "raw" / "metadata.json"

def load_schema() -> Dict[str, Any]:
    """Load the dataset schema from the contracts directory."""
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE}")
    
    with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_field_presence(schema: Dict[str, Any]) -> List[str]:
    """
    Validate that all required fields are present in the schema.
    
    Returns a list of missing fields.
    """
    properties = schema.get("properties", {})
    missing = []
    
    for field in REQUIRED_FIELDS:
        if field not in properties:
            missing.append(field)
    
    return missing

def validate_field_types(schema: Dict[str, Any]) -> List[str]:
    """
    Validate that field types match expectations.
    
    Returns a list of type mismatches.
    """
    properties = schema.get("properties", {})
    mismatches = []
    
    for field, expected_types in REQUIRED_TYPES.items():
        if field in properties:
            actual_type = properties[field].get("type")
            if actual_type not in expected_types:
                mismatches.append(
                    f"Field '{field}': expected type in {expected_types}, got '{actual_type}'"
                )
    
    return mismatches

def validate_enum_constraints(schema: Dict[str, Any]) -> List[str]:
    """
    Validate that stimulus_type has valid enum constraints.
    
    Returns a list of constraint violations.
    """
    properties = schema.get("properties", {})
    violations = []
    
    if "stimulus_type" in properties:
        field_def = properties["stimulus_type"]
        enum_values = field_def.get("enum", [])
        
        if enum_values:
            # Check if all valid types are present
            for valid_type in VALID_STIMULUS_TYPES:
                if valid_type not in enum_values:
                    violations.append(
                        f"stimulus_type enum missing valid value: '{valid_type}'"
                    )
        else:
            violations.append("stimulus_type should have an 'enum' constraint")
    
    return violations

def validate_required_constraint(schema: Dict[str, Any]) -> List[str]:
    """
    Validate that the 'required' array includes all mandatory fields.
    
    Returns a list of missing required field constraints.
    """
    required_fields = schema.get("required", [])
    missing_required = []
    
    for field in REQUIRED_FIELDS:
        if field not in required_fields:
            missing_required.append(field)
    
    return missing_required

def validate_schema_version(schema: Dict[str, Any]) -> Optional[str]:
    """
    Validate that the schema has a version field.
    
    Returns an error message if version is missing or invalid.
    """
    version = schema.get("version")
    if not version:
        return "Schema is missing 'version' field"
    
    if not isinstance(version, str):
        return f"Schema 'version' must be a string, got {type(version).__name__}"
    
    return None

def validate_data_types_in_sample(data_file: Path) -> List[str]:
    """
    If a sample data file exists, validate that actual data types match schema.
    
    Returns a list of type mismatches found in the sample data.
    """
    if not data_file.exists():
        return []  # Skip if no sample data exists
    
    errors = []
    try:
        import pandas as pd
        df = pd.read_csv(data_file)
        properties = load_schema().get("properties", {})
        
        for field, expected_types in REQUIRED_TYPES.items():
            if field in df.columns:
                dtype = str(df[field].dtype)
                # Map pandas dtypes to JSON types
                type_mapping = {
                    'int64': 'integer',
                    'int32': 'integer',
                    'float64': 'number',
                    'float32': 'number',
                    'object': 'string',
                    'string': 'string'
                }
                actual_type = type_mapping.get(dtype, dtype)
                
                if actual_type not in expected_types:
                    errors.append(
                        f"Data file column '{field}': pandas dtype '{dtype}' "
                        f"maps to '{actual_type}', expected {expected_types}"
                    )
    except Exception as e:
        errors.append(f"Error reading sample data file: {str(e)}")
    
    return errors

class TestDatasetSchema:
    """Contract tests for dataset schema validation."""
    
    @pytest.fixture(scope="class")
    def schema(self) -> Dict[str, Any]:
        """Load the schema once for all tests in this class."""
        return load_schema()
    
    def test_schema_file_exists(self):
        """Test that the schema file exists."""
        assert SCHEMA_FILE.exists(), f"Schema file missing: {SCHEMA_FILE}"
    
    def test_schema_is_valid_yaml(self, schema):
        """Test that the schema is valid YAML and parseable."""
        assert isinstance(schema, dict), "Schema must be a dictionary"
    
    def test_schema_version_present(self, schema):
        """Test that schema has a version field."""
        version_error = validate_schema_version(schema)
        assert version_error is None, version_error
    
    def test_required_fields_present(self, schema):
        """Test that all required fields are defined in the schema."""
        missing = validate_field_presence(schema)
        assert not missing, f"Missing required fields: {missing}"
    
    def test_required_fields_constraint(self, schema):
        """Test that required fields are listed in the 'required' array."""
        missing = validate_required_constraint(schema)
        assert not missing, f"Missing from 'required' array: {missing}"
    
    def test_field_types_correct(self, schema):
        """Test that field types match expected types."""
        mismatches = validate_field_types(schema)
        assert not mismatches, "Type mismatches found:\n" + "\n".join(mismatches)
    
    def test_stimulus_type_enum(self, schema):
        """Test that stimulus_type has valid enum constraints."""
        violations = validate_enum_constraints(schema)
        assert not violations, "Enum violations found:\n" + "\n".join(violations)
    
    def test_field_descriptions_present(self, schema):
        """Test that all fields have descriptions."""
        properties = schema.get("properties", {})
        missing_descriptions = []
        
        for field in REQUIRED_FIELDS:
            if field in properties:
                if not properties[field].get("description"):
                    missing_descriptions.append(field)
        
        assert not missing_descriptions, f"Fields missing descriptions: {missing_descriptions}"
    
    def test_age_range_constraint(self, schema):
        """Test that age field has appropriate range constraints."""
        properties = schema.get("properties", {})
        
        if "age" in properties:
            age_def = properties["age"]
            minimum = age_def.get("minimum")
            maximum = age_def.get("maximum")
            
            # At least one bound should be defined
            assert minimum is not None or maximum is not None, \
                "Age field should have at least one range constraint (minimum/maximum)"
            
            # If minimum is defined, it should be >= 0
            if minimum is not None:
                assert minimum >= 0, "Age minimum must be >= 0"
    
    def test_non_negative_constraints(self, schema):
        """Test that count fields have non-negative constraints."""
        properties = schema.get("properties", {})
        count_fields = ["perseverative_errors", "categories_completed"]
        
        for field in count_fields:
            if field in properties:
                minimum = properties[field].get("minimum")
                assert minimum is not None and minimum >= 0, \
                    f"Field '{field}' should have minimum >= 0"
    
    def test_sample_data_types_match_schema(self):
        """Test that sample data types match schema definitions."""
        errors = validate_data_types_in_sample(PROJECT_ROOT / "data" / "raw" / "raw_dataset.csv")
        assert not errors, "Data type mismatches in sample file:\n" + "\n".join(errors)
    
    def test_schema_completeness(self, schema):
        """
        Comprehensive test: verify schema meets all contract requirements.
        
        This test aggregates all validation checks into a single comprehensive
        validation to ensure the schema is production-ready.
        """
        all_errors = []
        
        # Check version
        version_error = validate_schema_version(schema)
        if version_error:
            all_errors.append(version_error)
        
        # Check required fields
        missing_fields = validate_field_presence(schema)
        if missing_fields:
            all_errors.append(f"Missing required fields: {missing_fields}")
        
        # Check required constraint
        missing_required = validate_required_constraint(schema)
        if missing_required:
            all_errors.append(f"Missing from 'required' array: {missing_required}")
        
        # Check types
        type_mismatches = validate_field_types(schema)
        if type_mismatches:
            all_errors.extend(type_mismatches)
        
        # Check enums
        enum_violations = validate_enum_constraints(schema)
        if enum_violations:
            all_errors.extend(enum_violations)
        
        assert not all_errors, "Schema validation failed with errors:\n" + "\n".join(all_errors)

if __name__ == "__main__":
    # Run tests manually if executed as script
    pytest.main([__file__, "-v"])