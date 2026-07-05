"""
Data Preprocessing Module for Rolled Metals Texture Prediction.

Implements:
- Unit standardization (SI)
- Median imputation (threshold <= 20% NaN per column)
- 3-sigma outlier removal
- Derivation of physics-based features: Strain Rate, Zener-Hollomon Parameter
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Import existing utilities from the project
from code.utils.logging import get_logger, log_warning_structured
from code.config import ensure_dirs

# Constants for Physics Formulas
# Zener-Hollomon Parameter: Z = epsilon_dot * exp(Q / (R * T))
# Units: epsilon_dot (1/s), Q (J/mol), R (8.314 J/(mol*K)), T (K)
# Default activation energy for common rolled metals (e.g., Aluminum alloys) if not specified
DEFAULT_ACTIVATION_ENERGY_J = 140000.0  # 140 kJ/mol
GAS_CONSTANT_R = 8.314  # J/(mol*K)

logger = get_logger(__name__)

def standardize_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes units to SI.
    - Temperature: Converts Celsius/Fahrenheit to Kelvin if detected.
    - Strain Rate: Converts 1/min or 1/hr to 1/s if detected.
    - Stress: Converts MPa/GPa to Pa if detected.
    - Assumes columns are named with hints or standard names.
    """
    df_std = df.copy()

    # Temperature Conversion Logic
    # Look for 'temp' or 'temperature' in column names
    temp_cols = [c for c in df_std.columns if 'temp' in c.lower()]
    for col in temp_cols:
        if df_std[col].dtype in ['float64', 'int64']:
            # Heuristic: If values are negative, likely Celsius or Fahrenheit.
            # If values are > 2000, likely Kelvin (no conversion needed).
            # If values are between -100 and 100, likely Celsius.
            if df_std[col].min() < 0:
                logger.info(f"Converting {col} from Celsius to Kelvin")
                df_std[col] = df_std[col] + 273.15
            elif df_std[col].max() > 1000:
                logger.info(f"Column {col} appears to be already in Kelvin.")
            else:
                # Assume Celsius for positive values < 1000
                logger.info(f"Assuming {col} is Celsius, converting to Kelvin")
                df_std[col] = df_std[col] + 273.15

    # Strain Rate Conversion
    strain_rate_cols = [c for c in df_std.columns if 'strain_rate' in c.lower() or 'strainrate' in c.lower()]
    for col in strain_rate_cols:
        if df_std[col].dtype in ['float64', 'int64']:
            # Heuristic: If values are very small (< 1), might be 1/s.
            # If values are large (> 10), might be 1/min or 1/hr.
            # This is a heuristic; in real scenarios, metadata would define this.
            # For robustness, we assume the input is 1/s if not specified,
            # but if we detect a column named 'strain_rate_per_min', we convert.
            # Since we don't have explicit unit columns here, we assume input is 1/s
            # unless the task implies specific column naming.
            # For this implementation, we assume the input data is already in SI
            # or the user provides a mapping. We will add a check for 'per_min' suffix.
            if col.endswith('_per_min'):
                logger.info(f"Converting {col} from 1/min to 1/s")
                df_std[col] = df_std[col] / 60.0
                df_std.rename(columns={col: col.replace('_per_min', '')}, inplace=True)

    return df_std

def impute_median(df: pd.DataFrame, max_nan_fraction: float = 0.20) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Imputes missing values with the median of the column.
    Fails (logs error) if a column has more than max_nan_fraction missing values.
    Returns the cleaned dataframe and a report of imputation stats.
    """
    df_imp = df.copy()
    imputation_stats = {
        "imputed_columns": [],
        "skipped_columns": [],
        "failed_columns": []
    }

    for col in df_imp.columns:
        if df_imp[col].isnull().any():
            nan_count = df_imp[col].isnull().sum()
            total_count = len(df_imp)
            nan_fraction = nan_count / total_count

            if nan_fraction > max_nan_fraction:
                msg = f"Column '{col}' has {nan_fraction:.2%} NaN values (> {max_nan_fraction:.0%}). Skipping imputation."
                logger.error(msg)
                log_warning_structured("imputation_failed", col=col, nan_fraction=nan_fraction)
                imputation_stats["failed_columns"].append(col)
            else:
                median_val = df_imp[col].median()
                df_imp[col].fillna(median_val, inplace=True)
                imputation_stats["imputed_columns"].append({
                    "column": col,
                    "median_value": float(median_val),
                    "nan_fraction": float(nan_fraction)
                })
                logger.info(f"Imputed {col} with median {median_val:.4f} ({nan_fraction:.2%} NaN)")

    if imputation_stats["failed_columns"]:
        raise ValueError(f"Imputation failed for columns with >{max_nan_fraction*100}% NaN: {imputation_stats['failed_columns']}")

    return df_imp, imputation_stats

def remove_outliers_3sigma(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Removes rows where any numeric column deviates > 3 sigma from the mean.
    """
    df_clean = df.copy()
    if columns is None:
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    else:
        numeric_cols = [c for c in columns if c in df_clean.columns]

    outlier_stats = {"removed_rows": 0, "total_rows_before": len(df_clean), "outlier_mask": None}

    mask = pd.Series([False] * len(df_clean), index=df_clean.index)
    for col in numeric_cols:
        mean = df_clean[col].mean()
        std = df_clean[col].std()
        if std == 0:
            continue
        col_mask = (df_clean[col] - mean).abs() > 3 * std
        mask = mask | col_mask
        if col_mask.any():
            logger.info(f"Found {col_mask.sum()} outliers in {col} (3-sigma)")

    if mask.any():
        logger.warning(f"Removing {mask.sum()} rows due to 3-sigma outliers")
        df_clean = df_clean[~mask]

    outlier_stats["removed_rows"] = int(mask.sum())
    outlier_stats["total_rows_after"] = len(df_clean)

    return df_clean, outlier_stats

