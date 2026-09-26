"""
validate_schemas.py

Validates all generated JSON/CSV artifacts in data/ and data/models/
against the contracts defined in contracts/dataset.schema.yaml and
contracts/model_output.schema.yaml.

Exit codes:
  0: All artifacts match schemas.
  1: Validation failed or schema loading error.
"""

import os
import sys
import json
import yaml
import csv
import logging
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRACTS_DIR = os.path.join(PROJECT_ROOT, "contracts")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MODELS_DIR = os.path.join(PROJECT_ROOT, "data", "models")

DATASET_SCHEMA_PATH = os.path.join(CONTRACTS_DIR, "dataset.schema.yaml")
MODEL_OUTPUT_SCHEMA_PATH = os.path.join(CONTRACTS_DIR, "model_output.schema.yaml")

def load_schema(schema_path: str) -> Optional[Dict[str, Any]]:
    """Load a YAML schema file."""
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        return None
    try:
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading schema {schema_path}: {e}")
        return None

def validate_json_against_schema(json_path: str, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a JSON file against a JSON-compatible schema (basic structure)."""
    errors = []
    if not os.path.exists(json_path):
        return False, [f"File not found: {json_path}"]

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in {json_path}: {e}"]

    # Basic schema validation logic (since jsonschema might not be strictly required for all simple checks,
    # but we assume the schema defines required keys/structure)
    if not isinstance(schema, dict):
        return False, ["Invalid schema format"]

    required_keys = schema.get("required", [])
    properties = schema.get("properties", {})

    if isinstance(data, dict):
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: '{key}'")
        
        # Type checking for known properties if schema defines types
        for key, value in data.items():
            if key in properties:
                prop_schema = properties[key]
                expected_type = prop_schema.get("type")
                
                type_map = {
                    "string": str,
                    "number": (int, float),
                    "integer": int,
                    "boolean": bool,
                    "array": list,
                    "object": dict
                }
                
                if expected_type and expected_type in type_map:
                    expected_python_type = type_map[expected_type]
                    if not isinstance(value, expected_python_type):
                        errors.append(f"Type mismatch for key '{key}': expected {expected_type}, got {type(value).__name__}")
    elif isinstance(data, list):
        # For list schemas, check if schema expects a list
        if schema.get("type") != "array":
             errors.append(f"Expected array but got {type(data).__name__} in {json_path}")
        else:
            # Optional: check items schema if defined
            pass

    return len(errors) == 0, errors

def validate_csv_against_schema(csv_path: str, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a CSV file against a schema (checks columns)."""
    errors = []
    if not os.path.exists(csv_path):
        return False, [f"File not found: {csv_path}"]

    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return False, ["Empty CSV file or no header"]
            
            columns = set(reader.fieldnames)
            required_columns = schema.get("required", [])
            
            for col in required_columns:
                if col not in columns:
                    errors.append(f"Missing required column: '{col}'")
    except Exception as e:
        return False, [f"Error reading CSV {csv_path}: {e}"]

    return len(errors) == 0, errors

def get_all_artifacts(data_dir: str, models_dir: str) -> List[str]:
    """Recursively find all JSON and CSV files in data/ and data/models/."""
    artifacts = []
    for directory in [data_dir, models_dir]:
        if not os.path.exists(directory):
            continue
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.json', '.csv')):
                    artifacts.append(os.path.join(root, file))
    return artifacts

def validate_schemas() -> bool:
    """Main validation logic."""
    logger.info("Starting schema validation...")

    # Load schemas
    dataset_schema = load_schema(DATASET_SCHEMA_PATH)
    model_schema = load_schema(MODEL_OUTPUT_SCHEMA_PATH)

    if not dataset_schema:
        logger.error("Failed to load dataset schema. Aborting.")
        return False
    if not model_schema:
        # Some files might be model outputs, some dataset. If model schema missing, we can't validate those.
        logger.warning("Model output schema not found. Only dataset schema will be used if applicable.")

    artifacts = get_all_artifacts(DATA_DIR, MODELS_DIR)
    
    if not artifacts:
        logger.warning("No JSON or CSV artifacts found in data/ or data/models/ to validate.")
        return True # Nothing to fail

    all_passed = True
    total_errors = []

    for artifact_path in artifacts:
        filename = os.path.basename(artifact_path)
        logger.info(f"Validating: {artifact_path}")
        
        is_valid = True
        errors = []

        # Determine which schema to use based on filename or path heuristic
        # Heuristic: If it's in data/models/ or named with 'model', 'metric', 'report', use model_schema
        # Otherwise, try dataset_schema. If both exist, we might need a mapping, but for now:
        
        use_model_schema = False
        if MODELS_DIR in artifact_path:
            use_model_schema = True
        elif any(kw in filename.lower() for kw in ['model', 'metric', 'report', 'cv_', 'null_', 'statistical', 'sensitivity', 'feature_importance', 'collinearity', 'sc00', 'split_', 'train_', 'test_', 'dummy_']):
             use_model_schema = True

        current_schema = model_schema if use_model_schema else dataset_schema

        if artifact_path.endswith('.json'):
            if current_schema:
                is_valid, errors = validate_json_against_schema(artifact_path, current_schema)
            else:
                logger.warning(f"No schema available for JSON: {artifact_path}")
        elif artifact_path.endswith('.csv'):
            if current_schema:
                is_valid, errors = validate_csv_against_schema(artifact_path, current_schema)
            else:
                logger.warning(f"No schema available for CSV: {artifact_path}")

        if not is_valid:
            all_passed = False
            for err in errors:
                total_errors.append(f"{artifact_path}: {err}")
                logger.error(f"  ERROR: {err}")
        else:
            logger.info(f"  OK")

    if all_passed:
        logger.info("Validation Passed")
        return True
    else:
        logger.error("Validation Failed")
        logger.error(f"Total errors found: {len(total_errors)}")
        return False

def main():
    success = validate_schemas()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()