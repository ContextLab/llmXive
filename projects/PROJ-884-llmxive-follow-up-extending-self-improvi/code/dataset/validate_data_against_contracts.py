"""
Validates generated puzzle datasets against the defined JSON schema contracts.

This script reads generated data (from T014c-exec) and the schema file
(contracts/dataset.schema.yaml) to verify schema compliance.

It produces a validation report at data/processed/data_validation_report.json.
"""
import json
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Attempt to import yaml. If missing, this script cannot run.
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load and parse the YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    if not isinstance(schema, dict):
        raise ValueError("Schema file must contain a valid YAML dictionary.")
    
    return schema

def validate_puzzle_instance(instance: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single puzzle instance against the schema.
    Returns a list of error messages (empty if valid).
    """
    errors = []
    
    # Define required top-level keys based on T000d-def
    required_keys = ['constraints', 'initial_state', 'target_state', 'verifier_output', 'metadata']
    
    for key in required_keys:
        if key not in instance:
            errors.append(f"Missing required key: {key}")
    
    if errors:
        return errors

    # Validate 'constraints' (array of strings)
    if not isinstance(instance['constraints'], list):
        errors.append("'constraints' must be an array")
    else:
        for i, item in enumerate(instance['constraints']):
            if not isinstance(item, str):
                errors.append(f"'constraints[{i}]' must be a string, got {type(item).__name__}")

    # Validate 'initial_state' (object)
    if not isinstance(instance['initial_state'], dict):
        errors.append("'initial_state' must be an object")

    # Validate 'target_state' (object)
    if not isinstance(instance['target_state'], dict):
        errors.append("'target_state' must be an object")

    # Validate 'verifier_output' (object with 'valid' boolean and 'error_code' string)
    verifier = instance['verifier_output']
    if not isinstance(verifier, dict):
        errors.append("'verifier_output' must be an object")
    else:
        if 'valid' not in verifier:
            errors.append("'verifier_output' missing 'valid' boolean")
        elif not isinstance(verifier['valid'], bool):
            errors.append("'verifier_output.valid' must be a boolean")
        
        if 'error_code' not in verifier:
            errors.append("'verifier_output' missing 'error_code' string")
        elif not isinstance(verifier['error_code'], str):
            errors.append("'verifier_output.error_code' must be a string")

    # Validate 'metadata' (object with 'source_id', 'generation_seed')
    metadata = instance['metadata']
    if not isinstance(metadata, dict):
        errors.append("'metadata' must be an object")
    else:
        if 'source_id' not in metadata:
            errors.append("'metadata' missing 'source_id'")
        elif not isinstance(metadata['source_id'], str):
            errors.append("'metadata.source_id' must be a string")
        
        if 'generation_seed' not in metadata:
            errors.append("'metadata' missing 'generation_seed'")
        elif not isinstance(metadata['generation_seed'], (int, str)):
            errors.append("'metadata.generation_seed' must be an int or string")

    return errors

def validate_dataset(data_path: Path, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a dataset file (JSON) against the schema.
    Returns a validation report dictionary.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    logger.info(f"Loading dataset from {data_path}...")
    with open(data_path, 'r', encoding='utf-8') as f:
        # Support both list of objects and object with 'puzzles' key
        data = json.load(f)
    
    if isinstance(data, list):
        puzzles = data
    elif isinstance(data, dict) and 'puzzles' in data:
        puzzles = data['puzzles']
    else:
        raise ValueError("Data file must be a JSON list of puzzles or an object with a 'puzzles' key.")

    logger.info(f"Validating {len(puzzles)} puzzle instances...")
    
    total_count = len(puzzles)
    valid_count = 0
    invalid_indices = []
    error_details = []

    for i, instance in enumerate(puzzles):
        errors = validate_puzzle_instance(instance, schema)
        if not errors:
            valid_count += 1
        else:
            invalid_indices.append(i)
            error_details.append({
                "index": i,
                "errors": errors
            })
            # Log first 5 errors for brevity
            if len(error_details) <= 5:
                logger.warning(f"Instance {i} failed validation: {errors}")

    is_valid = len(invalid_indices) == 0
    report = {
        "is_valid": is_valid,
        "total_count": total_count,
        "valid_count": valid_count,
        "invalid_count": len(invalid_indices),
        "invalid_indices": invalid_indices,
        "error_details": error_details,
        "schema_path": str(schema.get('$id', schema.get('id', 'unknown'))),
        "data_path": str(data_path),
        "validation_timestamp": None # Will be set by caller or default
    }
    
    # Add timestamp if not present (using simple ISO format string)
    from datetime import datetime
    report["validation_timestamp"] = datetime.utcnow().isoformat() + "Z"

    return report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the validation report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Validate generated puzzle datasets against the contract schema."
    )
    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to the generated dataset JSON file (e.g., data/raw/puzzles.json)."
    )
    parser.add_argument(
        "--schema",
        type=str,
        required=True,
        help="Path to the schema YAML file (e.g., contracts/dataset.schema.yaml)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/data_validation_report.json",
        help="Path to save the validation report (default: data/processed/data_validation_report.json)."
    )

    args = parser.parse_args()

    data_path = Path(args.data)
    schema_path = Path(args.schema)
    output_path = Path(args.output)

    try:
        # 1. Load Schema
        schema = load_schema(schema_path)
        logger.info(f"Schema loaded successfully from {schema_path}")

        # 2. Validate Dataset
        report = validate_dataset(data_path, schema)

        # 3. Save Report
        save_report(report, output_path)

        # 4. Exit with appropriate code
        if report["is_valid"]:
            logger.info("Validation PASSED. All puzzles conform to the schema.")
            sys.exit(0)
        else:
            logger.error(f"Validation FAILED. {report['invalid_count']} invalid instances found.")
            sys.exit(1)

    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(2)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in data file: {e}")
        sys.exit(3)
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in schema file: {e}")
        sys.exit(4)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(5)

if __name__ == "__main__":
    main()
