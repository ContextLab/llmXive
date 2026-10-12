"""
Data Loading Utilities (T013, T018, T026)

Functions:
- load_smiles: Load SMILES from a CSV file.
- filter_missing_targets: Drop rows with missing target values.
- load_and_validate_target: Load and validate the target variable.
- validate_target_variable: Check dynamic range and existence.
- apply_log_transformation: Apply natural log to the target variable.
- process_molecule_with_error_handling: Process a SMILES string safely.
- load_processed_data: Load processed CSV data.
- main: CLI entry point.
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Tuple
import logging

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Configuration constants (fallback defaults if config module missing)
try:
    from code.config import TARGET_VAR, RAW_DATA_PATH, DATA_PATH
except Exception:
    TARGET_VAR = "conductivity"
    RAW_DATA_PATH = str(paths.data("raw", "smiles.csv"))
    DATA_PATH = str(paths.root)

def load_smiles(path: str) -> pd.DataFrame:
    """Load SMILES from a CSV file and add validity columns."""
    log.info(f"Loading SMILES from {path}")
    df = pd.read_csv(path)
    if "smiles" not in df.columns:
        raise ValueError("Input CSV must contain a 'smiles' column.")
    df["valid"] = df["smiles"].astype(str).str.strip() != ""
    df["error_msg"] = ""
    df.loc[~df["valid"], "error_msg"] = "Empty or invalid SMILES"
    log.info(f"Loaded {len(df)} rows.")
    return df

def filter_missing_targets(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """Drop rows where target column is NaN."""
    if target_col not in df.columns:
        log.warning(f"Target column '{target_col}' not found.")
        return df
    before = len(df)
    df = df.dropna(subset=[target_col])
    log.info(f"Dropped {before - len(df)} rows with missing {target_col}.")
    return df

def load_and_validate_target(path: str) -> Tuple[pd.DataFrame, str]:
    """
    Load raw data, detect the appropriate target column, and return the DataFrame
    together with the chosen target name.
    """
    log.info(f"Loading raw data from {path}")
    df = pd.read_csv(path)

    candidates = ["conductivity", "charge_carrier_mobility", "HOMO_LUMO_gap"]
    target = None
    for cand in candidates:
        if cand in df.columns:
            target = cand
            break

    if target is None:
        log.warning("No direct conductivity target found; will use proxy later.")
        target = "log_conductivity_proxy"

    return df, target

def validate_target_variable(df: pd.DataFrame, target_col: str) -> bool:
    """Check that the target spans at least three orders of magnitude."""
    if target_col not in df.columns:
        return False
    vals = df[target_col].dropna()
    if vals.empty:
        return False
    positive = vals[vals > 0]
    if positive.empty:
        return False
    log_range = np.log10(positive.max()) - np.log10(positive.min())
    log.info(f"Target '{target_col}' log10 range = {log_range:.2f}")
    return log_range >= 3.0

def apply_log_transformation(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """Add a natural‑log transformed column."""
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found.")
    df[f"log_{target_col}"] = np.log(df[target_col])
    log.info(f"Added column 'log_{target_col}'.")
    return df

def process_molecule_with_error_handling(smiles: str) -> dict:
    """Placeholder for molecule processing – returns a trivial dict."""
    return {"smiles": smiles, "valid": True}

def load_processed_data(path: str) -> pd.DataFrame:
    """Read a processed CSV file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed file not found: {path}")
    return pd.read_csv(path)

def main() -> int:
    """CLI for data loading – ensures raw SMILES file exists."""
    from code.download_dataset import main as download_main

    raw_path = paths.data("raw", "smiles.csv")
    if not raw_path.exists():
        log.info("Raw SMILES file missing – triggering download.")
        download_main()
    else:
        log.info(f"Raw SMILES already present at {raw_path}")

    # Simple sanity check
    df = load_smiles(str(raw_path))
    log.info(f"Sanity check: {len(df)} SMILES loaded.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
