import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Custom Exceptions
class MissingDataError(Exception):
    """Raised when required data variables are missing."""
    pass

class StreamingNotSupportedError(Exception):
    """Raised when streaming is required but not supported."""
    pass

# Constants
CONFIG_DIR = Path("data/config")
SCHEMAS_DIR = Path("specs/001-gut-microbiome-sleep-architecture/contracts")
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
METADATA_DIR = DATA_DIR / "metadata"

def load_schema(schema_name: str) -> Dict:
    """Load a schema definition from the contracts directory."""
    schema_path = SCHEMAS_DIR / f"{schema_name}.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def load_required_variables() -> Tuple[List[str], List[str]]:
    """Load required predictor and outcome variables from config."""
    config_path = CONFIG_DIR / "required_variables.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Required variables config not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    predictors = config.get('predictors', [])
    outcomes = config.get('outcomes', [])
    return predictors, outcomes

def validate_variables(df: pd.DataFrame, predictors: List[str], outcomes: List[str]) -> Dict:
    """
    Validate that the dataframe contains all required predictors and outcomes.
    Returns a metrics dictionary with load percentage and missing variables.
    """
    all_required = predictors + outcomes
    total_required = len(all_required)
    if total_required == 0:
        return {
            "total_required": 0,
            "loaded_count": 0,
            "percentage": 100.0,
            "missing_variables": [],
            "status": "PASS"
        }
    
    loaded_count = 0
    missing = []
    
    for var in all_required:
        if var in df.columns:
            loaded_count += 1
        else:
            missing.append(var)
    
    percentage = (loaded_count / total_required) * 100.0
    
    status = "PASS" if len(missing) == 0 else "FAIL"
    
    return {
        "total_required": total_required,
        "loaded_count": loaded_count,
        "percentage": percentage,
        "missing_variables": missing,
        "status": status
    }

def save_variable_metrics(metrics: Dict, output_path: Path):
    """Save variable load metrics to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Variable load metrics saved to {output_path}")

def load_data(input_path: str) -> pd.DataFrame:
    """Load data from CSV or TSV file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    suffix = path.suffix.lower()
    if suffix == '.csv':
        return pd.read_csv(path)
    elif suffix == '.tsv':
        return pd.read_csv(path, sep='\t')
    elif suffix == '.parquet':
        return pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

