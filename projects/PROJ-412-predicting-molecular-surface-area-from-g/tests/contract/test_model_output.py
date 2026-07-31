"""
Contract test for model output schema.
Validates model output artifacts against data/schemas/model_schema.yaml.
"""
import os
import sys
import json
import yaml
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "data" / "schemas" / "model_schema.yaml"


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_type(value: Any, expected_type: str, field_path: str) -> List[str]:
    """Validate a value against an expected type definition."""
    errors = []
    
    type_map = {
        'string': str,
        'number': (int, float),
        'integer': int,
        'boolean': bool,
        'object': dict,
        'array': list
    }
    
    if expected_type not in type_map:
        errors.append(f"Unknown type '{expected_type}' at {field_path}")
        return errors
    
    expected_python_type = type_map[expected_type]
    if not isinstance(value, expected_python_type):
        errors.append(f"Type mismatch at {field_path}: expected {expected_type}, got {type(value).__name__}")
    
    return errors


def validate_enum(value: Any, allowed_values: List[Any], field_path: str) -> List[str]:
    """Validate a value against an enum definition."""
    errors = []
    if value not in allowed_values:
        errors.append(f"Value '{value}' at {field_path} not in allowed values: {allowed_values}")
    return errors


def validate_required_fields(data: Dict[str, Any], required_fields: List[str], parent_path: str = "") -> List[str]:
    """Validate that all required fields are present."""
    errors = []
    for field in required_fields:
        field_path = f"{parent_path}.{field}" if parent_path else field
        if field not in data:
            errors.append(f"Missing required field: {field_path}")
    return errors


def validate_properties(
    data: Dict[str, Any], 
    properties: Dict[str, Any], 
    parent_path: str = "",
    additional_properties_allowed: bool = True
) -> List[str]:
    """Validate data against property definitions."""
    errors = []
    
    for field, definition in properties.items():
        if field not in data:
            continue  # Missing non-required field is okay
        
        field_path = f"{parent_path}.{field}" if parent_path else field
        value = data[field]
        
        # Check type
        if 'type' in definition:
            errors.extend(validate_type(value, definition['type'], field_path))
            
            # Check enum if present
            if definition['type'] == 'string' and 'enum' in definition:
                errors.extend(validate_enum(value, definition['enum'], field_path))
        
        # Recurse into nested objects
        if definition.get('type') == 'object':
            # Check required fields in nested object
            if 'required' in definition:
                errors.extend(validate_required_fields(value, definition['required'], field_path))
            
            # Validate nested properties
            if 'properties' in definition:
                nested_additional = definition.get('additionalProperties', True)
                errors.extend(validate_properties(value, definition['properties'], field_path, nested_additional))
            
            # Check for additional properties if not allowed
            if not nested_additional:
                allowed_keys = set(definition['properties'].keys())
                for key in value.keys():
                    if key not in allowed_keys:
                        errors.append(f"Additional property '{key}' not allowed at {field_path}")
        
        # Validate array items if type is array
        if definition.get('type') == 'array' and 'items' in definition:
            if isinstance(value, list):
                item_type = definition['items'].get('type')
                if item_type:
                    for idx, item in enumerate(value):
                        errors.extend(validate_type(item, item_type, f"{field_path}[{idx}]"))
    
    # Check for additional properties at this level
    if not additional_properties_allowed:
        allowed_keys = set(properties.keys())
        for key in data.keys():
            if key not in allowed_keys:
                errors.append(f"Additional property '{key}' not allowed at {parent_path if parent_path else 'root'}")
    
    return errors


