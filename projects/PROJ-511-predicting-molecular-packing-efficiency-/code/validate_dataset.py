import os
import sys
import logging
import yaml
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd

from config import get_data_dir, get_base_dir, get_cod_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(get_data_dir(), '..', 'logs', 'validation.log'))
    ]
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema from file."""
    try:
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing schema file: {e}")
        raise

def validate_schema(data: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate dataset against JSON schema.
    Returns a list of validation errors.
    """
    errors = []
    
    # Check required columns
    required_cols = schema.get('properties', {}).keys()
    missing_cols = set(required_cols) - set(data.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Validate data types and constraints for each column
    for col_name, col_schema in schema.get('properties', {}).items():
        if col_name not in data.columns:
            continue
        
        col_data = data[col_name]
        
        # Check for null values if not allowed
        if col_schema.get('type') != 'null' and col_data.isnull().any():
            # Check if null is explicitly allowed in enum or pattern
            if 'enum' not in col_schema and 'pattern' not in col_schema:
                errors.append(f"Column '{col_name}' contains null values")
        
        # Type-specific validations
        if col_schema.get('type') == 'string':
            # Check minLength
            if 'minLength' in col_schema:
                invalid_rows = col_data[col_data.str.len() < col_schema['minLength']]
                if not invalid_rows.empty:
                    errors.append(f"Column '{col_name}' has values with length < {col_schema['minLength']}")
            
            # Check pattern
            if 'pattern' in col_schema:
                import re
                pattern = re.compile(col_schema['pattern'])
                invalid_rows = col_data[~col_data.astype(str).str.match(pattern)]
                if not invalid_rows.empty:
                    errors.append(f"Column '{col_name}' has values not matching pattern: {col_schema['pattern']}")
            
            # Check enum
            if 'enum' in col_schema:
                invalid_rows = col_data[~col_data.isin(col_schema['enum'])]
                if not invalid_rows.empty:
                    errors.append(f"Column '{col_name}' has values not in enum: {col_schema['enum']}")
        
        elif col_schema.get('type') == 'number':
            # Check minimum
            if 'minimum' in col_schema:
                invalid_rows = col_data[col_data < col_schema['minimum']]
                if not invalid_rows.empty:
                    errors.append(f"Column '{col_name}' has values < {col_schema['minimum']}")
            
            # Check maximum
            if 'maximum' in col_schema:
                invalid_rows = col_data[col_data > col_schema['maximum']]
                if not invalid_rows.empty:
                    errors.append(f"Column '{col_name}' has values > {col_schema['maximum']}")
            
            # Check exclusiveMinimum
            if 'exclusiveMinimum' in col_schema:
                invalid_rows = col_data[col_data <= col_schema['exclusiveMinimum']]
                if not invalid_rows.empty:
                    errors.append(f"Column '{col_name}' has values <= {col_schema['exclusiveMinimum']}")
        
        elif col_schema.get('type') == 'integer':
            # Check minimum
            if 'minimum' in col_schema:
                invalid_rows = col_data[col_data < col_schema['minimum']]
                if not invalid_rows.empty:
                    errors.append(f"Column '{col_name}' has values < {col_schema['minimum']}")
            
            # Check maximum
            if 'maximum' in col_schema:
                invalid_rows = col_data[col_data > col_schema['maximum']]
                if not invalid_rows.empty:
                    errors.append(f"Column '{col_name}' has values > {col_schema['maximum']}")
        
        elif col_schema.get('type') == 'boolean':
            # Check valid boolean values
            valid_bools = [True, False, 0, 1, 'True', 'False', 'true', 'false']
            invalid_rows = col_data[~col_data.isin(valid_bools)]
            if not invalid_rows.empty:
                errors.append(f"Column '{col_name}' has non-boolean values")
        
        elif col_schema.get('type') == 'array':
            # Check array constraints
            if 'minItems' in col_schema:
                # For array columns stored as strings or lists
                if col_data.dtype == object:
                    invalid_rows = col_data[col_data.apply(lambda x: len(x) < col_schema['minItems'] if isinstance(x, list) else False)]
                    if not invalid_rows.empty:
                        errors.append(f"Column '{col_name}' has arrays with < {col_schema['minItems']} items")
            
            if 'maxItems' in col_schema:
                if col_data.dtype == object:
                    invalid_rows = col_data[col_data.apply(lambda x: len(x) > col_schema['maxItems'] if isinstance(x, list) else False)]
                    if not invalid_rows.empty:
                        errors.append(f"Column '{col_name}' has arrays with > {col_schema['maxItems']} items")
    
    return errors

def cross_reference_cif_ids(dataset_path: str, cif_dir: str) -> List[str]:
    """
    Cross-reference COD IDs in the dataset against downloaded CIF files.
    Returns a list of errors if any COD IDs are missing.
    """
    errors = []
    
    # Load dataset
    try:
        df = pd.read_csv(dataset_path)
    except Exception as e:
        errors.append(f"Failed to load dataset: {e}")
        return errors
    
    # Get list of CIF files
    cif_files = [f for f in os.listdir(cif_dir) if f.endswith('.cif')]
    cif_ids_in_files = set()
    
    for cif_file in cif_files:
        # Extract COD ID from filename (assumes format COD-XXXXXXX.cif)
        cif_id = cif_file.replace('.cif', '')
        cif_ids_in_files.add(cif_id)
    
    # Check for missing CIF files
    cod_ids_in_dataset = set(df['cod_id'].unique())
    missing_cif_ids = cod_ids_in_dataset - cif_ids_in_files
    
    if missing_cif_ids:
        errors.append(f"Missing CIF files for COD IDs: {missing_cif_ids}")
    
    return errors

def validate_dataset(
    dataset_path: str,
    schema_path: str,
    cif_dir: str,
    output_report_path: str
) -> bool:
    """
    Main validation function.
    Returns True if validation passes, False otherwise.
    """
    logger.info(f"Starting validation of dataset: {dataset_path}")
    
    # Load schema
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False
    
    # Validate schema
    schema_errors = validate_schema(pd.read_csv(dataset_path), schema)
    if schema_errors:
        logger.error(f"Schema validation failed with {len(schema_errors)} errors:")
        for error in schema_errors:
            logger.error(f"  - {error}")
    else:
        logger.info("Schema validation passed")
    
    # Cross-reference CIF IDs
    cif_errors = cross_reference_cif_ids(dataset_path, cif_dir)
    if cif_errors:
        logger.error(f"CIF cross-reference validation failed with {len(cif_errors)} errors:")
        for error in cif_errors:
            logger.error(f"  - {error}")
    else:
        logger.info("CIF cross-reference validation passed")
    
    # Compile validation report
    validation_report = {
        'dataset_path': dataset_path,
        'schema_path': schema_path,
        'cod_source_url': get_cod_url(),
        'validation_passed': len(schema_errors) == 0 and len(cif_errors) == 0,
        'schema_errors': schema_errors,
        'cif_errors': cif_errors,
        'total_schema_errors': len(schema_errors),
        'total_cif_errors': len(cif_errors)
    }
    
    # Write validation report
    try:
        with open(output_report_path, 'w') as f:
            json.dump(validation_report, f, indent=2)
        logger.info(f"Validation report written to: {output_report_path}")
    except Exception as e:
        logger.error(f"Failed to write validation report: {e}")
        return False
    
    return validation_report['validation_passed']

def main():
    """Main entry point for dataset validation."""
    # Define paths
    base_dir = get_base_dir()
    data_dir = get_data_dir()
    contracts_dir = os.path.join(base_dir, 'contracts')
    
    dataset_path = os.path.join(data_dir, 'dataset.csv')
    schema_path = os.path.join(contracts_dir, 'dataset.schema.yaml')
    cif_dir = os.path.join(data_dir, 'raw_cif')
    report_path = os.path.join(data_dir, 'validation_report.json')
    
    # Check if dataset exists
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset not found: {dataset_path}")
        sys.exit(1)
    
    # Check if schema exists
    if not os.path.exists(schema_path):
        logger.error(f"Schema not found: {schema_path}")
        sys.exit(1)
    
    # Check if CIF directory exists
    if not os.path.exists(cif_dir):
        logger.warning(f"CIF directory not found: {cif_dir}")
        logger.warning("Skipping CIF cross-reference validation")
    
    # Run validation
    is_valid = validate_dataset(dataset_path, schema_path, cif_dir, report_path)
    
    if is_valid:
        logger.info("Dataset validation PASSED")
        sys.exit(0)
    else:
        logger.error("Dataset validation FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()