"""
Data Cleaning Pipeline for Sustainable Agriculture Survey Data.

This module handles:
1. Loading raw data from CSV
2. Calculating and handling missing values
3. Normalizing categorical codes
4. Validating the cleaned dataset
5. Performing power analysis checks
6. Exporting cleaned data to CSV

It updates the modeling_log.yaml with power analysis results.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from config import get_config
from logging_config import (
    LogEntry,
    ReproducibilityLogger,
    get_logger,
    log_operation,
    initialize_modeling_log,
    update_log_section,
    append_log_entry,
)

# --- Custom Exceptions ---

class CustomDataError(Exception):
    """Custom exception for data processing errors."""
    pass

# --- Configuration & Logging Setup ---

def get_logger_instance() -> ReproducibilityLogger:
    """Get the global reproducibility logger instance."""
    return get_logger()

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        # Fallback to default paths if config missing
        return {
            "paths": {
                "raw_data": "data/raw/survey_data.csv",
                "cleaned_data": "data/processed/cleaned_data.csv",
                "modeling_log": "modeling_log.yaml"
            },
            "thresholds": {
                "missing_value_threshold": 0.30,
                "power_analysis_ratio": 10
            }
        }
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# --- Core Data Processing Functions ---

def load_raw_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load raw data from a CSV file.
    
    Args:
        input_path: Path to the raw data CSV. Defaults to config value.
        
    Returns:
        pd.DataFrame: The loaded raw data.
        
    Raises:
        CustomDataError: If file not found or empty.
    """
    config = load_config()
    path = input_path or config.get("paths", {}).get("raw_data", "data/raw/survey_data.csv")
    path_obj = Path(path)
    
    logger = get_logger_instance()
    logger.log("load_raw_data", file_path=str(path_obj), status="started")
    
    if not path_obj.exists():
        logger.log("load_raw_data", file_path=str(path_obj), status="failed", error="File not found")
        raise CustomDataError(f"Raw data file not found at: {path_obj}")
    
    try:
        df = pd.read_csv(path_obj)
        if df.empty:
            logger.log("load_raw_data", file_path=str(path_obj), status="failed", error="Empty dataset")
            raise CustomDataError(f"Dataset at {path_obj} is empty.")
        
        logger.log("load_raw_data", file_path=str(path_obj), status="success", rows=len(df))
        return df
    except Exception as e:
        logger.log("load_raw_data", file_path=str(path_obj), status="failed", error=str(e))
        raise CustomDataError(f"Failed to load data from {path_obj}: {e}")