def detect_outliers_iqr(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Detect outliers using the IQR method (>1.5x IQR above 75th or <1.5x below 25th).
    Returns a dataframe with an 'outlier_flag' column (1 if outlier, 0 otherwise).
    """
    if columns is None:
        # Select only numeric columns for outlier detection
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    df = df.copy()
    df['outlier_flag'] = 0
    
    for col in columns:
        if col not in df.columns:
            continue
        
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Mark rows where the value is outside the bounds
        outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
        df.loc[outliers, 'outlier_flag'] = 1
        
    return df

def filter_outliers(df: pd.DataFrame, output_path: str) -> pd.DataFrame:
    """
    Remove rows flagged as outliers and save the filtered dataset.
    Input: DataFrame with 'outlier_flag' column (1 = outlier).
    Output: Filtered DataFrame and saved parquet file.
    """
    if 'outlier_flag' not in df.columns:
        raise ValueError("Input DataFrame must contain 'outlier_flag' column. Run detect_outliers_iqr first.")
    
    # Filter out rows where outlier_flag is 1
    filtered_df = df[df['outlier_flag'] == 0].reset_index(drop=True)
    
    # Drop the outlier_flag column from the final output
    if 'outlier_flag' in filtered_df.columns:
        filtered_df = filtered_df.drop(columns=['outlier_flag'])
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to parquet
    filtered_df.to_parquet(output_path, index=False)
    print(f"Filtered dataset saved to {output_path}")
    print(f"Original rows: {len(df)}, Filtered rows: {len(filtered_df)}, Removed: {len(df) - len(filtered_df)}")
    
    return filtered_df

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def register_checksum_in_state(file_path: Path, state_path: Path):
    """Register the checksum of a file in the project state YAML."""
    if not state_path.exists():
        # Create a minimal state file if it doesn't exist
        state_data = {
            "project_id": "PROJ-340-investigating-the-correlation-between-gu",
            "artifact_hashes": {}
        }
    else:
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f)
    
    checksum = calculate_checksum(file_path)
    state_data["artifact_hashes"][str(file_path)] = checksum
    
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    print(f"Checksum registered for {file_path} in {state_path}")

def load_streamed_dataset(input_path: str, chunksize: int = 10000) -> pd.DataFrame:
    """
    Load a large dataset in chunks to avoid memory issues.
    Currently aggregates into a single DataFrame; in future, could process incrementally.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    chunks = []
    for chunk in pd.read_csv(path, chunksize=chunksize):
        chunks.append(chunk)
    
    if not chunks:
        raise ValueError("No data loaded from input file.")
    
    return pd.concat(chunks, ignore_index=True)

def fetch_verified_real_dataset(dataset_id: str) -> pd.DataFrame:
    """
    Fetch a verified real dataset.
    Currently raises NotImplementedError as no verified source is available yet.
    """
    raise NotImplementedError("Real data fetching is not yet implemented. Use synthetic mode or wait for T051a completion.")

def validate_loaded_data(df: pd.DataFrame, required_vars: List[str]) -> bool:
    """Validate that loaded data contains required variables."""
    missing = [var for var in required_vars if var not in df.columns]
    if missing:
        raise MissingDataError(f"Missing required variables: {missing}")
    return True

def main():
    """
    Main entry point for the ingest module.
    Handles command-line arguments for synthetic data generation and validation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Ingestion and Validation Module")
    parser.add_argument('--input', type=str, default=None, help='Path to input data file')
    parser.add_argument('--output', type=str, default=None, help='Path for output filtered data')
    parser.add_argument('--mode', type=str, choices=['real', 'synthetic'], default='synthetic', help='Data mode')
    parser.add_argument('--generate-manifest', action='store_true', help='Generate synthetic data manifest')
    
    args = parser.parse_args()
    
    # If generating manifest, delegate to data_generator
    if args.generate_manifest:
        from data_generator import generate_synthetic_manifest
        generate_synthetic_manifest()
        return
    
    if args.mode == 'synthetic' and not args.input:
        # Generate synthetic data if in synthetic mode and no input provided
        from data_generator import generate_synthetic_dataset
        synthetic_path = "data/raw/synthetic_data.csv"
        print(f"Generating synthetic data to {synthetic_path}")
        generate_synthetic_dataset(output_path=synthetic_path)
        args.input = synthetic_path
    
    if not args.input:
        parser.error("Input file is required or use --mode synthetic to generate data.")
    
    # Load data
    print(f"Loading data from {args.input}")
    df = load_data(args.input)
    
    # Load required variables
    predictors, outcomes = load_required_variables()
    
    # Validate variables
    metrics = validate_variables(df, predictors, outcomes)
    metrics_path = RESULTS_DIR / "variable_load_metrics.json"
    save_variable_metrics(metrics, metrics_path)
    
    if metrics['status'] == 'FAIL':
        print(f"Validation FAILED. Missing variables: {metrics['missing_variables']}")
        sys.exit(1)
    
    # Detect outliers
    print("Detecting outliers...")
    df_with_flags = detect_outliers_iqr(df)
    
    # Filter outliers
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = PROCESSED_DIR / "filtered_data.parquet"
    
    print("Filtering outliers...")
    filtered_df = filter_outliers(df_with_flags, str(output_path))
    
    # Register checksum
    state_path = Path("state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml")
    register_checksum_in_state(output_path, state_path)
    
    print("Ingestion and filtering complete.")

if __name__ == "__main__":
    main()
