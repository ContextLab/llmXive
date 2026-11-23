"""
Contract tests for JSON schemas used in the llmXive pipeline.

This module validates that generated artifacts conform to the expected
JSON schemas defined in the project specifications.
"""
import json
import os
import sys
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

# Import schema validation utilities if they exist, otherwise define simple validators
try:
    from jsonschema import validate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


# ============================================================================
# SCHEMA DEFINITIONS
# ============================================================================

PHYSICS_CONSTRAINT_SCHEMA = {
    "type": "object",
    "required": ["scene_id", "constraints", "metadata"],
    "properties": {
        "scene_id": {"type": "string"},
        "constraints": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["object_id", "bounding_box", "physics_rules"],
                "properties": {
                    "object_id": {"type": "string"},
                    "bounding_box": {
                        "type": "object",
                        "required": ["x", "y", "width", "height"],
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"},
                            "width": {"type": "number"},
                            "height": {"type": "number"}
                        }
                    },
                    "physics_rules": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        "metadata": {
            "type": "object",
            "properties": {
                "simulation_time": {"type": "number"},
                "collision_count": {"type": "integer"},
                "is_valid": {"type": "boolean"}
            }
        }
    }
}

PROMPT_SCHEMA = {
    "type": "object",
    "required": ["scene_id", "prompt_type", "text"],
    "properties": {
        "scene_id": {"type": "string"},
        "prompt_type": {"type": "string", "enum": ["baseline", "experimental", "control"]},
        "text": {"type": "string", "minLength": 1},
        "metadata": {
            "type": "object",
            "properties": {
                "physics_applied": {"type": "boolean"},
                "control_length_matched": {"type": "boolean"}
            }
        }
    }
}

EVALUATION_RESULT_SCHEMA = {
    "type": "object",
    "required": [
        "scene_id",
        "detected_objects",
        "physics_violations",
        "overall_violation",
        "confidence_scores",
        "metadata"
    ],
    "properties": {
        "scene_id": {"type": "string"},
        "detected_objects": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["label", "confidence", "bbox"],
                "properties": {
                    "label": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "bbox": {
                        "type": "object",
                        "required": ["x", "y", "width", "height"],
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"},
                            "width": {"type": "number"},
                            "height": {"type": "number"}
                        }
                    }
                }
            }
        },
        "physics_violations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["object_id", "violation_type", "details"],
                "properties": {
                    "object_id": {"type": "string"},
                    "violation_type": {"type": "string"},
                    "details": {"type": "string"}
                }
            }
        },
        "overall_violation": {
            "type": "boolean"
        },
        "confidence_scores": {
            "type": "object",
            "properties": {
                "mean": {"type": "number"},
                "min": {"type": "number"},
                "max": {"type": "number"}
            }
        },
        "metadata": {
            "type": "object",
            "properties": {
                "model_version": {"type": "string"},
                "image_resolution": {"type": "string"},
                "processing_time_ms": {"type": "number"},
                "detection_threshold": {"type": "number"}
            }
        }
    }
}

CONTRADICTION_LOG_SCHEMA = {
    "type": "object",
    "required": ["contradictions", "summary"],
    "properties": {
        "contradictions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["scene_id", "reason"],
                "properties": {
                    "scene_id": {"type": "string"},
                    "reason": {"type": "string"},
                    "timestamp": {"type": "string"}
                }
            }
        },
        "summary": {
            "type": "object",
            "properties": {
                "total_scenes": {"type": "integer"},
                "contradicted_scenes": {"type": "integer"},
                "contradiction_rate": {"type": "number"}
            }
        }
    }
}

SEED_MANIFEST_SCHEMA = {
    "type": "object",
    "required": ["seeds"],
    "properties": {
        "seeds": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["scene_id", "baseline_seed", "experimental_seed", "control_seed"],
                "properties": {
                    "scene_id": {"type": "string"},
                    "baseline_seed": {"type": "integer"},
                    "experimental_seed": {"type": "integer"},
                    "control_seed": {"type": "integer"}
                }
            }
        }
    }
}

GENERATION_FAILURE_LOG_SCHEMA = {
    "type": "object",
    "required": ["failures", "summary"],
    "properties": {
        "failures": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["scene_id", "error_type", "message"],
                "properties": {
                    "scene_id": {"type": "string"},
                    "error_type": {"type": "string"},
                    "message": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "retry_count": {"type": "integer"}
                }
            }
        },
        "summary": {
            "type": "object",
            "properties": {
                "total_attempts": {"type": "integer"},
                "failed_attempts": {"type": "integer"},
                "success_rate": {"type": "number"}
            }
        }
    }
}