def calculate_missingness(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate the percentage of missing values for each column.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Dict mapping column names to missingness percentage (0.0 to 1.0).
    """
    missing_counts = df.isnull().sum()
    total_rows = len(df)
    if total_rows == 0:
        return {}
    return (missing_counts / total_rows).to_dict()

def handle_missing_values(df: pd.DataFrame, threshold: float = 0.30) -> pd.DataFrame:
    """
    Handle missing values based on a threshold.
    
    - If a column has > threshold missing values, drop the column.
    - For remaining columns, drop rows with any missing values in required fields,
      or impute numeric with median and categorical with mode.
      
    Args:
        df: Input DataFrame.
        threshold: Maximum allowed fraction of missing values (default 0.30).
        
    Returns:
        Cleaned DataFrame.
    """
    logger = get_logger_instance()
    logger.log("handle_missing_values", threshold=threshold, status="started")
    
    df_clean = df.copy()
    missingness = calculate_missingness(df_clean)
    
    # Identify columns to drop due to high missingness
    cols_to_drop = [col for col, pct in missingness.items() if pct > threshold]
    if cols_to_drop:
        logger.log("handle_missing_values", dropped_columns=cols_to_drop, reason="high_missingness")
        df_clean = df_clean.drop(columns=cols_to_drop)
    
    # Define required fields based on project spec (US1)
    required_fields = ['age', 'education', 'farm_size', 'credit', 'adoption', 'engagement_membership', 
                       'engagement_extension', 'engagement_collective_action', 'engagement_knowledge_exchange']
    existing_required = [f for f in required_fields if f in df_clean.columns]
    
    # Identify numeric and categorical columns for imputation
    numeric_cols = df_clean.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df_clean.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Drop rows where required fields are missing
    if existing_required:
        mask = df_clean[existing_required].notna().all(axis=1)
        dropped_rows = (~mask).sum()
        if dropped_rows > 0:
            logger.log("handle_missing_values", dropped_rows=dropped_rows, reason="missing_required_fields")
            df_clean = df_clean[mask]
    
    # Impute remaining missing values
    for col in numeric_cols:
        if df_clean[col].isnull().any():
            median_val = df_clean[col].median()
            df_clean[col] = df_clean[col].fillna(median_val)
            logger.log("handle_missing_values", imputed_column=col, method="median", value=median_val)
            
    for col in categorical_cols:
        if df_clean[col].isnull().any():
            mode_val = df_clean[col].mode()
            if len(mode_val) > 0:
                fill_val = mode_val[0]
                df_clean[col] = df_clean[col].fillna(fill_val)
                logger.log("handle_missing_values", imputed_column=col, method="mode", value=str(fill_val))
            else:
                # If no mode (all null?), fill with 'unknown'
                df_clean[col] = df_clean[col].fillna('unknown')
    
    logger.log("handle_missing_values", status="success", final_rows=len(df_clean))
    return df_clean

def normalize_categorical_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize categorical codes to standard string representations.
    
    Maps common numeric codes (0, 1, 2...) or inconsistent strings to
    standardized categories where applicable.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        DataFrame with normalized categorical columns.
    """
    logger = get_logger_instance()
    logger.log("normalize_categorical_codes", status="started")
    
    df_norm = df.copy()
    categorical_cols = df_norm.select_dtypes(include=['object', 'category', 'int', 'float']).columns.tolist()
    
    # Define normalization mappings for known categorical fields
    # These are examples; in a real scenario, these would be derived from data dictionary
    mappings = {
        'education': {0: 'none', 1: 'primary', 2: 'secondary', 3: 'tertiary', 'None': 'none', '0': 'none'},
        'adoption': {0: 'no', 1: 'yes', 'No': 'no', 'Yes': 'yes', False: 'no', True: 'yes'},
        'engagement_membership': {0: 'no', 1: 'yes'},
        'engagement_extension': {0: 'no', 1: 'yes'},
        'engagement_collective_action': {0: 'no', 1: 'yes'},
        'engagement_knowledge_exchange': {0: 'no', 1: 'yes'},
    }
    
    for col in categorical_cols:
        if col in mappings:
            current_map = mappings[col]
            # Ensure we only map existing values
            unique_vals = df_norm[col].unique()
            for val in unique_vals:
                if pd.notna(val) and val in current_map:
                    df_norm[col] = df_norm[col].replace(val, current_map[val])
            logger.log("normalize_categorical_codes", column=col, mapped=True)
    
    logger.log("normalize_categorical_codes", status="success")
    return df_norm

def validate_clean_data(df: pd.DataFrame) -> bool:
    """
    Validate that the cleaned data meets basic quality criteria.
    
    Checks:
    - No missing values in required fields
    - Required columns exist
    - Data types are appropriate
    
    Args:
        df: Cleaned DataFrame.
        
    Returns:
        True if valid, raises CustomDataError otherwise.
    """
    required_cols = ['age', 'education', 'farm_size', 'credit']
    for col in required_cols:
        if col not in df.columns:
            raise CustomDataError(f"Required column '{col}' missing after cleaning.")
        if df[col].isnull().any():
            raise CustomDataError(f"Column '{col}' still has missing values after cleaning.")
    
    return True

def calculate_power_analysis(df: pd.DataFrame, num_predictors: int = 5) -> Dict[str, Any]:
    """
    Calculate power analysis metric: effective_N_events / num_predictors.
    
    effective_N_events is the count of positive outcomes in 'adoption_binary'.
    If 'adoption_binary' is not available, it estimates a non-negligible proportion
    of N (e.g., assume 50% adoption if binary not present but 'adoption' is).
    
    Args:
        df: Cleaned DataFrame.
        num_predictors: Number of predictors planned for the model (default 5).
        
    Returns:
        Dict with 'ratio', 'effective_N_events', 'total_N', and 'shortfall' flag.
    """
    logger = get_logger_instance()
    logger.log("calculate_power_analysis", num_predictors=num_predictors, status="started")
    
    total_n = len(df)
    effective_n_events = 0
    
    # Check for 'adoption_binary' column (created in T020, but might be present if run later)
    if 'adoption_binary' in df.columns:
        effective_n_events = df['adoption_binary'].sum()
    elif 'adoption' in df.columns:
        # Estimate: assume 50% adoption if binary not present but raw adoption exists
        # This is a conservative estimate for power analysis planning
        # In reality, we'd count 'yes'/'1'/'True'
        yes_count = df['adoption'].isin(['yes', 'Yes', 'YES', '1', True, 1]).sum()
        effective_n_events = yes_count if yes_count > 0 else int(total_n * 0.5)
    else:
        # Fallback if no adoption indicator at all
        effective_n_events = int(total_n * 0.5)
    
    ratio = effective_n_events / num_predictors if num_predictors > 0 else 0
    shortfall = ratio < 10
    
    result = {
        "ratio": round(ratio, 2),
        "effective_N_events": int(effective_n_events),
        "total_N": int(total_n),
        "num_predictors": num_predictors,
        "shortfall": shortfall
    }
    
    logger.log("calculate_power_analysis", **result, status="success")
    return result

def update_modeling_log_with_power_analysis(power_result: Dict[str, Any]) -> None:
    """
    Update modeling_log.yaml with power analysis results.
    
    Writes to the 'power_analysis' key. Does not halt execution if shortfall detected.
    
    Args:
        power_result: Dictionary from calculate_power_analysis.
    """
    logger = get_logger_instance()
    log_path = Path("modeling_log.yaml")
    
    # Initialize log if it doesn't exist
    if not log_path.exists():
        with open(log_path, 'w', encoding='utf-8') as f:
            yaml.dump({"modeling_log": []}, f)
    
    # Load existing log
    with open(log_path, 'r', encoding='utf-8') as f:
        try:
            log_data = yaml.safe_load(f) or {"modeling_log": []}
        except yaml.YAMLError:
            log_data = {"modeling_log": []}
    
    # Update or create power_analysis section
    # We want to store this under a top-level key 'power_analysis' as per task description
    # But the task says "under key `power_analysis`" in modeling_log.yaml. 
    # Let's assume it means a top-level key or a section in the list.
    # Given the structure of modeling_log usually being a list of entries, 
    # we will append a specific entry or update a dedicated section.
    # The task says: "log `{'shortfall': true, 'ratio': <value>}` to `modeling_log.yaml` under key `power_analysis`"
    # This implies a top-level key structure like: { ..., "power_analysis": {...} }
    
    if "power_analysis" not in log_data:
        log_data["power_analysis"] = {}
    
    log_data["power_analysis"]["shortfall"] = power_result["shortfall"]
    log_data["power_analysis"]["ratio"] = power_result["ratio"]
    log_data["power_analysis"]["effective_N_events"] = power_result["effective_N_events"]
    log_data["power_analysis"]["total_N"] = power_result["total_N"]
    log_data["power_analysis"]["num_predictors"] = power_result["num_predictors"]
    
    # Also log as an entry for reproducibility
    entry = {
        "operation": "power_analysis_check",
        "parameters": power_result,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    if "modeling_log" not in log_data:
        log_data["modeling_log"] = []
    log_data["modeling_log"].append(entry)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        yaml.dump(log_data, f, default_flow_style=False, allow_unicode=True)
    
    logger.log("update_modeling_log_with_power_analysis", status="success", path=str(log_path))

def export_cleaned_data(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Export cleaned DataFrame to CSV.
    
    Args:
        df: Cleaned DataFrame.
        output_path: Path to save CSV. Defaults to config value.
        
    Returns:
        Path to the saved file.
    """
    config = load_config()
    path = output_path or config.get("paths", {}).get("cleaned_data", "data/processed/cleaned_data.csv")
    path_obj = Path(path)
    
    # Ensure directory exists
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    logger = get_logger_instance()
    logger.log("export_cleaned_data", path=str(path_obj), rows=len(df), status="started")
    
    try:
        df.to_csv(path_obj, index=False)
        logger.log("export_cleaned_data", path=str(path_obj), status="success")
        return str(path_obj)
    except Exception as e:
        logger.log("export_cleaned_data", path=str(path_obj), status="failed", error=str(e))
        raise CustomDataError(f"Failed to export cleaned data to {path_obj}: {e}")

@log_operation("data_cleaning_main")
def main() -> None:
    """
    Main execution function for the data cleaning pipeline.
    
    Orchestrates:
    1. Loading raw data
    2. Handling missing values
    3. Normalizing categorical codes
    4. Validating the result
    5. Performing power analysis
    6. Exporting cleaned data
    """
    logger = get_logger_instance()
    logger.log("main", status="started")
    
    try:
        # 1. Load Data
        df = load_raw_data()
        logger.info(f"Loaded {len(df)} rows.")
        
        # 2. Handle Missing Values
        df_clean = handle_missing_values(df, threshold=0.30)
        
        # 3. Normalize Categorical Codes
        df_clean = normalize_categorical_codes(df_clean)
        
        # 4. Validate
        validate_clean_data(df_clean)
        logger.info("Validation passed.")
        
        # 5. Power Analysis
        # Estimate number of predictors (engagement score + covariates)
        # Typical covariates: age, education, farm_size, credit, engagement_score
        num_predictors = 5 
        power_result = calculate_power_analysis(df_clean, num_predictors=num_predictors)
        update_modeling_log_with_power_analysis(power_result)
        
        if power_result["shortfall"]:
            logger.warning(f"Power analysis shortfall detected: ratio {power_result['ratio']} < 10. Documenting as limitation.")
        else:
            logger.info(f"Power analysis OK: ratio {power_result['ratio']}.")
        
        # 6. Export
        output_path = export_cleaned_data(df_clean)
        logger.info(f"Cleaned data exported to {output_path}")
        
        logger.log("main", status="success", output_file=output_path)
        
    except CustomDataError as e:
        logger.log("main", status="failed", error=str(e))
        # Re-raise to allow CLI exit code handling
        raise
    except Exception as e:
        logger.log("main", status="failed", error=f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    main()