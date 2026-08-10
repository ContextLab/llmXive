"""
Schema validation module for the ball milling dataset.

This module enforces the schema defined in contracts/dataset.schema.yaml
and raises InsufficientDataError when schema structure (field types, presence) fails.

Note: This task does NOT check row count; row count validation is handled
later in T015a and T017c.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import pandas as pd
import yaml
from src.utils.exceptions import InsufficientDataError, SchemaValidationError

logger = logging.getLogger(__name__)

# Expected field types mapping
FIELD_TYPES = {
    'string': str,
    'float': (float, int),  # Allow int to be castable to float
    'integer': int,
    'boolean': bool,
}

REQUIRED_FIELDS = [
    'experiment_id', 'source', 'source_id', 'material_type',
    'milling_speed', 'milling_time', 'ball_to_powder_ratio',
    'youngs_modulus', 'density', 'd10', 'd50', 'd90'
]

def load_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.
    
    Args:
        schema_path: Path to the schema YAML file. Defaults to 
                    'contracts/dataset.schema.yaml' relative to project root.
    
    Returns:
        Dictionary containing the schema definition.
    
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file contains invalid YAML.
    """
    if schema_path is None:
        # Default path relative to project root
        schema_path = Path(__file__).parent.parent.parent / 'contracts' / 'dataset.schema.yaml'
    else:
        schema_path = Path(schema_path)
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    return schema

def _validate_field_presence(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate that all required fields are present in the dataframe.
    
    Args:
        df: The dataframe to validate.
        schema: The schema definition.
    
    Returns:
        List of missing required field names.
    """
    required_fields = set(REQUIRED_FIELDS)
    actual_fields = set(df.columns)
    missing_fields = required_fields - actual_fields
    return list(missing_fields)

def _validate_field_types(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate that field types match the schema requirements.
    
    Args:
        df: The dataframe to validate.
        schema: The schema definition.
    
    Returns:
        List of field names with type mismatches.
    """
    type_errors = []
    fields_info = schema.get('fields', [])
    
    for field_def in fields_info:
        field_name = field_def['name']
        expected_type_str = field_def['type']
        
        if field_name not in df.columns:
            continue  # Already caught by presence check
        
        expected_type = FIELD_TYPES.get(expected_type_str)
        if expected_type is None:
            logger.warning(f"Unknown type '{expected_type_str}' for field '{field_name}'")
            continue
        
        # Check if column values are compatible with expected type
        col = df[field_name]
        # For float, allow int and float, but not string or object
        if expected_type_str == 'float':
            # Check if the column can be numeric
            try:
                pd.to_numeric(col, errors='raise')
            except (ValueError, TypeError):
                type_errors.append(field_name)
        elif expected_type_str == 'string':
            # Check if column is object (string) or can be cast to string
            if not (col.dtype == object or pd.api.types.is_string_dtype(col)):
                # Allow numeric columns to be treated as strings if needed
                if not pd.api.types.is_numeric_dtype(col):
                    type_errors.append(field_name)
        elif expected_type_str == 'integer':
            if not pd.api.types.is_integer_dtype(col):
                type_errors.append(field_name)
        elif expected_type_str == 'boolean':
            if not pd.api.types.is_bool_dtype(col):
                type_errors.append(field_name)
    
    return type_errors

def _validate_constraints(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate data constraints defined in the schema.
    
    Args:
        df: The dataframe to validate.
        schema: The schema definition.
    
    Returns:
        List of constraint violation descriptions.
    """
    violations = []
    constraints = schema.get('constraints', [])
    
    for constraint in constraints:
        field = constraint['field']
        condition = constraint['condition']
        
        if field not in df.columns:
            continue  # Skip if field is missing (caught by presence check)
        
        try:
            # Evaluate the condition
            # Note: This is a simple evaluator for basic comparisons
            # For complex logic, we'd need a more robust parser
            if 'd10 >= 0' in condition:
                if (df[field] < 0).any():
                    violations.append(f"Field '{field}' contains negative values")
            elif 'd10 <= d50' in condition:
                if (df['d10'] > df['d50']).any():
                    violations.append("d10 values exceed d50 values")
            elif 'd50 <= d90' in condition:
                if (df['d50'] > df['d90']).any():
                    violations.append("d50 values exceed d90 values")
            elif 'milling_speed > 0' in condition:
                if (df[field] <= 0).any():
                    violations.append(f"Field '{field}' contains non-positive values")
            elif 'milling_time > 0' in condition:
                if (df[field] <= 0).any():
                    violations.append(f"Field '{field}' contains non-positive values")
        except Exception as e:
            logger.warning(f"Could not evaluate constraint '{condition}': {e}")
    
    return violations

def validate_schema(dataframe: pd.DataFrame, schema_path: Optional[str] = None) -> None:
    """
    Validate a dataframe against the dataset schema.
    
    This function checks:
    1. Presence of all required fields
    2. Data type compatibility for each field
    3. Constraint satisfaction (e.g., d10 <= d50 <= d90)
    
    Args:
        dataframe: The pandas DataFrame to validate.
        schema_path: Optional path to the schema YAML file.
    
    Raises:
        InsufficientDataError: If required fields are missing or data types are incorrect.
        SchemaValidationError: If data constraints are violated.
    
    Note:
        This function does NOT check row count. Row count validation is handled
        separately in T015a and T017c.
    """
    if not isinstance(dataframe, pd.DataFrame):
        raise InsufficientDataError(f"Input must be a pandas DataFrame, got {type(dataframe)}")
    
    if dataframe.empty:
        # Empty dataframe fails schema validation for required fields
        raise InsufficientDataError("Input dataframe is empty; required fields are missing")
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Check field presence
    missing_fields = _validate_field_presence(dataframe, schema)
    if missing_fields:
        raise InsufficientDataError(
            f"Missing required fields: {', '.join(missing_fields)}. "
            f"Schema requires: {', '.join(REQUIRED_FIELDS)}"
        )
    
    # Check field types
    type_errors = _validate_field_types(dataframe, schema)
    if type_errors:
        raise InsufficientDataError(
            f"Data type mismatches for fields: {', '.join(type_errors)}. "
            "Please ensure field types match the schema definition."
        )
    
    # Check constraints
    constraint_violations = _validate_constraints(dataframe, schema)
    if constraint_violations:
        raise SchemaValidationError(
            f"Data constraint violations: {'; '.join(constraint_violations)}"
        )
    
    logger.info("Schema validation passed successfully")

def validate_file(file_path: str, schema_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load a file and validate it against the schema.
    
    Args:
        file_path: Path to the data file (supports CSV, Parquet, JSON).
        schema_path: Optional path to the schema YAML file.
    
    Returns:
        The validated pandas DataFrame.
    
    Raises:
        FileNotFoundError: If the data file does not exist.
        InsufficientDataError: If the file cannot be loaded or validated.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    # Load based on extension
    suffix = path.suffix.lower()
    if suffix == '.csv':
        df = pd.read_csv(path)
    elif suffix in ['.parquet', '.pq']:
        df = pd.read_parquet(path)
    elif suffix == '.json':
        df = pd.read_json(path)
    else:
        raise InsufficientDataError(f"Unsupported file format: {suffix}")
    
    # Validate
    validate_schema(df, schema_path)
    
    return df