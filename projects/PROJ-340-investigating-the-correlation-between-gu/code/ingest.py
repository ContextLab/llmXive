import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Custom Exceptions
class MissingDataError(Exception):
    """Raised when required data is missing."""
    pass

class StreamingNotSupportedError(Exception):
    """Raised when streaming is required but not supported."""
    pass

class HarmonizedDataNotFoundError(Exception):
    """Raised when harmonized data is expected but not found."""
    pass

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def calculate_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def register_checksum_in_state(file_path: str, state_path: str, artifact_name: str):
    """Register a file checksum in the project state YAML."""
    state_file = Path(state_path)
    if not state_file.exists():
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_data = {"artifact_hashes": {}}
    else:
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f) or {"artifact_hashes": {}}
    
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    checksum = calculate_checksum(file_path)
    state_data["artifact_hashes"][artifact_name] = checksum

    with open(state_file, 'w') as f:
        yaml.dump(state_data, f)

def validate_variables(df: pd.DataFrame, required_vars: List[str], var_type: str) -> Tuple[bool, List[str], float]:
    """
    Validate that required variables are present in the DataFrame.
    Returns: (all_present, missing_list, percentage_loaded)
    """
    missing = [v for v in required_vars if v not in df.columns]
    total = len(required_vars)
    loaded = total - len(missing)
    percentage = (loaded / total * 100) if total > 0 else 0.0
    return len(missing) == 0, missing, percentage

def save_variable_metrics(metrics: Dict[str, Any], output_path: str):
    """Save variable load metrics to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def detect_outliers_iqr(df: pd.DataFrame, columns: List[str]) -> pd.Series:
    """
    Detect outliers using the IQR method (>1.5x IQR above 75th or <1.5x below 25th).
    Returns a boolean series where True indicates an outlier.
    """
    outlier_mask = pd.Series([False] * len(df), index=df.index)
    for col in columns:
        if col in df.columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            col_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_mask |= col_outliers
    return outlier_mask

def filter_outliers(df: pd.DataFrame, outlier_mask: pd.Series) -> pd.DataFrame:
    """Remove rows flagged as outliers."""
    return df[~outlier_mask].reset_index(drop=True)

def load_harmonized_data(harmonized_path: str) -> pd.DataFrame:
    """
    Load the harmonized dataset from a Parquet file.
    This function specifically handles the output of T068.
    """
    if not os.path.exists(harmonized_path):
        raise HarmonizedDataNotFoundError(f"Harmonized data file not found at: {harmonized_path}")
    
    try:
        df = pd.read_parquet(harmonized_path)
        return df
    except Exception as e:
        raise MissingDataError(f"Failed to load harmonized data from {harmonized_path}: {str(e)}")

def load_streamed_dataset(path: str, chunk_size: int = 1000) -> pd.DataFrame:
    """
    Load a large dataset in chunks to manage memory.
    """
    chunks = []
    for chunk in pd.read_csv(path, chunksize=chunk_size):
        chunks.append(chunk)
    return pd.concat(chunks, ignore_index=True)

def main():
    """Main entry point for ingestion scripts."""
    parser = argparse.ArgumentParser(description="Data Ingestion and Validation")
    parser.add_argument('--input', type=str, help='Input data path')
    parser.add_argument('--schema', type=str, help='Schema path')
    parser.add_argument('--output', type=str, help='Output path for filtered data')
    args = parser.parse_args()

    if not args.input:
        print("Error: Input path required")
        sys.exit(1)

    # Placeholder for actual ingestion logic
    print(f"Ingesting data from {args.input}")

if __name__ == "__main__":
    main()
