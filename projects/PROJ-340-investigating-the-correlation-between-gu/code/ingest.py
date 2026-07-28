"""
Data Ingestion and Validation Module.

Handles loading, validation, outlier detection, and filtering of microbiome and sleep data.
"""
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

# Configure logging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/ingest.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
REQUIRED_VARIABLES_PATH = "data/config/required_variables.yaml"
VARIABLE_METRICS_PATH = "data/results/variable_load_metrics.json"
OUTLIER_REPORT_PATH = "data/results/outlier_report.json"
FILTERED_DATA_PATH = "data/processed/filtered_data.parquet"
STATE_FILE_PATH = "state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml"

def load_schema(schema_path: str = REQUIRED_VARIABLES_PATH) -> Dict[str, Any]:
    """Load the schema from a YAML file."""
    logger.info(f"Loading schema from {schema_path}")
    try:
        with open(schema_path, 'r') as f:
            import yaml
            schema = yaml.safe_load(f)
            logger.info(f"Schema loaded successfully with {len(schema)} keys")
            return schema
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading schema: {e}")
        raise

def load_required_variables(schema: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Extract required predictor and outcome variables from the schema."""
    logger.info("Extracting required variables from schema")
    predictors = schema.get('required_predictors', [])
    outcomes = schema.get('required_outcomes', [])
    logger.info(f"Found {len(predictors)} predictors and {len(outcomes)} outcomes")
    return predictors, outcomes

def validate_variables(df: pd.DataFrame, predictors: List[str], outcomes: List[str]) -> Dict[str, Any]:
    """
    Validate that the dataframe contains all required variables.
    Returns a metrics dictionary with status, percentage, and missing variables.
    """
    logger.info("Validating variables against required list")
    all_required = predictors + outcomes
    total_required = len(all_required)
    
    if total_required == 0:
        logger.warning("No required variables found in schema")
        return {
            "status": "FAIL",
            "percentage_loaded": 0.0,
            "missing_variables": [],
            "total_required": 0
        }

    missing = []
    for var in all_required:
        if var not in df.columns:
            missing.append(var)
    
    present_count = total_required - len(missing)
    percentage = (present_count / total_required) * 100.0
    status = "PASS" if len(missing) == 0 else "FAIL"
    
    metrics = {
        "status": status,
        "percentage_loaded": percentage,
        "missing_variables": missing,
        "total_required": total_required
    }
    
    logger.info(f"Validation complete: {status}, {percentage:.2f}% loaded, missing: {missing}")
    return metrics

def save_variable_metrics(metrics: Dict[str, Any], output_path: str = VARIABLE_METRICS_PATH) -> None:
    """Save variable validation metrics to a JSON file."""
    logger.info(f"Saving variable metrics to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info("Variable metrics saved successfully")

def load_data(input_path: str, mode: str = "synthetic") -> pd.DataFrame:
    """
    Load data from a CSV or TSV file.
    Validates that all required variables are present before returning.
    """
    logger.info(f"Loading data from {input_path} in {mode} mode")
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Determine file type
    if input_path.endswith('.csv'):
        df = pd.read_csv(input_path)
    elif input_path.endswith('.tsv'):
        df = pd.read_csv(input_path, sep='\t')
    else:
        logger.error(f"Unsupported file format: {input_path}")
        raise ValueError(f"Unsupported file format: {input_path}")
    
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    
    # Load schema and validate
    try:
        schema = load_schema()
        predictors, outcomes = load_required_variables(schema)
        metrics = validate_variables(df, predictors, outcomes)
        
        # Save metrics immediately
        save_variable_metrics(metrics)
        
        if metrics['status'] == "FAIL":
            missing_str = ", ".join(metrics['missing_variables'])
            error_msg = f"CRITICAL: Missing required variables: {missing_str}"
            logger.error(error_msg)
            sys.exit(1)
        
        logger.info("Data validation passed")
        return df
    except Exception as e:
        logger.error(f"Error during data validation: {e}")
        raise

def detect_outliers_iqr(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Detect outliers using the IQR method (>1.5x IQR above 75th or < 1.5x IQR below 25th).
    Returns a report with excluded indices and counts.
    """
    logger.info("Detecting outliers using IQR method")
    if columns is None:
        # Select only numeric columns
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    excluded_indices = set()
    outlier_details = {}
    
    for col in columns:
        if col not in df.columns:
            continue
        
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Find indices of outliers
        col_outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)].index.tolist()
        excluded_indices.update(col_outliers)
        outlier_details[col] = {
            "count": len(col_outliers),
            "lower_bound": lower_bound,
            "upper_bound": upper_bound
        }
    
    report = {
        "count": len(excluded_indices),
        "excluded_indices": sorted(list(excluded_indices)),
        "details_by_column": outlier_details
    }
    
    logger.info(f"Detected {report['count']} outliers across {len(columns)} columns")
    return report

def save_outlier_report(report: Dict[str, Any], output_path: str = OUTLIER_REPORT_PATH) -> None:
    """Save outlier detection report to a JSON file."""
    logger.info(f"Saving outlier report to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info("Outlier report saved successfully")

def filter_outliers(df: pd.DataFrame, report: Dict[str, Any]) -> pd.DataFrame:
    """
    Filter out rows identified as outliers in the report.
    """
    logger.info(f"Filtering {report['count']} outliers from data")
    excluded = report.get('excluded_indices', [])
    filtered_df = df.drop(index=excluded)
    logger.info(f"Filtered data shape: {filtered_df.shape}")
    return filtered_df

def save_filtered_data(df: pd.DataFrame, output_path: str = FILTERED_DATA_PATH) -> None:
    """Save filtered data to a Parquet file."""
    logger.info(f"Saving filtered data to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info("Filtered data saved successfully")

def record_checksum(file_path: str, state_file: str = STATE_FILE_PATH) -> None:
    """Record the SHA256 checksum of an artifact in the state file."""
    logger.info(f"Recording checksum for {file_path}")
    if not os.path.exists(file_path):
        logger.error(f"File not found for checksum: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    state_data = {}
    if os.path.exists(state_file):
        import yaml
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f) or {}
    
    if 'artifact_hashes' not in state_data:
        state_data['artifact_hashes'] = {}
    
    state_data['artifact_hashes'][file_path] = f"sha256:{file_hash}"
    
    import yaml
    with open(state_file, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    
    logger.info(f"Checksum recorded: {file_hash}")

def main():
    """Main entry point for data ingestion and validation."""
    parser = argparse.ArgumentParser(description="Data Ingestion and Validation Module")
    parser.add_argument('--input', type=str, required=True, help='Path to input data file (CSV/TSV)')
    parser.add_argument('--output', type=str, default='data/processed/filtered_data.parquet', help='Path to output filtered data file')
    parser.add_argument('--mode', type=str, default='synthetic', choices=['synthetic', 'real'], help='Data mode')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='Logging level')
    
    args = parser.parse_args()
    
    # Set logging level
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {args.log_level}')
    logging.getLogger().setLevel(numeric_level)
    
    logger.info(f"Starting ingestion pipeline: input={args.input}, mode={args.mode}")
    
    try:
        # Load data
        df = load_data(args.input, args.mode)
        
        # Detect outliers
        outlier_report = detect_outliers_iqr(df)
        
        # Save outlier report
        save_outlier_report(outlier_report)
        
        # Filter outliers
        filtered_df = filter_outliers(df, outlier_report)
        
        # Save filtered data
        save_filtered_data(filtered_df, args.output)
        
        # Record checksum
        record_checksum(args.output)
        
        logger.info("Ingestion pipeline completed successfully")
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()