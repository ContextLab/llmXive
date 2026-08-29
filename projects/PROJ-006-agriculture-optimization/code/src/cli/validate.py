import argparse
import logging
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.utils.io_helpers import load_json_strict, read_csv_strict
from src.config.schemas import validate_dataset_schema, validate_regression_output

def validate_csv_artifact(file_path: Path, schema_type: str = 'dataset'):
    """Validate a CSV artifact against a schema."""
    try:
        df = read_csv_strict(file_path)
        if schema_type == 'dataset':
            is_valid, msg = validate_dataset_schema(df)
        else:
            logging.error(f"Unknown schema type for CSV: {schema_type}")
            return False
        
        if is_valid:
            logging.info(f"CSV validation passed for {file_path}")
            return True
        else:
            logging.error(f"CSV validation failed for {file_path}: {msg}")
            return False
    except Exception as e:
        logging.error(f"Error validating CSV {file_path}: {e}")
        return False

def validate_json_artifact(file_path: Path, schema_type: str = 'regression'):
    """Validate a JSON artifact against a schema."""
    try:
        data = load_json_strict(file_path)
        if schema_type == 'regression':
            is_valid, msg = validate_regression_output(data)
        else:
            logging.error(f"Unknown schema type for JSON: {schema_type}")
            return False

        if is_valid:
            logging.info(f"JSON validation passed for {file_path}")
            return True
        else:
            logging.error(f"JSON validation failed for {file_path}: {msg}")
            return False
    except Exception as e:
        logging.error(f"Error validating JSON {file_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Validate pipeline artifacts.")
    parser.add_argument('file_path', type=str, help='Path to the file to validate.')
    parser.add_argument('--schema-type', type=str, choices=['dataset', 'regression', 'sensitivity'],
                        default='dataset', help='Type of schema to validate against.')
    parser.add_argument('--no-strict', action='store_true', help='Do not fail on warnings.')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    file_path = Path(args.file_path)
    if not file_path.exists():
        logging.error(f"File not found: {file_path}")
        sys.exit(1)

    is_valid = False
    if file_path.suffix == '.csv':
        is_valid = validate_csv_artifact(file_path, args.schema_type)
    elif file_path.suffix == '.json':
        is_valid = validate_json_artifact(file_path, args.schema_type)
    else:
        logging.error(f"Unsupported file type: {file_path.suffix}")
        sys.exit(1)

    if is_valid:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
