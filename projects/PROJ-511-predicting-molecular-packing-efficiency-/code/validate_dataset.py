import os
import sys
import logging
import yaml
import json
from typing import List, Dict, Any, Optional
import pandas as pd
from jsonschema import validate, ValidationError, Draft7Validator
from pathlib import Path

# Import shared utilities from existing project files
from utils import fix_seed, setup_logging
from error_handling import DataValidationError, log_processing_statistics
from config import ensure_directories

# Configure logging
logger = logging.getLogger(__name__)

SCHEMA_PATH = "contracts/dataset.schema.yaml"
INPUT_CSV = "data/dataset.csv"
RAW_CIF_DIR = "data/raw_cif"

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load and return the JSON schema from a YAML file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Convert YAML schema to JSON-compatible structure if needed
    # jsonschema expects a dict, which yaml.safe_load provides
    return schema

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate the DataFrame against the provided schema.
    Returns a list of validation error messages.
    """
    errors = []
    
    # Convert DataFrame to list of dicts for validation
    # Note: jsonschema validates one object at a time
    records = df.to_dict('records')
    
    try:
        # Validate the first record to check structure
        # For a full dataset validation, we might need a schema for 'items'
        # Assuming the schema defines the structure of a single record
        validator = Draft7Validator(schema)
        
        for i, record in enumerate(records):
            # Ensure all expected columns are present
            for field in schema.get('properties', {}):
                if field not in record:
                    errors.append(f"Row {i}: Missing required field '{field}'")
            
            # Validate each field against its definition
            properties = schema.get('properties', {})
            for field, value in record.items():
                if field in properties:
                    field_schema = properties[field]
                    expected_type = field_schema.get('type')
                    
                    # Type checking
                    if expected_type == 'number':
                        if not isinstance(value, (int, float)) or pd.isna(value):
                            errors.append(f"Row {i}: Field '{field}' must be a number, got {type(value).__name__}")
                    elif expected_type == 'string':
                        if not isinstance(value, str):
                            errors.append(f"Row {i}: Field '{field}' must be a string, got {type(value).__name__}")
                    elif expected_type == 'boolean':
                        if not isinstance(value, bool):
                            errors.append(f"Row {i}: Field '{field}' must be a boolean, got {type(value).__name__}")
                    
                    # Specific constraints
                    if 'minimum' in field_schema and isinstance(value, (int, float)):
                        if value < field_schema['minimum']:
                            errors.append(f"Row {i}: Field '{field}' value {value} is less than minimum {field_schema['minimum']}")
                    
                    if 'pattern' in field_schema and isinstance(value, str):
                        import re
                        if not re.match(field_schema['pattern'], value):
                            errors.append(f"Row {i}: Field '{field}' value '{value}' does not match pattern '{field_schema['pattern']}'")
            
            # Check for required fields
            required_fields = schema.get('required', [])
            for req_field in required_fields:
                if req_field not in record:
                    errors.append(f"Row {i}: Missing required field '{req_field}'")
                    
    except Exception as e:
        errors.append(f"Schema validation error: {str(e)}")
    
    return errors

def cross_reference_cif_ids(df: pd.DataFrame, cif_dir: str) -> List[str]:
    """
    Cross-reference COD IDs in the CSV against the original CIF filenames.
    Ensures data integrity per FR-017.
    """
    errors = []
    
    if not os.path.exists(cif_dir):
        logger.warning(f"CIF directory not found: {cif_dir}. Skipping cross-reference check.")
        return errors
    
    # Get all CIF files in the directory
    cif_files = [f for f in os.listdir(cif_dir) if f.endswith('.cif')]
    cif_ids_in_dir = set()
    for f in cif_files:
        # Extract ID from filename (assuming format like cod_1234567.cif or similar)
        base_name = os.path.splitext(f)[0]
        # Try to extract numeric ID
        import re
        match = re.search(r'(\d+)', base_name)
        if match:
            cif_ids_in_dir.add(match.group(1))
    
    # Check each row in the DataFrame
    if 'cod_id' in df.columns:
        missing_ids = []
        for idx, row in df.iterrows():
            cod_id = str(row['cod_id']).strip()
            if cod_id and cod_id not in cif_ids_in_dir:
                missing_ids.append(cod_id)
        
        if missing_ids:
            errors.append(f"Found {len(missing_ids)} COD IDs in dataset that are not present in {cif_dir}: {missing_ids[:10]}...")
    else:
        errors.append("Dataset does not contain 'cod_id' column for cross-referencing.")
    
    return errors

def validate_dataset(input_csv: str, schema_path: str, cif_dir: str) -> bool:
    """
    Main validation function for the dataset.
    
    Args:
        input_csv: Path to the dataset CSV file
        schema_path: Path to the schema YAML file
        cif_dir: Path to the directory containing original CIF files
    
    Returns:
        True if validation passes, False otherwise
    """
    # Check if input file exists
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input dataset not found: {input_csv}")
    
    # Load the dataset
    logger.info(f"Loading dataset from {input_csv}")
    df = pd.read_csv(input_csv)
    
    logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
    
    # Load schema
    logger.info(f"Loading schema from {schema_path}")
    schema = load_schema(schema_path)
    
    # Perform schema validation
    logger.info("Validating dataset against schema...")
    schema_errors = validate_schema(df, schema)
    
    if schema_errors:
        logger.error(f"Schema validation failed with {len(schema_errors)} errors:")
        for err in schema_errors[:10]:  # Log first 10 errors
            logger.error(f"  - {err}")
        if len(schema_errors) > 10:
            logger.error(f"  ... and {len(schema_errors) - 10} more errors")
    else:
        logger.info("Schema validation passed.")
    
    # Perform cross-reference validation
    logger.info("Cross-referencing COD IDs with CIF files...")
    cross_ref_errors = cross_reference_cif_ids(df, cif_dir)
    
    if cross_ref_errors:
        logger.error(f"Cross-reference validation failed with {len(cross_ref_errors)} errors:")
        for err in cross_ref_errors:
            logger.error(f"  - {err}")
    else:
        logger.info("Cross-reference validation passed.")
    
    # Combine all errors
    all_errors = schema_errors + cross_ref_errors
    
    # Log summary statistics
    log_processing_statistics(
        total_records=len(df),
        valid_records=len(df) if not all_errors else len(df) - len(set([e.split(':')[0].replace('Row ', '') for e in all_errors if e.startswith('Row')])),
        error_count=len(all_errors),
        phase="Validation"
    )
    
    if all_errors:
        logger.error(f"Dataset validation FAILED with {len(all_errors)} errors.")
        return False
    else:
        logger.info("Dataset validation PASSED successfully.")
        return True

def main():
    """Main entry point for the validation script."""
    # Setup logging
    setup_logging(level=logging.INFO)
    
    # Ensure directories exist
    ensure_directories()
    
    # Fix seed for reproducibility
    fix_seed(42)
    
    try:
        # Run validation
        is_valid = validate_dataset(
            input_csv=INPUT_CSV,
            schema_path=SCHEMA_PATH,
            cif_dir=RAW_CIF_DIR
        )
        
        if is_valid:
            print("✅ Dataset validation successful. All checks passed.")
            sys.exit(0)
        else:
            print("❌ Dataset validation failed. Check logs for details.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()