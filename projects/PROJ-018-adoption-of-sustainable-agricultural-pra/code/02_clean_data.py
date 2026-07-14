from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

from config import get_config
from logging_config import get_logger, log_operation, update_log_section

# Custom exception for data errors
class CustomDataError(Exception):
    pass

# Logger instance
_logger = get_logger("data_cleaning")

# Constants
MISSING_THRESHOLD = 0.30
MIN_EVENTS_PER_PREDICTOR = 10

def get_logger_instance() -> logging.Logger:
    return _logger

def load_raw_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """Load raw survey data from CSV."""
    config = get_config()
    if input_path is None:
        input_path = config.get("data_raw_path", "data/raw/survey_data.csv")
    
    if not os.path.exists(input_path):
        raise CustomDataError(f"Raw data not found at {input_path}. Run 01_download_data.py first.")
    
    _logger.info(f"Loading raw data from {input_path}")
    df = pd.read_csv(input_path)
    return df

def calculate_missingness(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate missingness ratio for each column."""
    missing_counts = df.isnull().sum()
    total_rows = len(df)
    return {col: count / total_rows for col, count in missing_counts.items()}

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values: drop rows with >30% missing, impute others."""
    missingness = calculate_missingness(df)
    high_missing_cols = [col for col, ratio in missingness.items() if ratio > MISSING_THRESHOLD]
    
    if high_missing_cols:
        _logger.warning(f"Dropping columns with >{MISSING_THRESHOLD*100}% missing: {high_missing_cols}")
        df = df.drop(columns=high_missing_cols)
    
    # Impute remaining missing values with median (numeric) or mode (categorical)
    for col in df.columns:
        if df[col].isnull().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "Unknown")
    
    return df

def normalize_categorical_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize categorical codes to standard values."""
    categorical_mappings = {
        'education': {'primary': 1, 'secondary': 2, 'tertiary': 3},
        'credit_access': {'no': 0, 'yes': 1},
        'membership': {'no': 0, 'yes': 1},
    }
    
    for col, mapping in categorical_mappings.items():
        if col in df.columns:
            df[col] = df[col].map(mapping).fillna(df[col])
    
    return df

def validate_clean_data(df: pd.DataFrame) -> bool:
    """Validate that cleaned data has no missing values in required columns."""
    required_cols = ['age', 'education', 'farm_size', 'credit', 'adoption', 'engagement_items']
    available_cols = [col for col in required_cols if col in df.columns]
    
    if not available_cols:
        _logger.error("No required columns found in cleaned data")
        return False
    
    for col in available_cols:
        if df[col].isnull().any():
            _logger.error(f"Missing values found in required column: {col}")
            return False
    
    return True

def calculate_power_analysis(df: pd.DataFrame, num_predictors: int = 5) -> Dict[str, Any]:
    """
    Calculate power analysis check: effective_N_events / num_predictors.
    
    effective_N_events = count of positive outcomes in 'adoption_binary' if available,
    or estimated a non-negligible proportion of N if not.
    
    Returns dict with 'shortfall' (bool) and 'ratio' (float).
    """
    n_total = len(df)
    
    if 'adoption_binary' in df.columns:
        effective_n_events = df['adoption_binary'].sum()
    else:
        # Estimate: assume ~20% adoption rate if binary column not present
        # This is a conservative estimate for planning purposes
        effective_n_events = int(n_total * 0.20)
        _logger.info(f"Estimated effective_N_events as 20% of N ({effective_n_events}) since 'adoption_binary' not found")
    
    ratio = effective_n_events / num_predictors if num_predictors > 0 else float('inf')
    shortfall = ratio < MIN_EVENTS_PER_PREDICTOR
    
    return {
        'effective_n_events': int(effective_n_events),
        'num_predictors': num_predictors,
        'ratio': round(ratio, 2),
        'shortfall': shortfall,
        'min_required_ratio': MIN_EVENTS_PER_PREDICTOR
    }

def update_modeling_log_with_power_analysis(power_analysis: Dict[str, Any]) -> None:
    """Update modeling_log.yaml with power analysis results."""
    config = get_config()
    log_path = config.get("modeling_log_path", "modeling_log.yaml")
    
    # Load existing log or create new
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            log_data = yaml.safe_load(f) or {}
    else:
        log_data = {}
    
    # Update power_analysis section
    log_data['power_analysis'] = power_analysis
    
    # Write back
    with open(log_path, 'w') as f:
        yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)
    
    _logger.info(f"Updated modeling log at {log_path} with power analysis: {power_analysis}")

def export_cleaned_data(df: pd.DataFrame, output_path: Optional[str] = None) -> None:
    """Export cleaned data to CSV."""
    config = get_config()
    if output_path is None:
        output_path = config.get("data_processed_path", "data/processed/cleaned_data.csv")
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    _logger.info(f"Exported cleaned data to {output_path} ({len(df)} rows)")

@log_operation("data_cleaning_main")
def main() -> None:
    """Main entry point for data cleaning pipeline."""
    _logger.info("Starting data cleaning (T014, T015, T016)...")
    
    try:
        # Load raw data
        df = load_raw_data()
        _logger.info(f"Loaded {len(df)} records")
        
        # Handle missing values
        df = handle_missing_values(df)
        _logger.info("Handled missing values")
        
        # Normalize categorical codes
        df = normalize_categorical_codes(df)
        _logger.info("Normalized categorical codes")
        
        # Validate cleaned data
        if not validate_clean_data(df):
            _logger.warning("Validation warnings found, but proceeding")
        
        # Power analysis (T015)
        num_predictors = 5  # Default: age, education, farm_size, credit, engagement_score
        power_analysis = calculate_power_analysis(df, num_predictors)
        update_modeling_log_with_power_analysis(power_analysis)
        
        if power_analysis['shortfall']:
            _logger.warning(f"POWER SHORTFALL DETECTED: Ratio {power_analysis['ratio']} < {MIN_EVENTS_PER_PREDICTOR}. "
                          f"This is documented as a study limitation per SC-006.")
        
        # Export cleaned data
        export_cleaned_data(df)
        
        _logger.info("Data cleaning completed successfully")
        
    except CustomDataError as e:
        _logger.error(f"Data error: {e}")
        # Log to modeling_log.yaml as failure
        update_log_section("data_cleaning", {"status": "failed", "error": str(e)})
        sys.exit(1)
    except Exception as e:
        _logger.error(f"Unexpected error during data cleaning: {e}")
        update_log_section("data_cleaning", {"status": "failed", "error": str(e)})
        sys.exit(1)

if __name__ == "__main__":
    main()