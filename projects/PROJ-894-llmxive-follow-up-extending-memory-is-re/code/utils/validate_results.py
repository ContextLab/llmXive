import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DATA_DIR = PROJECT_ROOT / "data" / "processed"
SCHEMA_PATH = CONTRACTS_DIR / "results.schema.yaml"

# List of all result files to validate
RESULT_FILES = [
    "baseline_results.csv",
    "lazy_results.csv",
    "greedy_results.csv",
    "noisy_baseline_results.csv",
    "noisy_lazy_results.csv",
    "noisy_greedy_results.csv"
]

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load and parse the YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    return schema

def validate_csv_structure(
    csv_path: Path, 
    schema: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate a single CSV file against the schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    if not csv_path.exists():
        return False, [f"File not found: {csv_path}"]
    
    try:
        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                return False, ["CSV file is empty or has no headers"]
            
            # Check required fields
            required_fields = schema.get('required', [])
            for field in required_fields:
                if field not in headers:
                    errors.append(f"Missing required field: {field}")
            
            # Check for additional properties
            allowed_fields = list(schema.get('properties', {}).keys())
            for header in headers:
                if header not in allowed_fields:
                    errors.append(f"Unexpected field: {header}")
            
            # Validate row data
            row_count = 0
            for row_num, row in enumerate(reader, start=2):
                row_count += 1
                
                # Validate types and constraints
                for field, constraints in schema.get('properties', {}).items():
                    if field not in row or row[field] == '':
                        if constraints.get('nullable') is not True:
                            errors.append(f"Row {row_num}: Missing value for field '{field}'")
                            continue
                        
                    value = row.get(field)
                    if value is None or value == '':
                        continue
                    
                    field_type = constraints.get('type')
                    
                    if field_type == 'string':
                        if not isinstance(value, str):
                            errors.append(f"Row {row_num}: Field '{field}' must be string")
                        
                        # Check pattern
                        if 'pattern' in constraints:
                            import re
                            if not re.match(constraints['pattern'], value):
                                errors.append(f"Row {row_num}: Field '{field}' does not match pattern {constraints['pattern']}")
                        
                        # Check enum
                        if 'enum' in constraints:
                            if value not in constraints['enum']:
                                errors.append(f"Row {row_num}: Field '{field}' value '{value}' not in allowed values {constraints['enum']}")
                    
                    elif field_type == 'number':
                        try:
                            num_val = float(value)
                            if 'minimum' in constraints and num_val < constraints['minimum']:
                                errors.append(f"Row {row_num}: Field '{field}' value {num_val} below minimum {constraints['minimum']}")
                            if 'maximum' in constraints and num_val > constraints['maximum']:
                                errors.append(f"Row {row_num}: Field '{field}' value {num_val} above maximum {constraints['maximum']}")
                        except ValueError:
                            errors.append(f"Row {row_num}: Field '{field}' must be a number, got '{value}'")
                    
                    elif field_type == 'integer':
                        try:
                            int_val = int(value)
                            if 'minimum' in constraints and int_val < constraints['minimum']:
                                errors.append(f"Row {row_num}: Field '{field}' value {int_val} below minimum {constraints['minimum']}")
                        except ValueError:
                            errors.append(f"Row {row_num}: Field '{field}' must be an integer, got '{value}'")
            
            if row_count == 0:
                errors.append("CSV file has no data rows")
                
    except csv.Error as e:
        errors.append(f"CSV parsing error: {str(e)}")
    except Exception as e:
        errors.append(f"Unexpected error reading CSV: {str(e)}")
    
    return len(errors) == 0, errors

def validate_all_results(
    schema: Dict[str, Any],
    result_files: List[str],
    data_dir: Path
) -> Dict[str, Any]:
    """
    Validate all result CSV files against the schema.
    Returns a summary report.
    """
    report = {
        "total_files": len(result_files),
        "valid_files": 0,
        "invalid_files": 0,
        "details": {}
    }
    
    for filename in result_files:
        file_path = data_dir / filename
        is_valid, errors = validate_csv_structure(file_path, schema)
        
        report["details"][filename] = {
            "valid": is_valid,
            "errors": errors,
            "file_path": str(file_path)
        }
        
        if is_valid:
            report["valid_files"] += 1
        else:
            report["invalid_files"] += 1
    
    return report

def main():
    """Main entry point for schema validation."""
    logger.info("Starting result schema validation...")
    
    # Ensure contracts directory exists
    CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create a default schema if it doesn't exist
    if not SCHEMA_PATH.exists():
        logger.warning(f"Schema file not found at {SCHEMA_PATH}. Creating default schema.")
        default_schema = {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "pattern": "^task_[0-9]+$"
                },
                "accuracy": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "nodes_visited": {
                    "type": "integer",
                    "minimum": 0
                },
                "latency_ms": {
                    "type": "number",
                    "minimum": 0
                },
                "strategy": {
                    "type": "string",
                    "enum": ["full", "lazy", "greedy", "noisy_full", "noisy_lazy", "noisy_greedy"]
                },
                "noise_level": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "nullable": True
                }
            },
            "required": ["task_id", "accuracy", "nodes_visited", "latency_ms", "strategy"],
            "additionalProperties": False
        }
        
        with open(SCHEMA_PATH, 'w') as f:
            yaml.dump(default_schema, f, default_flow_style=False)
        logger.info(f"Default schema created at {SCHEMA_PATH}")
    
    # Load schema
    try:
        schema = load_schema(SCHEMA_PATH)
        logger.info(f"Schema loaded from {SCHEMA_PATH}")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        sys.exit(1)
    
    # Ensure data directory exists
    if not DATA_DIR.exists():
        logger.warning(f"Data directory not found: {DATA_DIR}. Creating it.")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Validate all result files
    report = validate_all_results(schema, RESULT_FILES, DATA_DIR)
    
    # Log results
    logger.info(f"Validation complete: {report['valid_files']}/{report['total_files']} files valid")
    
    for filename, details in report["details"].items():
        if details["valid"]:
            logger.info(f"✓ {filename}: Valid")
        else:
            logger.error(f"✗ {filename}: Invalid")
            for error in details["errors"]:
                logger.error(f"  - {error}")
    
    # Exit with error code if any validation failed
    if report["invalid_files"] > 0:
        logger.error("Validation failed for some files.")
        sys.exit(1)
    else:
        logger.info("All files passed validation.")
        sys.exit(0)

if __name__ == "__main__":
    main()