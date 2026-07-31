"""
Data cleaning and transformation pipeline for aluminum alloy data.

Implements:
- Schema validation
- Independence filtering (measurement method)
- Monolithic filtering
- Unit normalization
- Major element filtering
- ILR transformation (T019)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import numpy as np
import pandas as pd
from compositional import ilr, clr, ilr_inv

from config import get_config
from logging_config import setup_logging, get_logger
from schemas.alloy_record import AlloyRecord

logger = get_logger(__name__)


def load_raw_data(raw_data_path: Path) -> pd.DataFrame:
    """Load raw data from JSON file."""
    logger.info(f"Loading raw data from {raw_data_path}")
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")

    with open(raw_data_path, 'r') as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    logger.info(f"Loaded {len(df)} records")
    return df


def apply_schema_validation(df: pd.DataFrame) -> pd.DataFrame:
    """Validate records against AlloyRecord schema."""
    logger.info("Applying schema validation")
    valid_records = []
    excluded_count = 0

    for idx, row in df.iterrows():
        try:
            # Convert row to dict and validate
            record_dict = row.to_dict()
            # Ensure measurement_method is present and non-null (T007 requirement)
            if record_dict.get('measurement_method') is None:
                excluded_count += 1
                continue

            # Validate numeric fields
            required_fields = ['poisson_ratio', 'young_modulus', 'cu_frac', 'mg_frac',
                               'si_frac', 'zn_frac', 'mn_frac']
            missing = [f for f in required_fields if record_dict.get(f) is None]
            if missing:
                excluded_count += 1
                continue

            valid_records.append(record_dict)
        except Exception as e:
            logger.warning(f"Record {idx} failed validation: {e}")
            excluded_count += 1

    logger.info(f"Schema validation: {len(valid_records)} valid, {excluded_count} excluded")
    return pd.DataFrame(valid_records)


def apply_independence_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out records with derived measurement methods (T014)."""
    logger.info("Applying independence filter (T014)")

    # Log directory setup
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    independence_log = log_dir / "independence_check.log"
    metrics_file = log_dir / "independence_metrics.json"

    kept_records = []
    excluded_derived = 0
    kept_count = 0

    # Configure file logger for independence check
    file_handler = logging.FileHandler(independence_log)
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    independence_logger = logging.getLogger('independence_check')
    independence_logger.addHandler(file_handler)
    independence_logger.setLevel(logging.WARNING)

    for idx, row in df.iterrows():
        method = row.get('measurement_method', '')
        method_lower = str(method).lower()

        # Exclude derived methods
        if method_lower in ['derived', 'calculated_from_youngs_modulus', 'calculated']:
            excluded_derived += 1
            independence_logger.warning(f"Record {idx}: Derived measurement_method '{method}', excluding record")
            continue

        # Keep valid methods
        if method_lower in ['ultrasonic', 'independent', 'direct measurement']:
            kept_count += 1
            kept_records.append(row.to_dict())
        else:
            # Unknown method - exclude for safety
            excluded_derived += 1
            independence_logger.warning(f"Record {idx}: Unknown measurement_method '{method}', excluding record")

    # Save metrics
    metrics = {
        "kept": kept_count,
        "excluded_derived": excluded_derived
    }
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Independence filter: {kept_count} kept, {excluded_derived} excluded (derived/unknown)")
    return pd.DataFrame(kept_records)


def apply_monolithic_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Filter for monolithic alloys with non-missing key properties (T011)."""
    logger.info("Applying monolithic filter (T011)")

    required_cols = ['poisson_ratio', 'young_modulus', 'cu_frac', 'mg_frac', 'si_frac', 'zn_frac', 'mn_frac']

    # Check for missing values in required columns
    mask = df[required_cols].notna().all(axis=1)
    filtered_df = df[mask].copy()

    logger.info(f"Monolithic filter: {len(filtered_df)} records remaining (from {len(df)})")
    return filtered_df


def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize units: convert elastic constants to GPa, ensure atomic fractions sum to 1 (T012)."""
    logger.info("Normalizing units (T012)")

    df = df.copy()

    # Convert Young's modulus to GPa if needed (assume input is in GPa or Pa)
    # If values are > 1000, assume Pa and convert to GPa
    if df['young_modulus'].mean() > 1000:
        df['young_modulus'] = df['young_modulus'] / 1000.0
        logger.info("Converted Young's modulus from Pa to GPa")

    # Normalize atomic fractions to sum to 1
    composition_cols = ['cu_frac', 'mg_frac', 'si_frac', 'zn_frac', 'mn_frac']
    df['sum_composition'] = df[composition_cols].sum(axis=1)

    # Avoid division by zero
    df['sum_composition'] = df['sum_composition'].replace(0, 1)

    for col in composition_cols:
        df[col] = df[col] / df['sum_composition']

    # Drop temporary column
    df.drop(columns=['sum_composition'], inplace=True)

    logger.info(f"Normalized units: {len(df)} records")
    return df


