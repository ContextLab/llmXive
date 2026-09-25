"""
Validates dataset instances against the defined JSON schema contracts.
This script reads the schema from contracts/dataset.schema.yaml and validates
a dataset file (JSON) against it. It does NOT generate data; it only validates.
"""
import json
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Simple YAML loader since pyyaml is a dependency
try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load and parse the JSON schema from a YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        # The file is YAML but contains a JSON Schema structure
        return yaml.safe_load(f)

def validate_puzzle_instance(instance: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single puzzle instance against the schema.
    Returns a list of error messages. Empty list means valid.
    """
    errors = []
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    # Check required fields
    for field in required_fields:
        if field not in instance:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    # Validate 'constraints' (array of strings)
    if 'constraints' in instance:
        if not isinstance(instance['constraints'], list):
            errors.append("Field 'constraints' must be an array")
        elif len(instance['constraints']) < 1:
            errors.append("Field 'constraints' must have at least 1 item")
        else:
            for i, c in enumerate(instance['constraints']):
                if not isinstance(c, str):
                    errors.append(f"Constraint at index {i} must be a string")

    # Validate 'initial_state' (object)
    if 'initial_state' in instance:
        if not isinstance(instance['initial_state'], dict):
            errors.append("Field 'initial_state' must be an object")

    # Validate 'target_state' (object)
    if 'target_state' in instance:
        if not isinstance(instance['target_state'], dict):
            errors.append("Field 'target_state' must be an object")

    # Validate 'verifier_output'
    if 'verifier_output' in instance:
        vo = instance['verifier_output']
        if not isinstance(vo, dict):
            errors.append("Field 'verifier_output' must be an object")
        else:
            vo_required = ['valid', 'error_code']
            for field in vo_required:
                if field not in vo:
                    errors.append(f"Missing field in verifier_output: {field}")
            
            if 'valid' in vo and not isinstance(vo['valid'], bool):
                errors.append("Field 'verifier_output.valid' must be boolean")
            
            if 'error_code' in vo:
                valid_codes = ['NONE', 'DUPLICATE_ROW', 'INVALID_PATH', 
                             'CONSTRAINT_VIOLATION', 'PARSE_FAILURE', 
                             'CONTRADICTION_DETECTED', 'VERIFIER_ERROR']
                if vo['error_code'] not in valid_codes:
                    errors.append(f"Invalid error_code: {vo['error_code']}")

    # Validate 'metadata'
    if 'metadata' in instance:
        meta = instance['metadata']
        if not isinstance(meta, dict):
            errors.append("Field 'metadata' must be an object")
        else:
            meta_required = ['source_id', 'generation_seed']
            for field in meta_required:
                if field not in meta:
                    errors.append(f"Missing field in metadata: {field}")
            
            if 'source_id' in meta and not isinstance(meta['source_id'], str):
                errors.append("Field 'metadata.source_id' must be a string")
            
            if 'generation_seed' in meta and not isinstance(meta['generation_seed'], int):
                errors.append("Field 'metadata.generation_seed' must be an integer")
            
            if 'complexity_metric' in meta:
                cm = meta['complexity_metric']
                if not isinstance(cm, dict):
                    errors.append("Field 'metadata.complexity_metric' must be an object")
                else:
                    cm_required = ['constraint_count', 'variable_domain_size']
                    for field in cm_required:
                        if field not in cm:
                            errors.append(f"Missing field in complexity_metric: {field}")
                    
                    if 'constraint_count' in cm:
                        if not isinstance(cm['constraint_count'], int) or cm['constraint_count'] < 0:
                            errors.append("Field 'constraint_count' must be a non-negative integer")
                    
                    if 'variable_domain_size' in cm:
                        if not isinstance(cm['variable_domain_size'], int) or cm['variable_domain_size'] < 1:
                            errors.append("Field 'variable_domain_size' must be a positive integer")

    return errors

def validate_dataset(data_path: Path, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a dataset file (JSON) containing a list of puzzle instances.
    Returns a report dictionary.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {data_path}")

    with open(data_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "total_count": 0,
                "valid_count": 0,
                "invalid_count": 0,
                "errors": [f"Failed to parse JSON: {str(e)}"],
                "details": []
            }

    if not isinstance(data, list):
        # Try to handle if it's a single object wrapped or just an object
        if isinstance(data, dict):
            data = [data]
        else:
            return {
                "valid": False,
                "total_count": 0,
                "valid_count": 0,
                "invalid_count": 0,
                "errors": ["Dataset must be a JSON list of instances"],
                "details": []
            }

    total = len(data)
    valid_count = 0
    invalid_count = 0
    all_errors = []
    details = []

    for i, instance in enumerate(data):
        errors = validate_puzzle_instance(instance, schema)
        if errors:
            invalid_count += 1
            all_errors.extend(errors)
            details.append({
                "index": i,
                "status": "INVALID",
                "errors": errors
            })
        else:
            valid_count += 1
            details.append({
                "index": i,
                "status": "VALID",
                "errors": []
            })

    is_valid = (invalid_count == 0)
    
    return {
        "valid": is_valid,
        "total_count": total,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "errors": all_errors if all_errors else [],
        "details": details
    }

def save_report(report: Dict[str, Any], output_path: Path):
    """Save the validation report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Validate dataset instances against the schema contracts."
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("contracts/dataset.schema.yaml"),
        help="Path to the schema file (YAML)"
    )
    parser.add_argument(
        "--data",
        type=Path,
        required=True,
        help="Path to the dataset JSON file to validate"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/validation_report.json"),
        help="Path to save the validation report"
    )

    args = parser.parse_args()

    try:
        logger.info(f"Loading schema from {args.schema}...")
        schema = load_schema(args.schema)
        
        logger.info(f"Validating dataset from {args.data}...")
        report = validate_dataset(args.data, schema)
        
        logger.info(f"Validation complete: {report['valid_count']} valid, {report['invalid_count']} invalid out of {report['total_count']}")
        
        save_report(report, args.output)
        
        if not report['valid']:
            logger.warning("Validation failed. See report for details.")
            sys.exit(1)
        else:
            logger.info("Validation passed.")
            sys.exit(0)

    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
