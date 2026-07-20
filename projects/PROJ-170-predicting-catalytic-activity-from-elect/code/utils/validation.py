import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from config import get_data_path, get_output_path

logger = logging.getLogger(__name__)

def verify_data_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """
    Verify the SHA-256 checksum of a data file against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected SHA-256 hex digest.
        
    Returns:
        True if checksums match, False otherwise.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        error_msg = f"File not found for checksum verification: {path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    computed = hashlib.sha256(path.read_bytes()).hexdigest()
    
    if computed == expected_checksum:
        logger.info(f"Checksum verified successfully for {path.name}")
        return True
    else:
        error_msg = (
            f"Checksum mismatch for {path.name}. "
            f"Expected: {expected_checksum}, Got: {computed}"
        )
        logger.error(error_msg)
        return False

def validate_schema(df: pd.DataFrame, schema: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate that a DataFrame matches a required schema.
    
    Args:
        df: The DataFrame to validate.
        schema: A dictionary mapping column names to expected dtype strings.
                Supported dtypes: 'object', 'float', 'int'.
                
    Returns:
        A tuple (is_valid, errors).
        is_valid: True if all columns match the schema, False otherwise.
        errors: A list of error messages describing mismatches.
    """
    errors = []
    
    for col, expected_dtype in schema.items():
        if col not in df.columns:
            errors.append(f"Missing required column: '{col}'")
            continue
        
        series = df[col]
        dtype_str = str(series.dtype)
        
        # Map pandas dtype strings to checks
        if expected_dtype == "object":
            if not isinstance(series.dtype, pd.StringDtype) and not (
                series.dtype == object and series.apply(lambda x: isinstance(x, (str, type(None)))).all()
            ):
                # More lenient check for object columns that might contain mixed types but primarily strings
                # However, strict schema check usually implies string-like
                if not pd.api.types.is_object_dtype(series):
                     errors.append(f"Column '{col}' has dtype '{dtype_str}', expected object (string)")
        elif expected_dtype == "float":
            if not pd.api.types.is_float_dtype(series):
                errors.append(f"Column '{col}' has dtype '{dtype_str}', expected float")
        elif expected_dtype == "int":
            if not pd.api.types.is_integer_dtype(series):
                errors.append(f"Column '{col}' has dtype '{dtype_str}', expected int")
        elif expected_dtype == "bool":
            if not pd.api.types.is_bool_dtype(series):
                errors.append(f"Column '{col}' has dtype '{dtype_str}', expected bool")
    
    if errors:
        logger.warning(f"Schema validation failed for DataFrame: {errors}")
        return False, errors
    
    logger.info("Schema validation passed.")
    return True, []

def validate_no_null_targets(df: pd.DataFrame, target_column: str) -> Tuple[bool, List[str]]:
    """
    Check that the target column has no null (NaN) values.
    
    Args:
        df: The DataFrame to validate.
        target_column: The name of the target column to check.
        
    Returns:
        A tuple (is_valid, errors).
    """
    if target_column not in df.columns:
        error_msg = f"Target column '{target_column}' not found in DataFrame. Available columns: {list(df.columns)}"
        logger.error(error_msg)
        return False, [error_msg]
    
    null_count = df[target_column].isna().sum()
    if null_count > 0:
        error_msg = f"Found {null_count} null values in target column '{target_column}'"
        logger.error(error_msg)
        return False, [error_msg]
    
    logger.info(f"Target column '{target_column}' has no null values.")
    return True, []

def generate_checksum_file(data_dir: Union[str, Path], output_path: Union[str, Path]) -> None:
    """
    Generate a JSON file containing SHA-256 checksums for all files in a directory.
    
    Args:
        data_dir: The directory containing files to checksum.
        output_path: The path where the checksum JSON file will be written.
    """
    data_dir = Path(data_dir)
    output_path = Path(output_path)
    
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    checksums = {}
    for file_path in sorted(data_dir.rglob("*")):
        if file_path.is_file():
            relative_path = str(file_path.relative_to(data_dir))
            checksums[relative_path] = hashlib.sha256(file_path.read_bytes()).hexdigest()
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)
    
    logger.info(f"Checksum file generated at {output_path} with {len(checksums)} entries.")

def main() -> None:
    """CLI entry point for validation utilities."""
    logging.basicConfig(level=logging.INFO)
    print("Validation utilities module loaded successfully.")
    print("Available functions:")
    print("  - verify_data_checksum(file_path, expected_checksum)")
    print("  - validate_schema(df, schema)")
    print("  - validate_no_null_targets(df, target_column)")
    print("  - generate_checksum_file(data_dir, output_path)")

if __name__ == "__main__":
    main()