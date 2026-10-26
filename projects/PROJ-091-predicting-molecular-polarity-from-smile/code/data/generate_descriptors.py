"""
T101 – Generate 2‑D descriptor matrix for QM9.

This script fulfills the requirements of task **T101**:
* Downloads the QM9 dataset using the verified `qm9pack` library.
* Computes ≥ 200 RDKit 2‑D topological descriptors per molecule,
  explicitly excluding any TPSA‑related descriptors and all SMARTS‑based
  functional‑group counts.
* Imputes NaN descriptor values with the column median; rows with > 5 %
  missing descriptor values are dropped and logged.
* Adds boolean flags:
  - ``stereochemistry_flag`` – true when the molecule has undefined
    stereochemistry (checked via presence of chiral centers vs SMILES markers).
  - ``flexible_flag`` – true when the rotatable‑bond count ≥ 5.
* Persists the ordered list of descriptor names to
  ``data/processed/descriptor_names.json``.
* Writes the descriptor matrix to ``data/processed/descriptors.parquet``.
* Logs total runtime, peak memory usage and basic statistics.
* Asserts that preprocessing completes within 15 minutes.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

import psutil
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

import qm9pack  # verified real data source

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
DATA_PROC_DIR = Path("data") / "processed"

DESCRIPTOR_EXCLUSIONS = {
    "TPSA", "TPSA_E", "TPSA_E2", "TPSA_E3", "TPSA_E4", "TPSA_E5",
    "TPSA_E6", "TPSA_E7", "TPSA_E8", "TPSA_E9", "TPSA_E10",
}

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def get_2d_descriptor_names() -> List[str]:
    """
    Return a list of RDKit 2‑D descriptor names, excluding TPSA, 3D, and SMARTS counts.
    """
    all_desc = [
        name
        for name in dir(Descriptors)
        if not name.startswith("_") and callable(getattr(Descriptors, name))
    ]

    filtered = []
    for name in all_desc:
        if name in DESCRIPTOR_EXCLUSIONS:
            continue
        if "3D" in name:
            continue
        if name.startswith("fr_"):
            continue
        filtered.append(name)

    logger.info(f"Found {len(all_desc)} total RDKit descriptors, {len(filtered)} after filtering.")
    return filtered

def check_undefined_stereo(smiles: str, mol: Chem.Mol) -> bool:
    """
    Flag molecules with undefined stereochemistry.
    True if the molecule has chiral centers but the SMILES lacks stereochemical markers.
    """
    has_centers = mol.GetNumChiralCenters() > 0 or mol.GetNumStereoCenters() > 0
    has_markers = any(c in smiles for c in ['@', '/', '\\'])
    return has_centers and not has_markers

def is_flexible(mol: Chem.Mol) -> bool:
    """Return True if the molecule has ≥ 5 rotatable bonds."""
    return rdMolDescriptors.CalcNumRotatableBonds(mol) >= 5

# -------------------------------------------------------------------------
# Main processing routine
# -------------------------------------------------------------------------
def generate_descriptors() -> None:
    start_time = time.time()
    process = psutil.Process(os.getpid())
    peak_memory = 0

    DATA_PROC_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Determine descriptor set
    descriptor_names = get_2d_descriptor_names()
    descriptor_names_path = DATA_PROC_DIR / "descriptor_names.json"
    descriptor_names_path.write_text(json.dumps(descriptor_names, indent=2))
    logger.info(f"Descriptor names written to {descriptor_names_path}")

    # 2. Load QM9 dataset
    logger.info("Loading QM9 dataset via qm9pack...")
    try:
        df_raw = qm9pack.get_data("qm9")
    except Exception as e:
        logger.error(f"Failed to load QM9 data: {e}")
        raise

    df_raw.columns = [c.lower() for c in df_raw.columns]
    SMILES_COL = "smiles"
    TARGET_COL = "dipole_debye"

    if SMILES_COL not in df_raw.columns or TARGET_COL not in df_raw.columns:
        raise ValueError(f"QM9 data must contain '{SMILES_COL}' and '{TARGET_COL}'.")

    # Pre-bind functions for performance
    desc_funcs = {name: getattr(Descriptors, name) for name in descriptor_names}

    # 3. Process molecules
    rows = []
    smiles_vals = df_raw[SMILES_COL].values
    target_vals = df_raw[TARGET_COL].values

    logger.info(f"Processing {len(df_raw)} molecules...")
    for idx in range(len(df_raw)):
        smiles = smiles_vals[idx]
        target = target_vals[idx]

        if pd.isna(smiles) or pd.isna(target):
            continue

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue

        # Compute descriptors
        desc_vals = {}
        for name, func in desc_funcs.items():
            try:
                val = func(mol)
                desc_vals[name] = float(val) if not (pd.isna(val) or np.isinf(val)) else np.nan
            except:
                desc_vals[name] = np.nan

        row = {
            "smiles": smiles,
            "target": float(target),
            "stereochemistry_flag": check_undefined_stereo(smiles, mol),
            "flexible_flag": is_flexible(mol),
            **desc_vals
        }
        rows.append(row)

        if (idx + 1) % 10000 == 0:
            current_rss = process.memory_info().rss
            peak_memory = max(peak_memory, current_rss)
            logger.info(f"Processed {idx + 1}/{len(df_raw)} records – RSS {current_rss / (1024**2):.1f} MiB")

    # 4. DataFrame and NaN handling
    df = pd.DataFrame(rows)
    descriptor_cols = descriptor_names

    # Drop rows with > 5% NaNs
    missing_mask = df[descriptor_cols].isna().mean(axis=1) > 0.05
    dropped_count = missing_mask.sum()
    if dropped_count > 0:
        logger.info(f"Dropping {dropped_count} rows with > 5% missing descriptors.")
        df = df[~missing_mask].reset_index(drop=True)

    # Impute remaining NaNs with median
    for col in descriptor_cols:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())

    # 5. Flag proportion checks
    stereo_prop = df["stereochemistry_flag"].mean()
    flex_prop = df["flexible_flag"].mean()
    logger.info(f"Stereochem flag proportion: {stereo_prop:.4%}")
    logger.info(f"Flexible flag proportion: {flex_prop:.4%}")

    # Verification of constraints (as per T101 requirements)
    assert stereo_prop <= 0.05, f"stereochemistry_flag exceeds 5% limit: {stereo_prop:.4%}"
    assert flex_prop <= 0.05, f"flexible_flag exceeds 5% limit: {flex_prop:.4%}"

    # 6. Persist results
    descriptors_path = DATA_PROC_DIR / "descriptors.parquet"
    df.to_parquet(descriptors_path, index=False)
    logger.info(f"Wrote descriptor matrix to {descriptors_path}. Shape: {df.shape}")

    elapsed = time.time() - start_time
    logger.info(f"Total runtime: {elapsed:.2f} s")
    logger.info(f"Peak RSS memory: {peak_memory / (1024**2):.1f} MiB")
    assert elapsed <= 15 * 60, f"Preprocessing exceeded 15 min limit: {elapsed:.2f} s"

def main() -> None:
    try:
        generate_descriptors()
    except Exception as exc:
        logger.exception(f"Fatal error: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()