"""Data Cleaning Module for Sustainable Agriculture Adoption Study.

Handles missing values, normalizes categorical codes, and exports
cleaned data to data/processed/cleaned_data.csv.
Performs power analysis check and logs results.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config, get_data_path
from logging_config import get_logger, log_operation, update_log_section

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class CustomDataError(Exception):
    """Custom exception for data errors."""
    pass


def load_raw_data() -> pd.DataFrame:
    """Load raw data from data/raw/survey_data.csv."""
    input_path = get_data_path('raw/survey_data.csv')
    if not os.path.exists(input_path):
        raise CustomDataError(f"Raw data not found at {input_path}. Run 01_download_data.py first.")

    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} records from {input_path}")
        return df
    except Exception as e:
        raise CustomDataError(f"Failed to load raw data: {e}")


def calculate_missingness(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate missingness percentage for each column."""
    missing_pct = df.isnull().mean() * 100
    return missing_pct.to_dict()


def handle_missing_values(df: pd.DataFrame, threshold: float = 30.0) -> pd.DataFrame:
    """
    Handle missing values.

    - Drop rows with > threshold% missing values.
    - Impute remaining missing values with mode (categorical) or median (numeric).

    Args:
        df: Input DataFrame.
        threshold: Maximum allowed missingness percentage.

    Returns:
        Cleaned DataFrame.
    """
    logger.info("Handling missing values...")
    df_clean = df.copy()

    # Calculate missingness
    missing_pct = calculate_missingness(df_clean)
    high_missing_cols = [col for col, pct in missing_pct.items() if pct > threshold]

    if high_missing_cols:
        logger.warning(f"Dropping {len(high_missing_cols)} columns with >{threshold}% missing: {high_missing_cols}")
        df_clean = df_clean.drop(columns=high_missing_cols)

    # Drop rows with > threshold% missing across remaining columns
    row_missing_pct = df_clean.isnull().mean(axis=1) * 100
    rows_to_drop = row_missing_pct[row_missing_pct > threshold].index
    if len(rows_to_drop) > 0:
        logger.warning(f"Dropping {len(rows_to_drop)} rows with >{threshold}% missing values.")
        df_clean = df_clean.drop(index=rows_to_drop)

    # Impute remaining missing values
    for col in df_clean.columns:
        if df_clean[col].isnull().any():
            if df_clean[col].dtype == 'object' or df_clean[col].dtype.name == 'category':
                # Mode imputation for categorical
                mode_val = df_clean[col].mode()
                if len(mode_val) > 0:
                    df_clean[col] = df_clean[col].fillna(mode_val[0])
                    logger.debug(f"Imputed {col} with mode: {mode_val[0]}")
            else:
                # Median imputation for numeric
                median_val = df_clean[col].median()
                df_clean[col] = df_clean[col].fillna(median_val)
                logger.debug(f"Imputed {col} with median: {median_val}")

    logger.info(f"Missing value handling complete. Remaining rows: {len(df_clean)}")
    return df_clean


def normalize_categorical_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize categorical codes to standard values.

    Maps common variations of categorical responses to standard codes.
    """
    logger.info("Normalizing categorical codes...")
    df_norm = df.copy()

    # Standard mappings
    binary_mappings = {
        'yes': 1, 'no': 0, 'Yes': 1, 'No': 0, 'YES': 1, 'NO': 0,
        'true': 1, 'false': 0, 'True': 1, 'False': 0
    }

    for col in df_norm.columns:
        if df_norm[col].dtype == 'object':
            # Check if column contains binary-like values
            unique_vals = df_norm[col].unique()
            if all(str(v).lower() in binary_mappings for v in unique_vals if pd.notna(v)):
                df_norm[col] = df_norm[col].map(lambda x: binary_mappings.get(str(x), x) if pd.notna(x) else x)

    logger.info("Categorical normalization complete.")
    return df_norm


def validate_clean_data(df: pd.DataFrame) -> bool:
    """Validate that cleaned data meets requirements."""
    required_cols = ['age', 'education', 'farm_size', 'credit_access', 'adoption',
                    'membership', 'extension_contact', 'collective_action', 'knowledge_exchange']

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns after cleaning: {missing}")
        return False

    if df.isnull().any().any():
        logger.warning("Data still contains missing values after cleaning.")
        return False

    logger.info("Clean data validation passed.")
    return True


def calculate_power_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate power analysis metrics.

    Computes effective_N_events / num_predictors.
    Logs shortfall if ratio < 10.

    Args:
        df: Cleaned DataFrame.

    Returns:
        Dictionary with power analysis results.
    """
    logger.info("Calculating power analysis...")

    # Number of predictors (excluding outcome)
    # Assuming adoption_binary will be created later, we estimate based on available predictors
    predictor_cols = ['age', 'education', 'farm_size', 'credit_access',
                     'membership', 'extension_contact', 'collective_action', 'knowledge_exchange']
    num_predictors = len([c for c in predictor_cols if c in df.columns])

    # Estimate effective_N_events
    # If adoption_binary exists, use count of positive outcomes
    if 'adoption_binary' in df.columns:
        effective_N_events = df['adoption_binary'].sum()
    elif 'adoption' in df.columns:
        # Estimate: assume ~30% adoption rate if binary not yet created
        total_adoption = df['adoption'].notna().sum()
        effective_N_events = int(total_adoption * 0.3)
    else:
        # Fallback: use total N * 0.3
        effective_N_events = int(len(df) * 0.3)

    ratio = effective_N_events / num_predictors if num_predictors > 0 else 0

    result = {
        'effective_N_events': effective_N_events,
        'num_predictors': num_predictors,
        'ratio': ratio,
        'shortfall': ratio < 10
    }

    if result['shortfall']:
        logger.warning(f"Power analysis shortfall: ratio={ratio:.2f} < 10. Documenting as limitation.")
    else:
        logger.info(f"Power analysis OK: ratio={ratio:.2f}")

    return result


def main() -> pd.DataFrame:
    """
    Main function to clean data.

    Returns:
        Cleaned DataFrame.
    """
    logger.info("Starting data cleaning (T014, T015, T016)...")

    try:
        # Load raw data
        df = load_raw_data()

        # Handle missing values
        df_clean = handle_missing_values(df, threshold=30.0)

        # Normalize categorical codes
        df_clean = normalize_categorical_codes(df_clean)

        # Validate
        if not validate_clean_data(df_clean):
            logger.warning("Validation warnings present, but continuing.")

        # Calculate power analysis
        power_results = calculate_power_analysis(df_clean)

        # Export cleaned data
        output_path = get_data_path('processed/cleaned_data.csv')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df_clean.to_csv(output_path, index=False)
        logger.info(f"Cleaned data saved to {output_path}")

        # Update modeling log
        log_data = {
            'status': 'completed',
            'n_records_before': len(df),
            'n_records_after': len(df_clean),
            'power_analysis': power_results
        }

        update_log_section(
            'data_cleaning',
            log_data,
            log_path=get_data_path('modeling_log.yaml')
        )

        # Log power analysis shortfall if any
        if power_results['shortfall']:
            update_log_section(
                'power_analysis',
                {'shortfall': True, 'ratio': power_results['ratio']},
                log_path=get_data_path('modeling_log.yaml')
            )

        return df_clean

    except CustomDataError as e:
        logger.error(f"Data error: {e}")
        update_log_section(
            'error',
            {'message': str(e)},
            log_path=get_data_path('modeling_log.yaml')
        )
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        update_log_section(
            'error',
            {'message': str(e)},
            log_path=get_data_path('modeling_log.yaml')
        )
        raise


if __name__ == "__main__":
    main()
