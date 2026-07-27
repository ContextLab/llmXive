import os
import sys
import json
import logging
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging for the ingest module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ingest")

class MissingDataError(Exception):
    """Raised when required data is missing or incomplete."""
    pass

class StreamingNotSupportedError(Exception):
    """Raised when streaming is requested but not supported for the dataset."""
    pass

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema definition.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary containing the schema.
    """
    logger.info(f"Loading schema from {schema_path}")
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    logger.info(f"Schema loaded successfully with {len(schema)} keys")
    return schema

def load_required_variables(config_path: str) -> Dict[str, List[str]]:
    """
    Load required predictor and outcome variables from config.
    
    Args:
        config_path: Path to the required_variables.yaml file.
        
    Returns:
        Dictionary with 'predictors' and 'outcomes' lists.
    """
    logger.info(f"Loading required variables from {config_path}")
    if not os.path.exists(config_path):
        logger.error(f"Required variables config not found at {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    predictors = config.get('predictors', [])
    outcomes = config.get('outcomes', [])
    
    logger.info(f"Loaded {len(predictors)} predictors and {len(outcomes)} outcomes")
    return {'predictors': predictors, 'outcomes': outcomes}

def validate_variables(df: pd.DataFrame, required: Dict[str, List[str]]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the dataframe contains all required variables.
    
    Args:
        df: Input dataframe.
        required: Dictionary of required predictors and outcomes.
        
    Returns:
        Tuple of (is_valid, metrics_dict)
    """
    logger.info("Starting variable validation")
    columns = set(df.columns)
    
    missing_predictors = [p for p in required['predictors'] if p not in columns]
    missing_outcomes = [o for o in required['outcomes'] if o not in columns]
    
    all_missing = missing_predictors + missing_outcomes
    total_required = len(required['predictors']) + len(required['outcomes'])
    found_count = total_required - len(all_missing)
    
    if total_required > 0:
        percentage_loaded = (found_count / total_required) * 100
    else:
        percentage_loaded = 100.0
        
    metrics = {
        'total_required': total_required,
        'found': found_count,
        'missing_count': len(all_missing),
        'percentage_loaded': percentage_loaded,
        'missing_predictors': missing_predictors,
        'missing_outcomes': missing_outcomes,
        'is_valid': len(all_missing) == 0
    }
    
    logger.info(f"Validation complete: {found_count}/{total_required} variables found ({percentage_loaded:.1f}%)")
    if all_missing:
        logger.warning(f"Missing variables: {all_missing}")
    
    return metrics['is_valid'], metrics

def save_variable_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Save variable load metrics to a JSON file.
    
    Args:
        metrics: Metrics dictionary from validate_variables.
        output_path: Path to write the JSON file.
    """
    logger.info(f"Saving variable metrics to {output_path}")
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info("Variable metrics saved successfully")

def load_data(input_path: str, required: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Load data from CSV/TSV and validate variables.
    
    Args:
        input_path: Path to the input data file.
        required: Dictionary of required variables.
        
    Returns:
        Loaded and validated DataFrame.
        
    Raises:
        MissingDataError: If required variables are missing.
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
    
    df = pd.read_csv(input_path, delimiter=delimiter)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    
    # Validate variables
    is_valid, metrics = validate_variables(df, required)
    
    # Always save metrics, even on failure, to satisfy SC-001
    metrics_path = "data/results/variable_load_metrics.json"
    save_variable_metrics(metrics, metrics_path)
    
    if not is_valid:
        missing_str = ", ".join(metrics['missing_predictors'] + metrics['missing_outcomes'])
        error_msg = f"Missing required variables: {missing_str}"
        logger.error(error_msg)
        raise MissingDataError(error_msg)
        
    logger.info("Data validation passed")
    return df

def detect_outliers_iqr(df: pd.DataFrame, column: str) -> List[int]:
    """
    Detect outliers using the IQR method (>1.5x IQR).
    
    Args:
        df: Input dataframe.
        column: Column name to check.
        
    Returns:
        List of row indices that are outliers.
    """
    logger.info(f"Detecting outliers in column '{column}' using IQR method")
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found in dataframe")
        return []
        
    values = df[column].dropna()
    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outlier_mask = (values < lower_bound) | (values > upper_bound)
    outlier_indices = values[outlier_mask].index.tolist()
    
    logger.info(f"Found {len(outlier_indices)} outliers in '{column}' (IQR method)")
    return outlier_indices

def filter_outliers(df: pd.DataFrame, outlier_map: Dict[str, List[int]]) -> pd.DataFrame:
    """
    Remove rows flagged as outliers.
    
    Args:
        df: Input dataframe.
        outlier_map: Dictionary mapping column names to outlier indices.
        
    Returns:
        Filtered dataframe.
    """
    logger.info("Filtering outliers")
    if not outlier_map:
        logger.info("No outliers to filter")
        return df
        
    all_outlier_indices = set()
    for indices in outlier_map.values():
        all_outlier_indices.update(indices)
        
    if not all_outlier_indices:
        logger.info("No rows marked for removal")
        return df
        
    logger.info(f"Removing {len(all_outlier_indices)} rows with outliers")
    filtered_df = df.drop(index=list(all_outlier_indices)).reset_index(drop=True)
    logger.info(f"Filtered dataset has {len(filtered_df)} rows")
    return filtered_df

def calculate_checksum(file_path: str) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest of the checksum.
    """
    logger.info(f"Calculating checksum for {file_path}")
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    checksum = sha256_hash.hexdigest()
    logger.info(f"Checksum calculated: {checksum[:16]}...")
    return checksum