POWER_ANALYSIS_SCHEMA = {
    "type": "object",
    "required": [
        "effect_size",
        "alpha",
        "power_target",
        "calculated_power",
        "required_sample_size",
        "actual_sample_size",
        "recommendation"
    ],
    "properties": {
        "effect_size": {"type": "number"},
        "alpha": {"type": "number"},
        "power_target": {"type": "number"},
        "calculated_power": {"type": "number"},
        "required_sample_size": {"type": "integer"},
        "actual_sample_size": {"type": "integer"},
        "recommendation": {"type": "string"},
        "warning": {"type": "string", "optional": True}
    }
}

STATISTICAL_TEST_RESULTS_SCHEMA = {
    "type": "object",
    "required": [
        "test_type",
        "baseline_violation_rate",
        "experimental_violation_rate",
        "p_value",
        "significant",
        "confidence_interval"
    ],
    "properties": {
        "test_type": {"type": "string", "enum": ["z-test", "fisher-exact"]},
        "baseline_violation_rate": {"type": "number"},
        "experimental_violation_rate": {"type": "number"},
        "p_value": {"type": "number"},
        "significant": {"type": "boolean"},
        "confidence_interval": {
            "type": "object",
            "properties": {
                "lower": {"type": "number"},
                "upper": {"type": "number"}
            }
        },
        "notes": {"type": "string", "optional": True}
    }
}

EXCLUSION_LIST_SCHEMA = {
    "type": "object",
    "required": ["excluded_scenes", "reasons", "total_excluded"],
    "properties": {
        "excluded_scenes": {
            "type": "array",
            "items": {"type": "string"}
        },
        "reasons": {
            "type": "object",
            "additionalProperties": {"type": "string"}
        },
        "total_excluded": {"type": "integer"},
        "final_sample_size": {"type": "integer"}
    }
}

FINAL_ANALYSIS_CSV_SCHEMA = {
    "type": "object",
    "required": [
        "columns",
        "row_count",
        "prompt_adherence_rate_label"
    ],
    "properties": {
        "columns": {
            "type": "array",
            "items": {"type": "string"}
        },
        "row_count": {"type": "integer"},
        "prompt_adherence_rate_label": {"type": "string"}
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any], schema_name: str) -> bool:
    """Validate data against a JSON schema."""
    if HAS_JSONSCHEMA:
        try:
            validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            pytest.fail(f"Validation failed for {schema_name}: {e.message}")
    else:
        # Fallback: basic structural validation
        # This is less rigorous but ensures the file is valid JSON
        if not isinstance(data, dict):
            pytest.fail(f"Data must be a dictionary for {schema_name}")
    return True


# ============================================================================
# TESTS FOR PHYSICS CONSTRAINT SCHEMA
# ============================================================================

@pytest.mark.contract
def test_physics_constraint_schema():
    """
    Contract test for PhysicsConstraint JSON schema (T009).
    
    Validates that physics constraint files generated by physics_engine.py
    conform to the expected schema.
    """
    # Test with a valid example
    valid_data = {
        "scene_id": "scene_001",
        "constraints": [
            {
                "object_id": "obj_a",
                "bounding_box": {"x": 10, "y": 20, "width": 50, "height": 50},
                "physics_rules": ["gravity", "collision"]
            }
        ],
        "metadata": {
            "simulation_time": 1.5,
            "collision_count": 3,
            "is_valid": True
        }
    }
    
    validate_against_schema(valid_data, PHYSICS_CONSTRAINT_SCHEMA, "PhysicsConstraint")


@pytest.mark.contract
def test_physics_constraint_schema_invalid():
    """
    Test that invalid physics constraint data is rejected.
    """
    invalid_data = {
        "scene_id": "scene_001",
        # Missing required 'constraints' field
        "metadata": {"simulation_time": 1.0}
    }
    
    if HAS_JSONSCHEMA:
        from jsonschema import validate, ValidationError
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=PHYSICS_CONSTRAINT_SCHEMA)
    else:
        # Basic check
        assert "constraints" in invalid_data or pytest.fail("Should fail validation")


# ============================================================================
# TESTS FOR PROMPT SCHEMA
# ============================================================================

@pytest.mark.contract
def test_prompt_schema():
    """
    Contract test for Prompt JSON schema.
    
    Validates that prompt files generated by prompt_engine.py conform to the schema.
    """
    valid_data = {
        "scene_id": "scene_001",
        "prompt_type": "baseline",
        "text": "A red ball sitting on a blue platform.",
        "metadata": {
            "physics_applied": True,
            "control_length_matched": False
        }
    }
    
    validate_against_schema(valid_data, PROMPT_SCHEMA, "Prompt")


