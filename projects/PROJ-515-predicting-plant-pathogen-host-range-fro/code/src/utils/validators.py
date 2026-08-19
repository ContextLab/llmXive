"""
Validation utilities to enforce contract schemas.
Implements base validation logic for data integrity and schema compliance.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from loguru import logger

from src.utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Global registry of loaded schemas
_schema_registry: Dict[str, Dict[str, Any]] = {}

def _load_schema(schema_name: str, contracts_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load a schema definition from the contracts directory.
    
    Args:
        schema_name: Name of the schema (e.g., 'dataset', 'genomic_features')
        contracts_dir: Path to contracts directory (defaults to config)
        
    Returns:
        Schema definition as a dictionary
        
    Raises:
        FileNotFoundError: If schema file does not exist
        ValueError: If schema name is invalid
    """
    # Resolve contracts directory
    if contracts_dir is None:
        # Default to project structure
        contracts_dir = Path(__file__).parent.parent.parent / "contracts"
    
    if not contracts_dir.exists():
        raise FileNotFoundError(f"Contracts directory not found: {contracts_dir}")
    
    # Construct file path
    schema_file = contracts_dir / f"{schema_name}.schema.yaml"
    
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    
    # Load schema content
    # Note: Using simple YAML parsing without external dependency for robustness
    # In production, pyyaml would be used for full YAML parsing
    schema_content = {}
    try:
        import yaml
        with open(schema_file, 'r') as f:
            schema_content = yaml.safe_load(f)
    except ImportError:
        # Fallback for environments without pyyaml
        logger.warning("pyyaml not available, using basic YAML parsing")
        with open(schema_file, 'r') as f:
            lines = f.readlines()
            current_key = None
            for line in lines:
                line = line.rstrip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('  '):
                    # Nested key
                    parts = line.strip().split(':')
                    if len(parts) >= 2:
                        key = parts[0].strip()
                        value = ':'.join(parts[1:]).strip()
                        if current_key:
                            if current_key not in schema_content:
                                schema_content[current_key] = {}
                            schema_content[current_key][key] = value
                else:
                    # Top-level key
                    parts = line.split(':')
                    if len(parts) >= 2:
                        current_key = parts[0].strip()
                        value = ':'.join(parts[1:]).strip()
                        schema_content[current_key] = value
    
    if not schema_content:
        raise ValueError(f"Empty or invalid schema: {schema_file}")
    
    return schema_content

def validate_schema_exists(schema_name: str, contracts_dir: Optional[Path] = None) -> bool:
    """
    Check if a schema definition exists in the contracts directory.
    
    Args:
        schema_name: Name of the schema to check
        contracts_dir: Path to contracts directory
        
    Returns:
        True if schema exists, False otherwise
    """
    if contracts_dir is None:
        contracts_dir = Path(__file__).parent.parent.parent / "contracts"
    
    schema_file = contracts_dir / f"{schema_name}.schema.yaml"
    exists = schema_file.exists()
    if exists:
        logger.debug(f"Schema exists: {schema_name}")
    else:
        logger.warning(f"Schema not found: {schema_name}")
    return exists

def list_available_schemas(contracts_dir: Optional[Path] = None) -> List[str]:
    """
    List all available schema definitions in the contracts directory.
    
    Args:
        contracts_dir: Path to contracts directory
        
    Returns:
        List of schema names (without .schema.yaml extension)
    """
    if contracts_dir is None:
        contracts_dir = Path(__file__).parent.parent.parent / "contracts"
    
    if not contracts_dir.exists():
        logger.warning(f"Contracts directory not found: {contracts_dir}")
        return []
    
    schemas = []
    for file in contracts_dir.glob("*.schema.yaml"):
        schema_name = file.stem.replace('.schema', '')
        schemas.append(schema_name)
    
    logger.info(f"Found {len(schemas)} schemas: {schemas}")
    return sorted(schemas)

