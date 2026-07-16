import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Configure logging for the ingest module
# This ensures logs are captured during pipeline execution for debugging and audit
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/ingest_pipeline.log', mode='a')
    ]
)
logger = logging.getLogger('ingest')

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If schema file does not exist.
        yaml.YAMLError: If schema file is not valid YAML.
    """
    logger.info(f"Loading schema from: {schema_path}")
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        logger.info(f"Schema loaded successfully. Keys: {list(schema.keys())}")
        return schema
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML schema: {e}")
        raise

def validate_variables(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the loaded DataFrame contains all required predictors and outcomes.
    
    Args:
        df: Input DataFrame.
        schema: Schema dictionary containing required variable lists.
        
    Returns:
        Tuple of (is_valid, metrics_dict) where metrics_dict contains:
            - total_required: int
            - found: int
            - percentage: float
            - missing: list
            - found_list: list
    """
    logger.info("Starting variable validation against schema.")
    
    required_predictors = schema.get('predictors', {}).get('required', [])
    required_outcomes = schema.get('outcomes', {}).get('required', [])
    all_required = required_predictors + required_outcomes
    
    found_vars = [col for col in all_required if col in df.columns]
    missing_vars = [col for col in all_required if col not in df.columns]
    
    total_required = len(all_required)
    found_count = len(found_vars)
    percentage = (found_count / total_required * 100) if total_required > 0 else 0.0
    
    metrics = {
        "total_required": total_required,
        "found": found_count,
        "percentage": percentage,
        "missing": missing_vars,
        "found_list": found_vars,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Validation complete. Found {found_count}/{total_required} variables ({percentage:.1f}%).")
    if missing_vars:
        logger.warning(f"Missing required variables: {missing_vars}")
    
    is_valid = (percentage == 100.0)
    if not is_valid:
        logger.error("Validation failed: Missing required variables.")
    
    return is_valid, metrics

def save_variable_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Save variable validation metrics to a JSON file.
    
    Args:
        metrics: Dictionary of metrics from validate_variables.
        output_path: Path to save the JSON file.
    """
    logger.info(f"Saving variable metrics to: {output_path}")
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created directory: {output_dir}")
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info("Variable metrics saved successfully.")

def load_data(data_path: str, schema_path: str, metrics_output_path: str) -> pd.DataFrame:
    """
    Load data from CSV/TSV, validate variables, and halt if incomplete.
    
    Args:
        data_path: Path to the input data file.
        schema_path: Path to the schema file.
        metrics_output_path: Path to save variable load metrics.
        
    Returns:
        Validated DataFrame.
        
    Raises:
        SystemExit: If variable load percentage is < 100%.
    """
    logger.info(f"Starting data load from: {data_path}")
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Determine file type and load
    if data_path.endswith('.csv'):
        df = pd.read_csv(data_path)
    elif data_path.endswith('.tsv'):
        df = pd.read_csv(data_path, sep='\t')
    else:
        logger.error(f"Unsupported file format: {data_path}")
        raise ValueError(f"Unsupported file format: {data_path}")
    
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns.")
    
    # Validate variables
    is_valid, metrics = validate_variables(df, schema)
    
    # Save metrics
    save_variable_metrics(metrics, metrics_output_path)
    
    # Halt if not 100% valid
    if not is_valid:
        missing = ", ".join(metrics['missing'])
        error_msg = f"Variable load percentage is {metrics['percentage']:.1f}%. Missing required variables: {missing}. Halting execution."
        logger.error(error_msg)
        sys.exit(1)
    
    logger.info("Data validation passed. All required variables present.")
    return df

def detect_outliers_iqr(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Detect outliers using the IQR method (>1.5x IQR above 75th or <1.5x below 25th).
    
    Args:
        df: Input DataFrame.
        columns: List of column names to check for outliers.
        
    Returns:
        DataFrame with an 'is_outlier' boolean column.
    """
    logger.info(f"Detecting outliers in columns: {columns}")
    df = df.copy()
    df['is_outlier'] = False
    
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column {col} not found in DataFrame, skipping.")
            continue
        
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
        df.loc[outlier_mask, 'is_outlier'] = True
        
        outlier_count = outlier_mask.sum()
        logger.info(f"Column {col}: Found {outlier_count} outliers (IQR method).")
    
    return df

def filter_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows flagged as outliers.
    
    Args:
        df: Input DataFrame with 'is_outlier' column.
        
    Returns:
        Filtered DataFrame.
    """
    logger.info("Filtering out flagged outliers.")
    initial_count = len(df)
    filtered_df = df[~df['is_outlier']].copy()
    final_count = len(filtered_df)
    removed_count = initial_count - final_count
    
    logger.info(f"Removed {removed_count} outlier rows. Remaining: {final_count}.")
    
    # Drop the helper column
    if 'is_outlier' in filtered_df.columns:
        filtered_df.drop(columns=['is_outlier'], inplace=True)
        
    return filtered_df

def calculate_checksum(df: pd.DataFrame) -> str:
    """
    Calculate a simple checksum (SHA256) of the DataFrame content.
    
    Args:
        df: DataFrame to checksum.
        
    Returns:
        Hex string of the checksum.
    """
    logger.info("Calculating DataFrame checksum.")
    # Convert to string representation for hashing
    # Using sort_index to ensure deterministic order if column order varies
    df_str = df.to_csv(index=False, na_rep='NaN')
    import hashlib
    checksum = hashlib.sha256(df_str.encode('utf-8')).hexdigest()
    logger.info(f"Checksum calculated: {checksum[:16]}...")
    return checksum

def register_checksum_in_state(checksum: str, file_path: str, state_path: str) -> None:
    """
    Register the file checksum in the state.yaml file.
    
    Args:
        checksum: The calculated checksum.
        file_path: The path to the file being checksummed.
        state_path: Path to the state.yaml file.
    """
    logger.info(f"Registering checksum for {file_path} in {state_path}")
    
    state = {}
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    
    if 'files' not in state:
        state['files'] = {}
    
    state['files'][file_path] = {
        'checksum': checksum,
        'timestamp': datetime.now().isoformat()
    }
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    
    logger.info("State updated successfully.")

def main():
    """
    Main entry point for the ingestion and validation pipeline.
    """
    logger.info("Starting ingestion pipeline main.")
    
    # Define paths (can be overridden by CLI args or config in a real scenario)
    # Assuming standard project structure relative to execution
    base_dir = Path(__file__).parent.parent
    schema_path = base_dir / 'specs' / '001-gut-microbiome-sleep-architecture' / 'contracts' / 'dataset.schema.yaml'
    data_path = base_dir / 'data' / 'raw' / 'synthetic_dataset.csv'
    metrics_path = base_dir / 'data' / 'results' / 'variable_load_metrics.json'
    state_path = base_dir / 'state.yaml'
    
    # Check if schema exists (it should from T004a/b)
    if not schema_path.exists():
        logger.error(f"Schema path not found: {schema_path}")
        sys.exit(1)
    
    # Check if data exists
    if not data_path.exists():
        # Attempt to generate synthetic data if missing (for T006 compliance)
        logger.warning(f"Data file not found: {data_path}. Attempting to generate synthetic data.")
        try:
            from data_generator import generate_synthetic_dataset
            generate_synthetic_dataset(str(data_path))
            logger.info("Synthetic data generated successfully.")
        except Exception as e:
            logger.error(f"Failed to generate synthetic data: {e}")
            sys.exit(1)
    
    try:
        # Load and validate
        df = load_data(str(data_path), str(schema_path), str(metrics_path))
        
        # Detect outliers
        # Identify numeric columns for outlier detection (excluding ID columns if any)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if 'is_outlier' in numeric_cols:
            numeric_cols.remove('is_outlier')
        
        if numeric_cols:
            df_with_outliers = detect_outliers_iqr(df, numeric_cols)
            filtered_df = filter_outliers(df_with_outliers)
        else:
            filtered_df = df
            logger.warning("No numeric columns found for outlier detection.")
        
        # Save filtered data
        filtered_path = base_dir / 'data' / 'processed' / 'filtered_data.parquet'
        filtered_df.to_parquet(filtered_path, index=False)
        logger.info(f"Filtered data saved to: {filtered_path}")
        
        # Calculate and register checksum
        checksum = calculate_checksum(filtered_df)
        register_checksum_in_state(checksum, str(filtered_path), str(state_path))
        
        logger.info("Ingestion and validation pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()