def register_checksum_in_state(file_path: str, state_path: str, artifact_name: str) -> None:
    """
    Register a file checksum in the project state file.
    
    Args:
        file_path: Path to the file being registered.
        state_path: Path to the state YAML file.
        artifact_name: Name to use in the state file.
    """
    logger.info(f"Registering checksum for {artifact_name} in state file")
    checksum = calculate_checksum(file_path)
    
    state_dir = os.path.dirname(state_path)
    if state_dir and not os.path.exists(state_dir):
        os.makedirs(state_dir)
        
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {'artifact_hashes': {}}
        
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
        
    state['artifact_hashes'][artifact_name] = checksum
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
        
    logger.info(f"Registered checksum for {artifact_name}")

def load_streamed_dataset(input_path: str, chunksize: int = 10000) -> pd.DataFrame:
    """
    Load a dataset in chunks to handle large files.
    
    Args:
        input_path: Path to the input file.
        chunksize: Number of rows per chunk.
        
    Returns:
        Concatenated DataFrame.
    """
    logger.info(f"Loading dataset in chunks (size={chunksize}) from {input_path}")
    chunks = []
    for chunk in pd.read_csv(input_path, chunksize=chunksize):
        chunks.append(chunk)
        logger.debug(f"Loaded chunk of {len(chunk)} rows")
        
    df = pd.concat(chunks, ignore_index=True)
    logger.info(f"Streamed dataset loaded: {len(df)} total rows")
    return df

def fetch_verified_real_dataset(dataset_id: str) -> pd.DataFrame:
    """
    Fetch a verified real dataset by ID.
    
    Args:
        dataset_id: Identifier for the dataset.
        
    Returns:
        Loaded DataFrame.
        
    Raises:
        MissingDataError: If the dataset cannot be fetched.
    """
    logger.info(f"Attempting to fetch verified real dataset: {dataset_id}")
    # Implementation would go here for specific fetch logic
    # For now, raise an error to prevent silent fallback
    raise MissingDataError(f"Real dataset '{dataset_id}' fetch logic not implemented or source unavailable.")

def validate_loaded_data(df: pd.DataFrame, required: Dict[str, List[str]]) -> bool:
    """
    Perform final validation on loaded data.
    
    Args:
        df: Loaded dataframe.
        required: Required variables dict.
        
    Returns:
        True if valid.
    """
    logger.info("Performing final data validation")
    is_valid, _ = validate_variables(df, required)
    if is_valid:
        logger.info("Final validation passed")
    else:
        logger.error("Final validation failed")
    return is_valid

def main():
    """
    Main entry point for standalone execution.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Ingestion and Validation Module")
    parser.add_argument('--mode', type=str, default='real', choices=['real', 'synthetic'],
                      help='Data mode: real or synthetic')
    parser.add_argument('--input', type=str, required=True, help='Input data file path')
    parser.add_argument('--output', type=str, required=True, help='Output path for processed data')
    parser.add_argument('--config', type=str, default='data/config/required_variables.yaml',
                      help='Path to required variables config')
                      
    args = parser.parse_args()
    
    logger.info(f"Starting ingestion in {args.mode} mode")
    
    # Load configuration
    try:
        required_vars = load_required_variables(args.config)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
        
    # Load and validate data
    try:
        df = load_data(args.input, required_vars)
    except MissingDataError as e:
        logger.error(str(e))
        # Metrics already saved in load_data
        sys.exit(1)
        
    # Detect outliers
    outlier_indices = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        outliers = detect_outliers_iqr(df, col)
        if outliers:
            outlier_indices[col] = outliers
            
    # Filter outliers
    if outlier_indices:
        df = filter_outliers(df, outlier_indices)
        
    # Save processed data
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    df.to_csv(args.output, index=False)
    logger.info(f"Processed data saved to {args.output}")
    
    # Register checksum in state
    state_path = "state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml"
    register_checksum_in_state(args.output, state_path, "filtered_data.parquet")
    
    logger.info("Ingestion and validation completed successfully")

if __name__ == "__main__":
    main()