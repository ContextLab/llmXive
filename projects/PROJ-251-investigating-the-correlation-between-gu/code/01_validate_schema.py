import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import yaml
import jsonschema
from jsonschema import ValidationError, SchemaError

# Import logging config to ensure consistent logging format
from utils.logging_config import get_logger, log_error_context
from utils.config import get_processed_path, get_specs_path

logger = get_logger(__name__)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load the YAML schema file and return it as a dictionary.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    if schema is None:
        raise ValueError(f"Schema file is empty: {schema_path}")
        
    logger.info(f"Successfully loaded schema from {schema_path}")
    return schema


def validate_csv_against_schema(data_path: Path, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate each row of the CSV dataset against the provided JSON schema.
    
    The schema expects a specific structure where:
    - subject_id is a string
    - taxa_abundances is an object with numeric values
    - titer_baseline and titer_post are numbers
    
    Since the CSV is flattened (taxa as columns), we reconstruct the expected
    object structure for each row before validation.
    
    Args:
        data_path: Path to the CSV file to validate.
        schema: The loaded schema dictionary.
        
    Returns:
        A list of validation error dictionaries. Empty if validation passes.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
        
    logger.info(f"Validating {data_path} against schema...")
    
    df = pd.read_csv(data_path)
    errors = []
    
    # Identify taxon columns (all columns except known metadata)
    known_metadata = {'subject_id', 'titer_baseline', 'titer_post', 'shannon_diversity', 'log_titer'}
    # We might have CLR transformed columns too, e.g., taxon_clr
    # We need to identify columns that represent taxa abundances
    # Based on the pipeline, these are likely the original taxon columns
    taxon_columns = [col for col in df.columns if col not in known_metadata and not col.endswith('_clr')]
    
    if not taxon_columns:
        logger.warning(f"No taxon columns found in {data_path}. Validation may be incomplete.")
    
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        
        # Reconstruct the expected structure for schema validation
        # The schema expects 'taxa_abundances' to be an object of taxon_name -> value
        validated_row = {
            'subject_id': row_dict.get('subject_id'),
            'titer_baseline': row_dict.get('titer_baseline'),
            'titer_post': row_dict.get('titer_post'),
            'taxa_abundances': {col: row_dict.get(col) for col in taxon_columns}
        }
        
        try:
            jsonschema.validate(instance=validated_row, schema=schema)
        except (ValidationError, SchemaError) as e:
            error_detail = {
                'row_index': idx,
                'subject_id': row_dict.get('subject_id'),
                'message': e.message,
                'path': list(e.path),
                'instance': str(e.instance)[:100]  # Truncate long instances
            }
            errors.append(error_detail)
            logger.warning(f"Validation error at row {idx} (subject {row_dict.get('subject_id')}): {e.message}")
    
    return errors


def run_validation() -> Dict[str, Any]:
    """
    Main validation runner that orchestrates loading the schema,
    validating the data, and generating a report.
    
    Returns:
        A dictionary containing the validation results summary.
    """
    specs_path = get_specs_path()
    schema_path = specs_path / "contracts" / "dataset.schema.yaml"
    data_path = get_processed_path() / "data_clr.csv"
    
    report = {
        'status': 'unknown',
        'data_file': str(data_path),
        'schema_file': str(schema_path),
        'total_rows': 0,
        'valid_rows': 0,
        'invalid_rows': 0,
        'errors': []
    }
    
    try:
        # Load schema
        schema = load_schema(schema_path)
        
        # Load and validate data
        errors = validate_csv_against_schema(data_path, schema)
        
        df = pd.read_csv(data_path)
        total_rows = len(df)
        invalid_rows = len(errors)
        valid_rows = total_rows - invalid_rows
        
        report['total_rows'] = total_rows
        report['valid_rows'] = valid_rows
        report['invalid_rows'] = invalid_rows
        report['errors'] = errors
        
        if invalid_rows == 0:
            report['status'] = 'passed'
            logger.info(f"Validation PASSED: {valid_rows}/{total_rows} rows are valid.")
        else:
            report['status'] = 'failed'
            logger.error(f"Validation FAILED: {invalid_rows}/{total_rows} rows failed validation.")
            
    except FileNotFoundError as e:
        report['status'] = 'error'
        report['error_message'] = str(e)
        log_error_context("Schema Validation Failed", str(e))
    except Exception as e:
        report['status'] = 'error'
        report['error_message'] = str(e)
        log_error_context("Schema Validation Failed", str(e))
        raise
        
    return report


def main():
    """Entry point for the schema validation script."""
    logger.info("Starting schema validation for T013...")
    
    result = run_validation()
    
    # Write the report to the results directory
    results_dir = get_processed_path().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    report_path = results_dir / "schema_validation_report.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)
        
    logger.info(f"Validation report written to {report_path}")
    
    if result['status'] == 'failed':
        logger.error("Validation failed. Check the report for details.")
        sys.exit(1)
    elif result['status'] == 'error':
        logger.error("Validation encountered an error.")
        sys.exit(1)
    else:
        logger.info("Validation completed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
