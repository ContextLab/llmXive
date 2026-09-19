"""
Preprocessing module for MgB2 impurity data.

This module handles:
- Merging Materials Project and SuperCon datasets
- Converting impurity units from weight% to atomic%
- Handling synthesis ranges (midpoint imputation)
- Attaching provenance metadata to the final dataset
- Filtering valid entries (non-null Tc and impurities)
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np

# Project-relative imports based on API surface
from code.src.utils.constants import get_atomic_weight
from code.src.utils.data_provenance import generate_provenance_header
from code.src.utils.logging import get_ingestion_logger

logger = get_ingestion_logger(__name__)

# Constants
MAGNESIUM_SYMBOL = "Mg"
BORON_SYMBOL = "B"
OUTPUT_FILE = "data/processed/mgb2_clean.csv"


def clean_column_name(col: str) -> str:
    """
    Clean column names by lowercasing, stripping whitespace,
    and replacing spaces/special chars with underscores.
    """
    if not isinstance(col, str):
        return str(col)
    return col.lower().strip().replace(" ", "_").replace("-", "_").replace("/", "_")


def weight_pct_to_atomic_pct(
    weight_pct: float,
    impurity_symbol: str,
    host_formula: str = "MgB2"
) -> float:
    """
    Convert weight percentage to atomic percentage.

    Formula:
    atomic_pct = (weight_pct / atomic_weight_impurity) /
                ( (weight_pct / atomic_weight_impurity) +
                  ((100 - weight_pct) / avg_host_atomic_weight) ) * 100

    For MgB2, the host is a compound. We calculate the average atomic weight
    of the host matrix (Mg + 2B) per formula unit, but strictly speaking,
    the conversion depends on the molar ratio of the host components.
    However, standard practice for dilute impurities in a compound host
    often treats the host as a single effective species or converts based
    on the specific site substitution.

    To be rigorous for MgB2:
    We assume the impurity substitutes into the lattice.
    Let's calculate based on the molar mass of the host components.
    Moles of host per 100g total = (100 - wt%) / (Avg_Mass_Host_Per_Atom)
    Moles of impurity = wt% / Atomic_Weight_Impurity

    Average mass of host per atom in MgB2:
    Mg (24.305) + 2*B (10.81) = 45.925 g/mol per formula unit.
    Formula unit has 3 atoms.
    Avg mass per atom = 45.925 / 3 = 15.308 g/mol/atom.

    Args:
        weight_pct: Weight percentage of the impurity.
        impurity_symbol: Chemical symbol of the impurity.
        host_formula: Host formula (default MgB2).

    Returns:
        Atomic percentage of the impurity.
    """
    if pd.isna(weight_pct) or weight_pct <= 0:
        return 0.0

    impurity_weight = get_atomic_weight(impurity_symbol)
    if impurity_weight is None:
        logger.warning(f"Unknown atomic weight for {impurity_symbol}, skipping conversion.")
        return np.nan

    # Average atomic weight of MgB2 per atom
    # Mg: 24.305, B: 10.81. Total formula weight = 45.925. Atoms per formula = 3.
    host_avg_atomic_weight = 15.308

    moles_impurity = weight_pct / impurity_weight
    moles_host = (100 - weight_pct) / host_avg_atomic_weight

    total_moles = moles_impurity + moles_host
    if total_moles == 0:
        return 0.0

    atomic_pct = (moles_impurity / total_moles) * 100
    return atomic_pct


def handle_synthesis_range(value: Any) -> float:
    """
    Handle synthesis ranges (e.g., "10-20" or "10 - 20").
    Returns the midpoint of the range.
    If the value is already a number, returns it.
    If the value is invalid or non-numeric, returns np.nan.
    """
    if pd.isna(value):
        return np.nan

    if isinstance(value, (int, float)):
        return float(value)

    value_str = str(value).strip()
    if not value_str:
        return np.nan

    # Check for range format (e.g., "10-20", "10 - 20")
    if "-" in value_str:
        parts = value_str.split("-")
        if len(parts) == 2:
            try:
                low = float(parts[0].strip())
                high = float(parts[1].strip())
                return (low + high) / 2.0
            except ValueError:
                return np.nan
    else:
        # Try direct conversion
        try:
            return float(value_str)
        except ValueError:
            return np.nan


def convert_impurity_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert impurity columns from weight% to atomic%.
    Assumes columns are named like 'impurity_X_weight_pct' or similar.
    We need to identify impurity columns dynamically.
    """
    df = df.copy()
    impurity_cols = []

    # Identify impurity columns: look for columns containing 'impurity' and 'weight'
    # or 'wt' and 'pct'
    for col in df.columns:
        col_lower = col.lower()
        if "impurity" in col_lower and ("weight" in col_lower or "wt" in col_lower):
            impurity_cols.append(col)

    if not impurity_cols:
        logger.warning("No weight% impurity columns found to convert.")
        return df

    for col in impurity_cols:
        # Extract impurity symbol from column name if possible, otherwise try to infer
        # Format expected: impurity_<symbol>_weight_pct
        parts = col.split("_")
        symbol = None
        for part in parts:
            # Heuristic: if part is 1-2 chars and looks like a symbol (capitalized)
            if len(part) <= 2 and part[0].isupper():
                symbol = part
                break

        # If we can't find a symbol, we might have to skip or use a generic one.
        # For now, if symbol is None, we log and skip this column or try to guess.
        # A robust implementation would require a mapping or strict naming convention.
        if symbol is None:
            logger.warning(f"Could not identify impurity symbol in column: {col}. Skipping conversion.")
            continue

        # Create new column name
        new_col = col.replace("weight_pct", "atomic_pct").replace("wt_pct", "atomic_pct")
        if new_col == col:
            new_col = col + "_atomic_pct"

        # Apply conversion
        df[new_col] = df[col].apply(lambda x: weight_pct_to_atomic_pct(x, symbol))

        # Drop the original weight column if it exists (optional, but cleaner)
        # We keep it for provenance but mark the atomic one as the primary
        # For this task, we will keep both but ensure the atomic one is used for analysis.
        # Actually, the task says "convert units", implying replacement or addition.
        # We will add the atomic column.

    return df


