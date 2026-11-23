"""
Preprocessing pipeline for adsorption isotherm data.
Implements filtering, normalization, imputation, and outlier detection.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import numpy as np

# Ensure imports align with the provided API surface
from data.descriptors import calculate_descriptors_batch, generate_descriptor_hash, log_missing_entry

logger = logging.getLogger(__name__)

# Ensure directories exist
def ensure_directories(base_dir: Path) -> None:
    """Create necessary output directories."""
    (base_dir / "validation").mkdir(parents=True, exist_ok=True)
    (base_dir / "processed").mkdir(parents=True, exist_ok=True)

def load_raw_data(data_dir: Path) -> pd.DataFrame:
    """Load the merged dataset."""
    path = data_dir / "merged_dataset.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Expected merged dataset not found at {path}")
    return pd.read_parquet(path)

def filter_type_isotherms(df: pd.DataFrame) -> pd.DataFrame:
    """Filter for Type I isotherms only."""
    if "isotherm_type" in df.columns:
        return df[df["isotherm_type"] == "Type I"].copy()
    # If column missing, assume all are Type I or log warning
    logger.warning("Column 'isotherm_type' not found. Assuming all entries are Type I.")
    return df.copy()

def remove_missing_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Remove entries where target variables are missing."""
    targets = ["langmuir_capacity", "henry_constant"]
    existing_targets = [t for t in targets if t in df.columns]
    if not existing_targets:
        raise ValueError("No target columns (langmuir_capacity, henry_constant) found in dataset.")
    initial_count = len(df)
    df = df.dropna(subset=existing_targets)
    excluded = initial_count - len(df)
    if excluded > 0:
        logger.info(f"Removed {excluded} rows due to missing target values.")
    return df

