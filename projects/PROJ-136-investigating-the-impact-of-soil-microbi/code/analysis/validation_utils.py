"""
Data validation utilities using jsonschema against contract schemas.

This module provides functions to load YAML schema contracts, validate
individual records (dicts), and validate entire DataFrames against those schemas.
"""
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd
from jsonschema import validate, ValidationError, Draft7Validator, ValidationError as JsonSchemaValidationError
from jsonschema.exceptions import best_match

# Configure logging for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON schema from a YAML or JSON file.
    
    Args:
        schema_path: Path to the schema file (.yaml, .yml, or .json)
        
    Returns:
        The schema as a dictionary
        
    Raises:
        FileNotFoundError: If the schema file does not exist
        ValueError: If the file format is unsupported or parsing fails
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix in ['.yaml', '.yml']:
            schema = yaml.safe_load(f)
        elif path.suffix == '.json':
            schema = json.load(f)
        else:
            raise ValueError(f"Unsupported schema file format: {path.suffix}")
            
    if schema is None:
        raise ValueError(f"Schema file is empty: {path}")
        
    logger.info(f"Successfully loaded schema from {path}")
    return schema


def get_schema_validator(schema: Dict[str, Any]) -> Draft7Validator:
    """
    Create a Draft7Validator instance from a schema dictionary.
    
    Args:
        schema: The schema dictionary
        
    Returns:
        A Draft7Validator instance
    """
    return Draft7Validator(schema)


def validate_record(record: Dict[str, Any], schema: Dict[str, Any], schema_name: str = "unknown") -> bool:
    """
    Validate a single record (dictionary) against a schema.
    
    Args:
        record: The record to validate
        schema: The schema to validate against
        schema_name: Name of the schema for logging purposes
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        ValidationError: If validation fails (optional, can be caught by caller)
    """
    try:
        validate(instance=record, schema=schema)
        logger.debug(f"Record validated successfully against {schema_name}")
        return True
    except ValidationError as e:
        logger.error(f"Validation error for {schema_name}: {e.message}")
        logger.error(f"Failed path: {list(e.absolute_path)}")
        # Log the best match for complex nested errors
        best = best_match(e.context) if e.context else None
        if best:
            logger.error(f"Best match: {best.message} at {list(best.absolute_path)}")
        return False


def validate_dataframe_records(
    df: pd.DataFrame, 
    schema: Dict[str, Any], 
    schema_name: str = "unknown",
    strict: bool = True
) -> List[Dict[str, Any]]:
    """
    Validate all records in a DataFrame against a schema.
    
    Args:
        df: The DataFrame to validate
        schema: The schema to validate against
        schema_name: Name of the schema for logging purposes
        strict: If True, raise an error if any record fails. If False, return details.
        
    Returns:
        A list of validation results. Each result is a dict with:
        - index: row index
        - valid: bool
        - error: error message if invalid, None otherwise
        
    Raises:
        ValidationError: If strict=True and any record fails validation
    """
    results = []
    failed_count = 0
    
    for idx, row in df.iterrows():
        record = row.to_dict()
        is_valid = validate_record(record, schema, schema_name)
        
        if not is_valid:
            failed_count += 1
            # Re-validate to capture the specific error message for this row
            try:
                validate(instance=record, schema=schema)
            except ValidationError as e:
                results.append({
                    "index": idx,
                    "valid": False,
                    "error": str(e.message)
                })
            continue
            
        results.append({
            "index": idx,
            "valid": True,
            "error": None
        })
        
    if failed_count > 0:
        logger.warning(f"Validation of {schema_name} found {failed_count}/{len(df)} invalid records")
        if strict:
            raise ValidationError(f"Found {failed_count} invalid records in {schema_name}")
    else:
        logger.info(f"All {len(df)} records in {schema_name} validated successfully")
        
    return results


def validate_file_against_schema(
    file_path: Union[str, Path],
    schema_path: Union[str, Path],
    schema_name: str = "unknown"
) -> bool:
    """
    Validate a CSV file against a JSON schema.
    
    Args:
        file_path: Path to the CSV file
        schema_path: Path to the schema file
        schema_name: Name for logging
        
    Returns:
        True if all records are valid, False otherwise
    """
    try:
        schema = load_schema(schema_path)
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} records from {file_path}")
        
        validate_dataframe_records(df, schema, schema_name, strict=True)
        return True
        
    except Exception as e:
        logger.error(f"Validation failed for {file_path}: {str(e)}")
        return False
