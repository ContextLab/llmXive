"""
code/ingest.py

Data ingestion, validation, and filtering utilities for the Gut Microbiome-Sleep Architecture pipeline.
Handles schema validation, variable checks, outlier detection, and dataset loading.
"""
import os
import sys
import json
import logging
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)

# --- Custom Exceptions ---
class MissingDataError(Exception):
    """Raised when required data or variables are missing."""
    pass

class StreamingNotSupportedError(Exception):
    """Raised when streaming is attempted but not supported for the given format."""
    pass

# --- Helper Functions ---

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema file.
    
    Args:
        schema_path: Path to the YAML schema file.
        
    Returns:
        Dictionary containing the schema.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is invalid YAML.
    """
    logger.info(f"Loading schema from {schema_path}")
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        logger.debug(f"Schema loaded successfully: {list(schema.keys())}")
        return schema
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing schema YAML: {e}")
        raise

def load_required_variables(config_path: str) -> Dict[str, List[str]]:
    """
    Load the list of required predictor and outcome variables from config.
    
    Args:
        config_path: Path to the required_variables.yaml file.
        
    Returns:
        Dictionary with keys 'predictors' and 'outcomes', each mapping to a list of strings.
    """
    logger.info(f"Loading required variables from {config_path}")
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        predictors = config.get('predictors', [])
        outcomes = config.get('outcomes', [])
        
        logger.info(f"Found {len(predictors)} required predictors and {len(outcomes)} required outcomes.")
        return {'predictors': predictors, 'outcomes': outcomes}
    except FileNotFoundError:
        logger.error(f"Required variables config not found: {config_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading required variables: {e}")
        raise

def validate_variables(df: pd.DataFrame, required_vars: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Validate that the dataset contains all required predictor and outcome variables.
    
    Args:
        df: The input DataFrame.
        required_vars: Dictionary containing 'predictors' and 'outcomes' lists.
        
    Returns:
        Dictionary containing validation metrics:
            - percentage_loaded (float)
            - missing_variables (list of strings)
            - total_required (int)
    """
    logger.info("Starting variable validation...")
    
    predictors = required_vars.get('predictors', [])
    outcomes = required_vars.get('outcomes', [])
    
    all_required = predictors + outcomes
    total_required = len(all_required)
    
    if total_required == 0:
        logger.warning("No required variables defined in config.")
        return {
            'percentage_loaded': 100.0,
            'missing_variables': [],
            'total_required': 0
        }
    
    available_columns = set(df.columns)
    missing_vars = [var for var in all_required if var not in available_columns]
    
    count_present = total_required - len(missing_vars)
    percentage_loaded = (count_present / total_required) * 100.0 if total_required > 0 else 0.0
    
    logger.info(f"Validation complete. Loaded {count_present}/{total_required} variables ({percentage_loaded:.2f}%).")
    if missing_vars:
        logger.warning(f"Missing variables: {missing_vars}")
    
    return {
        'percentage_loaded': percentage_loaded,
        'missing_variables': missing_vars,
        'total_required': total_required
    }
    
    logger.info(f"Validation complete: {found_count}/{total_required} variables found ({percentage_loaded:.1f}%)")
    if all_missing:
        logger.warning(f"Missing variables: {all_missing}")
    
    return metrics['is_valid'], metrics

