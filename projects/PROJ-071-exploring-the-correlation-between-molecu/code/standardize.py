"""
Standardization & Stratification Module (T020).

Implements:
1. Gate check: Reads data/gate_status.json. Halts if FAIL.
2. Data Loading: Reads data/processed/merged_drugs.csv.
3. Standardization: Converts rate constants (k) to half-lives (t1/2 = ln(2)/k).
   Standardizes time units to hours.
4. Stratification:
   - Full Dataset: Saves to data/processed/full_dataset_with_covariates.csv.
   - Standard Subset: Filters for Temp 24.5-25.5°C and near-neutral pH.
5. Statistical Gate: Checks N >= 30 in standard subset. Writes data/stat_gate_status.json.
   Halts pipeline with FatalDataError if N < 30.
"""
from __future__ import annotations

import csv
import json
import logging
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Import shared logging utilities (tolerant API)
from logging_config import get_logger, log_operation

# Local error definitions
from error_handlers import DataIngestionError, StatisticalInsufficiencyError

# Constants
LN2 = math.log(2)
STANDARD_TEMP_MIN = 24.5
STANDARD_TEMP_MAX = 25.5
# Define "near-neutral" pH range. Typically 6.5 to 7.5.
STANDARD_PH_MIN = 6.5
STANDARD_PH_MAX = 7.5
TIME_UNIT_HOURS = "hours"

# Paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
GATE_STATUS_PATH = DATA_DIR / "gate_status.json"
STAT_GATE_STATUS_PATH = DATA_DIR / "stat_gate_status.json"
MERGED_CSV_PATH = PROCESSED_DIR / "merged_drugs.csv"
FULL_DATASET_PATH = PROCESSED_DIR / "full_dataset_with_covariates.csv"
STANDARD_SUBSET_PATH = PROCESSED_DIR / "standard_subset.csv"


def get_data_path() -> Path:
    """Returns the project root path."""
    return PROJECT_ROOT


def load_gate_status() -> Dict[str, Any]:
    """
    Loads data/gate_status.json.
    Raises DataIngestionError if file missing or status is FAIL.
    """
    if not GATE_STATUS_PATH.exists():
        msg = f"Gate status file not found: {GATE_STATUS_PATH}. Pipeline cannot proceed."
        logging.error(msg)
        raise DataIngestionError(msg)

    with open(GATE_STATUS_PATH, "r", encoding="utf-8") as f:
        status = json.load(f)

    if status.get("status") == "FAIL":
        reason = status.get("reason", "Unknown reason")
        msg = f"Data Availability Gate FAILED: {reason}. Halting pipeline."
        logging.error(msg)
        # Log to the tolerant logger as well
        logger = get_logger()
        logger.log("GateCheck", {"status": "FAIL", "reason": reason})
        raise DataIngestionError(msg)

    return status


