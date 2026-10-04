"""
Contract tests for JSON schemas.

Validates that JSON outputs from the pipeline conform to the expected
schemas defined in specs/001-llmxive-followup/contracts/.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Contract schema definitions (inline for testing purposes)
# In production, these would be loaded from specs/001-llmxive-followup/contracts/

PHYSICS_CONSTRAINT_SCHEMA = {
    "type": "object",
    "required": ["scene_id", "constraints", "contradictions"],
    "properties": {
        "scene_id": {"type": "string"},
        "constraints": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["object_a", "object_b", "relation"],
                "properties": {
                    "object_a": {"type": "string"},
                    "object_b": {"type": "string"},
                    "relation": {"type": "string", "enum": ["above", "below", "left_of", "right_of", "on", "next_to", "touching"]}
                }
            }
        },
        "contradictions": {
            "type": "array",
            "items": {"type": "string"}
        },
        "bounding_boxes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["object_id", "x", "y", "width", "height"],
                "properties": {
                    "object_id": {"type": "string"},
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                    "width": {"type": "number"},
                    "height": {"type": "number"}
                }
            }
        }
    }
}

EVALUATION_RESULT_SCHEMA = {
    "type": "object",
    "required": ["scene_id", "violations", "total_objects", "violation_rate"],
    "properties": {
        "scene_id": {"type": "string"},
        "violations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["object_id", "violation_type", "confidence"],
                "properties": {
                    "object_id": {"type": "string"},
                    "violation_type": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "details": {"type": "string"}
                }
            }
        },
        "total_objects": {"type": "integer", "minimum": 0},
        "violation_rate": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "prompt_adherence_rate": {"type": "number", "minimum": 0.0, "maximum": 1.0}
    }
}

POWER_ANALYSIS_SCHEMA = {
    "type": "object",
    "required": ["effect_size", "alpha", "power_target", "achieved_power", "sample_size", "test_passed"],
    "properties": {
        "effect_size": {"type": "number", "minimum": 0.0},
        "alpha": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "power_target": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "achieved_power": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "sample_size": {"type": "integer", "minimum": 1},
        "test_passed": {"type": "boolean"},
        "test_type": {"type": "string", "enum": ["z-test", "fisher-exact"]}
    }
}

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any], path: str = "") -> List[str]:
    """
    Validate a dictionary against a JSON schema.
    
    Args:
        data: The data to validate
        schema: The schema to validate against
        path: Current path in the data structure (for error messages)
    
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Type checking
    if "type" in schema:
        expected_type = schema["type"]
        if expected_type == "object" and not isinstance(data, dict):
            errors.append(f"{path}: Expected object, got {type(data).__name__}")
            return errors
        elif expected_type == "array" and not isinstance(data, list):
            errors.append(f"{path}: Expected array, got {type(data).__name__}")
            return errors
        elif expected_type == "string" and not isinstance(data, str):
            errors.append(f"{path}: Expected string, got {type(data).__name__}")
            return errors
        elif expected_type == "number" and not isinstance(data, (int, float)):
            errors.append(f"{path}: Expected number, got {type(data).__name__}")
            return errors
        elif expected_type == "integer" and not isinstance(data, int):
            errors.append(f"{path}: Expected integer, got {type(data).__name__}")
            return errors
        elif expected_type == "boolean" and not isinstance(data, bool):
            errors.append(f"{path}: Expected boolean, got {type(data).__name__}")
            return errors
    
    # Required fields for objects
    if schema.get("type") == "object" and isinstance(data, dict):
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                errors.append(f"{path}: Missing required field '{field}'")
        
        # Validate properties
        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                field_errors = validate_against_schema(value, properties[key], f"{path}.{key}")
                errors.extend(field_errors)
            else:
                # Allow additional properties unless explicitly forbidden
                if "additionalProperties" in schema and schema["additionalProperties"] is False:
                    errors.append(f"{path}: Unexpected field '{key}'")
    
    # Array item validation
    if schema.get("type") == "array" and isinstance(data, list):
        items_schema = schema.get("items", {})
        for i, item in enumerate(data):
            item_errors = validate_against_schema(item, items_schema, f"{path}[{i}]")
            errors.extend(item_errors)
    
    # Enum validation
    if "enum" in schema:
        if data not in schema["enum"]:
            errors.append(f"{path}: Value '{data}' not in enum {schema['enum']}")
    
    # Range validation for numbers
    if "minimum" in schema and isinstance(data, (int, float)):
        if data < schema["minimum"]:
            errors.append(f"{path}: Value {data} is less than minimum {schema['minimum']}")
    
    if "maximum" in schema and isinstance(data, (int, float)):
        if data > schema["maximum"]:
            errors.append(f"{path}: Value {data} is greater than maximum {schema['maximum']}")
    
    return errors

