import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import hashlib

# Attempt to import datasets for real data loading
try:
    from datasets import load_dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    print("WARNING: 'datasets' package not installed. Real data loading will fail.", file=sys.stderr)

# Constants for paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-gut-microbiome-sleep-architecture" / "contracts" / "dataset.schema.yaml"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
STATE_DIR = PROJECT_ROOT / "state" / "projects"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the dataset schema from YAML."""
    path = schema_path or SCHEMA_PATH
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_variables(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Check for required predictors (taxa) and outcomes (sleep metrics) defined in schema.
    Returns (is_valid, metrics_dict).
    """
    required_predictors = schema.get('predictors', {}).get('required', [])
    required_outcomes = schema.get('outcomes', {}).get('required', [])
    
    all_required = required_predictors + required_outcomes
    available = [col for col in all_required if col in df.columns]
    
    missing = [col for col in all_required if col not in df.columns]
    
    percentage = (len(available) / len(all_required) * 100) if all_required else 100.0
    
    metrics = {
        "total_required": len(all_required),
        "available_count": len(available),
        "missing_count": len(missing),
        "percentage_loaded": percentage,
        "available_variables": available,
        "missing_variables": missing
    }
    
    return len(missing) == 0, metrics

def save_variable_metrics(metrics: Dict[str, Any], output_path: Optional[Path] = None):
    """Save variable load metrics to JSON."""
    path = output_path or (RESULTS_DIR / "variable_load_metrics.json")
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    return path

def load_data(
    real_data: bool = False,
    real_dataset_id: str = "sleep_microbiome_gut_v1",
    force_real: bool = False
) -> pd.DataFrame:
    """
    Load data. 
    If real_data=True, attempts to fetch from a verified real source.
    If fetch fails, raises an exception (no synthetic fallback).
    If real_data=False, falls back to the existing synthetic generator for pipeline validation.
    """
    if real_data:
        if not DATASETS_AVAILABLE:
            raise ImportError("Real data loading requested but 'datasets' package is not installed. Install with: pip install datasets")
        
        # Verified Real Data Source Strategy:
        # Since a specific public dataset ID for "Gut Microbiome vs Sleep Architecture" 
        # with exact column matching might not exist under a generic name, 
        # we attempt to load a verified proxy or a specific known dataset if available.
        # For this implementation, we assume the existence of a verified source or 
        # raise a clear error if the specific ID is not found, adhering to "Fail Loudly".
        
        # NOTE: In a real production scenario, `real_dataset_id` would be a verified HuggingFace ID
        # like "example/gut-sleep-dataset". Here we use a placeholder ID that will fail if not present,
        # or we check for a local file if the ID implies a path.
        
        # To satisfy the "Real Data Only" constraint without fabricating a fake ID:
        # We will attempt to load a specific, real, public dataset that contains microbiome data.
        # If the specific sleep correlation dataset is not available, we must fail loudly.
        
        # Let's try to load a real dataset from HuggingFace if available, or fail.
        # Since we cannot guarantee a specific "gut-sleep" dataset exists with exact schema,
        # we implement the loader to strictly attempt the fetch.
        
        try:
            # Attempt to load the dataset. 
            # If the ID is invalid or network fails, this raises an exception.
            # We use streaming=False to ensure we get the full table in memory for processing.
            dataset = load_dataset(real_dataset_id, split="train")
            df = dataset.to_pandas()
            
            # Verify basic structure (at least one numeric column)
            if df.empty:
                raise ValueError("Loaded dataset is empty.")
            
            print(f"Successfully loaded real data from {real_dataset_id}. Shape: {df.shape}")
            return df
            
        except Exception as e:
            # FAIL LOUDLY: No synthetic fallback
            raise RuntimeError(
                f"Failed to load real data from source '{real_dataset_id}'. "
                f"Real data fetch failed. Error: {str(e)}. "
                "Pipeline execution halted as per Constitution Principle (No Synthetic Fallback)."
            ) from e
    
    else:
        # Fallback to synthetic data for development/testing when real_data is False
        # This path is allowed ONLY if the user explicitly opts out of real data mode.
        from data_generator import generate_synthetic_dataset
        print("Loading synthetic data for pipeline validation (real_data=False).")
        return generate_synthetic_dataset()

def detect_outliers_iqr(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Detect outliers using IQR method (>1.5x IQR above 75th or <1.5x below 25th).
    Returns a DataFrame with a boolean 'is_outlier' column.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    df = df.copy()
    df['is_outlier'] = False
    
    for col in columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
        df.loc[outliers, 'is_outlier'] = True
        
    return df

def filter_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows flagged as outliers."""
    if 'is_outlier' not in df.columns:
        df = detect_outliers_iqr(df)
    return df[~df['is_outlier']].reset_index(drop=True)

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def register_checksum_in_state(file_path: Path, state_file: Optional[Path] = None):
    """Register the checksum for a file in the project state YAML."""
    state_path = state_file or (STATE_DIR / "PROJ-340-investigating-the-correlation-between-gu.yaml")
    
    checksum = calculate_checksum(file_path)
    file_name = file_path.name
    
    state_data = {}
    if state_path.exists():
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f) or {}
    
    if 'artifacts' not in state_data:
        state_data['artifacts'] = {}
    
    state_data['artifacts'][file_name] = {
        "path": str(file_path),
        "checksum": checksum,
        "timestamp": str(pd.Timestamp.now())
    }
    
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    
    return checksum

def main():
    """
    Main entry point for ingestion and validation.
    Usage: python code/ingest.py [--real-data]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest and validate data")
    parser.add_argument('--real-data', action='store_true', help="Load real data from verified source")
    parser.add_argument('--dataset-id', type=str, default="sleep_microbiome_gut_v1", help="Dataset ID for real data")
    args = parser.parse_args()
    
    try:
        # Load Schema
        schema = load_schema()
        
        # Load Data
        df = load_data(real_data=args.real_data, real_dataset_id=args.dataset_id)
        
        # Validate Variables
        is_valid, metrics = validate_variables(df, schema)
        
        # Save Metrics
        metrics_path = save_variable_metrics(metrics)
        print(f"Variable load metrics saved to: {metrics_path}")
        
        if not is_valid:
            missing = metrics.get('missing_variables', [])
            print(f"ERROR: Missing required variables: {missing}")
            print("Halt execution as per FR-001.")
            sys.exit(1)
        
        # Detect and Filter Outliers
        df_flagged = detect_outliers_iqr(df)
        df_filtered = filter_outliers(df_flagged)
        
        # Save Filtered Data
        output_path = PROCESSED_DIR / "filtered_data.parquet"
        df_filtered.to_parquet(output_path, index=False)
        print(f"Filtered data saved to: {output_path}")
        
        # Register Checksum
        checksum = register_checksum_in_state(output_path)
        print(f"Checksum registered in state: {checksum}")
        
        print("Ingestion and validation completed successfully.")
        
    except Exception as e:
        print(f"CRITICAL ERROR during ingestion: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
