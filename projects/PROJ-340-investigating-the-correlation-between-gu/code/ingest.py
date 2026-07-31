"""
Data Ingestion and Validation Module.

Handles loading, validation, outlier detection, and filtering of data.
Implements T012, T013, T014, T014b, and T017 (Logging).
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

# Setup logging configuration
# T017: Configure logging for ingestion and validation steps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/ingestion.log')
    ]
)
logger = logging.getLogger("ingest")

def load_schema(schema_path):
    """Load schema from YAML/JSON file."""
    logger.info(f"Attempting to load schema from: {schema_path}")
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found: {schema_path}")
        return {}
    
    try:
        # Simplified schema loading for this implementation
        # In a real scenario, this would parse YAML
        logger.debug("Schema file found, parsing structure...")
        return {}
    except Exception as e:
        logger.error(f"Failed to parse schema: {e}")
        return {}

def load_required_variables(config_path):
    """Load required variables from config."""
    logger.info(f"Loading required variables from config: {config_path}")
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        return [], []
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        predictors = config.get("required_predictors", [])
        outcomes = config.get("required_outcomes", [])
        
        logger.info(f"Loaded {len(predictors)} predictors and {len(outcomes)} outcomes.")
        return predictors, outcomes
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        return [], []
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
        return [], []

def validate_variables(df, required_predictors, required_outcomes):
    """
    T012: Validate that required variables are present in the dataset.
    Returns a status object.
    """
    logger.info("Starting variable validation.")
    missing = []
    all_required = required_predictors + required_outcomes
    
    for var in all_required:
        if var not in df.columns:
            missing.append(var)
    
    total_required = len(all_required)
    loaded = total_required - len(missing)
    percentage = (loaded / total_required * 100) if total_required > 0 else 0.0
    
    status = "PASS" if len(missing) == 0 else "FAIL"
    
    logger.info(f"Validation result: {status} ({loaded}/{total_required} variables found).")
    if missing:
        logger.warning(f"Missing variables: {missing}")
    
    return {
        "status": status,
        "percentage_loaded": percentage,
        "missing_variables": missing,
        "total_required": total_required
    }

def save_variable_metrics(output_path, metrics):
    """Save variable load metrics to JSON."""
    logger.info(f"Saving variable metrics to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Variable metrics saved successfully.")

def load_data(input_path, config_path):
    """
    T013: Load data and validate variables.
    Halts execution if validation fails.
    """
    logger.info(f"Loading data from {input_path}")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Successfully loaded dataset with {len(df)} rows and {len(df.columns)} columns.")
    except Exception as e:
        logger.error(f"Failed to read CSV file: {e}")
        raise
    
    predictors, outcomes = load_required_variables(config_path)
    
    if not predictors and not outcomes:
        logger.error("No required variables loaded from config. Cannot proceed.")
        sys.exit(1)
    
    status = validate_variables(df, predictors, outcomes)
    
    if status["status"] == "FAIL":
        logger.error(f"Validation failed. Missing variables: {status['missing_variables']}")
        sys.exit(1)
    
    logger.info(f"Validation passed. Loaded {status['percentage_loaded']:.1f}% of required variables.")
    return df

def detect_outliers_iqr(df, columns):
    """
    T014: Detect outliers using IQR method.
    Returns list of row indices that are outliers.
    """
    logger.info("Detecting outliers using IQR method.")
    outlier_indices = set()
    
    for col in columns:
        if col not in df.columns:
            continue
        
        try:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            indices = df[mask].index.tolist()
            outlier_indices.update(indices)
            
            logger.debug(f"Column {col}: Found {len(indices)} outliers.")
        except Exception as e:
            logger.warning(f"Could not calculate outliers for column {col}: {e}")
    
    logger.info(f"Total unique outlier rows detected: {len(outlier_indices)}")
    return list(outlier_indices)

def save_outlier_report(output_path, outlier_indices, total_rows):
    """
    T014b: Save outlier report to JSON.
    """
    logger.info(f"Saving outlier report to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "count": len(outlier_indices),
        "excluded_indices": sorted(outlier_indices),
        "percentage_total": (len(outlier_indices) / total_rows * 100) if total_rows > 0 else 0.0
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Outlier report saved: {report['count']} points excluded ({report['percentage_total']:.2f}%).")
    return report

def filter_outliers(df, outlier_indices):
    """
    T014b: Filter out outliers from the dataframe.
    """
    logger.info(f"Filtering out {len(outlier_indices)} outlier rows.")
    filtered_df = df.drop(index=outlier_indices)
    logger.info(f"Filtered dataset size: {len(filtered_df)} rows.")
    return filtered_df

def save_filtered_data(df, output_path):
    """
    T014b: Save filtered data to Parquet.
    """
    logger.info(f"Saving filtered data to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info("Filtered data saved successfully.")

def main():
    logger.info("Starting Ingestion and Validation Pipeline.")
    parser = argparse.ArgumentParser(description="Ingest and validate data")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file")
    parser.add_argument("--config", type=str, default="data/config/research_design.yaml", help="Config file")
    parser.add_argument("--output", type=str, default="data/processed/filtered_data.parquet", help="Output path")
    args = parser.parse_args()
    
    try:
        # Load and validate
        df = load_data(args.input, args.config)
        
        # Detect outliers
        outliers = detect_outliers_iqr(df, df.columns.tolist())
        
        # Save report
        report_path = str(Path(args.output).parent.parent / "results" / "outlier_report.json")
        save_outlier_report(report_path, outliers, len(df))
        
        # Filter and save
        filtered_df = filter_outliers(df, outliers)
        save_filtered_data(filtered_df, args.output)
        
        logger.info("Ingestion and validation pipeline completed successfully.")
        print("Ingestion complete.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()