import os
import sys
import json
import hashlib
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Define the expected schema for features.csv
EXPECTED_COLUMNS = [
    'file_path',
    'cc',           # Cyclomatic Complexity (int)
    'halstead',     # Halstead Volume (float)
    'loc',          # Lines of Code (int)
    'is_buggy'      # Binary label (0 or 1)
]

EXPECTED_DTYPES = {
    'file_path': 'object',
    'cc': 'Int64',      # Nullable integer
    'halstead': 'float64',
    'loc': 'Int64',     # Nullable integer
    'is_buggy': 'Int64' # Nullable integer (0/1)
}

class SchemaValidationError(Exception):
    """Raised when the CSV schema does not match expectations."""
    pass

def validate_schema(csv_path: str, strict: bool = True) -> Dict[str, Any]:
    """
    Validates that the CSV file at csv_path matches the expected schema.
    
    Args:
        csv_path: Path to the features.csv file.
        strict: If True, raises SchemaValidationError on failure. 
                If False, returns a report dict with 'valid': False.
    
    Returns:
        A dictionary with validation results.
    
    Raises:
        SchemaValidationError: If strict=True and validation fails.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(csv_path)
    if not path.exists():
        if strict:
            raise FileNotFoundError(f"File not found: {csv_path}")
        return {"valid": False, "error": "File not found", "path": str(path)}

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        if strict:
            raise SchemaValidationError(f"Failed to read CSV: {e}")
        return {"valid": False, "error": str(e), "path": str(path)}

    issues = []

    # Check columns
    missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
    extra_cols = set(df.columns) - set(EXPECTED_COLUMNS)
    
    if missing_cols:
        issues.append(f"Missing columns: {missing_cols}")
    if extra_cols:
        issues.append(f"Extra columns found: {extra_cols}")
    
    # Check dtypes (basic check)
    for col, expected_type in EXPECTED_DTYPES.items():
        if col in df.columns:
            if not pd.api.types.is_dtype_equal(df[col].dtype, expected_type):
                # Allow minor variations (e.g. int64 vs Int64) if non-null
                if not (expected_type.startswith('Int') and str(df[col].dtype) == 'int64'):
                    issues.append(f"Column '{col}' has dtype {df[col].dtype}, expected {expected_type}")

    # Check for empty file
    if df.empty:
        issues.append("DataFrame is empty")

    is_valid = len(issues) == 0

    report = {
        "valid": is_valid,
        "path": str(path),
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns_found": list(df.columns),
        "issues": issues
    }

    if strict and not is_valid:
        raise SchemaValidationError(f"Schema validation failed: {'; '.join(issues)}")

    return report

def generate_checksum(csv_path: str, output_json: str, algorithm: str = 'sha256') -> Dict[str, Any]:
    """
    Generates a SHA-256 checksum and metadata for the CSV file and saves it to JSON.
    
    Args:
        csv_path: Path to the features.csv file.
        output_json: Path where the checksum JSON will be saved.
        algorithm: Hash algorithm to use (default: sha256).
    
    Returns:
        The checksum dictionary.
    
    Raises:
        FileNotFoundError: If the CSV file does not exist.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {csv_path}")

    hasher = hashlib.new(algorithm)
    size_bytes = path.stat().st_size

    with open(path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)

    checksum = hasher.hexdigest()
    
    checksum_data = {
        "file": path.name,
        "sha256": checksum,
        "size_bytes": size_bytes,
        "timestamp": str(path.stat().st_mtime),
        "algorithm": algorithm
    }

    # Load existing checksums if present, then update
    output_path = Path(output_json)
    if output_path.exists():
        try:
            with open(output_path, 'r') as f:
                all_checksums = json.load(f)
        except (json.JSONDecodeError, IOError):
            all_checksums = {}
    else:
        all_checksums = {}

    all_checksums[path.name] = checksum_data

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(all_checksums, f, indent=2)

    return checksum_data

def main():
    """
    Main entry point for schema validation and checksum generation.
    Expects the features.csv to be at code/data/processed/features.csv
    and writes checksums to code/data/checksums.json.
    """
    # Determine paths relative to project root
    # Assuming script is run from project root or code/data/
    base_dir = Path(__file__).resolve().parent.parent
    processed_dir = base_dir / 'data' / 'processed'
    features_csv = processed_dir / 'features.csv'
    checksums_json = base_dir / 'data' / 'checksums.json'

    if not features_csv.exists():
        print(f"Error: {features_csv} not found. Please run the pipeline first.")
        sys.exit(1)

    try:
        # Validate schema
        print(f"Validating schema for {features_csv}...")
        validation_report = validate_schema(str(features_csv), strict=True)
        print(f"Schema validation passed. Rows: {validation_report['row_count']}")

        # Generate checksum
        print(f"Generating checksum for {features_csv}...")
        checksum_data = generate_checksum(str(features_csv), str(checksums_json))
        print(f"Checksum saved to {checksums_json}")
        print(f"SHA256: {checksum_data['sha256']}")
        print(f"Size: {checksum_data['size_bytes']} bytes")

    except SchemaValidationError as e:
        print(f"Schema Validation Failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"File Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
