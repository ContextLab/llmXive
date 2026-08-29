import os
import sys
import json
import hashlib
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple
from src.config import get_memory_limit_bytes

REQUIRED_COLUMNS = ['file_path', 'cc', 'halstead', 'loc', 'is_buggy']
REQUIRED_TYPES = {
    'file_path': 'object',
    'cc': 'int64',
    'halstead': 'float64',
    'loc': 'int64',
    'is_buggy': 'int64'
}

def validate_schema(csv_path: str) -> Tuple[bool, List[str]]:
    """
    Validates that the CSV file at csv_path has the required schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    path = Path(csv_path)
    
    if not path.exists():
        errors.append(f"File not found: {csv_path}")
        return False, errors

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        errors.append(f"Failed to read CSV: {str(e)}")
        return False, errors

    # Check columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        return False, errors

    extra_cols = set(df.columns) - set(REQUIRED_COLUMNS)
    if extra_cols:
        errors.append(f"Unexpected columns found: {extra_cols}")
        # We might decide to be strict or lenient here. For now, just warn.

    # Check types
    for col, expected_type in REQUIRED_TYPES.items():
        actual_type = str(df[col].dtype)
        if actual_type != expected_type:
            errors.append(f"Column '{col}' has type '{actual_type}', expected '{expected_type}'")

    # Check for NaN in numeric columns
    numeric_cols = ['cc', 'halstead', 'loc', 'is_buggy']
    for col in numeric_cols:
        if df[col].isna().any():
            count = df[col].isna().sum()
            errors.append(f"Column '{col}' contains {count} NaN values")

    return len(errors) == 0, errors

def generate_checksum(csv_path: str, checksum_path: str) -> Dict[str, Any]:
    """
    Generates a SHA256 checksum and metadata for the CSV file.
    Writes the result to checksum_path.
    Returns the checksum dictionary.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot generate checksum for non-existent file: {csv_path}")

    sha256_hash = hashlib.sha256()
    size_bytes = 0
    
    # Read in chunks to handle large files
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
            size_bytes += len(chunk)
    
    hex_dig = sha256_hash.hexdigest()
    
    checksum_data = {
        "file": path.name,
        "sha256": hex_dig,
        "size_bytes": size_bytes,
        "timestamp": str(path.stat().st_mtime),
        "algorithm": "sha256"
    }

    checksum_file = Path(checksum_path)
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(checksum_file, 'w') as f:
        json.dump(checksum_data, f, indent=2)
    
    return checksum_data

def main():
    """
    Main entry point for schema validation and checksum generation.
    Expects the features.csv to be at code/data/processed/features.csv
    Outputs checksum to code/data/checksums.json
    """
    project_root = Path(__file__).resolve().parent.parent
    csv_path = project_root / "data" / "processed" / "features.csv"
    checksum_path = project_root / "data" / "checksums.json"

    if not csv_path.exists():
        print(f"Error: {csv_path} does not exist. Run the feature generation pipeline first.")
        sys.exit(1)

    print(f"Validating schema for {csv_path}...")
    is_valid, errors = validate_schema(str(csv_path))
    
    if not is_valid:
        print("Schema validation FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    
    print("Schema validation PASSED.")
    
    print(f"Generating checksum for {csv_path}...")
    try:
        checksum_data = generate_checksum(str(csv_path), str(checksum_path))
        print(f"Checksum generated successfully: {checksum_data['sha256']}")
        print(f"Output written to: {checksum_path}")
    except Exception as e:
        print(f"Error generating checksum: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