def validate_all_schemas_exist(contracts_dir: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Validate that all expected schemas exist.
    
    Args:
        contracts_dir: Path to contracts directory
        
    Returns:
        Tuple of (all_exist, list_of_missing_schemas)
    """
    expected_schemas = ['dataset', 'genomic_features', 'interaction', 'model_output']
    missing = []
    
    for schema_name in expected_schemas:
        if not validate_schema_exists(schema_name, contracts_dir):
            missing.append(schema_name)
    
    all_exist = len(missing) == 0
    if not all_exist:
        logger.error(f"Missing schemas: {missing}")
    else:
        logger.info("All expected schemas are present")
    
    return all_exist, missing

def check_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if all required fields are present in a data dictionary.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        Tuple of (all_present, list_of_missing_fields)
    """
    missing = []
    for field in required_fields:
        if field not in data:
            missing.append(field)
    
    all_present = len(missing) == 0
    if not all_present:
        logger.warning(f"Missing required fields: {missing}")
    return all_present, missing

def validate_dataframe_schema(df: Any, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a pandas DataFrame against a schema definition.
    
    Args:
        df: DataFrame to validate
        schema: Schema definition dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    import pandas as pd
    
    errors = []
    
    # Check if input is a DataFrame
    if not isinstance(df, pd.DataFrame):
        errors.append(f"Expected DataFrame, got {type(df).__name__}")
        return False, errors
    
    # Extract schema requirements
    schema_columns = schema.get('columns', {})
    required_columns = schema.get('required_columns', [])
    
    # Check required columns
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    # Check column types if specified
    for col_name, col_schema in schema_columns.items():
        if col_name in df.columns:
            expected_type = col_schema.get('type')
            if expected_type:
                actual_type = df[col_name].dtype
                # Simple type mapping
                type_map = {
                    'int': ['int64', 'int32', 'int16', 'int8'],
                    'float': ['float64', 'float32'],
                    'string': ['object', 'string'],
                    'bool': ['bool']
                }
                if expected_type in type_map:
                    if actual_type not in type_map[expected_type]:
                        errors.append(
                            f"Column '{col_name}' has type {actual_type}, "
                            f"expected {expected_type}"
                        )
                elif str(actual_type) != expected_type:
                    errors.append(
                        f"Column '{col_name}' has type {actual_type}, "
                        f"expected {expected_type}"
                    )
        
        # Check for null values if required
        if col_schema.get('required', False) and col_name in df.columns:
            null_count = df[col_name].isna().sum()
            if null_count > 0:
                errors.append(
                    f"Column '{col_name}' has {null_count} null values "
                    f"but is marked as required"
                )
    
    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(f"DataFrame validation failed: {errors}")
    return is_valid, errors

def validate_data(data: Any, schema_name: str, contracts_dir: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Validate data against a named schema.
    
    Args:
        data: Data to validate (dict, DataFrame, or file path)
        schema_name: Name of the schema to validate against
        contracts_dir: Path to contracts directory
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Load schema
    try:
        schema = _load_schema(schema_name, contracts_dir)
    except (FileNotFoundError, ValueError) as e:
        return False, [f"Failed to load schema '{schema_name}': {str(e)}"]
    
    # Validate based on data type
    if isinstance(data, dict):
        # Check required fields in dictionary
        required_fields = schema.get('required_fields', [])
        is_valid, missing = check_required_fields(data, required_fields)
        if not is_valid:
            errors.extend([f"Missing field: {f}" for f in missing])
        
        # Additional type checks if defined
        field_types = schema.get('field_types', {})
        for field, expected_type in field_types.items():
            if field in data:
                actual_type = type(data[field]).__name__
                if expected_type != actual_type:
                    errors.append(
                        f"Field '{field}' has type {actual_type}, "
                        f"expected {expected_type}"
                    )
    
    elif hasattr(data, 'columns'):  # DataFrame-like
        is_valid, df_errors = validate_dataframe_schema(data, schema)
        errors.extend(df_errors)
    
    elif isinstance(data, (str, Path)):
        # Validate file existence
        file_path = Path(data)
        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
        else:
            # Try to load and validate content
            try:
                if file_path.suffix == '.json':
                    with open(file_path, 'r') as f:
                        content = json.load(f)
                    is_valid, content_errors = validate_data(content, schema_name, contracts_dir)
                    errors.extend(content_errors)
                elif file_path.suffix == '.csv':
                    import pandas as pd
                    df = pd.read_csv(file_path)
                    is_valid, df_errors = validate_dataframe_schema(df, schema)
                    errors.extend(df_errors)
            except Exception as e:
                errors.append(f"Failed to load file {file_path}: {str(e)}")
    else:
        errors.append(f"Unsupported data type for validation: {type(data)}")
    
    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(f"Data validation failed for '{schema_name}': {errors}")
    return is_valid, errors

def validate_file(file_path: Union[str, Path], schema_name: str, contracts_dir: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Validate a file against a schema.
    
    Args:
        file_path: Path to the file to validate
        schema_name: Name of the schema to validate against
        contracts_dir: Path to contracts directory
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    return validate_data(file_path, schema_name, contracts_dir)

def validate_pipeline_output(
    output_dir: Union[str, Path],
    contracts_dir: Optional[Path] = None
) -> Dict[str, bool]:
    """
    Validate all outputs from a pipeline run against their respective schemas.
    
    Args:
        output_dir: Directory containing pipeline outputs
        contracts_dir: Path to contracts directory
        
    Returns:
        Dictionary mapping output file names to validation status
    """
    output_dir = Path(output_dir)
    if not output_dir.exists():
        logger.error(f"Output directory not found: {output_dir}")
        return {}
    
    results = {}
    
    # Define expected outputs and their schemas
    output_mappings = {
        'features_matrix.csv': 'genomic_features',
        'interactions_merged.csv': 'interaction',
        'model_output.json': 'model_output',
        'dataset.csv': 'dataset'
    }
    
    for filename, schema_name in output_mappings.items():
        file_path = output_dir / filename
        if file_path.exists():
            is_valid, errors = validate_file(file_path, schema_name, contracts_dir)
            results[filename] = is_valid
            if not is_valid:
                logger.warning(f"Validation failed for {filename}: {errors}")
            else:
                logger.info(f"Validation passed for {filename}")
        else:
            # File not found is not necessarily a validation error
            # but may indicate incomplete pipeline run
            logger.debug(f"Expected output not found: {filename}")
            results[filename] = False
    
    return results