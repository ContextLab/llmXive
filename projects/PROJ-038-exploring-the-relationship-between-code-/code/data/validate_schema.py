import os
import sys
import json
import pandas as pd
from pathlib import Path
from src.config import get_memory_limit_bytes

def validate_schema(file_path: str) -> bool:
    """Validate the schema of the features.csv file."""
    required_cols = ["file_path", "cc", "halstead", "loc", "is_buggy"]
    df = pd.read_csv(file_path)
    if not all(col in df.columns for col in required_cols):
        return False
    # Check for NaN in numeric columns
    if df[["cc", "halstead", "loc", "is_buggy"]].isnull().any().any():
        return False
    return True

def generate_checksum(file_path: str) -> str:
    """Generate a simple checksum for the file."""
    import hashlib
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def main():
    path = "code/data/processed/features.csv"
    if os.path.exists(path):
        if validate_schema(path):
            print(f"Schema valid for {path}")
            print(f"Checksum: {generate_checksum(path)}")
        else:
            print(f"Schema invalid for {path}")
    else:
        print(f"File not found: {path}")

if __name__ == "__main__":
    main()
