import os
import sys
import csv
import yaml
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from config import get_raw_data_dir, get_project_root

logger = None

def setup_logger():
    global logger
    if logger is None:
        import logging
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

def load_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.
    
    Args:
        schema_path: Path to the schema file. Defaults to contracts/dataset.schema.yaml.
        
    Returns:
        Dictionary containing the schema definition.
    """
    setup_logger()
    
    if schema_path is None:
        project_root = get_project_root()
        schema_path = os.path.join(project_root, "contracts", "dataset.schema.yaml")
    
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    logger.info(f"Schema loaded from {schema_path}")
    return schema

def validate_csv_schema(csv_path: str, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a CSV file against the provided schema.
    
    Args:
        csv_path: Path to the CSV file.
        schema: Schema dictionary.
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    setup_logger()
    errors = []
    
    if not os.path.exists(csv_path):
        return False, [f"CSV file not found: {csv_path}"]
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        if not headers:
            return False, ["CSV file is empty or has no headers"]
        
        # Check required columns
        required_cols = [col['name'] for col in schema.get('required_columns', [])]
        missing_cols = [col for col in required_cols if col not in headers]
        
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        # Check optional columns presence (just logging, not error)
        optional_cols = [col['name'] for col in schema.get('optional_columns', [])]
        present_optional = [col for col in optional_cols if col in headers]
        if present_optional:
            logger.info(f"Found optional columns: {present_optional}")
        
        # Validate data types (basic check)
        for row_num, row in enumerate(reader, start=2):
            for col_name in required_cols:
                val = row.get(col_name)
                if val is None or val.strip() == '':
                    # Missing values are allowed but tracked later in preprocessing
                    continue
                try:
                    float(val)
                except ValueError:
                    errors.append(f"Row {row_num}, Column '{col_name}': Invalid numeric value '{val}'")
                    # Stop after first type error to avoid flooding
                    break
            if errors:
                break
    
    is_valid = len(errors) == 0
    if is_valid:
        logger.info(f"CSV schema validation passed for {csv_path}")
    else:
        logger.error(f"CSV schema validation failed for {csv_path}: {errors}")
    
    return is_valid, errors

def validate_and_report(csv_path: str, schema_path: Optional[str] = None) -> bool:
    """
    Validate a CSV file against the schema and print a report.
    
    Args:
        csv_path: Path to the CSV file.
        schema_path: Optional path to schema file.
        
    Returns:
        True if valid, False otherwise.
    """
    setup_logger()
    schema = load_schema(schema_path)
    is_valid, errors = validate_csv_schema(csv_path, schema)
    
    if is_valid:
        print(f"Validation PASSED for {csv_path}")
        return True
    else:
        print(f"Validation FAILED for {csv_path}:")
        for err in errors:
            print(f"  - {err}")
        return False

def main():
    """
    CLI entry point for schema validation.
    Usage: python -m code.data.schema_validator <csv_path> [schema_path]
    """
    setup_logger()
    if len(sys.argv) < 2:
        print("Usage: python -m code.data.schema_validator <csv_path> [schema_path]")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    schema_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = validate_and_report(csv_path, schema_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
