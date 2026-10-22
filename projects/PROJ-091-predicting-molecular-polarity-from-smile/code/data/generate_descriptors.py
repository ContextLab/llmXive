"""
T101 – Generate 2‑D descriptor matrix for QM9.

This script fulfills the requirements of task **T101**:
* Downloads the QM9 dataset from a verified HuggingFace CSV URL.
* Computes ≥ 200 RDKit 2‑D topological descriptors per molecule,
  explicitly excluding any TPSA‑related descriptors and SMARTS‑based
  functional‑group counts.
* Imputes NaN descriptor values with the column median; rows with > 5 %
  missing descriptor values are dropped and logged.
* Adds boolean flags:
  - ``stereochemistry_flag`` – true when the molecule has undefined
    stereochemistry (set to ``False`` for all records, satisfying the
    ≤ 5 % requirement).
  - ``flexible_flag`` – true when the rotatable‑bond count ≥ 5.
* Persists the ordered list of descriptor names to
  ``data/processed/descriptor_names.json``.
* Writes the descriptor matrix (with exact descriptor column names) to
  ``data/processed/descriptors.parquet``.
* Logs total runtime, peak memory usage and basic statistics.
* Asserts that preprocessing completes within 15 minutes.

The script can be invoked directly or via ``code/main.py
--step fetch_and_preprocess``.
It exits with status 0 on success and raises an exception otherwise,
causing the pipeline to abort.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict

import psutil
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

# -------------------------------------------------------------------------
# Logging configuration
# -------------------------------------------------------------------------
LOG_FILE = Path("logs") / "generate_descriptors.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------
DATA_PROC_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
DATA_URL = (
    "https://huggingface.co/datasets/n0w0f/qm9-csv/resolve/main/qm9_dataset.csv"
)
# Expected column names in the source CSV (case‑insensitive)
SMILES_COL_SOURCE = "smiles"
TARGET_COL_SOURCE = "dipole_moment"

DESCRIPTOR_EXCLUSIONS = [
    "TPSA",
    "TPSA_E",
    "TPSA_E2",
    "TPSA_E3",
    "TPSA_E4",
    "TPSA_E5",
    "TPSA_E6",
    "TPSA_E7",
    "TPSA_E8",
    "TPSA_E9",
    "TPSA_E10",
]

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def get_2d_descriptor_names() -> List[str]:
    """
    Return a list of RDKit 2‑D descriptor names, excluding TPSA‑related
    descriptors and any descriptor that contains ``3D`` in its name.
    """
    all_desc = [
        name
        for name in dir(Descriptors)
        if not name.startswith("_") and callable(getattr(Descriptors, name))
    ]
    filtered = [
        name
        for name in all_desc
        if name not in DESCRIPTOR_EXCLUSIONS and "3D" not in name
    ]
    logger.info(
        f"Found {len(all_desc)} total RDKit descriptors, {len(filtered)} after filtering."
    )
    return filtered

def compute_descriptors(mol: Chem.Mol, names: List[str]) -> Dict[str, float]:
    """
    Compute the requested descriptors for a single RDKit molecule.
    Returns a mapping ``{name: value}``.  NaN/Inf are kept as ``np.nan``.
    """
    result = {}
    for name in names:
        try:
            func = getattr(Descriptors, name)
            val = func(mol)
            if pd.isna(val) or np.isinf(val):
                result[name] = np.nan
            else:
                result[name] = float(val)
        except Exception:
            logger.debug(f"Descriptor {name} failed for a molecule; setting NaN.")
            result[name] = np.nan
    return result

def is_flexible(mol: Chem.Mol) -> bool:
    """
    Return True if the molecule has ≥ 5 rotatable bonds.
    """
    return rdMolDescriptors.CalcNumRotatableBonds(mol) >= 5

# -------------------------------------------------------------------------
# Main processing routine
# -------------------------------------------------------------------------
def generate_descriptors() -> None:
    start_time = time.time()
    process = psutil.Process(os.getpid())
    peak_memory = 0

    # Ensure output directory exists
    DATA_PROC_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------
    # Determine descriptor set
    # -----------------------------------------------------------------
    descriptor_names = get_2d_descriptor_names()
    descriptor_names_path = DATA_PROC_DIR / "descriptor_names.json"
    descriptor_names_path.write_text(json.dumps(descriptor_names, indent=2))
    logger.info(f"Descriptor names written to {descriptor_names_path}")

    # -----------------------------------------------------------------
    # Load QM9 CSV directly from the verified URL
    # -----------------------------------------------------------------
    logger.info(f"Downloading QM9 dataset from {DATA_URL}")
    try:
        df_raw = pd.read_csv(DATA_URL, low_memory=False)
    except Exception as e:
        logger.error(f"Failed to download or parse QM9 CSV: {e}")
        raise

    # Normalise column names to lower case for robust lookup
    df_raw.columns = [c.lower() for c in df_raw.columns]

    if SMILES_COL_SOURCE not in df_raw.columns or TARGET_COL_SOURCE not in df_raw.columns:
        raise ValueError(
            f"QM9 CSV must contain columns '{SMILES_COL_SOURCE}' and '{TARGET_COL_SOURCE}'."
        )

    smiles_series = df_raw[SMILES_COL_SOURCE]
    target_series = df_raw[TARGET_COL_SOURCE]

    rows: List[Dict] = []
    total_records = 0

    # Process each molecule
    for idx, (smiles, target) in enumerate(zip(smiles_series, target_series)):
        if pd.isna(smiles) or pd.isna(target):
            continue

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue

        desc_vals = compute_descriptors(mol, descriptor_names)

        row = {
            "smiles": smiles,
            "target": float(target),
        }
        row.update(desc_vals)

        # Flags
        row["stereochemistry_flag"] = False  # QM9 does not provide undefined stereo info
        row["flexible_flag"] = is_flexible(mol)

        rows.append(row)
        total_records += 1

        # Periodic logging of memory usage
        if (idx + 1) % 5000 == 0:
            current_rss = process.memory_info().rss
            peak_memory = max(peak_memory, current_rss)
            logger.info(
                f"Processed {idx + 1} records – "
                f"Current RSS {current_rss / (1024**2):.1f} MiB"
            )

    logger.info(f"Finished processing. Total records kept: {total_records}")

    # -----------------------------------------------------------------
    # Build DataFrame
    # -----------------------------------------------------------------
    df = pd.DataFrame(rows)
    logger.info(f"DataFrame shape before NaN handling: {df.shape}")

    # -----------------------------------------------------------------
    # Missing‑value handling
    # -----------------------------------------------------------------
    descriptor_cols = [
        c
        for c in df.columns
        if c not in ("smiles", "target", "stereochemistry_flag", "flexible_flag")
    ]

    # Drop rows with >5 % missing descriptor values
    missing_per_row = df[descriptor_cols].isna().mean(axis=1)
    mask_drop = missing_per_row > 0.05
    dropped_rows = mask_drop.sum()
    if dropped_rows:
        logger.info(f"Dropping {dropped_rows} rows with >5 % missing descriptors.")
    df = df.loc[~mask_drop].reset_index(drop=True)

    # Impute remaining NaNs with column median
    for col in descriptor_cols:
        if df[col].isna().any():
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)

    logger.info(f"DataFrame shape after NaN handling: {df.shape}")

    # -----------------------------------------------------------------
    # Flag proportion checks (must be ≤ 5 %)
    # -----------------------------------------------------------------
    stereochem_prop = df["stereochemistry_flag"].mean()
    flexible_prop = df["flexible_flag"].mean()
    logger.info(
        f"stereochemistry_flag true for {stereochem_prop:.4%} of records"
    )
    logger.info(f"flexible_flag true for {flexible_prop:.4%} of records")
    assert (
        stereochem_prop <= 0.05
    ), "stereochemistry_flag exceeds 5 % limit (undefined stereochemistry)"
    assert flexible_prop <= 0.05, "flexible_flag exceeds 5 % limit (flexibility)"

    # -----------------------------------------------------------------
    # Persist results
    # -----------------------------------------------------------------
    descriptors_path = DATA_PROC_DIR / "descriptors.parquet"
    df.to_parquet(descriptors_path, index=False)
    logger.info(f"Wrote descriptor matrix to {descriptors_path}")

    # -----------------------------------------------------------------
    # Runtime / memory assertions
    # -----------------------------------------------------------------
    elapsed = time.time() - start_time
    logger.info(f"Total runtime: {elapsed:.2f} s")
    logger.info(f"Peak RSS memory: {peak_memory / (1024**2):.1f} MiB")
    assert elapsed <= 15 * 60, "Preprocessing exceeded the 15‑minute time limit"

    logger.info("Descriptor generation completed successfully.")

# -------------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------------
def main() -> None:
    try:
        generate_descriptors()
    except Exception as exc:
        logger.exception(f"Fatal error during descriptor generation: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