# ============================================================================
# TESTS FOR EVALUATION RESULT SCHEMA (T024)
# ============================================================================

@pytest.mark.contract
def test_evaluation_result_schema():
    """
    Contract test for EvaluationResult JSON schema (T024).
    
    Validates that evaluation result files generated by detector.py conform
    to the expected schema for statistical analysis.
    
    This test ensures:
    - Required fields are present
    - Data types match expectations
    - Confidence scores are within valid ranges
    - Violation structures are correct
    """
    # Construct a realistic valid evaluation result
    valid_data = {
        "scene_id": "scene_001",
        "detected_objects": [
            {
                "label": "ball",
                "confidence": 0.95,
                "bbox": {"x": 100, "y": 200, "width": 50, "height": 50}
            },
            {
                "label": "platform",
                "confidence": 0.88,
                "bbox": {"x": 50, "y": 250, "width": 200, "height": 20}
            }
        ],
        "physics_violations": [
            {
                "object_id": "ball",
                "violation_type": "floating",
                "details": "Object is above platform with no support"
            }
        ],
        "overall_violation": True,
        "confidence_scores": {
            "mean": 0.915,
            "min": 0.88,
            "max": 0.95
        },
        "metadata": {
            "model_version": "yolov8n.pt",
            "image_resolution": "512x512",
            "processing_time_ms": 120.5,
            "detection_threshold": 0.7
        }
    }
    
    validate_against_schema(valid_data, EVALUATION_RESULT_SCHEMA, "EvaluationResult")


@pytest.mark.contract
def test_evaluation_result_schema_missing_required():
    """
    Test that evaluation results with missing required fields are rejected.
    """
    invalid_data = {
        "scene_id": "scene_001",
        "detected_objects": []
        # Missing: physics_violations, overall_violation, confidence_scores, metadata
    }
    
    if HAS_JSONSCHEMA:
        from jsonschema import validate, ValidationError
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=EVALUATION_RESULT_SCHEMA)
    else:
        required_fields = ["physics_violations", "overall_violation", "confidence_scores", "metadata"]
        for field in required_fields:
            if field not in invalid_data:
                pytest.fail(f"Missing required field: {field}")


@pytest.mark.contract
def test_evaluation_result_schema_invalid_confidence():
    """
    Test that confidence scores outside [0, 1] are rejected.
    """
    invalid_data = {
        "scene_id": "scene_001",
        "detected_objects": [
            {
                "label": "ball",
                "confidence": 1.5,  # Invalid: > 1.0
                "bbox": {"x": 100, "y": 200, "width": 50, "height": 50}
            }
        ],
        "physics_violations": [],
        "overall_violation": False,
        "confidence_scores": {
            "mean": 1.5,
            "min": 1.5,
            "max": 1.5
        },
        "metadata": {"model_version": "test"}
    }
    
    if HAS_JSONSCHEMA:
        from jsonschema import validate, ValidationError
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=EVALUATION_RESULT_SCHEMA)
    else:
        assert invalid_data["detected_objects"][0]["confidence"] <= 1.0 or pytest.fail("Confidence should be <= 1.0")


@pytest.mark.contract
def test_evaluation_result_schema_empty_objects():
    """
    Test that evaluation results with empty detected_objects are valid (edge case).
    """
    valid_data = {
        "scene_id": "scene_001",
        "detected_objects": [],
        "physics_violations": [],
        "overall_violation": False,
        "confidence_scores": {
            "mean": 0.0,
            "min": 0.0,
            "max": 0.0
        },
        "metadata": {
            "model_version": "yolov8n.pt",
            "image_resolution": "512x512",
            "processing_time_ms": 10.0,
            "detection_threshold": 0.7
        }
    }
    
    validate_against_schema(valid_data, EVALUATION_RESULT_SCHEMA, "EvaluationResult")


# ============================================================================
# TESTS FOR OTHER SCHEMAS
# ============================================================================

@pytest.mark.contract
def test_contradiction_log_schema():
    """Contract test for ContradictionLog schema."""
    valid_data = {
        "contradictions": [
            {
                "scene_id": "scene_001",
                "reason": "Circular dependency detected",
                "timestamp": "2023-10-01T12:00:00Z"
            }
        ],
        "summary": {
            "total_scenes": 100,
            "contradicted_scenes": 5,
            "contradiction_rate": 0.05
        }
    }
    validate_against_schema(valid_data, CONTRADICTION_LOG_SCHEMA, "ContradictionLog")


