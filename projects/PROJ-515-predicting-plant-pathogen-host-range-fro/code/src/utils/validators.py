"""
Validation utilities for enforcing contract schemas.

This module provides functions to validate data against the JSON schemas
defined in the contracts/ directory. It ensures data integrity throughout
the pipeline by checking required fields, types, and value constraints.
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from loguru import logger

# Attempt to import jsonschema, provide clear error if missing
try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    logger.error("jsonschema library not installed. Install with: pip install jsonschema")
    raise

from src.utils.logging import get_logger

# Initialize logger
log = get_logger(__name__)

# Path to contracts directory relative to project root
# Assuming project root is one level up from code/src
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Mapping of schema names to file paths
SCHEMA_FILES = {
    "dataset": "dataset.schema.yaml",
    "genomic_features": "genomic_features.schema.yaml",
    "interaction": "interaction.schema.yaml",
    "model_output": "model_output.schema.yaml",
}

def _load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON schema from the contracts directory.

    Args:
        schema_name: Key from SCHEMA_FILES (e.g., 'dataset', 'interaction')

    Returns:
        Dictionary containing the parsed schema

    Raises:
        FileNotFoundError: If the schema file does not exist
        json.JSONDecodeError: If the schema file is not valid JSON/YAML
    """
    if schema_name not in SCHEMA_FILES:
        raise ValueError(f"Unknown schema name: {schema_name}. Valid names: {list(SCHEMA_FILES.keys())}")

    schema_path = CONTRACTS_DIR / SCHEMA_FILES[schema_name]

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    # Handle YAML schemas (common for JSON Schema in .yaml files)
    # If jsonschema doesn't handle YAML directly, we might need PyYAML
    try:
        import yaml
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
    except ImportError:
        raise ImportError("PyYAML is required to load .yaml schema files. Install with: pip install pyyaml")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in schema file {schema_path}: {e}")

    log.debug(f"Loaded schema '{schema_name}' from {schema_path}")
    return schema

def validate_data(data: Union[Dict, List], schema_name: str, instance_name: str = "data") -> Tuple[bool, Optional[str]]:
    """
    Validate data against a named schema.

    Args:
        data: The data to validate (dict or list)
        schema_name: Key from SCHEMA_FILES
        instance_name: Optional name for error reporting

    Returns:
        Tuple of (is_valid, error_message)
        If valid, (True, None)
        If invalid, (False, error_details)
    """
    try:
        schema = _load_schema(schema_name)
        # jsonschema.validate raises ValidationError if validation fails
        validate(instance=data, schema=schema)
        log.info(f"Validation passed for '{instance_name}' against schema '{schema_name}'")
        return True, None
    except ValidationError as e:
        error_msg = f"Validation failed for '{instance_name}' against schema '{schema_name}': {e.message}"
        log.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error validating '{instance_name}': {str(e)}"
        log.error(error_msg)
        return False, error_msg