def save_variable_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Save variable load metrics to a JSON file.
    
    Args:
        metrics: The metrics dictionary from validate_variables.
        output_path: Path to the output JSON file.
    """
    logger.info(f"Saving variable metrics to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info("Variable metrics saved.")

def load_data(input_path: str, required_vars: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Load data from a CSV/TSV file and validate variables.
    
    Args:
        input_path: Path to the input data file.
        required_vars: Dictionary containing 'predictors' and 'outcomes' lists.
        
    Returns:
        The loaded DataFrame.
        
    Raises:
        MissingDataError: If required variables are missing.
        FileNotFoundError: If the input file is not found.
    """
    logger.info(f"Loading data from {input_path}")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    # Detect delimiter
    with open(input_path, 'r') as f:
        first_line = f.readline()
        if '\t' in first_line:
            delimiter = '\t'
            logger.info("Detected TSV format")
        else:
            delimiter = ','
            logger.info("Detected CSV format")
    
    # Infer separator
    with open(input_path, 'r') as f:
        first_line = f.readline()
        separator = '\t' if '\t' in first_line else ','
    
    try:
        df = pd.read_csv(input_path, sep=separator)
        logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns.")
    except Exception as e:
        logger.error(f"Error reading data file: {e}")
        raise
    
    # Validate variables
    metrics = validate_variables(df, required_vars)
    
    # Save metrics to disk BEFORE any exit check (per T012)
    metrics_output_path = "data/results/variable_load_metrics.json"
    save_variable_metrics(metrics, metrics_output_path)
    
    # Check for 100% completion
    if metrics['percentage_loaded'] < 100.0:
        missing = ", ".join(metrics['missing_variables'])
        error_msg = f"CRITICAL: Variable load incomplete. Missing: {missing}. Halting execution."
        logger.error(error_msg)
        raise MissingDataError(error_msg)
    
    logger.info("Variable validation passed (100%).")
    return df