def merge_datasets(mp_df: pd.DataFrame, supercon_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge Materials Project and SuperCon datasets.
    Performs a simple concatenation as they likely have different row sets.
    Standardizes column names.
    """
    logger.info(f"MP dataset shape: {mp_df.shape}")
    logger.info(f"SuperCon dataset shape: {supercon_df.shape}")

    # Clean column names
    mp_df.columns = [clean_column_name(c) for c in mp_df.columns]
    supercon_df.columns = [clean_column_name(c) for c in supercon_df.columns]

    # Concatenate
    merged = pd.concat([mp_df, supercon_df], ignore_index=True)

    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged


def filter_valid_entries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter rows where Tc and impurities are not null.
    Specifically, we need at least one valid impurity entry and a valid Tc.
    """
    logger.info(f"Filtering valid entries. Original shape: {df.shape}")

    # Identify Tc column
    tc_col = None
    for col in df.columns:
        if "tc" in col.lower() and "critical" not in col.lower(): # Exclude "critical_temperature" if separate
            if "temperature" in col.lower() or "tc" == col.lower():
                tc_col = col
                break
    if tc_col is None:
        # Fallback
        tc_col = "tc" if "tc" in df.columns else next((c for c in df.columns if "temperature" in c), None)

    if tc_col is None:
        logger.error("Could not identify Tc column.")
        return df

    # Filter out null Tc
    df = df.dropna(subset=[tc_col])

    # Filter out rows with no impurities
    # Check for any column starting with 'impurity' that has a value > 0
    impurity_cols = [c for c in df.columns if c.startswith("impurity")]
    if impurity_cols:
        # Create a mask where at least one impurity column is not null
        mask = df[impurity_cols].notna().any(axis=1)
        df = df[mask]

    logger.info(f"Filtered valid entries. New shape: {df.shape}")
    return df


def attach_provenance(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """
    Attach provenance metadata to the dataset.
    FR-001: Ensure provenance metadata is attached to CACHED files.
    We add a 'provenance' column or store it in metadata attributes.
    For CSV, we append a header comment or a specific column.
    The task asks to attach metadata. We will add a column 'data_source' and 'processed_timestamp'.
    """
    df = df.copy()
    timestamp = datetime.utcnow().isoformat()
    version = "1.0.0"

    # Generate provenance header dict
    prov_header = generate_provenance_header(source=source, timestamp=timestamp, version=version)

    # Add columns to dataframe
    df['data_source'] = prov_header['source']
    df['processed_timestamp'] = prov_header['timestamp']
    df['data_version'] = prov_header['version']

    # Store full provenance in a separate metadata file or attribute if needed.
    # For CSV, we can save the header info to a sidecar JSON.
    return df, prov_header


def preprocess_datasets(mp_df: pd.DataFrame, supercon_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main preprocessing pipeline:
    1. Merge datasets
    2. Convert units (weight% -> atomic%)
    3. Handle synthesis ranges (midpoint imputation)
    4. Filter valid entries
    5. Attach provenance
    """
    logger.info("Starting preprocessing pipeline...")

    # 1. Merge
    df = merge_datasets(mp_df, supercon_df)

    # 2. Handle synthesis ranges for numeric columns that might be strings
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    # Also check object columns that might be ranges
    for col in df.columns:
        if df[col].dtype == 'object':
            # Check if any value looks like a range
            if df[col].astype(str).str.contains("-").any():
                df[col] = df[col].apply(handle_synthesis_range)

    # 3. Convert units
    df = convert_impurity_units(df)

    # 4. Filter valid entries
    df = filter_valid_entries(df)

    # 5. Attach provenance
    df, provenance = attach_provenance(df, source="MP+SuperCon")

    logger.info("Preprocessing pipeline complete.")
    return df, provenance


def main():
    """
    Entry point for the preprocessing script.
    Expects pre-downloaded JSON/CSV files from T012 and T013.
    """
    logger.info("Running preprocess.py main...")

    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    data_processed_dir = project_root / "data" / "processed"

    mp_file = data_raw_dir / "materials_project_mgb2.json"
    supercon_file = data_raw_dir / "supercon_mgb2.csv"

    # Check if files exist
    if not mp_file.exists():
        logger.error(f"MP file not found: {mp_file}. Run T012 first.")
        sys.exit(1)
    if not supercon_file.exists():
        logger.error(f"SuperCon file not found: {supercon_file}. Run T013 first.")
        sys.exit(1)

    # Load data
    logger.info(f"Loading MP data from {mp_file}")
    with open(mp_file, 'r') as f:
        mp_data = json.load(f)
    mp_df = pd.DataFrame(mp_data)

    logger.info(f"Loading SuperCon data from {supercon_file}")
    supercon_df = pd.read_csv(supercon_file)

    # Preprocess
    clean_df, provenance = preprocess_datasets(mp_df, supercon_df)

    # Ensure output directory exists
    data_processed_dir.mkdir(parents=True, exist_ok=True)

    # Save clean dataset
    output_path = data_processed_dir / "mgb2_clean.csv"
    clean_df.to_csv(output_path, index=False)
    logger.info(f"Saved clean dataset to {output_path}")

    # Save provenance metadata
    provenance_file = data_processed_dir / "mgb2_clean_provenance.json"
    with open(provenance_file, 'w') as f:
        json.dump(provenance, f, indent=2)
    logger.info(f"Saved provenance metadata to {provenance_file}")

    logger.info("Preprocessing completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