def validate_dataframe_schema(df: Any, schema_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a pandas DataFrame against a schema.
    Converts DataFrame to a dict of records for validation.

    Args:
        df: pandas DataFrame to validate
        schema_name: Key from SCHEMA_FILES

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        import pandas as pd
        if not isinstance(df, pd.DataFrame):
            return False, f"Expected pandas DataFrame, got {type(df)}"

        # Convert to list of dicts (records)
        data_dict = df.to_dict(orient='records')
        if not data_dict:
            log.warning(f"DataFrame for '{schema_name}' is empty. Skipping validation.")
            return True, None

        return validate_data(data_dict, schema_name, instance_name=f"DataFrame_{schema_name}")

    except ImportError:
        return False, "pandas is required for DataFrame validation"
    except Exception as e:
        return False, f"Error during DataFrame validation: {str(e)}"

def validate_file(file_path: Union[str, Path], schema_name: str, format_hint: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Load data from a file and validate it against a schema.

    Args:
        file_path: Path to the data file
        schema_name: Key from SCHEMA_FILES
        format_hint: Optional hint for parsing ('json', 'csv', 'yaml')

    Returns:
        Tuple of (is_valid, error_message)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    try:
        # Determine format if not provided
        if format_hint is None:
            suffix = file_path.suffix.lower()
            if suffix in ['.json']:
                format_hint = 'json'
            elif suffix in ['.yaml', '.yml']:
                format_hint = 'yaml'
            elif suffix in ['.csv']:
                format_hint = 'csv'
            else:
                return False, f"Cannot determine format for file: {file_path}"

        # Load data
        data = None
        if format_hint == 'json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif format_hint == 'yaml':
            import yaml
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        elif format_hint == 'csv':
            import pandas as pd
            df = pd.read_csv(file_path)
            return validate_dataframe_schema(df, schema_name)
        else:
            return False, f"Unsupported format: {format_hint}"

        if data is None:
            return False, f"File {file_path} is empty or null"

        return validate_data(data, schema_name, instance_name=str(file_path))

    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in {file_path}: {e}"
    except Exception as e:
        return False, f"Error loading/validating {file_path}: {str(e)}"

def check_required_fields(data: Dict, required_fields: List[str], instance_name: str = "data") -> Tuple[bool, List[str]]:
    """
    Manually check if required fields exist in a dictionary.

    Args:
        data: Dictionary to check
        required_fields: List of field names that must be present
        instance_name: Name for error reporting

    Returns:
        Tuple of (all_present, missing_fields)
    """
    missing = [field for field in required_fields if field not in data]
    if missing:
        log.warning(f"Missing required fields in '{instance_name}': {missing}")
        return False, missing
    return True, []

def validate_schema_exists(schema_name: str) -> bool:
    """
    Check if a schema file exists.

    Args:
        schema_name: Key from SCHEMA_FILES

    Returns:
        True if schema file exists, False otherwise
    """
    if schema_name not in SCHEMA_FILES:
        return False
    schema_path = CONTRACTS_DIR / SCHEMA_FILES[schema_name]
    return schema_path.exists()

def list_available_schemas() -> List[str]:
    """
    List all available schema names.

    Returns:
        List of schema names (keys from SCHEMA_FILES)
    """
    return list(SCHEMA_FILES.keys())

def validate_all_schemas_exist() -> Tuple[bool, List[str]]:
    """
    Validate that all expected schema files exist.

    Returns:
        Tuple of (all_exist, missing_schemas)
    """
    missing = []
    for name in SCHEMA_FILES:
        if not validate_schema_exists(name):
            missing.append(name)
    
    if missing:
        log.warning(f"Missing schema files: {missing}")
        return False, missing
    
    log.info("All required schema files are present")
    return True, []

def validate_pipeline_output(
    model_path: Union[str, Path],
    feature_importance_path: Union[str, Path],
    prediction_path: Union[str, Path]
) -> Dict[str, Any]:
    """
    Validate all primary pipeline output files against their schemas.

    Args:
        model_path: Path to model.pkl (binary, schema validation skipped)
        feature_importance_path: Path to feature_importance.csv
        prediction_path: Path to prediction.csv

    Returns:
        Dictionary with validation results for each file
    """
    results = {}
    
    # Model file is binary, just check existence
    model_path = Path(model_path)
    results['model'] = {
        'exists': model_path.exists(),
        'valid': model_path.exists()  # Cannot validate binary schema easily
    }
    if not results['model']['exists']:
        log.error(f"Model file not found: {model_path}")

    # Feature importance (CSV)
    if feature_importance_path:
        fp = Path(feature_importance_path)
        if fp.exists():
            # Determine schema name based on filename or mapping
            # Assuming feature_importance matches 'genomic_features' or a specific report schema
            # For now, we'll try to validate as 'genomic_features' if it contains feature data
            is_valid, error = validate_file(fp, 'genomic_features', format_hint='csv')
            results['feature_importance'] = {
                'exists': True,
                'valid': is_valid,
                'error': error
            }
        else:
            results['feature_importance'] = {
                'exists': False,
                'valid': False,
                'error': f"File not found: {fp}"
            }
            log.error(f"Feature importance file not found: {fp}")

    # Prediction output (CSV)
    if prediction_path:
        pp = Path(prediction_path)
        if pp.exists():
            # Assuming prediction output matches 'model_output' schema
            is_valid, error = validate_file(pp, 'model_output', format_hint='csv')
            results['prediction'] = {
                'exists': True,
                'valid': is_valid,
                'error': error
            }
        else:
            results['prediction'] = {
                'exists': False,
                'valid': False,
                'error': f"File not found: {pp}"
            }
            log.error(f"Prediction file not found: {pp}")

    return results

# Export public API
__all__ = [
    'validate_data',
    'validate_dataframe_schema',
    'validate_file',
    'check_required_fields',
    'validate_schema_exists',
    'list_available_schemas',
    'validate_all_schemas_exist',
    'validate_pipeline_output',
    'SCHEMA_FILES',
    'CONTRACTS_DIR'
]
