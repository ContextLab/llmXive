"""
Data Cleaning Module for PROJ-018
Handles missing values, normalizes categorical codes, and performs power analysis.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Import from project modules
from config import get_config, get_config_path
from logging_config import update_log_section, initialize_modeling_log

# Custom Exceptions
class CustomDataError(Exception):
    """Custom exception for data processing errors."""
    pass

# --- Configuration & Logging Setup ---

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    config_path = get_config_path()
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise CustomDataError(f"Configuration file not found at {config_path}")
    except yaml.YAMLError as e:
        raise CustomDataError(f"Error parsing configuration file: {e}")

def setup_logging() -> logging.Logger:
    """Setup logging for the cleaning module."""
    logger = logging.getLogger('clean_data')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# --- Data Loading & Validation ---

def load_raw_data(logger: logging.Logger) -> pd.DataFrame:
    """
    Load raw data from the configured raw data path.
    Supports CSV and JSON formats.
    """
    config = get_config()
    base_dir = Path(config.get("project_root", "."))
    raw_path = base_dir / config.get("raw_data_path", "data/raw")
    
    # Look for the expected raw file
    raw_file = raw_path / "raw_survey_data.csv"
    if not raw_file.exists():
        # Fallback: check if processed data exists and needs re-cleaning (shouldn't happen in pipeline)
        # Or check for other common names
        alt_files = list(raw_path.glob("*.csv"))
        if alt_files:
            raw_file = alt_files[0]
            logger.warning(f"Using fallback raw file: {raw_file.name}")
        else:
            raise CustomDataError(f"No raw data file found in {raw_path}")

    logger.info(f"Loading raw data from {raw_file}")
    try:
        if raw_file.suffix == '.csv':
            df = pd.read_csv(raw_file)
        elif raw_file.suffix == '.json':
            df = pd.read_json(raw_file)
        else:
            raise CustomDataError(f"Unsupported file format: {raw_file.suffix}")
        
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
        return df
    except Exception as e:
        raise CustomDataError(f"Failed to load raw data: {e}")

def validate_variables(df: pd.DataFrame, logger: logging.Logger) -> List[str]:
    """
    Check for required fields and log gaps.
    Returns list of missing variable names.
    """
    required_vars = [
        'age', 'education', 'farm_size', 'credit_access', 
        'adoption_practices', 'community_engagement', 
        'engagement_membership', 'engagement_extension', 
        'engagement_collective', 'engagement_knowledge'
    ]
    
    missing = [var for var in required_vars if var not in df.columns]
    
    if missing:
        logger.warning(f"Missing required variables: {missing}")
        update_log_section("variable_validation", {
            "status": "warning",
            "missing_variables": missing,
            "timestamp": datetime.utcnow().isoformat()
        })
    else:
        logger.info("All required variables present")
        update_log_section("variable_validation", {
            "status": "passed",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    return missing

# --- Cleaning Logic ---

def calculate_missingness(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate missing value percentage per column."""
    return (df.isnull().sum() / len(df)) * 100

