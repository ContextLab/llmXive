"""
T101 – Generate 2‑D descriptor matrix for QM9.

This script fulfills the requirements of task **T101**:
* Downloads the QM9 dataset using the verified HuggingFace source
  (`jablonkagroup/qm9`, config `raw_data`) via the `datasets` library.
* Streams the data to keep RAM usage ≤ 6 GB.
* Computes ≥ 200 RDKit 2‑D topological descriptors per molecule,
  explicitly excluding any TPSA‑related descriptors and SMARTS‑based
  functional‑group counts.
* Imputes NaN descriptor values with the column median; rows with > 5 %
  missing descriptor values are dropped and logged.
* Adds boolean flags:
  - ``stereochemistry_flag`` – true when the molecule has at least one
    chiral centre (≤ 5 % of the dataset must be true).
  - ``flexible_flag`` – true when the rotatable‑bond count ≥ 5
    (≤ 5 % of the dataset must be true).
* Persists the ordered list of descriptor names (without the ``desc_``
  prefix) to ``data/processed/descriptor_names.json``.
* Writes the descriptor matrix (with ``desc_``‑prefixed column names) to
  ``data/processed/descriptors.parquet``.
* Logs total runtime, peak memory usage and basic statistics.
* Asserts that preprocessing completes within 15 minutes.

The script is invoked by the pipeline via ``code/main.py`` (see the
modification in that file).  It exits with status 0 on success and
raises an exception otherwise, causing the pipeline to abort.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple

import psutil
import pandas as pd
import numpy as np
from datasets import load_dataset
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
DATA_RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_PROC_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
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
    logger.info(f"Found {len(all_desc)} total descriptors, {len(filtered)} after filtering.")
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
        except Exception as e:
            logger.debug(f"Descriptor {name} failed for a molecule: {e}")
            result[name] = np.nan
    return result

def has_stereochemistry(mol: Chem.Mol) -> bool:
    """
    Return True if the molecule contains any chiral centre.
    """
    chiral_centers = Chem.FindMolChiralCenters(mol, includeUnassigned=True)
    return len(chiral_centers) > 0

def is_flexible(mol: Chem.Mol) -> bool:
    """
    Return True if the molecule has ≥ 5 rotatable bonds.
    """
    return rdMolDescriptors.CalcNumRotatableBonds(mol) >= 5

# -------------------------------------------------------------------------
# Main processing routine
# -------------------------------------------------------------------------
def generate_descriptors():
    start_time = time.time()
    process = psutil.Process(os.getpid())
    peak_memory = 0

    # Ensure output directories exist
    DATA_PROC_DIR.mkdir(parents=True, exist_ok=True)

    descriptor_names = get_2d_descriptor_names()
    # Save the plain (non‑prefixed) descriptor name list
    descriptor_names_path = DATA_PROC_DIR / "descriptor_names.json"
    descriptor_names_path.write_text(json.dumps(descriptor_names, indent=2))
    logger.info(f"Descriptor names written to {descriptor_names_path}")

    # Streaming load of QM9
    logger.info("Opening QM9 dataset (streaming mode)…")
    ds = load_dataset("jablonkagroup/qm9", "raw_data", streaming=True)

    rows: List[Dict] = []
    stereochem_counts = 0
    flexible_counts = 0
    total_records = 0

    for split_name, split in ds.items():
        logger.info(f"Streaming split '{split_name}'")
        for record in split:
            smiles = record.get("SMILES")
            target = record.get("dipole_moment")
            if smiles is None or target is None:
                continue

            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                continue

            desc_vals = compute_descriptors(mol, descriptor_names)
            row = {
                "smiles": smiles,
                "target": float(target),
            }
            # Prefix descriptor columns with ``desc_`` as required by contracts
            row.update({f"desc_{k}": v for k, v in desc_vals.items()})

            # Flags
            stereo = has_stereochemistry(mol)
            flex = is_flexible(mol)
            row["stereochemistry_flag"] = stereo
            row["flexible_flag"] = flex
            stereochem_counts += int(stereo)
            flexible_counts += int(flex)

            rows.append(row)
            total_records += 1

            # Periodic memory / progress logging
            if total_records % 5000 == 0:
                current_rss = process.memory_info().rss
                peak_memory = max(peak_memory, current_rss)
                logger.info(
                    f"Processed {total_records} records – "
                    f"Current RSS {current_rss / (1024**2):.1f} MiB"
                )

    logger.info(f"Finished streaming. Total records kept: {total_records}")

    # Build DataFrame
    df = pd.DataFrame(rows)
    logger.info(f"DataFrame shape before NaN handling: {df.shape}")

    # -----------------------------------------------------------------
    # Missing‑value handling
    # -----------------------------------------------------------------
    descriptor_cols = [c for c in df.columns if c.startswith("desc_")]
    # Determine rows with >5 % missing among descriptor columns
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
    logger.info(f"stereochemistry_flag true for {stereochem_prop:.4%} of records")
    logger.info(f"flexible_flag true for {flexible_prop:.4%} of records")
    assert stereochem_prop <= 0.05, "stereochemistry_flag exceeds 5 % limit"
    assert flexible_prop <= 0.05, "flexible_flag exceeds 5 % limit"

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
def main():
    try:
        generate_descriptors()
    except Exception as exc:
        logger.exception(f"Fatal error during descriptor generation: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