def validate_model_output(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate model output data against schema."""
    errors = []
    
    # Validate top-level type
    if schema.get('type') == 'object':
        if not isinstance(data, dict):
            errors.append("Root must be an object")
            return errors
        
        # Check required fields
        if 'required' in schema:
            errors.extend(validate_required_fields(data, schema['required']))
        
        # Validate properties
        if 'properties' in schema:
            additional_allowed = schema.get('additionalProperties', True)
            errors.extend(validate_properties(data, schema['properties'], "", additional_allowed))
    
    return errors


def validate_timestamp_format(timestamp: str) -> bool:
    """Validate ISO 8601 timestamp format."""
    try:
        # Try parsing common ISO 8601 formats
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return True
    except (ValueError, AttributeError):
        return False


class TestModelOutputSchema:
    """Contract tests for model output schema validation."""
    
    @pytest.fixture
    def schema(self) -> Dict[str, Any]:
        """Load the model output schema."""
        return load_schema(SCHEMA_PATH)
    
    @pytest.fixture
    def valid_model_output(self) -> Dict[str, Any]:
        """Generate a valid model output sample."""
        return {
            "model_type": "GCN",
            "metrics": {
                "mae": 12.45,
                "rmse": 15.23,
                "r2": 0.85,
                "comparison": {
                    "p_value": 0.001,
                    "cohen_d": 0.8,
                    "corrected_p_value": 0.003,
                    "normality_warning": False
                }
            },
            "hyperparameters": {
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 50,
                "hidden_channels": 128,
                "dropout": 0.1,
                "num_layers": 3
            },
            "timestamp": "2024-01-15T10:30:00Z",
            "dataset_checksum": "abc123def456789",
            "split_info": {
                "train_size": 800,
                "test_size": 200,
                "split_seed": 42,
                "stratification_field": "molecular_weight"
            },
            "runtime_info": {
                "total_seconds": 3600.5,
                "peak_memory_mb": 1024.0
            }
        }
    
    @pytest.fixture
    def valid_geometry_baseline_output(self) -> Dict[str, Any]:
        """Generate a valid GeometryOracle model output sample."""
        return {
            "model_type": "GeometryOracle",
            "metrics": {
                "mae": 10.2,
                "rmse": 13.1,
                "r2": 0.90
            },
            "hyperparameters": {
                "alpha": 0.0001,
                "max_iter": 1000
            },
            "timestamp": "2024-01-15T11:00:00Z",
            "dataset_checksum": "xyz789abc123456"
        }
    
    def test_schema_loads_successfully(self, schema):
        """Test that the schema file loads without errors."""
        assert schema is not None
        assert 'properties' in schema
        assert 'required' in schema
    
    def test_valid_gcn_output_passes(self, schema, valid_model_output):
        """Test that a valid GCN model output passes validation."""
        errors = validate_model_output(valid_model_output, schema)
        assert len(errors) == 0, f"Validation failed with errors: {errors}"
    
    def test_valid_geometry_baseline_output_passes(self, schema, valid_geometry_baseline_output):
        """Test that a valid GeometryOracle model output passes validation."""
        errors = validate_model_output(valid_geometry_baseline_output, schema)
        assert len(errors) == 0, f"Validation failed with errors: {errors}"
    
    def test_missing_required_field_fails(self, schema, valid_model_output):
        """Test that missing a required field causes validation failure."""
        del valid_model_output['model_type']
        errors = validate_model_output(valid_model_output, schema)
        assert any('model_type' in err for err in errors)
    
    def test_invalid_model_type_enum_fails(self, schema, valid_model_output):
        """Test that an invalid model_type enum value causes validation failure."""
        valid_model_output['model_type'] = "InvalidModelType"
        errors = validate_model_output(valid_model_output, schema)
        assert any('model_type' in err for err in errors)
    
    def test_invalid_timestamp_format_fails(self, schema, valid_model_output):
        """Test that an invalid timestamp format causes validation failure."""
        valid_model_output['timestamp'] = "not-a-date"
        errors = validate_model_output(valid_model_output, schema)
        assert any('timestamp' in err for err in errors)
    
    def test_missing_metrics_fields_fails(self, schema, valid_model_output):
        """Test that missing required metric fields cause validation failure."""
        del valid_model_output['metrics']['mae']
        errors = validate_model_output(valid_model_output, schema)
        assert any('mae' in err for err in errors)
    
    def test_wrong_type_for_mae_fails(self, schema, valid_model_output):
        """Test that wrong type for mae causes validation failure."""
        valid_model_output['metrics']['mae'] = "not_a_number"
        errors = validate_model_output(valid_model_output, schema)
        assert any('mae' in err for err in errors)
    
    def test_all_enum_values_valid(self, schema):
        """Test that all enum values in model_type are valid."""
        model_type_def = schema['properties']['model_type']
        enum_values = model_type_def['enum']
        expected_values = ["GCN", "GeometryOracle", "RandomForest", "Baseline3D"]
        assert set(enum_values) == set(expected_values)
    
    def test_real_artifact_validation(self, schema):
        """Test validation against a real model output file if it exists."""
        # Look for model output files in results directory
        results_dir = PROJECT_ROOT / "results"
        model_output_files = list(results_dir.rglob("*.json"))
        
        if not model_output_files:
            pytest.skip("No model output files found to validate")
        
        for file_path in model_output_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                errors = validate_model_output(data, schema)
                # Only assert on files that look like model outputs (have model_type)
                if 'model_type' in data:
                    assert len(errors) == 0, f"File {file_path} failed validation: {errors}"
            except json.JSONDecodeError:
                continue  # Skip non-JSON files


if __name__ == "__main__":
    pytest.main([__file__, "-v"])