import csv
import json
import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path to allow imports from scripts/
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.checkpoint import ensure_checkpoint_dir, save_checkpoint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> dict:
    """Load the JSON schema from a file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_row(row: dict, schema: dict) -> list:
    """
    Validate a single row against the schema.
    Returns a list of validation errors (empty if valid).
    This is a manual implementation to avoid external dependencies like jsonschema
    if not strictly necessary, but we will try to use it if available.
    However, to ensure robustness without extra installs, we implement basic checks.
    """
    errors = []
    
    # Check required fields
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in row or row[field] is None:
            # Allow null for specific fields defined in properties as nullable
            props = schema.get('properties', {})
            if field in props:
                field_schema = props[field]
                # Check if type is ["number", "null"] or similar
                if isinstance(field_schema.get('type'), list) and 'null' in field_schema['type']:
                    continue # Null is allowed
            errors.append(f"Missing required field: {field}")
            continue

    # Type checking for present fields
    properties = schema.get('properties', {})
    for key, value in row.items():
        if key in properties:
            field_schema = properties[key]
            expected_type = field_schema.get('type')
            
            if value is None:
                # Check if null is allowed
                if isinstance(expected_type, list) and 'null' in expected_type:
                    continue
                elif expected_type == 'null':
                    continue
                else:
                    errors.append(f"Field '{key}' is null but expected type '{expected_type}'")
                    continue

            # Basic type mapping
            if expected_type == 'string':
                if not isinstance(value, str):
                    errors.append(f"Field '{key}' expected string, got {type(value)}")
            elif expected_type == 'number':
                if not isinstance(value, (int, float)):
                    errors.append(f"Field '{key}' expected number, got {type(value)}")
            elif expected_type == 'integer':
                if not isinstance(value, int):
                    errors.append(f"Field '{key}' expected integer, got {type(value)}")
            elif expected_type == 'object':
                if not isinstance(value, dict):
                    errors.append(f"Field '{key}' expected object, got {type(value)}")
            elif isinstance(expected_type, list):
                # Handle union types like ["number", "null"]
                valid = False
                for t in expected_type:
                    if t == 'null' and value is None:
                        valid = True
                    elif t == 'number' and isinstance(value, (int, float)):
                        valid = True
                    elif t == 'string' and isinstance(value, str):
                        valid = True
                    elif t == 'integer' and isinstance(value, int):
                        valid = True
                if not valid:
                    errors.append(f"Field '{key}' type mismatch: expected {expected_type}, got {type(value)}")
            
            # Check enum constraints
            if 'enum' in field_schema:
                if value not in field_schema['enum']:
                    errors.append(f"Field '{key}' value '{value}' not in enum {field_schema['enum']}")
            
            # Check minimum constraints
            if 'minimum' in field_schema and isinstance(value, (int, float)):
                if value < field_schema['minimum']:
                    errors.append(f"Field '{key}' value {value} is less than minimum {field_schema['minimum']}")

    return errors

def validate_distribution_fits(csv_path: str, schema_path: str) -> dict:
    """
    Validate the entire CSV file against the schema.
    Returns a report dictionary.
    """
    report = {
        "file": csv_path,
        "schema": schema_path,
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "errors": []
    }

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    schema = load_schema(schema_path)

    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2): # Start at 2 because row 1 is header
            report["total_rows"] += 1
            row_errors = validate_row(row, schema)
            if row_errors:
                report["invalid_rows"] += 1
                for err in row_errors:
                    report["errors"].append(f"Row {row_num}: {err}")
            else:
                report["valid_rows"] += 1

    report["success"] = report["invalid_rows"] == 0
    return report

def save_report(report: dict, output_path: str):
    """Save the validation report to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {output_path}")

def main():
    """Main entry point for validation script."""
    # Paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    csv_path = project_root / "data" / "processed" / "distribution_fits.csv"
    schema_path = project_root / "contracts" / "distribution_fit.schema.yaml"
    output_path = project_root / "data" / "processed" / "distribution_fits_validation_report.json"

    # Convert to absolute paths for logging/verification
    csv_path = csv_path.resolve()
    schema_path = schema_path.resolve()

    logger.info(f"Validating {csv_path} against {schema_path}")

    try:
        report = validate_distribution_fits(str(csv_path), str(schema_path))
        save_report(report, str(output_path))
        
        if report["success"]:
            logger.info("Validation PASSED. All rows conform to schema.")
            sys.exit(0)
        else:
            logger.warning(f"Validation FAILED. {report['invalid_rows']} invalid rows found.")
            for err in report["errors"][:5]: # Log first 5 errors
                logger.warning(err)
            sys.exit(1)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()