def handle_missing_values(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Handle missing values:
    - Drop rows with >30% missing values across required columns
    - Impute remaining numeric columns with median
    - Impute categorical with mode
    """
    df_clean = df.copy()
    
    # Identify numeric and categorical columns
    numeric_cols = df_clean.select_dtypes(include=['number']).columns
    categorical_cols = df_clean.select_dtypes(include=['object', 'category']).columns
    
    # Calculate row-wise missingness for required columns
    required_cols = ['age', 'education', 'farm_size', 'credit_access', 'adoption_practices']
    available_required = [c for c in required_cols if c in df_clean.columns]
    
    if available_required:
        missing_ratio = df_clean[available_required].isnull().mean(axis=1)
        rows_to_drop = missing_ratio > 0.30
        dropped_count = rows_to_drop.sum()
        
        if dropped_count > 0:
            logger.info(f"Dropping {dropped_count} rows with >30% missing required values")
            df_clean = df_clean[~rows_to_drop]
    
    # Impute numeric
    for col in numeric_cols:
        if df_clean[col].isnull().any():
            median_val = df_clean[col].median()
            df_clean[col] = df_clean[col].fillna(median_val)
            logger.debug(f"Imputed {col} with median {median_val}")
    
    # Impute categorical
    for col in categorical_cols:
        if df_clean[col].isnull().any():
            mode_val = df_clean[col].mode()
            if not mode_val.empty:
                df_clean[col] = df_clean[col].fillna(mode_val[0])
                logger.debug(f"Imputed {col} with mode {mode_val[0]}")
    
    return df_clean

def normalize_categorical_codes(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Normalize categorical codes to standard values.
    e.g., 'Yes', 'yes', 'Y' -> 'Yes'
    """
    df_norm = df.copy()
    
    # Standard mappings for common fields
    standardizations = {
        'credit_access': {'yes': 'Yes', 'no': 'No', 'y': 'Yes', 'n': 'No', 1: 'Yes', 0: 'No'},
        'education': {'primary': 'Primary', 'secondary': 'Secondary', 'tertiary': 'Tertiary', 
                      'none': 'None', 'high_school': 'Secondary'},
    }
    
    for col, mapping in standardizations.items():
        if col in df_norm.columns:
            df_norm[col] = df_norm[col].map(lambda x: mapping.get(x, x) if x in mapping else x)
            logger.debug(f"Normalized categorical codes for {col}")
    
    return df_norm

def calculate_power_analysis(df: pd.DataFrame, num_predictors: int = 5) -> Dict[str, Any]:
    """
    Calculate power analysis metrics.
    
    effective_N_events = count of positive outcomes in adoption_binary (or estimated proportion)
    ratio = effective_N_events / num_predictors
    
    Returns dict with 'shortfall' (bool) and 'ratio' (float).
    """
    # Check if adoption_binary exists
    if 'adoption_binary' in df.columns:
        # Count positive outcomes
        effective_N_events = int(df['adoption_binary'].sum())
        logger.info(f"Found adoption_binary column. Positive events: {effective_N_events}")
    else:
        # Estimate: assume a non-negligible proportion (e.g., 20%) if not available
        # This is a conservative estimate for planning purposes
        estimated_proportion = 0.20
        effective_N_events = int(len(df) * estimated_proportion)
        logger.warning(f"adoption_binary not found. Estimating events as {estimated_proportion*100}% of N ({effective_N_events})")
    
    if num_predictors <= 0:
        num_predictors = 1 # Avoid division by zero
    
    ratio = effective_N_events / num_predictors
    
    result = {
        "effective_N_events": effective_N_events,
        "num_predictors": num_predictors,
        "ratio": round(ratio, 2),
        "shortfall": ratio < 10
    }
    
    logger.info(f"Power analysis: {effective_N_events} events / {num_predictors} predictors = {ratio:.2f}")
    if result['shortfall']:
        logger.warning(f"Power shortfall detected! Ratio ({ratio:.2f}) < 10. Documenting as study limitation.")
    
    return result

def update_modeling_log_with_power_analysis(power_result: Dict[str, Any], logger: logging.Logger) -> None:
    """Update modeling_log.yaml with power analysis results."""
    config = get_config()
    base_dir = Path(config.get("project_root", "."))
    log_path = base_dir / config.get("modeling_log_path", "modeling_log.yaml")
    
    # Ensure log file exists
    if not log_path.exists():
        initialize_modeling_log()
    
    try:
        with open(log_path, 'r') as f:
            log_data = yaml.safe_load(f) or {}
        
        # Update power_analysis section
        log_data['power_analysis'] = power_result
        log_data['power_analysis']['timestamp'] = datetime.utcnow().isoformat()
        
        with open(log_path, 'w') as f:
            yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Updated modeling log with power analysis at {log_path}")
        
    except Exception as e:
        logger.error(f"Failed to update modeling log: {e}")
        # Do not raise, as per task requirement: "Do not halt execution"

def export_cleaned_data(df: pd.DataFrame, logger: logging.Logger) -> Path:
    """Export cleaned data to processed directory."""
    config = get_config()
    base_dir = Path(config.get("project_root", "."))
    proc_dir = base_dir / config.get("processed_data_path", "data/processed")
    
    proc_dir.mkdir(parents=True, exist_ok=True)
    output_path = proc_dir / "cleaned_data.csv"
    
    df.to_csv(output_path, index=False)
    logger.info(f"Exported cleaned data to {output_path} ({len(df)} records)")
    return output_path

# --- Main Execution ---

def main():
    """Main entry point for data cleaning pipeline."""
    logger = setup_logging()
    logger.info("Starting data cleaning pipeline...")
    
    try:
        # 1. Load Raw Data
        df = load_raw_data(logger)
        
        # 2. Validate Variables
        validate_variables(df, logger)
        
        # 3. Handle Missing Values
        df_clean = handle_missing_values(df, logger)
        
        # 4. Normalize Categorical Codes
        df_clean = normalize_categorical_codes(df_clean, logger)
        
        # 5. Power Analysis Check (Task T015)
        # Estimate number of predictors (simplified: age, education, farm_size, credit, engagement_score)
        # In a real scenario, this would be determined by the modeling plan
        num_predictors = 5 
        power_result = calculate_power_analysis(df_clean, num_predictors)
        update_modeling_log_with_power_analysis(power_result, logger)
        
        # 6. Export Cleaned Data
        export_cleaned_data(df_clean, logger)
        
        logger.info("Data cleaning pipeline completed successfully.")
        
    except CustomDataError as e:
        logger.error(f"Data processing error: {e}")
        update_log_section("data_cleaning", {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        update_log_section("data_cleaning", {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        sys.exit(1)

if __name__ == "__main__":
    main()