def save_stat_gate_status(status: Dict[str, Any]) -> None:
    """Writes the statistical gate status to data/stat_gate_status.json."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(STAT_GATE_STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)
    logging.info(f"Statistical gate status saved: {STAT_GATE_STATUS_PATH}")


def convert_k_to_half_life(k_value: float) -> float:
    """
    Converts a rate constant k (1/time) to half-life t1/2 = ln(2) / k.
    """
    if k_value is None or (isinstance(k_value, float) and math.isnan(k_value)):
        return float('nan')
    if k_value == 0:
        return float('inf')
    return LN2 / k_value


def normalize_time_unit_to_hours(value: float, unit: str) -> float:
    """
    Converts time values to hours.
    Expected units: 'hours', 'h', 'days', 'd', 'minutes', 'min', 'seconds', 's'.
    """
    if pd.isna(value):
        return float('nan')

    unit_lower = str(unit).lower().strip()

    if unit_lower in ['hours', 'h']:
        return value
    elif unit_lower in ['days', 'd']:
        return value * 24.0
    elif unit_lower in ['minutes', 'min']:
        return value / 60.0
    elif unit_lower in ['seconds', 's']:
        return value / 3600.0
    else:
        # If unit is unknown, assume hours or log warning and return as-is?
        # Spec says "standardize time units to hours". Assume input is hours if unknown.
        logging.warning(f"Unknown time unit '{unit}' for value {value}. Assuming hours.")
        return value


def check_data_coverage(df: pd.DataFrame) -> Tuple[int, int]:
    """
    Checks how many rows have valid degradation data (half_life or k).
    Returns (total_rows, valid_rows).
    """
    total = len(df)
    # Look for any column that might represent degradation rate or half-life
    degradation_cols = [c for c in df.columns if 'half' in c.lower() or 'k_' in c.lower() or 'rate' in c.lower()]
    if not degradation_cols:
        # Fallback: check for 'degradation' column
        degradation_cols = [c for c in df.columns if 'degradation' in c.lower()]

    valid_rows = 0
    if degradation_cols:
        # Check if any of these columns have non-null values
        valid_mask = df[degradation_cols].notna().any(axis=1)
        valid_rows = valid_mask.sum()
    else:
        # If no specific columns found, check if 'half_life' exists by name directly
        if 'half_life' in df.columns:
            valid_mask = df['half_life'].notna()
            valid_rows = valid_mask.sum()

    return total, valid_rows


def standardize_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs standardization:
    1. Identify degradation column (prefer 'half_life', then 'k_degradation', etc.).
    2. If 'k_degradation' exists, convert to 'half_life'.
    3. Ensure 'half_life' is in hours.
    4. Clean up unit columns if possible.
    """
    df = df.copy()

    # Prioritize columns
    priority_cols = ['half_life', 't_half', 'half_life_hours', 't1/2']
    k_cols = ['k_degradation', 'k', 'rate_constant', 'k_rate']

    target_col = None
    k_source_col = None

    # Find target half-life column
    for col in priority_cols:
        if col in df.columns:
            target_col = col
            break

    # If no half-life found, look for k
    if target_col is None:
        for col in k_cols:
            if col in df.columns:
                k_source_col = col
                break

    if target_col is not None:
        # Ensure values are numeric
        df[target_col] = pd.to_numeric(df[target_col], errors='coerce')
        # If there is a unit column, try to normalize
        # Assume unit column is named like 'half_life_unit' or 'time_unit'
        unit_col = None
        for c in df.columns:
            if 'unit' in c.lower() and target_col.replace('half', '').replace('life', '').replace('t', '').replace('/', '').lower() in c.lower():
                unit_col = c
                break
        if unit_col is None:
            # Generic fallback
            unit_col = 'time_unit' if 'time_unit' in df.columns else None

        if unit_col and unit_col in df.columns:
            df[target_col] = df.apply(
                lambda row: normalize_time_unit_to_hours(row[target_col], row[unit_col]),
                axis=1
            )
    elif k_source_col is not None:
        # Convert k to half_life
        k_col = k_source_col
        df[k_col] = pd.to_numeric(df[k_col], errors='coerce')
        # Assume k is in 1/hours or convert if unit exists
        # For simplicity, assume k is in 1/hours unless specified otherwise
        # If unit exists for k, we'd need to convert k first.
        # Let's assume k is in 1/hours for now as per common practice if not specified.
        new_col_name = 'half_life'
        df[new_col_name] = df[k_col].apply(convert_k_to_half_life)
        target_col = new_col_name
    else:
        logging.warning("No degradation column found to standardize. Skipping standardization.")
        return df

    # Ensure target column is numeric
    if target_col:
        df[target_col] = pd.to_numeric(df[target_col], errors='coerce')

    return df


def generate_data_characteristics_table(df: pd.DataFrame) -> Dict[str, Any]:
    """Generates a summary of the dataset characteristics."""
    return {
        "total_records": len(df),
        "columns": list(df.columns),
        "null_counts": df.isnull().sum().to_dict(),
        "timestamp": datetime.utcnow().isoformat()
    }


def log_arrhenius_exclusion(df: pd.DataFrame, excluded_rows: int) -> None:
    """Logs exclusion details for Arrhenius/condition filtering."""
    if excluded_rows > 0:
        logging.info(f"Excluded {excluded_rows} rows due to non-standard conditions.")


def merge_audit_trail(source_path: str, target_path: str, operation: str) -> None:
    """Appends an audit log entry for data transformations."""
    audit_path = PROCESSED_DIR / "data_audit_log.json"
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source_path,
        "target": target_path,
        "operation": operation
    }
    logs = []
    if audit_path.exists():
        with open(audit_path, "r") as f:
            logs = json.load(f)
    logs.append(entry)
    with open(audit_path, "w") as f:
        json.dump(logs, f, indent=2)


