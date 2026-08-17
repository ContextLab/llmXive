"""
Validates the generated features.json against the output schema contract.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> dict:
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_type(value: any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == "object":
        return isinstance(value, dict)
    elif expected_type == "array":
        return isinstance(value, list)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "null":
        return value is None
    return False

def validate_record(record: dict, schema: dict) -> list:
    errors = []
    properties = schema.get('properties', {})
    required = schema.get('required', [])

    # Check required fields
    for field in required:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Check types
    for field, value in record.items():
        if field in properties:
            field_schema = properties[field]
            expected_type = field_schema.get('type')
            
            # Handle nullable fields
            if expected_type == "number" and value is None:
                if not field_schema.get('nullable', False):
                    errors.append(f"Field '{field}' is null but not nullable")
                continue
            elif value is None:
                continue

            if not validate_type(value, expected_type):
                errors.append(f"Field '{field}' has wrong type. Expected {expected_type}, got {type(value).__name__}")
        elif not schema.get('additionalProperties', True):
            errors.append(f"Unexpected field: {field}")

    return errors

def validate_output(output_path: str, schema_path: str) -> bool:
    try:
        schema = load_schema(schema_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)

        # Handle both list and single object formats
        records = data if isinstance(data, list) else [data]
        
        if not records:
            logger.warning("Output file is empty")
            return True

        all_errors = []
        for i, record in enumerate(records):
            record_errors = validate_record(record, schema)
            if record_errors:
                all_errors.append(f"Record {i}: {record_errors}")

        if all_errors:
            logger.error("Schema validation failed:")
            for error in all_errors:
                logger.error(f"  - {error}")
            return False
        
        logger.info(f"Schema validation passed for {len(records)} records")
        return True

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return False
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML schema: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def parse_args():
    parser = argparse.ArgumentParser(description="Validate output features against schema")
    parser.add_argument("--output", required=True, help="Path to features.json")
    parser.add_argument("--schema", required=True, help="Path to output.schema.yaml")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args()

def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")
    
    success = validate_output(args.output, args.schema)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()