def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize surface_area to m²/g."""
    if "surface_area" in df.columns:
        # Assuming input is already in m²/g or needs conversion
        # If unit column exists, convert logic here. For now, assume raw is m²/g.
        pass
    return df

def filter_and_normalize(df: pd.DataFrame, exclusion_log_path: Path) -> pd.DataFrame:
    """
    Main filtering and normalization step.
    1. Filter Type I.
    2. Remove missing targets.
    3. Normalize units.
    4. Log excluded entries.
    """
    ensure_directories(exclusion_log_path.parent)
    df = filter_type_isotherms(df)
    df = remove_missing_targets(df)
    df = normalize_units(df)

    # Log excluded entries (simplified: log count and reason)
    log_entry = {
        "step": "filter_and_normalize",
        "reason": "Missing targets or non-Type I",
        "timestamp": str(pd.Timestamp.now())
    }
    if exclusion_log_path.exists():
        with open(exclusion_log_path, 'r') as f:
            logs = json.load(f)
    else:
        logs = []
    logs.append(log_entry)
    with open(exclusion_log_path, 'w') as f:
        json.dump(logs, f, indent=2)

    return df

def impute_pore_volume(df: pd.DataFrame, exclusion_log_path: Path) -> pd.DataFrame:
    """
    Impute missing pore_volume using hierarchical grouping.
    1. Group by (material_type, surface_area_bin).
    2. If group size > 0, assign group mean.
    3. If group size == 0, assign material_type global mean.
    4. If no material_type, assign global dataset mean.
    5. Log failures.
    """
    if "pore_volume" not in df.columns:
        logger.warning("Column 'pore_volume' not found. Skipping imputation.")
        return df

    df = df.copy()
    df["pore_area_bin"] = pd.qcut(df["surface_area"], q=10, labels=False, duplicates="drop")
    
    # Group 1: (material_type, surface_area_bin)
    group1 = df.groupby(["material_type", "pore_area_bin"])["pore_volume"]
    
    # Group 2: material_type
    group2 = df.groupby("material_type")["pore_volume"]
    
    # Group 3: Global
    global_mean = df["pore_volume"].mean()

    mask_missing = df["pore_volume"].isna()
    if not mask_missing.any():
        return df

    # Strategy:
    # 1. Fill with group1 mean
    # 2. Fill remaining with group2 mean
    # 3. Fill remaining with global_mean
    
    # Calculate group means
    g1_means = group1.transform('mean')
    g2_means = group2.transform('mean')

    # Apply imputation
    df.loc[mask_missing, "pore_volume"] = g1_means
    
    # Still missing? Try group2
    still_missing = df["pore_volume"].isna()
    if still_missing.any():
        df.loc[still_missing, "pore_volume"] = g2_means
    
    # Still missing? Try global
    still_missing = df["pore_volume"].isna()
    if still_missing.any():
        df.loc[still_missing, "pore_volume"] = global_mean
    
    # Log any that are still missing (should be rare if global mean exists)
    still_missing = df["pore_volume"].isna()
    if still_missing.any():
        log_entry = {
            "step": "impute_pore_volume",
            "reason": "Imputation failed (no group or global mean)",
            "count": int(still_missing.sum()),
            "timestamp": str(pd.Timestamp.now())
        }
        if exclusion_log_path.exists():
            with open(exclusion_log_path, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        logs.append(log_entry)
        with open(exclusion_log_path, 'w') as f:
            json.dump(logs, f, indent=2)
        df = df.dropna(subset=["pore_volume"])

    return df

def detect_outliers(df: pd.DataFrame, output_path: Path, config: Optional[Dict] = None) -> pd.DataFrame:
    """
    Detect outliers based on descriptor_hash groups.
    Logic:
    1. Group by `descriptor_hash`.
    2. For groups with size > 1, calculate mean and std of target variable.
    3. Flag entries where |value - group_mean| > 3 * group_std.
    4. DO NOT exclude. Write to CSV.
    """
    if config is None:
        config = {"target": "langmuir_capacity"}
    
    target_col = config.get("target", "langmuir_capacity")
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")
    
    if "descriptor_hash" not in df.columns:
        logger.warning("Column 'descriptor_hash' not found. Cannot perform outlier detection by hash.")
        # Fallback: maybe log and return empty
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_out = pd.DataFrame(columns=["material_id", "descriptor_hash", "target_value", "group_mean", "group_std", "exclusion_reason"])
        df_out.to_csv(output_path, index=False)
        return df

    flagged_entries = []

    # Group by descriptor_hash
    grouped = df.groupby("descriptor_hash")

    for hash_val, group in grouped:
        if len(group) <= 1:
            continue  # Skip groups with only 1 entry (cannot calculate std)
        
        values = group[target_col]
        mean_val = values.mean()
        std_val = values.std()
        
        if std_val == 0:
            continue # No variance, no outliers

        # Flag condition
        mask = np.abs(values - mean_val) > 3 * std_val
        
        if mask.any():
            for idx in group[mask].index:
                row = df.loc[idx]
                flagged_entries.append({
                    "material_id": row.get("material_id", idx),
                    "descriptor_hash": hash_val,
                    "target_value": float(row[target_col]),
                    "group_mean": float(mean_val),
                    "group_std": float(std_val),
                    "exclusion_reason": "Outlier detected (|value - mean| > 3*std)"
                })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_out = pd.DataFrame(flagged_entries)
    df_out.to_csv(output_path, index=False)
    logger.info(f"Detected {len(flagged_entries)} outliers. Saved to {output_path}")

    return df # Return original df, do not drop

def save_logs(logs: List[Dict], log_path: Path) -> None:
    """Save logs to JSON."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=2)

def main():
    """
    Entry point for preprocessing pipeline.
    Expects data in data/raw/merged_dataset.parquet
    Outputs:
      - data/validation/exclusion_log.json
      - data/validation/outliers_flagged.csv (T016)
      - data/processed/cleaned_data.csv (final output)
    """
    logging.basicConfig(level=logging.INFO)
    
    # Paths
    base_dir = Path("data")
    raw_dir = base_dir / "raw"
    val_dir = base_dir / "validation"
    proc_dir = base_dir / "processed"
    
    input_file = raw_dir / "merged_dataset.parquet"
    exclusion_log = val_dir / "exclusion_log.json"
    outliers_file = val_dir / "outliers_flagged.csv"
    output_file = proc_dir / "cleaned_data.csv"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    logger.info("Loading raw data...")
    df = load_raw_data(raw_dir)
    
    logger.info("Filtering and normalizing...")
    df = filter_and_normalize(df, exclusion_log)
    
    logger.info("Imputing pore volume...")
    df = impute_pore_volume(df, exclusion_log)
    
    logger.info("Detecting outliers...")
    df = detect_outliers(df, outliers_file)
    
    logger.info("Saving cleaned data...")
    df.to_csv(output_file, index=False)
    logger.info(f"Pipeline complete. Output: {output_file}")

if __name__ == "__main__":
    main()