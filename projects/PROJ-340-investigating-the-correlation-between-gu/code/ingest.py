import os
import sys
import json
import logging
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Project relative imports
from config import load_config, get_config

# --- Logging Setup (Fixed: Ensure directory exists) ---
def setup_logging(log_file: str = "data/logs/ingest.log") -> logging.Logger:
    """Setup logging with file and console handlers. Ensures directory exists."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("ingest")
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates in repeated runs
    if logger.handlers:
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

logger = setup_logging()

# --- Schema & Variable Loading ---
def load_schema(schema_path: str = "specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml") -> Dict[str, Any]:
    """Loads the dataset schema definition."""
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found at {schema_path}. Using default schema structure.")
        return {"predictors": [], "outcomes": []}
    
    try:
        import yaml
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return {"predictors": [], "outcomes": []}

def load_required_variables(config_path: str = "data/config/required_variables.yaml") -> Tuple[List[str], List[str]]:
    """
    Loads required predictors and outcomes from the config file.
    Returns: (list of required_predictors, list of required_outcomes)
    """
    try:
        import yaml
        if not os.path.exists(config_path):
            logger.error(f"Required variables config not found at {config_path}")
            return [], []
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        predictors = config.get('required_predictors', [])
        outcomes = config.get('required_outcomes', [])
        logger.info(f"Loaded {len(predictors)} predictors and {len(outcomes)} outcomes from config.")
        return predictors, outcomes
    except Exception as e:
        logger.error(f"Failed to load required variables: {e}")
        return [], []

# --- Validation Logic ---
def validate_variables(df: pd.DataFrame, required_predictors: List[str], required_outcomes: List[str]) -> Dict[str, Any]:
    """
    Validates that the dataframe contains all required variables.
    Returns status, percentage loaded, missing variables, and total required.
    """
    columns = set(df.columns)
    missing_predictors = [p for p in required_predictors if p not in columns]
    missing_outcomes = [o for o in required_outcomes if o not in columns]
    
    missing_all = missing_predictors + missing_outcomes
    total_required = len(required_predictors) + len(required_outcomes)
    missing_count = len(missing_all)
    
    percentage_loaded = ((total_required - missing_count) / total_required * 100) if total_required > 0 else 0.0
    status = "PASS" if missing_count == 0 else "FAIL"

    result = {
        "status": status,
        "percentage_loaded": round(percentage_loaded, 2),
        "missing_variables": missing_all,
        "total_required": total_required
    }
    
    if status == "FAIL":
        logger.error(f"Validation FAILED. Missing variables: {missing_all}")
    else:
        logger.info("Validation PASSED. All required variables present.")
        
    return result

def save_variable_metrics(metrics: Dict[str, Any], output_path: str = "data/results/variable_load_metrics.json"):
    """Saves validation metrics to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Variable metrics saved to {output_path}")

# --- Data Loading & Outlier Handling ---
def load_data(input_path: str) -> pd.DataFrame:
    """Loads data from CSV or Parquet."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    if input_path.endswith('.parquet'):
        return pd.read_parquet(input_path)
    else:
        return pd.read_csv(input_path)

def detect_outliers_iqr(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Detects outliers using the IQR method (>1.5x IQR).
    Returns report with counts and excluded indices.
    """
    if columns is None:
        # Exclude non-numeric columns
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    excluded_indices = set()
    outlier_details = {}

    for col in columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Identify outliers
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
        if not outliers.empty:
            indices = outliers.index.tolist()
            excluded_indices.update(indices)
            outlier_details[col] = {
                "count": len(indices),
                "indices": indices
            }
    
    result = {
        "count": len(excluded_indices),
        "excluded_indices": sorted(list(excluded_indices)),
        "details_by_column": outlier_details
    }
    
    logger.info(f"Detected {len(excluded_indices)} outlier rows across {len(outlier_details)} columns.")
    return result

def save_outlier_report(report: Dict[str, Any], output_path: str = "data/results/outlier_report.json"):
    """Saves outlier report to JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Outlier report saved to {output_path}")

def filter_outliers(df: pd.DataFrame, excluded_indices: List[int]) -> pd.DataFrame:
    """Removes rows with indices in excluded_indices."""
    logger.info(f"Filtering out {len(excluded_indices)} rows.")
    return df.drop(index=excluded_indices).reset_index(drop=True)

def save_filtered_data(df: pd.DataFrame, output_path: str = "data/processed/filtered_data.parquet"):
    """Saves the filtered dataframe to Parquet."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Filtered data saved to {output_path}")

# --- Checksum Registration (T014c) ---
def record_checksum(file_path: str, state_file: str = "state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml"):
    """
    Registers the SHA256 checksum of a file in the project state file.
    Implements Constitution Principle III.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Cannot record checksum: File not found - {file_path}")
    
    # Calculate SHA256
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    checksum = f"sha256:{sha256_hash.hexdigest()}"
    logger.info(f"Calculated checksum for {file_path}: {checksum}")
    
    # Load or initialize state
    state = {}
    if os.path.exists(state_file):
        try:
            import yaml
            with open(state_file, 'r') as f:
                state = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load existing state file: {e}. Starting fresh.")
            state = {}
    
    # Ensure structure exists
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    # Update checksum
    state['artifact_hashes'][file_path] = checksum
    
    # Write back
    Path(state_file).parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml
        with open(state_file, 'w') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Checksum recorded in {state_file}")
    except Exception as e:
        logger.error(f"Failed to write state file: {e}")
        raise

# --- Main Entry Point ---
def main():
    parser = argparse.ArgumentParser(description="Data Ingestion, Validation, and Outlier Handling Pipeline")
    parser.add_argument('--input', type=str, default='data/raw/synthetic_data.csv', help='Input data file path')
    parser.add_argument('--output-dir', type=str, default='data/processed', help='Output directory for processed data')
    parser.add_argument('--mode', type=str, default='real', choices=['real', 'synthetic'], help='Execution mode')
    args = parser.parse_args()

    # Ensure output directories exist
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    Path("data/results").mkdir(parents=True, exist_ok=True)
    Path("data/logs").mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load Required Variables
        required_predictors, required_outcomes = load_required_variables()
        if not required_predictors and not required_outcomes:
            logger.error("No required variables loaded. Cannot proceed.")
            sys.exit(1)

        # 2. Load Data
        df = load_data(args.input)
        logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns.")

        # 3. Validate Variables
        validation_result = validate_variables(df, required_predictors, required_outcomes)
        save_variable_metrics(validation_result)

        if validation_result['status'] == 'FAIL':
            logger.error("Validation failed. Missing required variables. Halting.")
            # Specific error message as per T013
            missing_str = ", ".join(validation_result['missing_variables'])
            logger.error(f"Variable(s) missing: {missing_str}")
            sys.exit(1)

        # 4. Detect Outliers
        outlier_report = detect_outliers_iqr(df)
        save_outlier_report(outlier_report)

        # 5. Filter Outliers
        filtered_df = filter_outliers(df, outlier_report['excluded_indices'])
        filtered_path = os.path.join(args.output_dir, "filtered_data.parquet")
        save_filtered_data(filtered_df, filtered_path)

        # 6. Register Checksum (T014c)
        # Path must be relative to project root for state consistency
        relative_path = filtered_path
        record_checksum(relative_path)

        logger.info("Ingestion and validation pipeline completed successfully.")

    except Exception as e:
        logger.exception(f"Pipeline failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()