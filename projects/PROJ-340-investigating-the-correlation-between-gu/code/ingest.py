import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib

# Constants for paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-gut-microbiome-sleep-architecture" / "contracts" / "dataset.schema.yaml"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the dataset schema from YAML."""
    if schema_path is None:
        schema_path = SCHEMA_PATH
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_variables(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the dataframe contains all required variables from the schema.
    Returns (is_valid, metrics_dict).
    """
    required_predictors = schema.get('predictors', {}).get('required', [])
    required_outcomes = schema.get('outcomes', {}).get('required', [])
    
    all_required = required_predictors + required_outcomes
    available_columns = set(df.columns)
    
    missing_vars = [var for var in all_required if var not in available_columns]
    total_required = len(all_required)
    found_count = total_required - len(missing_vars)
    percentage = (found_count / total_required * 100) if total_required > 0 else 100.0
    
    metrics = {
        "total_required_variables": total_required,
        "variables_found": found_count,
        "variables_missing": len(missing_vars),
        "percentage_loaded": percentage,
        "missing_variables": missing_vars,
        "found_variables": [var for var in all_required if var in available_columns]
    }
    
    return (len(missing_vars) == 0, metrics)

def save_variable_metrics(metrics: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """Save variable load metrics to JSON."""
    if output_path is None:
        output_path = DATA_RESULTS_DIR / "variable_load_metrics.json"
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return output_path

def load_data(data_path: Path) -> pd.DataFrame:
    """Load data from CSV or TSV."""
    if data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    elif data_path.suffix == '.tsv':
        return pd.read_csv(data_path, sep='\t')
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

def detect_outliers_iqr(df: pd.DataFrame, columns: List[str], multiplier: float = 1.5) -> pd.DataFrame:
    """
    Detect outliers using the IQR method.
    Returns a dataframe with an 'is_outlier' column.
    """
    outlier_flags = pd.Series(False, index=df.index)
    
    for col in columns:
        if col not in df.columns:
            continue
        
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        
        col_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
        outlier_flags = outlier_flags | col_outliers
    
    df_with_flags = df.copy()
    df_with_flags['is_outlier'] = outlier_flags
    return df_with_flags

def filter_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows flagged as outliers."""
    if 'is_outlier' not in df.columns:
        return df
    return df[~df['is_outlier']].drop(columns=['is_outlier'])

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def register_checksum_in_state(file_path: Path, state_path: Optional[Path] = None) -> None:
    """Register the checksum in the project state file."""
    if state_path is None:
        state_path = PROJECT_ROOT / "state" / "projects" / "PROJ-340-investigating-the-correlation-between-gu.yaml"
    
    checksum = calculate_checksum(file_path)
    
    state_data = {}
    if state_path.exists():
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f) or {}
    
    # Update state with new checksum
    if 'artifacts' not in state_data:
        state_data['artifacts'] = {}
    
    state_data['artifacts'][file_path.name] = {
        'path': str(file_path),
        'checksum': checksum,
        'registered_at': pd.Timestamp.now().isoformat()
    }
    
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)

