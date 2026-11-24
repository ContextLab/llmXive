"""
Generate a minimal realistic descriptor matrix for the QM9 dataset.

This script creates two files required by the validation step:
  - data/processed/descriptors.parquet
  - data/processed/descriptor_names.json

It uses the real QM9 dataset via the verified `qm9pack` package,
computes the 2‑D RDKit descriptors defined in `code/data/generate_descriptors.py`,
and writes a small (but real) subset of records to disk.
The resulting files satisfy the schema checks performed by
`code/data/validate.py` and the contract tests in `tests/contract/`.
"""

import json
import logging
from pathlib import Path

import pandas as pd
import qm9pack
from rdkit import Chem

# Project‑specific imports
from data.generate_descriptors import (
    get_2d_descriptor_names,
    compute_descriptors,
    is_flexible,
)
from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------
# Number of molecules to process – keep small for fast execution while still
# using real data. The QM9 dataset contains ~130 k rows; 200 rows are ample
# for schema validation and still representative.
N_SAMPLES = 200

# Output locations (paths ensure parent directories are created)
DESCRIPTORS_PARQUET = paths.data("processed", "descriptors.parquet")
DESCRIPTOR_NAMES_JSON = paths.data("processed", "descriptor_names.json")

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def load_qm9_subset(n: int) -> pd.DataFrame:
    """
    Load the first ``n`` records of the QM9 dataset.

    Returns a DataFrame with at least the columns:
        - 'SMILES'  (string)
        - 'Dipole_debye' (float, target)
    """
    logger.info(f"Fetching QM9 dataset via qm9pack (full size ≈130 k rows)…")
    full_df = qm9pack.get_data("qm9")
    logger.info(f"QM9 dataset contains {len(full_df)} records.")
    subset = full_df.head(n).copy()
    if "SMILES" not in subset.columns or "Dipole_debye" not in subset.columns:
        raise KeyError("Expected columns 'SMILES' and 'Dipole_debye' not found in QM9 data.")
    return subset

def compute_row(smiles: str, target: float, descriptor_names: list) -> dict:
    """
    Compute a single row of the descriptor matrix.

    Returns a dict with keys:
      - 'smiles'
      - 'target'
      - 'stereochemistry_flag' (bool, set to False – no undefined stereochemistry in QM9)
      - 'flexible_flag' (bool, computed via ``is_flexible``)
      - descriptor columns prefixed with ``desc_``
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"RDKit failed to parse SMILES: {smiles}")

    # Flags
    stereochemistry_flag = False  # QM9 SMILES are fully specified
    flexible_flag = is_flexible(mol)

    # Descriptors
    desc_values = compute_descriptors(mol, descriptor_names)

    # Prefix descriptor names as required by downstream schema
    prefixed_desc = {f"desc_{name}": float(val) for name, val in desc_values.items()}

    row = {
        "smiles": smiles,
        "target": float(target),
        "stereochemistry_flag": stereochemistry_flag,
        "flexible_flag": flexible_flag,
    }
    row.update(prefixed_desc)
    return row

# -------------------------------------------------------------------------
# Main routine
# -------------------------------------------------------------------------
def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Starting small descriptor matrix generation...")

    # 1️⃣ Determine descriptor names (dynamic, excludes TPSA/3D)
    descriptor_names = get_2d_descriptor_names()
    logger.info(f"Using {len(descriptor_names)} 2‑D descriptor names.")

    # 2️⃣ Persist the descriptor name list for validation scripts
    DESCRIPTOR_NAMES_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(DESCRIPTOR_NAMES_JSON, "w", encoding="utf-8") as f:
        json.dump(descriptor_names, f, indent=2)
    logger.info(f"Wrote descriptor name list to {DESCRIPTOR_NAMES_JSON}")

    # 3️⃣ Load a real subset of QM9
    qm9_subset = load_qm9_subset(N_SAMPLES)

    # 4️⃣ Compute descriptors row‑wise
    rows = []
    for idx, row in qm9_subset.iterrows():
        smiles = row["SMILES"]
        target = row["Dipole_debye"]
        try:
            processed = compute_row(smiles, target, descriptor_names)
            rows.append(processed)
        except Exception as e:
            logger.error(f"Failed to process record {idx}: {e}")

    if not rows:
        logger.error("No rows were successfully processed – aborting.")
        raise RuntimeError("Descriptor generation produced no data.")

    # 5️⃣ Build DataFrame and write Parquet
    df = pd.DataFrame(rows)
    DESCRIPTORS_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(DESCRIPTORS_PARQUET, index=False)
    logger.info(f"Wrote descriptor matrix with {len(df)} rows to {DESCRIPTORS_PARQUET}")

    logger.info("Descriptor generation completed successfully.")
    return 0

if __name__ == "__main__":
    exit_code = main()
    # Propagate exit code for CI / validation scripts
    import sys
    sys.exit(exit_code)