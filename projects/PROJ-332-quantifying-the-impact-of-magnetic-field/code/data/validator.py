import logging
import json
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import yaml
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

# Global cache for loaded schemas to avoid repeated I/O
_schemas: Dict[str, Dict[str, Any]] = {}
_schema_path_map = {
    "input": "contracts/dataset.schema.yaml",
    "output": "contracts/output.schema.yaml"
}

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a schema from the contracts directory.
    Caches the result in memory for subsequent calls.

    Args:
        schema_name: Either 'input' or 'output'.

    Returns:
        The loaded schema dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the schema_name is invalid.
    """
    if schema_name not in _schema_path_map:
        raise ValueError(f"Unknown schema name: {schema_name}. Must be 'input' or 'output'.")

    if schema_name in _schemas:
        return _schemas[schema_name]

    path_str = _schema_path_map[schema_name]
    # Resolve relative to project root
    base_dir = Path(__file__).resolve().parent.parent.parent
    schema_path = base_dir / path_str

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    _schemas[schema_name] = schema
    logger.debug(f"Loaded schema '{schema_name}' from {schema_path}")
    return schema

def validate_dataframe_against_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates a pandas DataFrame against a JSON Schema definition.
    Currently performs structural validation (columns, types) as full
    JSON Schema validation of DataFrames is complex and often overkill
    for simple column checks.

    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary.

    Returns:
        A tuple (is_valid, list_of_errors).
    """
    errors = []

    if schema.get("type") != "object":
        # If schema expects an object but we have a DF, we check the DF rows or structure
        pass

    # Check required columns if defined in schema properties
    if "properties" in schema:
        required_cols = schema.get("required", [])
        df_cols = set(df.columns)
        
        # If schema defines specific columns required for the output
        # We map schema properties to DataFrame columns if the schema is for the output record
        # For the output schema, 'data' contains the records.
        # For simplicity in this stage, we validate the top-level structure if it matches the schema's expectation
        # or we validate the 'data' list items if the schema is for the output file structure.
        
        # Heuristic: If schema has 'data' property with 'items', we validate the items against 'items.properties'
        if "data" in schema and "items" in schema["data"]:
            item_schema = schema["data"]["items"]
            item_required = item_schema.get("required", [])
            item_properties = item_schema.get("properties", {})
            
            # Check if the DataFrame columns match the item properties keys
            # We assume the DF represents the 'data' list flattened
            for col in item_required:
                if col not in df_cols:
                    errors.append(f"Missing required column: {col}")
            
            # Type checks (basic)
            for col, col_schema in item_properties.items():
                if col in df_cols:
                    dtype = df[col].dtype
                    expected_type = col_schema.get("type")
                    if expected_type == "integer" and not np.issubdtype(dtype, np.integer):
                        # Allow float if it holds integers, but strict check for now
                        if not np.issubdtype(dtype, np.floating):
                            errors.append(f"Column {col} should be numeric (int), found {dtype}")
                    elif expected_type == "number" and not np.issubdtype(dtype, np.number):
                        errors.append(f"Column {col} should be numeric, found {dtype}")
                    elif expected_type == "string" and not np.issubdtype(dtype, np.object_) and not np.issubdtype(dtype, np.str_):
                        # Pandas often stores strings as object
                        if not (np.issubdtype(dtype, np.object_) or np.issubdtype(dtype, np.str_)):
                            errors.append(f"Column {col} should be string, found {dtype}")
        
        # If schema is for the input raw structure (dict), we might not validate DF directly
        # unless the DF is a row representation.
        
    return len(errors) == 0, errors

def validate_input_schema(data: Any) -> Tuple[bool, List[str]]:
    """
    Validates input data (expected to be a dict or DataFrame row) against the input schema.
    Called BEFORE parsing/analysis to ensure raw data integrity.

    Args:
        data: The raw data object (dict or DataFrame).

    Returns:
        Tuple (is_valid, errors).
    """
    schema = load_schema("input")
    errors = []

    if isinstance(data, pd.DataFrame):
        # If a whole DF is passed, we assume it's a list of records
        # But for input validation, we usually get a single discharge dict
        # We'll handle the common case of a dict or list of dicts
        pass

    if isinstance(data, dict):
        # Validate top-level keys
        required = schema.get("required", [])
        for key in required:
            if key not in data:
                errors.append(f"Input missing required key: {key}")
        
        # If 'fields' is present, check for expected sub-keys if we want to be strict
        # For now, we just ensure the structure exists
        if "fields" in data and not isinstance(data["fields"], dict):
            errors.append("Input 'fields' must be a dictionary.")
    elif isinstance(data, list):
        # Validate each item in the list
        for i, item in enumerate(data):
            valid, item_errors = validate_input_schema(item)
            if not valid:
                errors.extend([f"Item {i}: {e}" for e in item_errors])
    else:
        errors.append(f"Input data must be a dict or list, got {type(data)}")

    return len(errors) == 0, errors

def validate_output_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates the processed DataFrame against the output schema.
    Called AFTER parsing/analysis to ensure the result meets specification.

    Args:
        df: The processed DataFrame.

    Returns:
        Tuple (is_valid, errors).
    """
    schema = load_schema("output")
    errors = []

    if not isinstance(df, pd.DataFrame):
        return False, ["Output must be a pandas DataFrame."]

    # Check required columns based on output schema 'data' -> 'items' -> 'required'
    if "data" in schema and "items" in schema["data"]:
        item_required = schema["data"]["items"].get("required", [])
        df_cols = set(df.columns)

        for col in item_required:
            if col not in df_cols:
                errors.append(f"Output missing required column: {col}")

        # Check enum values for confinement_mode
        if "confinement_mode" in df_cols:
            allowed_modes = ["L-mode", "H-mode"]
            invalid_modes = set(df["confinement_mode"].unique()) - set(allowed_modes)
            if invalid_modes:
                errors.append(f"Invalid values in 'confinement_mode': {invalid_modes}")

        # Check numeric types
        numeric_cols = ["island_width", "tau_e", "h98y2", "resonant_surface_density"]
        for col in numeric_cols:
            if col in df_cols:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    errors.append(f"Column '{col}' must be numeric.")

    return len(errors) == 0, errors

def validate_parsed_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Wrapper function to perform full validation pipeline.
    Validates input structure (if needed) and output structure.
    Raises ValueError if validation fails.

    Args:
        df: The DataFrame to validate.

    Returns:
        The same DataFrame if valid.

    Raises:
        ValueError: If validation fails.
    """
    # We assume the input to this function is already parsed into a DF.
    # We validate it against the output schema as per FR-009.
    is_valid, errors = validate_output_schema(df)
    
    if not is_valid:
        error_msg = "Schema validation failed:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Schema validation passed.")
    return df