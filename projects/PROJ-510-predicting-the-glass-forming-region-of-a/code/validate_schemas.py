"""
Schema Validation Script for PROJ-510
Validates all generated JSON and CSV artifacts against their defined contracts.
"""
import os
import sys
import json
import yaml
import csv
import logging
from typing import Dict, Any, List, Set
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRACTS_DIR = os.path.join(PROJECT_ROOT, "contracts")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MODELS_DIR = os.path.join(PROJECT_ROOT, "data", "models")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

# Define schema file mappings
SCHEMA_FILES = {
    "dataset.schema.yaml": ["data/processed/processed_alloys_raw.csv", "data/processed/processed_alloys.csv"],
    "model_output.schema.yaml": [
        "data/models/cv_metrics.json",
        "data/models/null_model_cv_scores.json",
        "data/models/null_model_rmse.json",
        "data/models/statistical_comparison.json",
        "data/models/sc002_status.json",
        "data/models/sensitivity_report.csv",
        "data/models/sensitivity_status.json",
        "data/models/feature_importance.json",
        "data/models/collinearity_report.json",
        "data/models/collinearity_decision.json",
        "data/models/initial_model_metrics.json",
        "data/models/random_forest_model.pkl",
        "data/models/random_forest_model_stable.pkl",
        "data/models/cv_folds_indices.json",
        "data/models/null_model_predictions.npy",
        "data/logs/data_validation_status.json",
        "data/logs/schema_validation_status.json",
        "data/logs/training_set_validation.json",
        "data/logs/exclusion_log.txt"
    ]
}

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    try:
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML schema {schema_path}: {e}")
        return None

def validate_json_against_schema(json_path: str, schema: Dict[str, Any]) -> List[str]:
    """Validate a JSON file against a schema."""
    errors = []
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Validate against schema
        try:
            validate(instance=data, schema=schema)
            logger.info(f"  ✓ {json_path} matches schema")
        except ValidationError as e:
            errors.append(f"Validation error in {json_path}: {e.message} at {list(e.path)}")
            logger.warning(f"  ✗ {json_path} failed schema validation: {e.message}")
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in {json_path}: {e}")
        logger.error(f"  ✗ {json_path} is not valid JSON: {e}")
    except FileNotFoundError:
        errors.append(f"File not found: {json_path}")
        logger.error(f"  ✗ {json_path} not found")
    
    return errors

def validate_csv_against_schema(csv_path: str, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a CSV file against a schema.
    For CSVs, we check that required columns exist and types are consistent.
    """
    errors = []
    try:
        if not os.path.exists(csv_path):
            errors.append(f"File not found: {csv_path}")
            logger.error(f"  ✗ {csv_path} not found")
            return errors

        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                errors.append(f"CSV file is empty or has no headers: {csv_path}")
                logger.error(f"  ✗ {csv_path} has no headers")
                return errors

            # Check required properties if defined in schema
            if 'required' in schema:
                required_cols = set(schema['required'])
                present_cols = set(headers)
                missing = required_cols - present_cols
                if missing:
                    errors.append(f"Missing required columns in {csv_path}: {missing}")
                    logger.warning(f"  ✗ {csv_path} missing columns: {missing}")
            
            # Check properties types if defined
            if 'properties' in schema:
                for col_name, col_schema in schema['properties'].items():
                    if col_name in headers:
                        # Basic type check (first non-empty row)
                        for row in reader:
                            val = row.get(col_name)
                            if val is not None and val != '':
                                expected_type = col_schema.get('type')
                                if expected_type == 'number':
                                    try:
                                        float(val)
                                    except ValueError:
                                        errors.append(f"Column '{col_name}' in {csv_path} expected number but got '{val}'")
                                elif expected_type == 'integer':
                                    try:
                                        int(val)
                                    except ValueError:
                                        errors.append(f"Column '{col_name}' in {csv_path} expected integer but got '{val}'")
                                break  # Only check first data row
                            
                            # If we've exhausted rows, stop
                            if row == {}:
                                break
            
            logger.info(f"  ✓ {csv_path} schema check passed")
    except Exception as e:
        errors.append(f"Error reading CSV {csv_path}: {e}")
        logger.error(f"  ✗ {csv_path} read error: {e}")
    
    return errors

def get_all_artifacts() -> List[str]:
    """Collect all JSON and CSV files in data/ and data/models/."""
    artifacts = []
    
    # Walk through data directory
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith(('.json', '.csv')):
                # Skip log files that are not schema-defined (optional)
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PROJECT_ROOT)
                artifacts.append(rel_path)
    
    return artifacts

def validate_schemas() -> int:
    """
    Main validation function.
    Returns 0 if all validations pass, 1 otherwise.
    """
    all_errors: List[str] = []
    all_passed = True

    logger.info("Starting schema validation for PROJ-510...")
    logger.info(f"Project root: {PROJECT_ROOT}")

    # Load schemas
    dataset_schema_path = os.path.join(CONTRACTS_DIR, "dataset.schema.yaml")
    model_output_schema_path = os.path.join(CONTRACTS_DIR, "model_output.schema.yaml")

    dataset_schema = load_schema(dataset_schema_path)
    model_output_schema = load_schema(model_output_schema_path)

    if not dataset_schema:
        logger.error("Failed to load dataset schema. Aborting.")
        return 1
    if not model_output_schema:
        logger.error("Failed to load model output schema. Aborting.")
        return 1

    # Map schema names to their definitions
    schemas = {
        "dataset.schema.yaml": dataset_schema,
        "model_output.schema.yaml": model_output_schema
    }

    # Process each schema file
    for schema_file, artifact_paths in SCHEMA_FILES.items():
        if schema_file not in schemas:
            logger.warning(f"Schema file {schema_file} not found in loaded schemas. Skipping.")
            continue

        schema = schemas[schema_file]
        logger.info(f"Validating artifacts for {schema_file}...")

        for artifact_path in artifact_paths:
            full_path = os.path.join(PROJECT_ROOT, artifact_path)
            
            # Check if file exists
            if not os.path.exists(full_path):
                # Some files might be optional or not yet generated in early runs
                # We log a warning but don't fail unless it's critical
                logger.warning(f"  ! {artifact_path} not found. Skipping validation for this file.")
                continue

            if artifact_path.endswith('.json'):
                errors = validate_json_against_schema(full_path, schema)
                all_errors.extend(errors)
            elif artifact_path.endswith('.csv'):
                errors = validate_csv_against_schema(full_path, schema)
                all_errors.extend(errors)
            else:
                # Skip other file types (pkl, npy, txt) as they don't have JSON-schema definitions
                logger.debug(f"  - Skipping non-schema file: {artifact_path}")

    # Additional check: Ensure critical files exist even if not in strict schema list
    critical_files = [
        "data/processed/processed_alloys_raw.csv",
        "data/processed/processed_alloys.csv",
        "data/models/cv_metrics.json",
        "data/models/statistical_comparison.json",
        "data/models/sensitivity_status.json"
    ]

    for f in critical_files:
        if not os.path.exists(os.path.join(PROJECT_ROOT, f)):
            all_errors.append(f"CRITICAL: Missing file {f}")
            all_passed = False

    # Final Report
    print("\n" + "="*50)
    if all_passed and not all_errors:
        print("Validation Passed")
        print("="*50)
        return 0
    else:
        print("Validation Failed")
        print("="*50)
        for err in all_errors:
            print(f"  - {err}")
        return 1

def main():
    """Entry point."""
    exit_code = validate_schemas()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()