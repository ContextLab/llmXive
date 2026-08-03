"""
Data standardization and stratification module.
"""
from __future__ import annotations

import csv
import json
import logging
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.logging_config import get_logger, log_operation

logger = get_logger("standardize")

# Configuration
GATE_STATUS_PATH = PROJECT_ROOT / "data" / "gate_status.json"
STAT_GATE_STATUS_PATH = PROJECT_ROOT / "data" / "stat_gate_status.json"
MERGED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "merged_drugs.csv"
FULL_DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "full_dataset_with_covariates.csv"
STANDARD_SUBSET_PATH = PROJECT_ROOT / "data" / "processed" / "standard_subset.csv"

def get_data_path() -> Path:
    """Return the path to the merged data."""
    return MERGED_DATA_PATH

def load_gate_status() -> Dict[str, Any]:
    """Load the main gate status."""
    if not GATE_STATUS_PATH.exists():
        return {"status": "FAIL", "reason": "Gate status file missing"}
    with open(GATE_STATUS_PATH, "r") as f:
        return json.load(f)

def save_stat_gate_status(status: Dict[str, Any]) -> None:
    """Save statistical gate status."""
    with open(STAT_GATE_STATUS_PATH, "w") as f:
        json.dump(status, f, indent=2)
    logger.log("Stat gate status saved", {"path": str(STAT_GATE_STATUS_PATH)})

def convert_k_to_half_life(k: float) -> float:
    """Convert rate constant k to half-life t1/2 = ln(2)/k."""
    if k <= 0:
        return float('nan')
    return math.log(2) / k

def normalize_time_unit_to_hours(value: float, unit: str) -> float:
    """Normalize time unit to hours."""
    unit = unit.lower()
    if unit in ["hour", "h", "hr"]:
        return value
    elif unit in ["day", "d"]:
        return value * 24
    elif unit in ["week", "w"]:
        return value * 168
    elif unit in ["year", "y"]:
        return value * 8760
    else:
        return value  # Assume hours if unknown

def check_data_coverage(df: pd.DataFrame) -> Dict[str, Any]:
    """Check data coverage for key columns."""
    coverage = {}
    key_cols = ["half_life_hours", "half_life", "k_degradation", "rate_constant", "t_half", "pH", "Temperature"]
    for col in key_cols:
        if col in df.columns:
            non_null = df[col].notna().sum()
            total = len(df)
            coverage[col] = {"non_null": int(non_null), "total": int(total), "pct": float(non_null / total * 100)}
        else:
            coverage[col] = {"non_null": 0, "total": len(df), "pct": 0.0, "missing": True}
    return coverage

def standardize_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize the dataset: convert rates to half-lives, normalize units."""
    df = df.copy()

    # Identify degradation column
    degradation_cols = ["half_life", "k_degradation", "rate_constant", "t_half"]
    target_col = None
    rate_col = None

    for col in degradation_cols:
        if col in df.columns and df[col].notna().sum() > 0:
            if col in ["half_life", "t_half"]:
                target_col = col
            else:
                rate_col = col
            break

    if target_col:
        # Ensure it's in hours
        if "unit" in df.columns:
            df["half_life_hours"] = df.apply(
                lambda row: normalize_time_unit_to_hours(row[target_col], row["unit"]) if pd.notna(row[target_col]) else row[target_col],
                axis=1
            )
        else:
            df["half_life_hours"] = df[target_col]
    elif rate_col:
        # Convert rate to half-life
        df["half_life_hours"] = df[rate_col].apply(lambda x: convert_k_to_half_life(x) if pd.notna(x) else x)
    else:
        df["half_life_hours"] = float('nan')

    # Normalize pH and Temperature if present
    if "pH" in df.columns:
        df["pH"] = pd.to_numeric(df["pH"], errors='coerce')

    if "Temperature" in df.columns or "temperature" in df.columns:
        temp_col = "Temperature" if "Temperature" in df.columns else "temperature"
        df["Temperature_C"] = pd.to_numeric(df[temp_col], errors='coerce')

    return df

def generate_data_characteristics_table(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a summary table of data characteristics."""
    characteristics = {
        "total_rows": int(len(df)),
        "columns": list(df.columns),
        "null_counts": df.isnull().sum().to_dict(),
        "numeric_stats": {}
    }

    numeric_cols = df.select_dtypes(include=[float, int]).columns
    for col in numeric_cols:
        characteristics["numeric_stats"][col] = {
            "mean": float(df[col].mean()) if not df[col].isna().all() else None,
            "std": float(df[col].std()) if not df[col].isna().all() else None,
            "min": float(df[col].min()) if not df[col].isna().all() else None,
            "max": float(df[col].max()) if not df[col].isna().all() else None
        }

    return characteristics