def fetch_verified_real_dataset(dataset_id: str = "sleep_microbiome_validation_v1") -> Path:
    """
    Fetch a verified real dataset.
    Currently, this attempts to load a specific verified dataset from HuggingFace.
    If the dataset is not available, it raises a clear error.
    
    Args:
        dataset_id: The identifier for the dataset to fetch.
        
    Returns:
        Path to the downloaded CSV file.
        
    Raises:
        MissingDataError: If the real data fetch fails.
    """
    try:
        # Attempt to import datasets (part of the project's requirements)
        from datasets import load_dataset
        
        # Try to load the specific verified dataset
        # Note: This ID is a placeholder for the actual verified dataset ID once found.
        # For now, we attempt to load a known public dataset structure.
        # If T049/T050 identified a specific dataset, use its ID here.
        
        # Since no specific real dataset ID was confirmed in T049/T050 to be universally accessible
        # without authentication or specific constraints, we will attempt to load a known 
        # structure from HuggingFace if available, or raise a specific error.
        
        # Simulating the check for a verified source found in T049/T050
        # If T050 identified a specific dataset, we would use:
        # ds = load_dataset("specific_verified_id", split="train")
        
        # For this implementation, we assume the user has configured the environment
        # or the dataset is available. If not, we fail loudly.
        
        # Placeholder for the actual verified dataset ID found in T049/T050
        # If T049/T050 concluded no single dataset exists, this function should not be called
        # or should raise a specific "No Single Dataset Available" error.
        
        # Attempting to load a hypothetical verified dataset
        # In a real scenario, this would be:
        # ds = load_dataset("path/to/verified/dataset", split="train")
        # df = ds.to_pandas()
        
        # Since we must not fabricate, and if no real dataset is available, we raise an error.
        # The task T051 is conditional on T049/T050 finding a dataset.
        # If T049/T050 found a dataset, we would use it here.
        # If not, we raise an error indicating the condition is not met.
        
        # To satisfy the requirement of "If a suitable single dataset is found",
        # we assume the user has set an environment variable or config for the dataset ID.
        dataset_name = os.getenv("VERIFIED_DATASET_ID", None)
        
        if not dataset_name:
            # Check if a default known dataset exists (this is a fallback for testing the mechanism)
            # In a real production run, this would fail if no dataset is configured.
            raise MissingDataError(
                "No verified dataset ID found in environment variable 'VERIFIED_DATASET_ID'. "
                "T049/T050 must identify a real dataset and configure it before T051 can proceed. "
                "To prevent fabrication, execution is halted."
            )
        
        ds = load_dataset(dataset_name, split="train")
        df = ds.to_pandas()
        
        output_path = DATA_RAW_DIR / f"{dataset_name.replace('/', '_')}.csv"
        df.to_csv(output_path, index=False)
        
        return output_path
        
    except ImportError:
        raise MissingDataError(
            "The 'datasets' library is required to fetch real data. "
            "Please install it via 'pip install datasets'."
        )
    except Exception as e:
        raise MissingDataError(
            f"Real data fetch failed for dataset '{dataset_name}': {str(e)}. "
            "Execution halted to prevent fabrication."
        )

def validate_loaded_data(df: pd.DataFrame, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validate the loaded data against the schema and generate a validation report.
    """
    if schema is None:
        schema = load_schema()
    
    is_valid, metrics = validate_variables(df, schema)
    
    report = {
        "validation_status": "PASSED" if is_valid else "FAILED",
        "dataset_shape": list(df.shape),
        "column_types": df.dtypes.astype(str).to_dict(),
        "missing_variable_metrics": metrics,
        "null_counts": df.isnull().sum().to_dict(),
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    return report

def main():
    """
    Main entry point for the real data fetcher and validator (T051).
    Fetches a verified real dataset, saves it, and generates a validation report.
    """
    print("Starting T051: Real Data Fetcher and Validator")
    
    try:
        # 1. Fetch the verified real dataset
        print("Attempting to fetch verified real dataset...")
        data_path = fetch_verified_real_dataset()
        print(f"Dataset fetched and saved to: {data_path}")
        
        # 2. Load the data
        print("Loading data...")
        df = load_data(data_path)
        
        # 3. Validate the data
        print("Validating data...")
        validation_report = validate_loaded_data(df)
        
        # 4. Save the validation report
        report_path = DATA_RESULTS_DIR / "dataset_validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(validation_report, f, indent=2)
        print(f"Validation report saved to: {report_path}")
        
        # 5. Check if validation passed
        if validation_report["validation_status"] != "PASSED":
            print("Validation FAILED. Missing required variables.")
            print(f"Missing variables: {validation_report['missing_variable_metrics']['missing_variables']}")
            sys.exit(1)
        
        print("T051 completed successfully.")
        
    except MissingDataError as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during T051: {e}")
        sys.exit(1)

class MissingDataError(Exception):
    """Custom exception for missing real data."""
    pass

if __name__ == "__main__":
    main()
