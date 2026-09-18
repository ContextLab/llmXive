"""
Validation utilities for molecular conductivity project.
Includes SMILES validation, target range checks, and schema validation.
"""
import logging
import sys
import os
import json
import argparse
from typing import Tuple, List, Optional, Dict, Any
import pandas as pd
import yaml
from rdkit import Chem

from code.logging_config import setup_logging

logger = setup_logging()

def validate_smiles(smiles_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a SMILES string using RDKit.
    
    Args:
        smiles_str: SMILES string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        mol = Chem.MolFromSmiles(smiles_str)
        if mol is None:
            return False, "RDKit failed to parse SMILES"
        if mol.GetNumAtoms() == 0:
            return False, "Parsed molecule has zero atoms"
        return True, None
    except Exception as e:
        return False, str(e)

def check_target_range(values: pd.Series, min_log_range: float = 3.0) -> bool:
    """
    Check if target values have sufficient dynamic range.
    
    Args:
        values: Series of target values
        min_log_range: Minimum required log range (default 3.0)
        
    Returns:
        True if range is sufficient, False otherwise
    """
    valid_values = values.dropna()
    if len(valid_values) == 0:
        logger.error("No valid target values found")
        return False
    
    log_values = np.log10(np.abs(valid_values) + 1e-10)
    value_range = log_values.max() - log_values.min()
    
    if value_range < min_log_range:
        logger.warning(f"Target dynamic range ({value_range:.2f}) is below threshold ({min_log_range})")
        return False
    return True

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema definition.
    
    Args:
        schema_path: Path to the schema YAML file
        
    Returns:
        Schema dictionary
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_against_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against a schema definition.
    
    Args:
        df: DataFrame to validate
        schema: Schema dictionary
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Check required columns
    if 'required_columns' in schema:
        required = schema['required_columns']
        missing = [col for col in required if col not in df.columns]
        if missing:
            errors.append(f"Missing required columns: {missing}")
    
    # Check column types if specified
    if 'column_types' in schema:
        for col, expected_type in schema['column_types'].items():
            if col in df.columns:
                if expected_type == 'numeric':
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        errors.append(f"Column '{col}' should be numeric")
                elif expected_type == 'string':
                    if not pd.api.types.is_string_dtype(df[col]):
                        errors.append(f"Column '{col}' should be string")
    
    # Check for NaN in required columns
    if 'required_columns' in schema:
        for col in schema['required_columns']:
            if col in df.columns and df[col].isna().any():
                errors.append(f"Column '{col}' contains NaN values")
    
    return len(errors) == 0, errors

def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a dictionary against a JSON schema definition.
    
    Args:
        data: Dictionary to validate
        schema: Schema dictionary
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Check required fields
    if 'required_fields' in schema:
        required = schema['required_fields']
        missing = [field for field in required if field not in data]
        if missing:
            errors.append(f"Missing required fields: {missing}")
    
    # Check field types if specified
    if 'field_types' in schema:
        for field, expected_type in schema['field_types'].items():
            if field in data:
                value = data[field]
                if expected_type == 'number':
                    if not isinstance(value, (int, float)):
                        errors.append(f"Field '{field}' should be a number")
                elif expected_type == 'string':
                    if not isinstance(value, str):
                        errors.append(f"Field '{field}' should be a string")
                elif expected_type == 'array':
                    if not isinstance(value, list):
                        errors.append(f"Field '{field}' should be an array")
                elif expected_type == 'object':
                    if not isinstance(value, dict):
                        errors.append(f"Field '{field}' should be an object")
    
    return len(errors) == 0, errors

def validate_file(file_path: str, schema_path: str) -> Tuple[bool, List[str]]:
    """
    Validate a file against its schema.
    
    Args:
        file_path: Path to the file to validate
        schema_path: Path to the schema file
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    if not os.path.exists(file_path):
        return False, [f"File not found: {file_path}"]
    
    schema = load_schema(schema_path)
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.csv':
        df = pd.read_csv(file_path)
        return validate_csv_against_schema(df, schema)
    elif ext == '.json':
        with open(file_path, 'r') as f:
            data = json.load(f)
        return validate_json_against_schema(data, schema)
    else:
        return False, [f"Unsupported file extension: {ext}"]

def main():
    """
    Main entry point for validation script.
    Validates all required output files against their schemas.
    """
    parser = argparse.ArgumentParser(description="Validate output files against schemas")
    parser.add_argument('--validate-all', action='store_true', 
                      help='Validate all required output files')
    args = parser.parse_args()
    
    if args.validate_all:
        validation_results = []
        all_valid = True
        
        # Define validation pairs
        validations = [
            ('data/processed/descriptors.csv', 'contracts/descriptor_schema.yaml'),
            ('data/processed/model_results.json', 'contracts/model_results_schema.yaml'),
            ('data/processed/analysis_summary.json', 'contracts/model_results_schema.yaml'),
        ]
        
        for file_path, schema_path in validations:
            logger.info(f"Validating {file_path} against {schema_path}")
            is_valid, errors = validate_file(file_path, schema_path)
            
            if is_valid:
                logger.info(f"✓ {file_path} passed validation")
                validation_results.append({
                    'file': file_path,
                    'status': 'passed',
                    'errors': []
                })
            else:
                logger.error(f"✗ {file_path} failed validation: {errors}")
                all_valid = False
                validation_results.append({
                    'file': file_path,
                    'status': 'failed',
                    'errors': errors
                })
        
        # Ensure state directory exists
        os.makedirs('state', exist_ok=True)
        
        # Write validation log
        log_path = 'state/validation_log.json'
        with open(log_path, 'w') as f:
            json.dump({
                'validation_results': validation_results,
                'all_valid': all_valid,
                'timestamp': pd.Timestamp.now().isoformat()
            }, f, indent=2)
        
        logger.info(f"Validation log written to {log_path}")
        
        if not all_valid:
            logger.error("Validation failed for one or more files")
            sys.exit(1)
        else:
            logger.info("All validations passed")
            sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
