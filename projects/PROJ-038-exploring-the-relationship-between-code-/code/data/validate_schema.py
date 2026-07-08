"""
Schema validator for the features.csv dataset.
Validates column names, data types, and absence of NaN in numeric columns.
"""
import os
import sys
import json
import pandas as pd
from pathlib import Path

# Ensure we can import from the project root if run as a script
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import get_memory_limit_bytes

# Expected schema based on T017 requirements
EXPECTED_COLUMNS = ['file_path', 'cc', 'halstead', 'loc', 'is_buggy']
NUMERIC_COLUMNS = ['cc', 'halstead', 'loc', 'is_buggy']
STRING_COLUMNS = ['file_path']

def validate_schema(csv_path: str) -> dict:
    """
    Validates the CSV file against the expected schema.
    
    Returns a dictionary with validation status and error details.
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "row_count": 0,
        "column_count": 0
    }

    try:
        # Check file existence
        if not os.path.exists(csv_path):
            result["valid"] = False
            result["errors"].append(f"File not found: {csv_path}")
            return result

        # Load CSV
        df = pd.read_csv(csv_path)
        result["row_count"] = len(df)
        result["column_count"] = len(df.columns)

        # Check columns
        missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
        extra_cols = set(df.columns) - set(EXPECTED_COLUMNS)

        if missing_cols:
            result["valid"] = False
            result["errors"].append(f"Missing required columns: {list(missing_cols)}")

        if extra_cols:
            result["warnings"].append(f"Extra columns found (allowed but not expected): {list(extra_cols)}")

        # Check data types and NaN values
        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                # Check for NaN in numeric columns
                if df[col].isna().any():
                    result["valid"] = False
                    result["errors"].append(f"Column '{col}' contains NaN values")
                
                # Check if it can be converted to numeric
                try:
                    pd.to_numeric(df[col], errors='raise')
                except (ValueError, TypeError):
                    result["valid"] = False
                    result["errors"].append(f"Column '{col}' contains non-numeric values")

        # Check file_path column
        if 'file_path' in df.columns:
            if df['file_path'].isna().any():
                result["valid"] = False
                result["errors"].append("Column 'file_path' contains NaN values")

        return result

    except pd.errors.EmptyDataError:
        result["valid"] = False
        result["errors"].append("CSV file is empty")
        return result
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Unexpected error during validation: {str(e)}")
        return result

def generate_checksum(csv_path: str, checksum_path: str) -> dict:
    """
    Generates SHA256 checksum for the CSV file and saves it to checksums.json.
    
    Args:
        csv_path: Path to the CSV file to checksum
        checksum_path: Path to save the checksums.json file
    
    Returns:
        Dictionary containing the checksum and metadata
    """
    import hashlib
    import time

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Cannot generate checksum: file not found at {csv_path}")

    # Calculate SHA256
    sha256_hash = hashlib.sha256()
    with open(csv_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    checksum = sha256_hash.hexdigest()
    file_size = os.path.getsize(csv_path)
    
    checksum_data = {
        "file": os.path.basename(csv_path),
        "sha256": checksum,
        "size_bytes": file_size,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "algorithm": "sha256"
    }

    # Ensure directory exists
    checksum_dir = os.path.dirname(checksum_path)
    if checksum_dir and not os.path.exists(checksum_dir):
        os.makedirs(checksum_dir)

    # Load existing checksums if present
    checksums = {}
    if os.path.exists(checksum_path):
        try:
            with open(checksum_path, 'r') as f:
                checksums = json.load(f)
        except (json.JSONDecodeError, IOError):
            checksums = {}

    # Update with new checksum
    checksums[os.path.basename(csv_path)] = checksum_data

    # Save updated checksums
    with open(checksum_path, 'w') as f:
        json.dump(checksums, f, indent=2)

    return checksum_data

def main():
    """Main entry point for schema validation and checksum generation."""
    # Default paths
    csv_path = ROOT_DIR / "data" / "processed" / "features.csv"
    checksum_path = ROOT_DIR / "data" / "checksums.json"

    # Allow command line override
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    if len(sys.argv) > 2:
        checksum_path = sys.argv[2]

    print(f"Validating schema for: {csv_path}")
    validation_result = validate_schema(csv_path)

    if validation_result["valid"]:
        print("✓ Schema validation PASSED")
        print(f"  Rows: {validation_result['row_count']}")
        print(f"  Columns: {validation_result['column_count']}")
        if validation_result["warnings"]:
            print("  Warnings:")
            for w in validation_result["warnings"]:
                print(f"    - {w}")
    else:
        print("✗ Schema validation FAILED")
        for error in validation_result["errors"]:
            print(f"  - {error}")

    # Generate checksum if validation passed and file exists
    if validation_result["valid"] and os.path.exists(csv_path):
        print(f"\nGenerating checksum for: {csv_path}")
        try:
            checksum_info = generate_checksum(str(csv_path), str(checksum_path))
            print(f"✓ Checksum generated and saved to: {checksum_path}")
            print(f"  SHA256: {checksum_info['sha256']}")
            print(f"  Size: {checksum_info['size_bytes']} bytes")
        except Exception as e:
            print(f"✗ Checksum generation failed: {e}")
    elif os.path.exists(csv_path):
        print("\n⚠ Skipping checksum generation due to validation failures.")

    return 0 if validation_result["valid"] else 1

if __name__ == "__main__":
    sys.exit(main())