def detect_outliers_iqr(df: pd.DataFrame, threshold: float = 1.5) -> pd.DataFrame:
    """
    Detect outliers using the IQR method.
    
    Args:
        df: The input DataFrame.
        threshold: The IQR multiplier threshold (default 1.5).
        
    Returns:
        A DataFrame with an 'is_outlier' boolean column.
    """
    logger.info("Detecting outliers using IQR method...")
    df_copy = df.copy()
    
    # Select only numeric columns for outlier detection
    numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
    
    outlier_flags = pd.Series(False, index=df_copy.index)
    
    for col in numeric_cols:
        Q1 = df_copy[col].quantile(0.25)
        Q3 = df_copy[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        
        col_outliers = (df_copy[col] < lower_bound) | (df_copy[col] > upper_bound)
        outlier_flags = outlier_flags | col_outliers
        
    df_copy['is_outlier'] = outlier_flags
    
    num_outliers = outlier_flags.sum()
    logger.info(f"Detected {num_outliers} outlier points across {len(numeric_cols)} numeric columns.")
    
    return df_copy

def filter_outliers(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[int]]:
    """
    Remove rows flagged as outliers.
    
    Args:
        df: The input DataFrame with an 'is_outlier' column.
        
    Returns:
        Tuple of (filtered DataFrame, list of excluded indices).
    """
    logger.info("Filtering outliers...")
    
    if 'is_outlier' not in df.columns:
        logger.warning("No 'is_outlier' column found. Returning original data.")
        return df, []
    
    excluded_indices = df[df['is_outlier']].index.tolist()
    filtered_df = df[~df['is_outlier']].copy()
    
    if 'is_outlier' in filtered_df.columns:
        filtered_df = filtered_df.drop(columns=['is_outlier'])
        
    logger.info(f"Excluded {len(excluded_indices)} rows. Remaining: {len(filtered_df)} rows.")
    return filtered_df, excluded_indices

def save_outlier_report(excluded_indices: List[int], output_path: str) -> None:
    """
    Save the outlier report to a JSON file.
    
    Args:
        excluded_indices: List of row indices that were excluded.
        output_path: Path to the output JSON file.
    """
    logger.info(f"Saving outlier report to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    report = {
        'count_excluded': len(excluded_indices),
        'excluded_indices': excluded_indices
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info("Outlier report saved.")

def save_filtered_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the filtered DataFrame to a Parquet file.
    
    Args:
        df: The filtered DataFrame.
        output_path: Path to the output Parquet file.
    """
    logger.info(f"Saving filtered data to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    logger.info(f"Filtered data saved: {output_path}")

def load_streamed_dataset(input_path: str, chunksize: int = 10000) -> pd.DataFrame:
    """
    Load a large dataset in chunks to manage memory.
    
    Args:
        input_path: Path to the input CSV file.
        chunksize: Number of rows per chunk.
        
    Returns:
        Concatenated DataFrame.
        
    Raises:
        StreamingNotSupportedError: If the file format doesn't support streaming.
    """
    logger.info(f"Loading streamed dataset from {input_path} (chunksize={chunksize})")
    
    if not input_path.endswith('.csv') and not input_path.endswith('.tsv'):
        raise StreamingNotSupportedError("Streaming only supported for CSV/TSV files.")
    
    sep = '\t' if input_path.endswith('.tsv') else ','
    chunks = []
    total_rows = 0
    
    for chunk in pd.read_csv(input_path, sep=sep, chunksize=chunksize):
        chunks.append(chunk)
        total_rows += len(chunk)
        logger.debug(f"Loaded chunk with {len(chunk)} rows. Total so far: {total_rows}")
    
    logger.info(f"Streamed load complete. Total rows: {total_rows}")
    return pd.concat(chunks, ignore_index=True)

def fetch_verified_real_dataset(dataset_id: str) -> pd.DataFrame:
    """
    Placeholder for fetching a verified real dataset.
    In a real implementation, this would query an API or download from a specific URL.
    
    Args:
        dataset_id: The identifier for the dataset.
        
    Returns:
        The loaded DataFrame.
        
    Raises:
        MissingDataError: If the dataset cannot be found or fetched.
    """
    logger.info(f"Attempting to fetch verified real dataset: {dataset_id}")
    # Implementation would go here based on specific data sources
    raise MissingDataError(f"Real dataset fetch for '{dataset_id}' not yet implemented or source unavailable.")

def validate_loaded_data(df: pd.DataFrame, required_vars: Dict[str, List[str]]) -> bool:
    """
    Final validation of the loaded data.
    
    Args:
        df: The loaded DataFrame.
        required_vars: Dictionary of required variables.
        
    Returns:
        True if valid, raises exception otherwise.
    """
    metrics = validate_variables(df, required_vars)
    if metrics['percentage_loaded'] < 100.0:
        raise MissingDataError(f"Data validation failed. Missing: {metrics['missing_variables']}")
    return True

def calculate_checksum(file_path: str) -> str:
    """
    Calculate the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest string.
    """
    import hashlib
    sha256_hash = hashlib.sha256()
    logger.debug(f"Calculating checksum for {file_path}")
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    checksum = sha256_hash.hexdigest()
    logger.info(f"Checksum calculated: {checksum[:16]}...")
    return checksum

def register_checksum_in_state(file_path: str, state_path: str) -> None:
    """
    Register a file checksum in the project state YAML.
    
    Args:
        file_path: Path to the file being checksummed.
        state_path: Path to the state YAML file.
    """
    logger.info(f"Registering checksum for {file_path} in {state_path}")
    checksum = calculate_checksum(file_path)
    
    state = {}
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    state['artifact_hashes'][os.path.basename(file_path)] = checksum
    
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    logger.info(f"Checksum registered: {checksum}")

def main():
    """
    Main entry point for the ingestion module when run as a script.
    Handles command-line arguments for testing or standalone execution.
    """
    parser = argparse.ArgumentParser(description="Data Ingestion and Validation Module")
    parser.add_argument('--input', type=str, required=True, help='Path to input data file (CSV/TSV)')
    parser.add_argument('--output', type=str, required=True, help='Path to output filtered data (Parquet)')
    parser.add_argument('--config', type=str, default='data/config/required_variables.yaml', help='Path to required variables config')
    parser.add_argument('--schema', type=str, default='specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml', help='Path to dataset schema')
    
    args = parser.parse_args()
    
    try:
        # 1. Load Config
        required_vars = load_required_variables(args.config)
        
        # 2. Load Data
        df = load_data(args.input, required_vars)
        
        # 3. Detect Outliers
        df_with_flags = detect_outliers_iqr(df)
        
        # 4. Filter Outliers
        filtered_df, excluded_indices = filter_outliers(df_with_flags)
        
        # 5. Save Artifacts
        save_outlier_report(excluded_indices, 'data/results/outlier_report.json')
        save_filtered_data(filtered_df, args.output)
        
        logger.info("Ingestion pipeline completed successfully.")
        
    except MissingDataError as e:
        logger.error(f"Data Error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"File Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()