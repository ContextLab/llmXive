"""
Validation utilities for enforcing contract schemas.

This module provides functions to validate data against the schema definitions
found in the contracts/ directory. It ensures data integrity throughout the
pipeline execution.
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from loguru import logger
from src.utils.logging import get_logger
import pandas as pd


def _get_logger() -> logger:
    """Get the project logger instance."""
    return get_logger()


def _load_schema(schema_name: str, contracts_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load a schema definition from the contracts directory.
    
    Args:
        schema_name: Name of the schema (without .yaml extension)
        contracts_dir: Path to the contracts directory
        
    Returns:
        Schema dictionary or None if not found
    """
    schema_path = contracts_dir / f"{schema_name}.schema.yaml"
    if not schema_path.exists():
        _get_logger().warning(f"Schema not found: {schema_path}")
        return None
    
    try:
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        _get_logger().error(f"Failed to load schema {schema_name}: {e}")
        return None


def validate_schema_exists(schema_name: str, contracts_dir: Optional[Path] = None) -> bool:
    """
    Check if a schema file exists in the contracts directory.
    
    Args:
        schema_name: Name of the schema to check
        contracts_dir: Path to contracts directory (defaults to project default)
        
    Returns:
        True if schema exists, False otherwise
    """
    if contracts_dir is None:
        contracts_dir = Path("code/contracts")
    
    schema_path = contracts_dir / f"{schema_name}.schema.yaml"
    exists = schema_path.exists()
    if exists:
        _get_logger().debug(f"Schema exists: {schema_name}")
    else:
        _get_logger().warning(f"Schema missing: {schema_name}")
    return exists


def list_available_schemas(contracts_dir: Optional[Path] = None) -> List[str]:
    """
    List all available schema files in the contracts directory.
    
    Args:
        contracts_dir: Path to contracts directory
        
    Returns:
        List of schema names (without extension)
    """
    if contracts_dir is None:
        contracts_dir = Path("code/contracts")
    
    if not contracts_dir.exists():
        _get_logger().warning(f"Contracts directory does not exist: {contracts_dir}")
        return []
    
    schemas = []
    for file in contracts_dir.glob("*.schema.yaml"):
        schemas.append(file.stem)
    
    _get_logger().info(f"Found {len(schemas)} schemas: {schemas}")
    return schemas


def validate_all_schemas_exist(contracts_dir: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Validate that all expected schemas exist.
    
    Args:
        contracts_dir: Path to contracts directory
        
    Returns:
        Tuple of (all_exist, missing_schemas_list)
    """
    expected_schemas = [
        "dataset",
        "genomic_features",
        "interaction",
        "model_output"
    ]
    
    missing = []
    for schema in expected_schemas:
        if not validate_schema_exists(schema, contracts_dir):
            missing.append(schema)
    
    all_exist = len(missing) == 0
    if not all_exist:
        _get_logger().error(f"Missing schemas: {missing}")
    
    return all_exist, missing


def check_required_fields(schema: Dict[str, Any], data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if all required fields are present in the data according to the schema.
    
    Args:
        schema: Schema dictionary
        data: Data dictionary to validate
        
    Returns:
        Tuple of (all_present, missing_fields_list)
    """
    required_fields = schema.get("required", [])
    missing = []
    
    for field in required_fields:
        if field not in data:
            missing.append(field)
    
    all_present = len(missing) == 0
    if not all_present:
        _get_logger().warning(f"Missing required fields: {missing}")
    
    return all_present, missing


def validate_dataframe_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against a schema definition.
    
    Args:
        df: DataFrame to validate
        schema: Schema dictionary with 'columns' definition
        
    Returns:
        Tuple of (valid, missing_columns_list)
    """
    if "columns" not in schema:
        _get_logger().warning("Schema has no 'columns' definition")
        return True, []
    
    schema_columns = schema["columns"]
    required_columns = [col.get("name") for col in schema_columns if col.get("required", False)]
    
    missing = []
    for col in required_columns:
        if col not in df.columns:
            missing.append(col)
    
    valid = len(missing) == 0
    if not valid:
        _get_logger().error(f"DataFrame missing required columns: {missing}")
    
    return valid, missing


def validate_data(data: Any, schema_name: str, contracts_dir: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Validate data against a named schema.
    
    Args:
        data: Data to validate (dict or DataFrame)
        schema_name: Name of the schema to validate against
        contracts_dir: Path to contracts directory
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if contracts_dir is None:
        contracts_dir = Path("code/contracts")
    
    schema = _load_schema(schema_name, contracts_dir)
    if schema is None:
        return False, f"Schema '{schema_name}' not found"
    
    if isinstance(data, dict):
        valid, missing = check_required_fields(schema, data)
        if not valid:
            return False, f"Missing required fields: {missing}"
    elif isinstance(data, pd.DataFrame):
        valid, missing = validate_dataframe_schema(data, schema)
        if not valid:
            return False, f"DataFrame missing columns: {missing}"
    else:
        return False, f"Unsupported data type: {type(data)}"
    
    _get_logger().info(f"Data validated successfully against schema: {schema_name}")
    return True, ""


def validate_file(file_path: Path, schema_name: str, contracts_dir: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Validate a file (JSON or CSV) against a schema.
    
    Args:
        file_path: Path to the file to validate
        schema_name: Name of the schema to validate against
        contracts_dir: Path to contracts directory
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    try:
        if file_path.suffix == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
            return validate_data(data, schema_name, contracts_dir)
        elif file_path.suffix == '.csv':
            df = pd.read_csv(file_path)
            return validate_data(df, schema_name, contracts_dir)
        else:
            return False, f"Unsupported file format: {file_path.suffix}"
    except Exception as e:
        return False, f"Error loading file: {e}"


def validate_pipeline_output(output_dir: Path, contracts_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Validate all expected pipeline output files against their schemas.
    
    Args:
        output_dir: Directory containing pipeline outputs
        contracts_dir: Path to contracts directory
        
    Returns:
        Dictionary with validation results for each output file
    """
    if contracts_dir is None:
        contracts_dir = Path("code/contracts")
    
    # Define expected outputs and their corresponding schemas
    outputs_to_check = [
        ("features_matrix.csv", "genomic_features"),
        ("interactions_merged.csv", "interaction"),
        ("model.pkl", None),  # Binary file, skip schema validation
        ("feature_importance.csv", "model_output"),
        ("data_quality_report.json", None),  # Report, skip schema validation
    ]
    
    results = {}
    for filename, schema_name in outputs_to_check:
        file_path = output_dir / filename
        if schema_name:
            valid, message = validate_file(file_path, schema_name, contracts_dir)
            results[filename] = {
                "exists": file_path.exists(),
                "valid": valid,
                "message": message
            }
        else:
            results[filename] = {
                "exists": file_path.exists(),
                "valid": True,
                "message": "Schema validation skipped"
            }
    
    # Log summary
    all_valid = all(r["valid"] for r in results.values())
    if all_valid:
        _get_logger().info("All pipeline outputs validated successfully")
    else:
        _get_logger().warning("Some pipeline outputs failed validation")
    
    return results