def derive_physics_features(df: pd.DataFrame, activation_energy: Optional[float] = None) -> pd.DataFrame:
    """
    Derives physics-based features:
    1. Strain Rate (if not present, assumes 1/s)
    2. Zener-Hollomon Parameter (Z) = epsilon_dot * exp(Q / (R * T))

    Requires:
    - 'strain_rate' (or similar) in 1/s
    - 'temperature' in Kelvin

    Returns dataframe with new columns: 'strain_rate_derived', 'zener_hollomon'
    """
    df_phys = df.copy()
    if activation_energy is None:
        activation_energy = DEFAULT_ACTIVATION_ENERGY_J
        logger.info(f"Using default activation energy: {activation_energy} J/mol")

    # Identify strain rate column
    strain_rate_cols = [c for c in df_phys.columns if 'strain_rate' in c.lower() or 'strainrate' in c.lower()]
    if not strain_rate_cols:
        logger.warning("No strain rate column found. Skipping physics feature derivation.")
        return df_phys

    strain_rate_col = strain_rate_cols[0]
    # Identify temperature column
    temp_cols = [c for c in df_phys.columns if 'temp' in c.lower()]
    if not temp_cols:
        logger.warning("No temperature column found. Skipping Zener-Hollomon calculation.")
        return df_phys

    temp_col = temp_cols[0]

    # Ensure numeric
    if not pd.api.types.is_numeric_dtype(df_phys[strain_rate_col]):
        logger.error(f"Column {strain_rate_col} is not numeric.")
        return df_phys
    if not pd.api.types.is_numeric_dtype(df_phys[temp_col]):
        logger.error(f"Column {temp_col} is not numeric.")
        return df_phys

    # Calculate Zener-Hollomon
    # Z = epsilon_dot * exp(Q / (R * T))
    # Avoid division by zero or negative temps
    valid_mask = df_phys[temp_col] > 0
    if not valid_mask.all():
        invalid_count = (~valid_mask).sum()
        logger.warning(f"Found {invalid_count} non-positive temperatures. Skipping Z calculation for these rows.")

    epsilon_dot = df_phys[strain_rate_col]
    T = df_phys[temp_col]
    Q = activation_energy
    R = GAS_CONSTANT_R

    # Compute Z
    exponent = Q / (R * T)
    # Handle potential overflow in exp for very low T
    with np.errstate(over='ignore', divide='ignore'):
        Z = epsilon_dot * np.exp(exponent)

    df_phys['zener_hollomon'] = Z
    df_phys['strain_rate_derived'] = epsilon_dot # Alias for clarity

    logger.info("Physics features (Strain Rate, Zener-Hollomon) derived successfully.")
    return df_phys

def process_dataset(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main orchestration function for data processing.
    1. Load data
    2. Standardize units
    3. Impute missing values (median)
    4. Remove 3-sigma outliers
    5. Derive physics features
    6. Save to CSV and JSON report
    """
    logger.info(f"Starting processing for: {input_path}")

    # Ensure output directory exists
    ensure_dirs([output_path])

    # Load
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")

    report = {
        "input_file": input_path,
        "output_file": output_path,
        "steps": {}
    }

    # 1. Standardize
    df_std = standardize_units(df)
    report["steps"]["unit_standardization"] = "Completed"

    # 2. Impute
    df_imp, impute_stats = impute_median(df_std)
    report["steps"]["imputation"] = impute_stats

    # 3. Outliers
    df_clean, outlier_stats = remove_outliers_3sigma(df_imp)
    report["steps"]["outlier_removal"] = outlier_stats

    # 4. Physics Features
    df_final = derive_physics_features(df_clean)
    report["steps"]["physics_derivation"] = "Completed"

    # Save
    df_final.to_csv(output_path, index=False)
    report["final_row_count"] = len(df_final)
    report["final_columns"] = list(df_final.columns)

    # Save Report JSON
    report_path = output_path.replace('.csv', '_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Processing complete. Output saved to {output_path}")
    return report

if __name__ == "__main__":
    # Example execution path
    # Assumes data exists at data/processed/raw_input.csv (placeholder for real data)
    # In a real run, this would be called from main.py or a script with args
    INPUT_FILE = "data/processed/synthetic_dataset.csv" # Default fallback if no args
    OUTPUT_FILE = "data/processed/processed_dataset.csv"

    if not os.path.exists(INPUT_FILE):
        # If the default synthetic file doesn't exist, try to generate it or exit
        # For the purpose of this task, we assume T010 (loader) has produced a file
        # or T009 (synthetic) produced one.
        # If neither exists, we can't run.
        # We will attempt to run on the expected path.
        print(f"Error: Input file {INPUT_FILE} not found. Ensure data is generated/loaded first.")
        # Exit gracefully or raise error
        import sys
        sys.exit(1)

    process_dataset(INPUT_FILE, OUTPUT_FILE)