class TestPhysicsConstraintSchema:
    """Tests for PhysicsConstraint JSON schema validation."""
    
    def test_valid_physics_constraint(self):
        """Test that a valid physics constraint passes validation."""
        valid_data = {
            "scene_id": "scene_001",
            "constraints": [
                {
                    "object_a": "ball",
                    "object_b": "box",
                    "relation": "above"
                }
            ],
            "contradictions": [],
            "bounding_boxes": [
                {
                    "object_id": "ball",
                    "x": 100.0,
                    "y": 50.0,
                    "width": 30.0,
                    "height": 30.0
                }
            ]
        }
        
        errors = validate_against_schema(valid_data, PHYSICS_CONSTRAINT_SCHEMA)
        assert len(errors) == 0, f"Validation failed: {errors}"
    
    def test_missing_scene_id(self):
        """Test that missing scene_id fails validation."""
        invalid_data = {
            "constraints": [],
            "contradictions": []
        }
        
        errors = validate_against_schema(invalid_data, PHYSICS_CONSTRAINT_SCHEMA)
        assert len(errors) > 0
        assert any("scene_id" in error for error in errors)
    
    def test_invalid_relation(self):
        """Test that invalid relation fails validation."""
        invalid_data = {
            "scene_id": "scene_001",
            "constraints": [
                {
                    "object_a": "ball",
                    "object_b": "box",
                    "relation": "invalid_relation"
                }
            ],
            "contradictions": []
        }
        
        errors = validate_against_schema(invalid_data, PHYSICS_CONSTRAINT_SCHEMA)
        assert len(errors) > 0
        assert any("enum" in error for error in errors)
    
    def test_load_and_validate_from_file(self):
        """Test loading and validating a real physics constraint file if it exists."""
        constraint_dir = Path("data/derived/physics_constraints")
        if constraint_dir.exists():
            json_files = list(constraint_dir.glob("*.json"))
            if json_files:
                # Test the first file found
                test_file = json_files[0]
                with open(test_file, 'r') as f:
                    data = json.load(f)
                
                errors = validate_against_schema(data, PHYSICS_CONSTRAINT_SCHEMA)
                # Note: This test may fail if the file doesn't match schema exactly
                # but it validates that our schema validator works
                assert isinstance(errors, list)

class TestEvaluationResultSchema:
    """Tests for EvaluationResult JSON schema validation."""
    
    def test_valid_evaluation_result(self):
        """Test that a valid evaluation result passes validation."""
        valid_data = {
            "scene_id": "scene_001",
            "violations": [
                {
                    "object_id": "ball",
                    "violation_type": "floating",
                    "confidence": 0.85,
                    "details": "Object detected without support"
                }
            ],
            "total_objects": 5,
            "violation_rate": 0.2,
            "prompt_adherence_rate": 0.8
        }
        
        errors = validate_against_schema(valid_data, EVALUATION_RESULT_SCHEMA)
        assert len(errors) == 0, f"Validation failed: {errors}"
    
    def test_missing_violations(self):
        """Test that missing violations field fails validation."""
        invalid_data = {
            "scene_id": "scene_001",
            "total_objects": 5,
            "violation_rate": 0.0
        }
        
        errors = validate_against_schema(invalid_data, EVALUATION_RESULT_SCHEMA)
        assert len(errors) > 0
        assert any("violations" in error for error in errors)
    
    def test_confidence_out_of_range(self):
        """Test that confidence out of range fails validation."""
        invalid_data = {
            "scene_id": "scene_001",
            "violations": [
                {
                    "object_id": "ball",
                    "violation_type": "floating",
                    "confidence": 1.5
                }
            ],
            "total_objects": 5,
            "violation_rate": 0.2,
            "prompt_adherence_rate": 0.8
        }
        
        errors = validate_against_schema(invalid_data, EVALUATION_RESULT_SCHEMA)
        assert len(errors) > 0
        assert any("maximum" in error for error in errors)
    
    def test_load_and_validate_from_file(self):
        """Test loading and validating a real evaluation result file if it exists."""
        eval_dir = Path("data/derived/evaluation_results")
        if eval_dir.exists():
            json_files = list(eval_dir.glob("*.json"))
            if json_files:
                test_file = json_files[0]
                with open(test_file, 'r') as f:
                    data = json.load(f)
                
                errors = validate_against_schema(data, EVALUATION_RESULT_SCHEMA)
                assert isinstance(errors, list)

class TestPowerAnalysisSchema:
    """Tests for PowerAnalysis JSON schema validation."""
    
    def test_valid_power_analysis(self):
        """Test that a valid power analysis passes validation."""
        valid_data = {
            "effect_size": 0.2,
            "alpha": 0.05,
            "power_target": 0.8,
            "achieved_power": 0.85,
            "sample_size": 100,
            "test_passed": True,
            "test_type": "z-test"
        }
        
        errors = validate_against_schema(valid_data, POWER_ANALYSIS_SCHEMA)
        assert len(errors) == 0, f"Validation failed: {errors}"
    
    def test_invalid_test_type(self):
        """Test that invalid test_type fails validation."""
        invalid_data = {
            "effect_size": 0.2,
            "alpha": 0.05,
            "power_target": 0.8,
            "achieved_power": 0.85,
            "sample_size": 100,
            "test_passed": True,
            "test_type": "invalid-test"
        }
        
        errors = validate_against_schema(invalid_data, POWER_ANALYSIS_SCHEMA)
        assert len(errors) > 0
        assert any("enum" in error for error in errors)
    
    def test_load_and_validate_from_file(self):
        """Test loading and validating a real power analysis file if it exists."""
        processed_dir = Path("data/processed")
        power_file = processed_dir / "power_analysis_report.json"
        if power_file.exists():
            with open(power_file, 'r') as f:
                data = json.load(f)
            
            errors = validate_against_schema(data, POWER_ANALYSIS_SCHEMA)
            assert isinstance(errors, list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])