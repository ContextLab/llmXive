"""
Ingestion module for Gut Microbiome and Sleep Architecture data.
Handles data loading, validation, outlier detection, and real-data fetching.
"""
import os
import sys
import json
import logging
import hashlib
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Custom exception for real data fetching failures
class RealDataFetchError(Exception):
    """Raised when real data fetching fails."""
    pass

# --- Logging Setup ---
def setup_logging(log_dir: str = "data/logs", log_file: str = "ingest.log") -> logging.Logger:
    """
    Sets up logging to both file and console.
    Creates the log directory if it does not exist.
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    log_file_path = log_path / log_file
    
    logger = logging.getLogger("ingest")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates in repeated runs
    if logger.handlers:
        logger.handlers.clear()
    
    # File Handler
    fh = logging.FileHandler(log_file_path, mode='a')
    fh.setLevel(logging.INFO)
    
    # Console Handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

# --- Schema & Config Loading ---
def load_schema(schema_path: str = "specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml") -> Dict:
    """Loads the dataset schema definition."""
    try:
        import yaml
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.warning(f"Schema file not found at {schema_path}. Proceeding with default validation logic.")
        return {}
    except Exception as e:
        logging.error(f"Error loading schema: {e}")
        return {}

def load_required_variables(config_path: str = "data/config/required_variables.yaml") -> Dict[str, List[str]]:
    """
    Loads the required predictor and outcome variables from the config file.
    Returns a dict with keys 'predictors' and 'outcomes'.
    """
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Ensure keys exist
        if 'predictors' not in config:
            config['predictors'] = []
        if 'outcomes' not in config:
            config['outcomes'] = []
            
        return config
    except FileNotFoundError:
        logging.error(f"Required variables config not found at {config_path}.")
        return {"predictors": [], "outcomes": []}
    except Exception as e:
        logging.error(f"Error loading required variables: {e}")
        return {"predictors": [], "outcomes": []}

# --- Validation Logic ---
def validate_variables(df: pd.DataFrame, required_config: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Validates that the dataframe contains all required variables defined in the config.
    Returns a status object with pass/fail, missing variables, and load percentage.
    
    This function DOES NOT exit; it returns the result for the caller to decide action.
    """
    required_predictors = required_config.get('predictors', [])
    required_outcomes = required_config.get('outcomes', [])
    all_required = required_predictors + required_outcomes
    
    available_columns = set(df.columns)
    missing_vars = []
    
    for var in all_required:
        # Check exact match or case-insensitive match if needed (strict match preferred)
        if var not in available_columns:
            missing_vars.append(var)
    
    total_required = len(all_required)
    loaded_count = total_required - len(missing_vars)
    percentage_loaded = (loaded_count / total_required * 100) if total_required > 0 else 0.0
    
    status = "PASS" if len(missing_vars) == 0 else "FAIL"
    
    result = {
        "status": status,
        "percentage_loaded": round(percentage_loaded, 2),
        "missing_variables": missing_vars,
        "total_required": total_required
    }
    
    logging.info(f"Variable Validation: Status={status}, Loaded={loaded_count}/{total_required} ({percentage_loaded:.2f}%)")
    if missing_vars:
        logging.warning(f"Missing variables: {missing_vars}")
        
    return result

def save_variable_metrics(metrics: Dict[str, Any], output_path: str = "data/results/variable_load_metrics.json"):
    """Saves the variable load metrics to a JSON file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logging.info(f"Variable metrics saved to {output_path}")

# --- Real Data Fetching ---
def fetch_real_data(output_path: str = "data/raw/real_data.csv") -> pd.DataFrame:
    """
    Attempts to fetch real data from a verified source.
    For this implementation, we attempt to load from a specific local path
    or a verified URL if available. If no real data is found, it raises RealDataFetchError.
    
    NOTE: In a real production run, this would fetch from NCBI/Zenodo.
    Here, we enforce the "Fail Loudly" rule: if the specific real file is missing,
    we raise an error rather than generating synthetic data.
    """
    # Check for the expected real data file
    if os.path.exists(output_path):
        logging.info(f"Real data found at {output_path}. Loading...")
        try:
            df = pd.read_csv(output_path)
            return df
        except Exception as e:
            raise RealDataFetchError(f"Failed to parse real data file {output_path}: {e}")
    else:
        # Attempt to fetch from a verified source if the file is missing
        # For this project, we assume the user must provide the file or the pipeline fails.
        # We do not fall back to synthetic data.
        raise RealDataFetchError(
            f"Real data file not found at {output_path}. "
            "The pipeline requires real data. Please provide a verified dataset "
            "or run the data generation script separately if this is a development run "
            "(but note: T083 requires real data validation)."
        )

# --- Data Loading & Orchestration ---
def load_data(input_path: Optional[str] = None, mode: str = "real") -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main entry point for loading and validating data.
    
    Args:
        input_path: Path to the input file. If None, fetches real data.
        mode: "real" (default) or "synthetic" (for testing only, requires explicit flag).
    
    Returns:
        Tuple of (DataFrame, validation_metrics)
    """
    logger = logging.getLogger("ingest")
    
    # 1. Load Required Variables Config
    required_config = load_required_variables()
    if not required_config.get('predictors') and not required_config.get('outcomes'):
        logger.error("Failed to load required variables configuration. Cannot proceed.")
        sys.exit(1)

    df = None

    # 2. Fetch/Load Data
    if mode == "real":
        if input_path:
            # If input_path provided in real mode, try to load it
            if os.path.exists(input_path):
                try:
                    df = pd.read_csv(input_path)
                    logger.info(f"Loaded data from provided path: {input_path}")
                except Exception as e:
                    logger.error(f"Failed to load data from {input_path}: {e}")
                    sys.exit(1)
            else:
                # If file missing, try to fetch real data
                try:
                    df = fetch_real_data()
                except RealDataFetchError as e:
                    logger.error(str(e))
                    sys.exit(1)
        else:
            # No path provided, try to fetch real data
            try:
                df = fetch_real_data()
            except RealDataFetchError as e:
                logger.error(str(e))
                sys.exit(1)
    elif mode == "synthetic":
        # Explicit synthetic mode (for development/testing only)
        # We assume a generator exists or we load a pre-generated synthetic file
        # For T083, we strictly validate real data, but we must handle the case
        # where the user explicitly asks for synthetic mode for testing the pipeline logic.
        # However, T083's core requirement is to validate REAL data.
        # We will attempt to load a synthetic file if it exists, otherwise fail.
        synthetic_path = "data/raw/synthetic_data.csv"
        if input_path:
            synthetic_path = input_path
        
        if os.path.exists(synthetic_path):
            try:
                df = pd.read_csv(synthetic_path)
                logger.warning("Running in SYNTHETIC mode. Validation logic applied to synthetic data.")
            except Exception as e:
                logger.error(f"Failed to load synthetic data: {e}")
                sys.exit(1)
        else:
            logger.error("Synthetic data file not found and no real data available. Aborting.")
            sys.exit(1)
    else:
        logger.error(f"Unknown mode: {mode}")
        sys.exit(1)

    if df is None or df.empty:
        logger.error("Dataframe is empty after loading.")
        sys.exit(1)

    # 3. Validate Variables
    validation_result = validate_variables(df, required_config)
    
    # 4. Save Metrics
    save_variable_metrics(validation_result)

    # 5. HALT IF FAIL
    if validation_result["status"] == "FAIL":
        missing = ", ".join(validation_result["missing_variables"])
        error_msg = f"Validation FAILED. Missing required variables: {missing}. Halting execution."
        logger.error(error_msg)
        # T013 Requirement: Halt execution immediately with specific error
        sys.exit(1)

    logger.info("Data validation passed. Proceeding with analysis.")
    return df, validation_result

