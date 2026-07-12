"""
Validate CSV data artifacts against JSON Schema.

Task: T032a
Validates `data/processed/correlation_results_fdr.csv` against 
`specs/001-neural-entropy-cognitive-flexibility/contracts/correlation_results.schema.yaml`.

Output: logs/validation_log.csv.txt
"""
import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    import yaml
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print("ERROR: Missing dependencies 'pyyaml' or 'jsonschema'. Please install them.")
    sys.exit(1)

from utils.logging_config import setup_general_logger

# Configuration
SCHEMA_PATH = project_root / "specs" / "001-neural-entropy-cognitive-flexibility" / "contracts" / "correlation_results.schema.yaml"
DATA_PATH = project_root / "data" / "processed" / "correlation_results_fdr.csv"
LOG_PATH = project_root / "logs" / "validation_log.csv.txt"

# Ensure logs directory exists
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = setup_general_logger("validate_csv_schema", log_file=str(LOG_PATH))

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_against_schema(data_path: Path, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate a CSV file against a JSON Schema.
    
    Since CSV is a flat structure, we treat each row as a JSON object
    and validate it against the schema's 'properties' (if it expects an object)
    or validate the whole file structure if the schema defines a 'type: array'.
    
    Returns a list of validation results (dicts with row info and errors).
    """
    results = []
    
    if not data_path.exists():
        results.append({
            "status": "ERROR",
            "message": f"Data file not found: {data_path}",
            "row": None
        })
        return results

    with open(data_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        if not headers:
            results.append({
                "status": "ERROR",
                "message": "CSV file is empty or has no headers.",
                "row": None
            })
            return results

        # Convert schema to a format suitable for row-by-row validation
        # If the schema expects an object, we validate each row as an object.
        # If the schema expects an array of objects, we validate each row individually.
        
        # Determine the expected item schema
        item_schema = schema.get("items", schema)
        
        # If the top level is an array, we validate each row against 'items'
        # If the top level is an object, we validate each row against the schema directly
        if schema.get("type") == "array":
            target_schema = schema.get("items", {})
        else:
            target_schema = schema

        # Check if target_schema expects an object
        if target_schema.get("type") == "object" or "properties" in target_schema:
            validator = Draft7Validator(target_schema)
            
            for row_idx, row in enumerate(reader, start=2): # Start at 2 because 1 is header
                # Convert types if necessary (CSV reads everything as string)
                # We attempt to parse numbers for fields defined as number/integer in schema
                parsed_row = {}
                for key, value in row.items():
                    if key in target_schema.get("properties", {}):
                        prop_type = target_schema["properties"][key].get("type")
                        if prop_type in ["number", "integer"] and value != "":
                            try:
                                parsed_row[key] = float(value)
                                if prop_type == "integer":
                                    parsed_row[key] = int(value)
                            except ValueError:
                                parsed_row[key] = value # Keep as string if conversion fails
                        else:
                            parsed_row[key] = value
                    else:
                        parsed_row[key] = value

                errors = list(validator.iter_errors(parsed_row))
                
                if errors:
                    error_messages = [f"{e.message} (instance: {e.instance})" for e in errors]
                    results.append({
                        "status": "INVALID",
                        "row": row_idx,
                        "errors": error_messages
                    })
                else:
                    results.append({
                        "status": "VALID",
                        "row": row_idx,
                        "errors": []
                    })
        else:
            # If schema is not an object (e.g., simple array of strings), this CSV validation logic needs adjustment.
            # Assuming standard tabular data schema (object per row).
            results.append({
                "status": "ERROR",
                "message": "Schema does not define an object structure for rows. Cannot validate CSV row-by-row.",
                "row": None
            })

    return results

def main():
    logger.info("Starting CSV Schema Validation (Task T032a)")
    logger.info(f"Schema Path: {SCHEMA_PATH}")
    logger.info(f"Data Path: {DATA_PATH}")
    
    try:
        schema = load_schema(SCHEMA_PATH)
        logger.info("Schema loaded successfully.")
        
        validation_results = validate_csv_against_schema(DATA_PATH, schema)
        
        valid_count = sum(1 for r in validation_results if r["status"] == "VALID")
        invalid_count = sum(1 for r in validation_results if r["status"] == "INVALID")
        error_count = sum(1 for r in validation_results if r["status"] == "ERROR")
        
        logger.info(f"Validation Complete. Total Rows: {len(validation_results)}, Valid: {valid_count}, Invalid: {invalid_count}, Errors: {error_count}")
        
        # Write summary to log file
        with open(LOG_PATH, 'w') as log_file:
            log_file.write(f"CSV Schema Validation Report\n")
            log_file.write(f"============================\n")
            log_file.write(f"File: {DATA_PATH.name}\n")
            log_file.write(f"Schema: {SCHEMA_PATH.name}\n")
            log_file.write(f"Date: {Path(__file__).stat().st_mtime}\n")
            log_file.write(f"Total Rows: {len(validation_results)}\n")
            log_file.write(f"Valid: {valid_count}\n")
            log_file.write(f"Invalid: {invalid_count}\n")
            log_file.write(f"Errors: {error_count}\n")
            log_file.write(f"============================\n\n")
            
            if invalid_count > 0 or error_count > 0:
                log_file.write("Detailed Results:\n")
                for res in validation_results:
                    if res["status"] != "VALID":
                        log_file.write(f"Row {res['row']}: {res['status']}\n")
                        if "errors" in res:
                            for err in res["errors"]:
                                log_file.write(f"  - {err}\n")
                        if "message" in res:
                            log_file.write(f"  - {res['message']}\n")
                        log_file.write("\n")
            else:
                log_file.write("All rows validated successfully against the schema.\n")

        if invalid_count > 0 or error_count > 0:
            logger.warning(f"Validation failed with {invalid_count} invalid rows and {error_count} errors.")
            # Do not exit with error code to allow pipeline to continue logging the failure state
            # unless strict mode is required. Here we log the failure.
        else:
            logger.info("All rows validated successfully.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Schema YAML error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()