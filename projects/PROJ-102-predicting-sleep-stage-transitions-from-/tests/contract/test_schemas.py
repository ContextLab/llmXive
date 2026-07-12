import pytest
import json
from pathlib import Path
import sys
import os

# Add project root to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Schema definitions for Sleep-EDF data validation
# These define the expected structure for processed data artifacts

REQUIRED_FEATURE_SCHEMA = {
    "type": "object",
    "properties": {
        "feature_name": {"type": "string"},
        "value": {"type": "number"},
        "timestamp": {"type": "string", "format": "date-time"},
        "subject_id": {"type": "string"},
        "epoch_index": {"type": "integer"},
        "stage_from": {"type": "string"},
        "stage_to": {"type": "string"}
    },
    "required": ["feature_name", "value", "subject_id", "epoch_index"]
}

REQUIRED_METRICS_SCHEMA = {
    "type": "object",
    "properties": {
        "accuracy": {"type": "number"},
        "precision": {"type": "number"},
        "recall": {"type": "number"},
        "f1_score": {"type": "number"},
        "model_params": {"type": "integer", "minimum": 0},
        "validation_method": {"type": "string"},
        "training_subjects": {"type": "array", "items": {"type": "string"}},
        "test_subjects": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["accuracy", "model_params", "validation_method"]
}

REQUIRED_WINDOW_SCHEMA = {
    "type": "object",
    "properties": {
        "subject_id": {"type": "string"},
        "window_type": {"type": "string", "enum": ["stable", "transition", "pre_transition"]},
        "start_time": {"type": "number"},
        "duration": {"type": "number"},
        "stage_label": {"type": "string"},
        "signal_data": {"type": "array", "items": {"type": "number"}},
        "channel": {"type": "string"}
    },
    "required": ["subject_id", "window_type", "start_time", "duration", "channel"]
}

def validate_json_schema(data, schema, name="data"):
    """
    Simple JSON schema validator (subset).
    Checks types and required fields.
    Returns a list of error strings.
    """
    errors = []
    
    if schema.get("type") == "object":
        if not isinstance(data, dict):
            errors.append(f"{name} is not an object")
            return errors
        
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field} in {name}")
        
        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                prop_schema = properties[key]
                expected_type = prop_schema.get("type")
                
                if expected_type == "string":
                    if not isinstance(value, str):
                        errors.append(f"Field {key} should be string, got {type(value).__name__}")
                elif expected_type == "number":
                    if not isinstance(value, (int, float)):
                        errors.append(f"Field {key} should be number, got {type(value).__name__}")
                elif expected_type == "integer":
                    if not isinstance(value, int):
                        errors.append(f"Field {key} should be integer, got {type(value).__name__}")
                elif expected_type == "array":
                    if not isinstance(value, list):
                        errors.append(f"Field {key} should be array, got {type(value).__name__}")
                    elif "items" in prop_schema:
                        item_schema = prop_schema["items"]
                        if item_schema.get("type") == "string":
                            for i, item in enumerate(value):
                                if not isinstance(item, str):
                                    errors.append(f"Field {key}[{i}] should be string, got {type(item).__name__}")
                        elif item_schema.get("type") == "number":
                            for i, item in enumerate(value):
                                if not isinstance(item, (int, float)):
                                    errors.append(f"Field {key}[{i}] should be number, got {type(item).__name__}")
                
                # Check enum constraints if present
                if "enum" in prop_schema and value not in prop_schema["enum"]:
                    errors.append(f"Field {key} must be one of {prop_schema['enum']}, got {value}")
    
    return errors

