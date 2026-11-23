"""
code/contracts/validator.py

Schema validation logic for synthetic images and regression results.
"""

import json
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator
import os

# Schema definitions (embedded for portability, or loaded from files if available)
SYNTHETIC_IMAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "image_id": {"type": "string"},
        "region_count": {"type": "integer"},
        "bounding_boxes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                    "w": {"type": "number"},
                    "h": {"type": "number"},
                    "id": {"type": "integer"}
                },
                "required": ["x", "y", "w", "h", "id"]
            }
        },
        "derived_relations": {
            "type": "array",
            "items": {"type": "string"}
        },
        "metadata": {"type": "object"}
    },
    "required": ["image_id", "region_count", "bounding_boxes", "derived_relations"]
}

REGRESSION_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "region_count": {"type": "integer"},
        "parallel_score": {"type": "number"},
        "sequential_score": {"type": "number"},
        "inference_time": {"type": "number"},
        "corrected_p_value": {"type": "number"},
        "is_significant": {"type": "boolean"}
    },
    "required": ["region_count", "parallel_score", "sequential_score", "inference_time", "corrected_p_value", "is_significant"]
}

def load_schema(schema_name: str) -> dict:
    """Load a schema by name."""
    if schema_name == "synthetic_image":
        return SYNTHETIC_IMAGE_SCHEMA
    elif schema_name == "regression_result":
        return REGRESSION_RESULT_SCHEMA
    else:
        raise ValueError(f"Unknown schema: {schema_name}")

def validate_synthetic_image(data: dict) -> bool:
    """Validate data against synthetic image schema."""
    try:
        validate(instance=data, schema=SYNTHETIC_IMAGE_SCHEMA)
        return True
    except ValidationError as e:
        print(f"Validation error: {e.message}")
        return False

def validate_regression_result(data: dict) -> bool:
    """Validate data against regression result schema."""
    try:
        validate(instance=data, schema=REGRESSION_RESULT_SCHEMA)
        return True
    except ValidationError as e:
        print(f"Validation error: {e.message}")
        return False

def validate_file(file_path: str, schema_name: str) -> bool:
    """Validate a JSON file against a schema."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return validate_synthetic_image(data) if schema_name == "synthetic_image" else validate_regression_result(data)

def main():
    """Test validator."""
    test_data = {
        "image_id": "test_01",
        "region_count": 25,
        "bounding_boxes": [{"x": 0, "y": 0, "w": 10, "h": 10, "id": 0}],
        "derived_relations": []
    }
    print(f"Valid: {validate_synthetic_image(test_data)}")

if __name__ == "__main__":
    main()
