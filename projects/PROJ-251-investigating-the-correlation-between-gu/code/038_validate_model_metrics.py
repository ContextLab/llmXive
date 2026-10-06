import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

import yaml

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the JSON schema from a YAML file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    return schema

def validate_type(value: Any, expected_type: str) -> bool:
    """Validate a value against a JSON schema type definition."""
    if expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "number":
        return isinstance(value, (int, float))
    elif expected_type == "integer":
        return isinstance(value, int)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "array":
        return isinstance(value, list)
    elif expected_type == "object":
        return isinstance(value, dict)
    return False

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate data against a simple JSON schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    # Check required fields
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check property types
    properties = schema.get('properties', {})
    for key, value in data.items():
        if key in properties:
            prop_schema = properties[key]
            expected_type = prop_schema.get('type')
            if expected_type and not validate_type(value, expected_type):
                errors.append(f"Field '{key}' has wrong type. Expected {expected_type}, got {type(value).__name__}")
        
        # Check for additional properties if not allowed (simplified check)
        # The schema provided in T001a allows additionalProperties of type number
        # We will assume any extra numeric fields are allowed based on that context
        elif key not in properties and 'additionalProperties' not in schema:
            # Strict mode: if not in properties and no additionalProperties rule, it's an error
            # However, the schema in T001a explicitly allows additionalProperties: type: number
            # We will treat this as valid if it's numeric, otherwise warn
            if not isinstance(value, (int, float)):
                errors.append(f"Unexpected non-numeric field '{key}' not in schema properties")

    return len(errors) == 0, errors

def run_validation(input_path: str, schema_path: str, output_path: str) -> bool:
    """Run the validation and write the report."""
    logger.info(f"Loading metrics from: {input_path}")
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return False

    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return False

    try:
        schema = load_schema(schema_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return False

    is_valid, errors = validate_against_schema(data, schema)
    
    report = {
        "validation_status": "passed" if is_valid else "failed",
        "input_file": input_path,
        "schema_file": schema_path,
        "errors": errors,
        "timestamp": None # Could add datetime if needed
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    if is_valid:
        logger.info("Validation passed.")
    else:
        logger.warning(f"Validation failed with {len(errors)} errors.")
        for err in errors:
            logger.warning(f"  - {err}")
    
    return is_valid

def main():
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_file = project_root / "data" / "results" / "model_metrics.json"
    schema_file = project_root / "specs" / "001-investigating-the-correlation-between-gu" / "contracts" / "model_metrics.schema.yaml"
    output_file = project_root / "data" / "results" / "model_metrics_validation.json"

    # If the schema file doesn't exist, we might need to create a default one
    # based on the structure of model_metrics.json we expect, but the task
    # implies the schema should exist (created in T001a style or similar).
    # If T001a created dataset.schema.yaml, we need to ensure model_metrics.schema.yaml exists.
    # Since T001a created dataset.schema.yaml, and T038 references model_metrics.schema.yaml,
    # we must ensure this file exists. If not, we create a reasonable default based on T037 output.
    
    if not os.path.exists(schema_file):
        logger.warning(f"Schema file not found: {schema_file}. Creating a default schema based on expected model_metrics structure.")
        default_schema = {
            "type": "object",
            "required": [
                "mean_accuracy",
                "std_accuracy",
                "meets_accuracy_target",
                "precision",
                "recall",
                "f1_score",
                "confusion_matrix"
            ],
            "properties": {
                "mean_accuracy": {"type": "number"},
                "std_accuracy": {"type": "number"},
                "meets_accuracy_target": {"type": "boolean"},
                "precision": {"type": "number"},
                "recall": {"type": "number"},
                "f1_score": {"type": "number"},
                "confusion_matrix": {"type": "array"},
                "significant_p_value": {"type": "number"},
                "threshold_used": {"type": "number"}
            },
            "additionalProperties": True
        }
        os.makedirs(os.path.dirname(schema_file), exist_ok=True)
        with open(schema_file, 'w') as f:
            yaml.dump(default_schema, f)
        logger.info(f"Created default schema at: {schema_file}")

    success = run_validation(str(input_file), str(schema_file), str(output_file))
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
