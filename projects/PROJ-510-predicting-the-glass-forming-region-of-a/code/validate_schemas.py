"""
validate_schemas.py

Validates all generated JSON/CSV artifacts in the data directory against
the YAML contracts defined in specs/001-predicting-the-glass-forming-region-of-a/contracts/.

The script scans for specific expected artifacts and validates their structure.
Exit codes:
  0: All found artifacts match schemas (or no artifacts found).
  1: One or more validation errors encountered.
"""

import os
import sys
import json
import yaml
import csv
import logging
from typing import Dict, Any, List, Tuple
import jsonschema
from llmxive_toolkit import paths, get_logger

# Configure logging to write to the specific log file required by T002
LOG_FILE = paths.data("logs", "schema_validation.log")
log = get_logger(__name__, log_file=str(LOG_FILE))

# Path to the contracts directory
CONTRACTS_DIR = paths.path("specs/001-predicting-the-glass-forming-region-of-a/contracts")

# Mapping of artifact filename to its corresponding schema file
# Based on plan.md and specs/
ARTIFACT_MAP = {
    "processed_alloys.csv": "processed_alloys.schema.yaml",
    "cv_metrics.json": "metrics.schema.yaml",
    "feature_importance.csv": "feature_importance.schema.yaml",
    "sensitivity_report.json": "sensitivity.schema.yaml",
    "model_output.json": "model_output.schema.yaml",
}

def load_yaml(path: os.PathLike) -> Dict[str, Any]:
    """Load a YAML file into a dictionary."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        log.error(f"Could not load YAML file {path}: {e}")
        return {}

def validate_json(file_path: os.PathLike, schema_path: os.PathLike) -> Tuple[bool, List[str]]:
    """Validate a JSON file against a YAML-defined JSON schema."""
    errors = []
    try:
        schema = load_yaml(schema_path)
        if not schema:
            return False, [f"Schema {schema_path} is empty or missing"]
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        errors.append(f"JSON Schema Error: {e.message}")
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON format: {e}")
    except Exception as e:
        errors.append(f"Unexpected error during JSON validation: {e}")
    
    return len(errors) == 0, errors

def validate_csv(file_path: os.PathLike, schema_path: os.PathLike) -> Tuple[bool, List[str]]:
    """Validate a CSV file's columns against the 'required' list in a YAML schema."""
    errors = []
    try:
        schema = load_yaml(schema_path)
        if not schema:
            return False, [f"Schema {schema_path} is empty or missing"]
        
        required_cols = schema.get("required", [])
        if not required_cols:
            return True, [] # No requirements defined

        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return False, ["CSV file is empty or missing header"]
            
            actual_cols = set(reader.fieldnames)
            for col in required_cols:
                if col not in actual_cols:
                    errors.append(f"Missing required column: '{col}'")
    except Exception as e:
        errors.append(f"Unexpected error during CSV validation: {e}")
    
    return len(errors) == 0, errors

def find_artifact(filename: str) -> Tuple[bool, os.PathLike]:
    """Recursively search for an artifact filename under the data directory."""
    data_root = paths.data()
    for root, _, files in os.walk(data_root):
        if filename in files:
            return True, os.path.join(root, filename)
    return False, None

def main():
    log.info("Starting schema validation process...")
    
    total_errors = 0
    artifacts_found = 0

    for artifact_name, schema_name in ARTIFACT_MAP.items():
        found, artifact_path = find_artifact(artifact_name)
        if not found:
            log.warning(f"Artifact {artifact_name} not found. Skipping.")
            continue
        
        artifacts_found += 1
        schema_path = CONTRACTS_DIR / schema_name
        
        if not schema_path.exists():
            log.error(f"ERROR: Schema file {schema_name} missing for {artifact_name}")
            total_errors += 1
            continue

        log.info(f"Validating {artifact_name} against {schema_name}...")
        
        if artifact_name.endswith('.json'):
            success, errors = validate_json(artifact_path, schema_path)
        elif artifact_name.endswith('.csv'):
            success, errors = validate_csv(artifact_path, schema_path)
        else:
            log.warning(f"Unsupported file extension for {artifact_name}. Skipping.")
            continue

        if not success:
            for err in errors:
                log.error(f"ERROR in {artifact_name}: {err}")
            total_errors += len(errors)
        else:
            log.info(f"Successfully validated {artifact_name}")

    log.info(f"Schema validation complete. Artifacts checked: {artifacts_found}. Total errors: {total_errors}")
    
    if total_errors == 0:
        log.info("All schemas validated - 0 errors.")
        sys.exit(0)
    else:
        log.error(f"Schema validation failed with {total_errors} errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()