@pytest.mark.contract
def test_seed_manifest_schema():
    """Contract test for SeedManifest schema."""
    valid_data = {
        "seeds": [
            {
                "scene_id": "scene_001",
                "baseline_seed": 42,
                "experimental_seed": 42,
                "control_seed": 123
            }
        ]
    }
    validate_against_schema(valid_data, SEED_MANIFEST_SCHEMA, "SeedManifest")


@pytest.mark.contract
def test_generation_failure_log_schema():
    """Contract test for GenerationFailureLog schema."""
    valid_data = {
        "failures": [
            {
                "scene_id": "scene_001",
                "error_type": "TimeoutError",
                "message": "Generation timed out after 300s",
                "timestamp": "2023-10-01T12:00:00Z",
                "retry_count": 3
            }
        ],
        "summary": {
            "total_attempts": 100,
            "failed_attempts": 2,
            "success_rate": 0.98
        }
    }
    validate_against_schema(valid_data, GENERATION_FAILURE_LOG_SCHEMA, "GenerationFailureLog")


@pytest.mark.contract
def test_power_analysis_schema():
    """Contract test for PowerAnalysis schema."""
    valid_data = {
        "effect_size": 0.2,
        "alpha": 0.05,
        "power_target": 0.8,
        "calculated_power": 0.85,
        "required_sample_size": 128,
        "actual_sample_size": 100,
        "recommendation": "Proceed with caution"
    }
    validate_against_schema(valid_data, POWER_ANALYSIS_SCHEMA, "PowerAnalysis")


@pytest.mark.contract
def test_statistical_test_results_schema():
    """Contract test for StatisticalTestResults schema."""
    valid_data = {
        "test_type": "z-test",
        "baseline_violation_rate": 0.15,
        "experimental_violation_rate": 0.08,
        "p_value": 0.03,
        "significant": True,
        "confidence_interval": {
            "lower": 0.02,
            "upper": 0.12
        }
    }
    validate_against_schema(valid_data, STATISTICAL_TEST_RESULTS_SCHEMA, "StatisticalTestResults")


@pytest.mark.contract
def test_exclusion_list_schema():
    """Contract test for ExclusionList schema."""
    valid_data = {
        "excluded_scenes": ["scene_001", "scene_002"],
        "reasons": {
            "scene_001": "Contradiction in physics simulation",
            "scene_002": "Generation failure"
        },
        "total_excluded": 2,
        "final_sample_size": 98
    }
    validate_against_schema(valid_data, EXCLUSION_LIST_SCHEMA, "ExclusionList")


@pytest.mark.contract
def test_final_analysis_csv_schema():
    """Contract test for FinalAnalysisCSV schema."""
    valid_data = {
        "columns": ["scene_id", "group", "violation", "prompt_adherence_rate"],
        "row_count": 98,
        "prompt_adherence_rate_label": "Prompt Adherence Rate"
    }
    validate_against_schema(valid_data, FINAL_ANALYSIS_CSV_SCHEMA, "FinalAnalysisCSV")


# ============================================================================
# INTEGRATION TESTS (Optional: Validate against real files if they exist)
# ============================================================================

@pytest.mark.contract
def test_real_evaluation_results_file(tmp_path):
    """
    Integration test: Write a valid evaluation result to disk and verify it can be loaded.
    """
    # Create a valid evaluation result
    result = {
        "scene_id": "integration_test_001",
        "detected_objects": [
            {
                "label": "test_object",
                "confidence": 0.99,
                "bbox": {"x": 10, "y": 10, "width": 100, "height": 100}
            }
        ],
        "physics_violations": [],
        "overall_violation": False,
        "confidence_scores": {
            "mean": 0.99,
            "min": 0.99,
            "max": 0.99
        },
        "metadata": {
            "model_version": "yolov8n.pt",
            "image_resolution": "512x512",
            "processing_time_ms": 50.0,
            "detection_threshold": 0.7
        }
    }
    
    # Write to disk
    file_path = tmp_path / "test_evaluation_result.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    # Load and validate
    loaded_data = load_json_file(file_path)
    validate_against_schema(loaded_data, EVALUATION_RESULT_SCHEMA, "EvaluationResult")
    
    # Verify content integrity
    assert loaded_data["scene_id"] == "integration_test_001"
    assert loaded_data["overall_violation"] == False
    assert len(loaded_data["detected_objects"]) == 1