def standardize_and_stratify() -> None:
    """
    Main entry point for T020.
    1. Check Gate.
    2. Load Data.
    3. Standardize.
    4. Stratify (Full vs Standard).
    5. Check Statistical Gate.
    """
    logger = get_logger()
    logger.log("StandardizeAndStratify", {"step": "start"})

    # 1. Gate Check
    try:
        gate_status = load_gate_status()
        logger.log("StandardizeAndStratify", {"step": "gate_check", "status": "PASS"})
    except DataIngestionError as e:
        logger.log("StandardizeAndStratify", {"step": "gate_check", "status": "FAIL", "error": str(e)})
        raise

    # 2. Load Data
    if not MERGED_CSV_PATH.exists():
        msg = f"Required merged data file not found: {MERGED_CSV_PATH}"
        logger.log("StandardizeAndStratify", {"step": "load_data", "status": "FAIL", "error": msg})
        raise FileNotFoundError(msg)

    logging.info(f"Loading {MERGED_CSV_PATH}...")
    df = pd.read_csv(MERGED_CSV_PATH)
    logger.log("StandardizeAndStratify", {"step": "load_data", "status": "PASS", "rows": len(df)})

    # 3. Standardize
    logging.info("Standardizing degradation rates and units...")
    df_std = standardize_dataset(df)
    characteristics = generate_data_characteristics_table(df_std)
    logger.log("StandardizeAndStratify", {"step": "standardize", "status": "PASS"})

    # 4. Stratify
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Save Full Dataset
    df_std.to_csv(FULL_DATASET_PATH, index=False)
    merge_audit_trail(str(MERGED_CSV_PATH), str(FULL_DATASET_PATH), "standardization")
    logging.info(f"Saved full dataset to {FULL_DATASET_PATH}")

    # Filter Standard Subset
    # Conditions: Temp 24.5-25.5, pH 6.5-7.5
    # Check if columns exist
    temp_col = None
    ph_col = None

    for c in df_std.columns:
        if 'temp' in c.lower() or 'temperature' in c.lower():
            temp_col = c
        if 'ph' in c.lower():
            ph_col = c

    mask = pd.Series([True] * len(df_std))

    if temp_col:
        df_std[temp_col] = pd.to_numeric(df_std[temp_col], errors='coerce')
        mask &= df_std[temp_col].between(STANDARD_TEMP_MIN, STANDARD_TEMP_MAX)
    else:
        logging.warning("Temperature column not found. Cannot filter by temperature.")

    if ph_col:
        df_std[ph_col] = pd.to_numeric(df_std[ph_col], errors='coerce')
        mask &= df_std[ph_col].between(STANDARD_PH_MIN, STANDARD_PH_MAX)
    else:
        logging.warning("pH column not found. Cannot filter by pH.")

    df_standard = df_std[mask]

    # 5. Statistical Gate
    n_standard = len(df_standard)
    logging.info(f"Standard subset count: {n_standard}")

    if n_standard < 30:
        status = {
            "status": "FAIL",
            "reason": "Insufficient Standard Condition Records",
            "N": n_standard,
            "threshold": 30
        }
        save_stat_gate_status(status)
        msg = f"Statistical Gate FAILED: N={n_standard} < 30. Halting pipeline."
        logger.log("StatisticalGate", status)
        logging.error(msg)
        raise StatisticalInsufficiencyError(msg)

    # Pass
    status = {
        "status": "PASS",
        "N": n_standard,
        "threshold": 30,
        "timestamp": datetime.utcnow().isoformat()
    }
    save_stat_gate_status(status)
    logger.log("StatisticalGate", status)

    # Save Standard Subset
    df_standard.to_csv(STANDARD_SUBSET_PATH, index=False)
    merge_audit_trail(str(FULL_DATASET_PATH), str(STANDARD_SUBSET_PATH), "stratification")
    logging.info(f"Saved standard subset ({n_standard} rows) to {STANDARD_SUBSET_PATH}")

    logger.log("StandardizeAndStratify", {"step": "complete", "status": "PASS"})


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    try:
        standardize_and_stratify()
        print("Standardization and Stratification completed successfully.")
    except Exception as e:
        logging.critical(f"Pipeline halted: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()