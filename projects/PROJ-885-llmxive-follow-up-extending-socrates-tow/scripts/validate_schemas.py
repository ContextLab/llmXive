"""
T060: Schema Validation Script
Validates data artifacts against their expected JSON schemas and generates a report.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories, setup_logging

# Configure logging
logger = setup_logging("schema_validation")

# --- Schema Definitions ---

CLASSIFIER_TRAINING_DATA_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "turn_text": {"type": "string"},
            "label": {"type": "string"},
            "trajectory_id": {"type": "string"},
            "confidence_score": {"type": "number"},
            "threshold_used": {"type": "number"},
            "turn_index": {"type": "integer"},
            "window_size": {"type": "integer"}
        },
        "required": ["turn_text", "label", "trajectory_id", "confidence_score", "threshold_used"]
    }
}

EXPERIMENT_LOGS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "trajectory_id": {"type": "string"},
            "condition": {"type": "string", "enum": ["Adapter", "Static"]},
            "turn_index": {"type": "integer"},
            "injected_state": {"type": ["string", "null"]},
            "confidence_score": {"type": ["number", "null"]},
            "llm_output": {"type": "string"},
            "timestamp": {"type": "string"},
            "model_name": {"type": "string"}
        },
        "required": ["trajectory_id", "condition", "turn_index", "llm_output", "timestamp", "model_name"]
    }
}

def validate_dict_against_schema(data: Dict, schema: Dict, schema_name: str, index: int) -> List[str]:
    """
    Validates a single dictionary against a schema definition.
    Returns a list of error messages.
    """
    errors = []
    
    # Check type
    if schema.get("type") == "object" and not isinstance(data, dict):
        errors.append(f"{schema_name}[{index}]: Expected object, got {type(data).__name__}")
        return errors

    # Check required fields
    if "required" in schema:
        for field in schema["required"]:
            if field not in data:
                errors.append(f"{schema_name}[{index}]: Missing required field '{field}'")
    
    # Check property types
    if "properties" in schema and isinstance(data, dict):
        for prop, prop_schema in schema["properties"].items():
            if prop in data:
                val = data[prop]
                expected_type = prop_schema.get("type")
                
                if expected_type == "string" and not isinstance(val, str):
                    errors.append(f"{schema_name}[{index}]: Field '{prop}' expected string, got {type(val).__name__}")
                elif expected_type == "integer" and not isinstance(val, int):
                    errors.append(f"{schema_name}[{index}]: Field '{prop}' expected integer, got {type(val).__name__}")
                elif expected_type == "number" and not isinstance(val, (int, float)):
                    errors.append(f"{schema_name}[{index}]: Field '{prop}' expected number, got {type(val).__name__}")
                elif expected_type == "boolean" and not isinstance(val, bool):
                    errors.append(f"{schema_name}[{index}]: Field '{prop}' expected boolean, got {type(val).__name__}")
                elif isinstance(expected_type, list):
                    # Handle union types like ["number", "null"]
                    if not any(
                        (t == "null" and val is None) or 
                        (t == "number" and isinstance(val, (int, float))) or
                        (t == "string" and isinstance(val, str)) or
                        (t == "integer" and isinstance(val, int)) or
                        (t == "boolean" and isinstance(val, bool))
                        for t in expected_type
                    ):
                        errors.append(f"{schema_name}[{index}]: Field '{prop}' expected one of {expected_type}, got {type(val).__name__}")
                
                # Enum check
                if "enum" in prop_schema and val not in prop_schema["enum"]:
                    errors.append(f"{schema_name}[{index}]: Field '{prop}' value '{val}' not in allowed enum {prop_schema['enum']}")

    return errors

def validate_file(filepath: Path, schema: Dict, schema_name: str) -> Tuple[bool, List[str]]:
    """
    Loads a JSON file and validates it against the provided schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    if not filepath.exists():
        return False, [f"File not found: {filepath}"]

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in {filepath}: {str(e)}"]

    if not isinstance(data, list):
        return False, [f"{schema_name}: Root element must be a list, got {type(data).__name__}"]

    if len(data) == 0:
        logger.warning(f"{schema_name} is empty. Validation passed trivially.")
        return True, []

    for i, item in enumerate(data):
        item_errors = validate_dict_against_schema(item, schema, schema_name, i)
        errors.extend(item_errors)

    return len(errors) == 0, errors

def main():
    """Main entry point for schema validation."""
    logger.info("Starting schema validation for T060.")
    
    # Ensure output directory exists
    output_dir = project_root / "data" / "results"
    ensure_directories([output_dir])
    
    input_files = [
        (project_root / "data" / "processed" / "classifier_training_data.json", CLASSIFIER_TRAINING_DATA_SCHEMA, "classifier_training_data"),
        (project_root / "data" / "processed" / "experiment_logs.json", EXPERIMENT_LOGS_SCHEMA, "experiment_logs")
    ]
    
    all_valid = True
    report = {
        "timestamp": str(Path(__file__).stat().st_mtime), # Using file mtime as a proxy for "now" in this script context, or use datetime
        "files_validated": [],
        "schema_valid": True,
        "errors": []
    }
    
    import datetime
    report["timestamp"] = datetime.datetime.now().isoformat()

    for filepath, schema, name in input_files:
        logger.info(f"Validating {name} at {filepath}...")
        is_valid, errors = validate_file(filepath, schema, name)
        
        file_report = {
            "file": str(filepath),
            "schema_name": name,
            "valid": is_valid,
            "error_count": len(errors),
            "errors": errors
        }
        report["files_validated"].append(file_report)
        
        if not is_valid:
            all_valid = False
            report["errors"].extend(errors)
            logger.error(f"Validation failed for {name}: {len(errors)} errors found.")
        else:
            logger.info(f"Validation passed for {name}.")

    report["schema_valid"] = all_valid
    
    output_path = output_dir / "schema_validation_report.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report written to {output_path}")
    
    if not all_valid:
        logger.error("Schema validation failed. Check data/processed/ files.")
        sys.exit(1)
    else:
        logger.info("All schemas validated successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()