def validate_file_content(file_path, schema, name="file"):
    """
    Load a JSON file and validate it against a schema.
    Returns a tuple (is_valid, errors).
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        errors = validate_json_schema(data, schema, name)
        return len(errors) == 0, errors
    except FileNotFoundError:
        return False, [f"File not found: {file_path}"]
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in {file_path}: {str(e)}"]

class TestSchemas:
    @pytest.fixture
    def sample_feature_data(self):
        return {
            "feature_name": "delta_power",
            "value": 12.5,
            "subject_id": "ST001",
            "timestamp": "2023-10-01T12:00:00Z",
            "epoch_index": 42,
            "stage_from": "W",
            "stage_to": "N1"
        }

    @pytest.fixture
    def sample_metrics_data(self):
        return {
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85,
            "model_params": 50000,
            "validation_method": "LOSO",
            "training_subjects": ["ST001", "ST002"],
            "test_subjects": ["ST003"]
        }

    @pytest.fixture
    def sample_window_data(self):
        return {
            "subject_id": "ST001",
            "window_type": "pre_transition",
            "start_time": 1200.0,
            "duration": 60.0,
            "stage_label": "N2",
            "signal_data": [0.1, 0.2, 0.3, 0.4, 0.5],
            "channel": "Fp1"
        }

    def test_valid_feature_schema(self, sample_feature_data):
        errors = validate_json_schema(sample_feature_data, REQUIRED_FEATURE_SCHEMA, "feature")
        assert len(errors) == 0, f"Schema validation failed: {errors}"

    def test_missing_required_field_feature(self):
        data = {"feature_name": "delta_power", "value": 12.5}
        errors = validate_json_schema(data, REQUIRED_FEATURE_SCHEMA, "feature")
        assert len(errors) > 0
        assert any("subject_id" in e for e in errors)
        assert any("epoch_index" in e for e in errors)

    def test_valid_metrics_schema(self, sample_metrics_data):
        errors = validate_json_schema(sample_metrics_data, REQUIRED_METRICS_SCHEMA, "metrics")
        assert len(errors) == 0, f"Schema validation failed: {errors}"

    def test_invalid_type_metrics(self):
        data = {
            "accuracy": "high", # Should be number
            "model_params": 50000,
            "validation_method": "LOSO"
        }
        errors = validate_json_schema(data, REQUIRED_METRICS_SCHEMA, "metrics")
        assert len(errors) > 0
        assert any("accuracy" in e for e in errors)

    def test_valid_window_schema(self, sample_window_data):
        errors = validate_json_schema(sample_window_data, REQUIRED_WINDOW_SCHEMA, "window")
        assert len(errors) == 0, f"Schema validation failed: {errors}"

    def test_invalid_window_type(self):
        data = {
            "subject_id": "ST001",
            "window_type": "invalid_type",
            "start_time": 1200.0,
            "duration": 60.0,
            "channel": "Fp1"
        }
        errors = validate_json_schema(data, REQUIRED_WINDOW_SCHEMA, "window")
        assert len(errors) > 0
        assert any("must be one of" in e for e in errors)

    def test_file_validation_logic(self, tmp_path):
        """Test that the validator can check actual files if they exist."""
        # Create a valid feature file
        valid_file = tmp_path / "valid_features.json"
        with open(valid_file, "w") as f:
            json.dump({
                "feature_name": "test", 
                "value": 1.0, 
                "subject_id": "S1", 
                "epoch_index": 1
            }, f)
        
        is_valid, errors = validate_file_content(valid_file, REQUIRED_FEATURE_SCHEMA, "test_file")
        assert is_valid
        assert len(errors) == 0

    def test_file_validation_missing_field(self, tmp_path):
        """Test file validation with missing required field."""
        invalid_file = tmp_path / "invalid_features.json"
        with open(invalid_file, "w") as f:
            json.dump({
                "feature_name": "test", 
                "value": 1.0
                # Missing subject_id and epoch_index
            }, f)
        
        is_valid, errors = validate_file_content(invalid_file, REQUIRED_FEATURE_SCHEMA, "test_file")
        assert not is_valid
        assert len(errors) == 2
        assert any("subject_id" in e for e in errors)
        assert any("epoch_index" in e for e in errors)

    def test_file_not_found(self, tmp_path):
        """Test validation of non-existent file."""
        is_valid, errors = validate_file_content(
            tmp_path / "non_existent.json", 
            REQUIRED_FEATURE_SCHEMA, 
            "test_file"
        )
        assert not is_valid
        assert len(errors) == 1
        assert "File not found" in errors[0]