# --- Outlier Detection (T014/T014b) ---
def detect_outliers_iqr(df: pd.DataFrame, columns: Optional[List[str]] = None, k: float = 1.5) -> Dict[str, List[int]]:
    """
    Detects outliers using the IQR method.
    Returns a dictionary mapping column names to lists of outlier indices.
    """
    if columns is None:
        # Use numeric columns only
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    outlier_indices = set()
    outlier_details = {}
    
    for col in columns:
        if col not in df.columns:
            continue
        
        lower_bound = Q1 - k * IQR
        upper_bound = Q3 + k * IQR
        
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)].index.tolist()
        if outliers:
            outlier_details[col] = outliers
            outlier_indices.update(outliers)
    
    return {"columns": outlier_details, "total_indices": list(outlier_indices)}

def save_outlier_report(report: Dict, output_path: str = "data/results/outlier_report.json"):
    """Saves the outlier report to JSON."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logging.info(f"Outlier report saved to {output_path}")

def filter_outliers(df: pd.DataFrame, outlier_indices: List[int]) -> pd.DataFrame:
    """Removes rows with outlier indices from the dataframe."""
    return df.drop(index=outlier_indices).reset_index(drop=True)

def save_filtered_data(df: pd.DataFrame, output_path: str = "data/processed/filtered_data.parquet"):
    """Saves the filtered dataframe to a parquet file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logging.info(f"Filtered data saved to {output_path}")

def record_checksum(file_path: str, state_file: str = "state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml"):
    """Calculates SHA256 checksum and records it in the state file."""
    if not os.path.exists(file_path):
        logging.warning(f"Cannot record checksum: file {file_path} not found.")
        return
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    checksum = f"sha256:{sha256_hash.hexdigest()}"
    
    # Simple YAML update logic (in a real project, use a proper YAML library)
    import yaml
    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    if state_path.exists():
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}
    
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    state['artifact_hashes'][file_path] = checksum
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    
    logging.info(f"Recorded checksum for {file_path}: {checksum}")

# --- Main Entry Point ---
def main():
    parser = argparse.ArgumentParser(description="Ingest and validate data for Gut Microbiome-Sleep Analysis.")
    parser.add_argument('--input', type=str, help='Path to input CSV file.')
    parser.add_argument('--mode', type=str, default='real', choices=['real', 'synthetic'], help='Data mode: real or synthetic.')
    parser.add_argument('--output', type=str, default='data/raw/synthetic_data.csv', help='Output path for synthetic data (if generating) or input path.')
    
    args = parser.parse_args()
    
    logger = setup_logging()
    logger.info("Starting Ingestion Pipeline.")
    
    try:
        # Load and validate data
        df, metrics = load_data(input_path=args.input, mode=args.mode)
        
        # T014: Detect Outliers
        outlier_result = detect_outliers_iqr(df)
        outlier_report = {
            "count": len(outlier_result["total_indices"]),
            "excluded_indices": outlier_result["total_indices"],
            "details_by_column": outlier_result["columns"]
        }
        save_outlier_report(outlier_report)
        
        # T014b: Filter Outliers
        if outlier_result["total_indices"]:
            df_filtered = filter_outliers(df, outlier_result["total_indices"])
        else:
            df_filtered = df
        
        save_filtered_data(df_filtered)
        
        # T014c: Record Checksum
        record_checksum("data/processed/filtered_data.parquet")
        
        logger.info("Ingestion and Validation completed successfully.")
        
    except RealDataFetchError as e:
        logger.error(f"Real Data Fetch Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()