def apply_major_element_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Exclude entries where major element sum < 0.95 (T013)."""
    logger.info("Applying major element filter (T013)")

    composition_cols = ['cu_frac', 'mg_frac', 'si_frac', 'zn_frac', 'mn_frac']
    df['sum_major'] = df[composition_cols].sum(axis=1)

    # Filter: sum >= 0.95
    mask = df['sum_major'] >= 0.95
    filtered_df = df[mask].copy()

    excluded_count = len(df) - len(filtered_df)
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} records with major element sum < 0.95")

    # Drop temporary column
    filtered_df.drop(columns=['sum_major'], inplace=True)

    logger.info(f"Major element filter: {len(filtered_df)} records remaining")
    return filtered_df


def apply_ilr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply ILR transformation to compositional data (T019).
    Uses the compositional package's ilr function for Cu, Mg, Si, Zn, Mn atomic fractions.
    Output: data/processed/filtered_alloys_ilr.csv
    """
    logger.info("Applying ILR transformation (T019)")

    config = get_config()
    processed_dir = Path(config.data_processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    composition_cols = ['cu_frac', 'mg_frac', 'si_frac', 'zn_frac', 'mn_frac']

    # Ensure we have positive values for ILR (compositional data must be > 0)
    # Add small epsilon to avoid log(0)
    epsilon = 1e-10
    df_clean = df.copy()
    for col in composition_cols:
        df_clean[col] = df_clean[col].clip(lower=epsilon)

    # Normalize again after clipping to ensure sum = 1
    df_clean['sum_comp'] = df_clean[composition_cols].sum(axis=1)
    df_clean['sum_comp'] = df_clean['sum_comp'].replace(0, 1)
    for col in composition_cols:
        df_clean[col] = df_clean[col] / df_clean['sum_comp']
    df_clean.drop(columns=['sum_comp'], inplace=True)

    # Convert to numpy array for compositional transformation
    comp_data = df_clean[composition_cols].values

    # Apply ILR transformation
    try:
        ilr_data = ilr(comp_data)
    except Exception as e:
        logger.error(f"ILR transformation failed: {e}")
        raise RuntimeError(f"ILR transformation failed: {e}")

    # Create new dataframe with ILR-transformed features
    ilr_col_names = [f'ilr_{col}' for col in composition_cols]
    ilr_df = pd.DataFrame(ilr_data, columns=ilr_col_names, index=df_clean.index)

    # Merge with original data (excluding composition columns)
    non_comp_cols = [col for col in df_clean.columns if col not in composition_cols]
    result_df = pd.concat([df_clean[non_comp_cols], ilr_df], axis=1)

    # Save output
    output_path = processed_dir / "filtered_alloys_ilr.csv"
    result_df.to_csv(output_path, index=False)
    logger.info(f"ILR transformation complete. Saved to {output_path}")
    logger.info(f"Output shape: {result_df.shape}")

    return result_df


def run_cleaning_pipeline() -> pd.DataFrame:
    """Run the full cleaning pipeline."""
    config = get_config()
    raw_data_path = Path(config.data_raw_dir) / "openml_aluminum.json"

    # Load data
    df = load_raw_data(raw_data_path)

    # Apply filters in order
    df = apply_schema_validation(df)
    df = apply_independence_filter(df)
    df = apply_monolithic_filter(df)
    df = normalize_units(df)
    df = apply_major_element_filter(df)

    # Apply ILR transformation (T019)
    df_ilr = apply_ilr_transformation(df)

    # Also save the cleaned (pre-ILR) data for downstream tasks
    processed_dir = Path(config.data_processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = processed_dir / "filtered_alloys.csv"
    df.to_csv(cleaned_path, index=False)
    logger.info(f"Cleaned data saved to {cleaned_path}")

    return df_ilr


def main():
    """Main entry point for data cleaning."""
    setup_logging()
    logger.info("Starting data cleaning pipeline")

    try:
        result_df = run_cleaning_pipeline()
        logger.info(f"Pipeline complete. Final shape: {result_df.shape}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()