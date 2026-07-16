import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

logger = logging.getLogger(__name__)

def verify_data_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """Verify the checksum of a data file."""
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {path}")
        return False
    
    computed = hashlib.sha256(path.read_bytes()).hexdigest()
    if computed == expected_checksum:
        logger.info(f"Checksum verified for {path}")
        return True
    else:
        logger.error(f"Checksum mismatch for {path}. Expected: {expected_checksum}, Got: {computed}")
        return False

def validate_schema(df: pd.DataFrame, schema: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate that a DataFrame matches a schema.
    Schema is a dict mapping column names to expected dtype strings.
    """
    errors = []
    for col, expected_dtype in schema.items():
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
        else:
            # Simple dtype check
            if expected_dtype == "object" and not df[col].dtype == object:
                errors.append(f"Column {col} has dtype {df[col].dtype}, expected object")
            elif expected_dtype == "float" and not pd.api.types.is_float_dtype(df[col]):
                errors.append(f"Column {col} has dtype {df[col].dtype}, expected float")
            elif expected_dtype == "int" and not pd.api.types.is_integer_dtype(df[col]):
                errors.append(f"Column {col} has dtype {df[col].dtype}, expected int")
    
    if errors:
        logger.error(f"Schema validation failed: {errors}")
        return False, errors
    return True, []

def validate_no_null_targets(df: pd.DataFrame, target_column: str) -> Tuple[bool, List[str]]:
    """Check that the target column has no null values."""
    if target_column not in df.columns:
        return False, [f"Target column {target_column} not found"]
    
    null_count = df[target_column].isna().sum()
    if null_count > 0:
        msg = f"Found {null_count} null values in target column {target_column}"
        logger.error(msg)
        return False, [msg]
    return True, []

def generate_checksum_file(data_dir: Union[str, Path], output_path: Union[str, Path]) -> None:
    """Generate a checksum file for all files in a directory."""
    data_dir = Path(data_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    checksums = {}
    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            checksums[str(file_path.relative_to(data_dir))] = hashlib.sha256(file_path.read_bytes()).hexdigest()
    
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksum file generated: {output_path}")

def main() -> None:
    """CLI entry point for validation utilities."""
    print("Validation utilities loaded.")

if __name__ == "__main__":
    main()