def log_arrhenius_exclusion(row: Dict[str, Any], reason: str) -> None:
    """Log excluded molecules due to Arrhenius equation constraints."""
    # Placeholder for exclusion logging
    pass

def merge_audit_trail(source_path: Path, target_path: Path, transformation: str) -> None:
    """Merge audit trail between source and target files."""
    # Placeholder for audit trail merging
    pass

def standardize_and_stratify() -> pd.DataFrame:
    """Standardize dataset and create standard subset."""
    df = pd.read_csv(MERGED_DATA_PATH)
    df_standardized = standardize_dataset(df)

    # Save full dataset
    df_standardized.to_csv(FULL_DATASET_PATH, index=False)
    logger.log("Full dataset saved", {"path": str(FULL_DATASET_PATH)})

    # Create standard subset: Temp 24.5-25.5°C, pH near-neutral (6.5-7.5)
    if "Temperature_C" in df_standardized.columns and "pH" in df_standardized.columns:
        standard_mask = (
            (df_standardized["Temperature_C"] >= 24.5) &
            (df_standardized["Temperature_C"] <= 25.5) &
            (df_standardized["pH"] >= 6.5) &
            (df_standardized["pH"] <= 7.5)
        )
    elif "Temperature_C" in df_standardized.columns:
        standard_mask = (
            (df_standardized["Temperature_C"] >= 24.5) &
            (df_standardized["Temperature_C"] <= 25.5)
        )
    elif "pH" in df_standardized.columns:
        standard_mask = (
            (df_standardized["pH"] >= 6.5) &
            (df_standardized["pH"] <= 7.5)
        )
    else:
        # If no conditions, use all data
        standard_mask = pd.Series([True] * len(df_standardized))

    standard_subset = df_standardized[standard_mask].copy()
    standard_subset.to_csv(STANDARD_SUBSET_PATH, index=False)
    logger.log("Standard subset saved", {"path": str(STANDARD_SUBSET_PATH), "n_rows": len(standard_subset)})

    return standard_subset

@log_operation("Standardize_And_Stratify")
def main() -> None:
    """Main entry point for standardization."""
    logger.log("Standardization started")

    # Check gate status
    gate_status = load_gate_status()
    if gate_status.get("status") == "FAIL":
        logger.log("Gate failed, halting standardization", {"reason": gate_status.get("reason")})
        raise RuntimeError("Main gate failed, cannot proceed with standardization")

    # Standardize and stratify
    standard_subset = standardize_and_stratify()

    # Check statistical gate
    n_standard = len(standard_subset)
    if n_standard < 30:
        stat_status = {
            "status": "FAIL",
            "reason": "Insufficient Standard Condition Records",
            "N": n_standard,
            "timestamp": pd.Timestamp.utcnow().isoformat()
        }
        save_stat_gate_status(stat_status)
        logger.log("Stat gate failed", {"N": n_standard})
        raise RuntimeError(f"Stat gate failed: N={n_standard} < 30")
    else:
        stat_status = {
            "status": "PASS",
            "N": n_standard,
            "timestamp": pd.Timestamp.utcnow().isoformat()
        }
        save_stat_gate_status(stat_status)
        logger.log("Stat gate passed", {"N": n_standard})

    logger.log("Standardization completed successfully")

if __name__ == "__main__":
    main()