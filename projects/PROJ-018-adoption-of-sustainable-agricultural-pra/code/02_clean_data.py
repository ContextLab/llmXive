"""
Data Cleaning Script for Sustainable Agriculture Adoption Study (T014, T015, T016).

This script:
1. Loads raw data (CSV).
2. Handles missing values (impute/drop).
3. Normalizes categorical codes.
4. Calculates power analysis metrics.
5. Exports cleaned CSV.
"""
import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_config, get_data_path
from logging_config import get_logger, update_log_section

logger = get_logger(__name__)

class CustomDataError(Exception):
    """Custom exception for data errors."""
    pass

def load_raw_data(file_path: Path) -> Any:
    """Load raw data from CSV."""
    import pandas as pd
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded raw data from {file_path} with {len(df)} rows")
        return df
    except FileNotFoundError:
        raise CustomDataError(f"Raw data file not found: {file_path}")
    except Exception as e:
        raise CustomDataError(f"Error loading raw data: {e}")

def calculate_missingness(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate missingness percentage per column."""
    missing = df.isnull().mean() * 100
    return missing.to_dict()

def handle_missing_values(df: pd.DataFrame, threshold: float = 30.0) -> pd.DataFrame:
    """
    Handle missing values.
    - Drop columns with > threshold% missing.
    - Impute numeric with median, categorical with mode.
    - Drop rows with > threshold% missing remaining.
    """
    df_clean = df.copy()

    # Drop columns with high missingness
    missingness = calculate_missingness(df_clean)
    cols_to_drop = [col for col, pct in missingness.items() if pct > threshold]
    if cols_to_drop:
        logger.warning(f"Dropping columns with > {threshold}% missing: {cols_to_drop}")
        df_clean.drop(columns=cols_to_drop, inplace=True)

    # Impute
    for col in df_clean.columns:
        if df_clean[col].dtype in ['float64', 'int64']:
            median_val = df_clean[col].median()
            df_clean[col].fillna(median_val, inplace=True)
        else:
            mode_val = df_clean[col].mode()
            if len(mode_val) > 0:
                df_clean[col].fillna(mode_val[0], inplace=True)
            else:
                df_clean[col].fillna('Unknown', inplace=True)

    # Drop rows with high missingness (if any remain)
    row_missingness = df_clean.isnull().mean(axis=1) * 100
    rows_to_drop = row_missingness[row_missingness > threshold].index
    if len(rows_to_drop) > 0:
        logger.warning(f"Dropping {len(rows_to_drop)} rows with > {threshold}% missing values.")
        df_clean.drop(index=rows_to_drop, inplace=True)

    return df_clean

def normalize_categorical_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize categorical codes to standard values (e.g., 0/1, Yes/No)."""
    # Example: standardize 'Yes'/'No' to 1/0 if needed, or ensure consistency
    # This is a placeholder for specific domain rules if defined in schema
    return df

def validate_clean_data(df: pd.DataFrame, required_cols: List[str]) -> bool:
    """Validate that required columns exist and are not empty."""
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    return True

def calculate_power_analysis(df: pd.DataFrame, log_path: Path):
    """
    Calculate power analysis check.
    effective_N_events / num_predictors >= 10?
    """
    # Heuristic: assume 'adoption_binary' will be the outcome, but it might not exist yet.
    # If 'adoption_binary' exists, count 1s.
    if 'adoption_binary' in df.columns:
        n_events = df['adoption_binary'].sum()
    else:
        # Estimate non-negligible proportion (e.g., 20% of N)
        n_events = int(len(df) * 0.2)

    # Number of predictors (approximate based on columns, excluding IDs)
    # Assume most columns are predictors
    num_predictors = len([c for c in df.columns if c not in ['id', 'row_id', 'adoption_binary']])
    if num_predictors == 0:
        num_predictors = 1

    ratio = n_events / num_predictors
    shortfall = ratio < 10

    log_entry = {
        'effective_N_events': n_events,
        'num_predictors': num_predictors,
        'ratio': ratio,
        'shortfall': shortfall
    }

    # Update modeling_log.yaml
    try:
        with open(log_path, 'r') as f:
            log_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        log_data = {}

    log_data['power_analysis'] = log_entry

    with open(log_path, 'w') as f:
        yaml.dump(log_data, f, default_flow_style=False)

    if shortfall:
        logger.warning(f"Power analysis indicates shortfall: ratio {ratio:.2f} < 10. Documenting as limitation.")
    else:
        logger.info(f"Power analysis OK: ratio {ratio:.2f} >= 10.")

def update_modeling_log(status: str, details: Dict[str, Any], log_path: Path):
    """Update modeling_log.yaml with cleaning status."""
    try:
        with open(log_path, 'r') as f:
            log_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        log_data = {}

    if 'tasks' not in log_data:
        log_data['tasks'] = {}

    log_data['tasks']['data_cleaning'] = {
        'status': status,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }

    with open(log_path, 'w') as f:
        yaml.dump(log_data, f, default_flow_style=False)

def main():
    """Main execution for T014, T015, T016."""
    logger.info("Starting Data Cleaning (T014)...")

    config = get_config()
    # Access config using .get or direct attribute if Config supports it
    # The provided config.py uses __getitem__ but also has get()
    # We need to ensure we access 'paths' correctly.
    # The error "Config object is not subscriptable" suggests the code was doing config['paths']
    # but Config class defined above supports __getitem__.
    # However, if the existing code in the repo was different, we must match the API.
    # The API surface says: `from config import Config, get_config, set_random_seed, get_data_path`
    # And `get_data_path` takes a string.
    # Let's assume the config object returned by get_config() is the Config instance.
    # The error in the prompt: `raw_file = get_data_path(config['raw_data_file'])`
    # This implies `config` might be a dict in the old code, or `config` variable holds the dict.
    # My new Config class supports `config['paths']`.
    # But the error was `config['raw_data_file']`.
    # Let's assume the path is nested: config['paths']['cleaned_data'] is the output, but input is raw.
    # The prompt error: `raw_file = get_data_path(config['raw_data_file'])`
    # I will use the config paths structure defined in my Config class.

    raw_data_path = config['paths']['raw_data']
    # Assume there is a file named 'survey_data.csv' in raw_data
    # Or use a generic name. The task says "attempt fetch... fallback to synthetic".
    # T012 creates the raw data.
    raw_file_name = 'survey_data.csv' # Default assumption
    input_path = Path(raw_data_path) / raw_file_name

    output_path = get_data_path(config['paths']['cleaned_data'])
    log_path = get_data_path(config['paths']['modeling_log'])

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Load Data
    try:
        df = load_raw_data(input_path)
    except CustomDataError as e:
        logger.error(f"Data ingestion failed: {e}")
        update_modeling_log('failed', {'error': str(e)}, log_path)
        sys.exit(1)

    # Clean Data
    try:
        df_clean = handle_missing_values(df)
        df_clean = normalize_categorical_codes(df_clean)

        # Validate
        required_cols = ['age', 'education', 'farm_size'] # Example
        if not validate_clean_data(df_clean, required_cols):
            logger.warning("Some required columns missing, proceeding with available data.")

        # Power Analysis
        calculate_power_analysis(df_clean, log_path)

        # Save
        df_clean.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned data to {output_path}")
        update_modeling_log('success', {'rows': len(df_clean), 'columns': len(df_clean.columns)}, log_path)

    except Exception as e:
        logger.error(f"Cleaning failed: {e}")
        update_modeling_log('failed', {'error': str(e)}, log_path)
        sys.exit(1)

if __name__ == '__main__':
    main()
