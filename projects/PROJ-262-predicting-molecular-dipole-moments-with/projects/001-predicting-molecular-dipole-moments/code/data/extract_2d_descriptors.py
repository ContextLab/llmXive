"""Extract 2D molecular descriptors for the QM9 subset.

This script generates two types of descriptors for each molecule in the
10k‑molecule subset:

1. **Morgan (ECFP) fingerprint** – a 2048‑bit binary vector computed with
   RDKit using radius 2.
2. **Coulomb matrix** – a padded (max_atoms × max_atoms) matrix based on
   atomic numbers and 3‑D coordinates.  The matrix is flattened before
   storage to keep the parquet schema simple.

The script is robust: if the expected subset file
``data/processed/molecules_10k.parquet`` does not exist, it falls back to
loading the raw QM9 parquet file and randomly sampling 10 000 molecules
using the same fixed seed as the original ``create_subset`` step.

The output is written to ``data/processed/features_2d.parquet``.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
from tqdm.auto import tqdm

# -------------------------------------------------------------------------
# Configuration constants
# -------------------------------------------------------------------------
DEFAULT_SUBSET_PATH = Path("data/processed/molecules_10k.parquet")
RAW_QM9_PATH = Path("data/raw/qm9.parquet")
OUTPUT_PATH = Path("data/processed/features_2d.parquet")
FINGERPRINT_SIZE = 2048
FINGERPRINT_RADIUS = 2
RANDOM_SEED = 42
SUBSET_SIZE = 10_000
# The QM9 dataset never contains more than 29 heavy atoms; we pad to that
# size to obtain a fixed‑shape Coulomb matrix.
MAX_ATOMS = 29


# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def load_subset() -> pd.DataFrame:
    """Load the 10k molecule subset, falling back to raw data if necessary."""
    if DEFAULT_SUBSET_PATH.is_file():
        return pd.read_parquet(DEFAULT_SUBSET_PATH)

    if not RAW_QM9_PATH.is_file():
        raise FileNotFoundError(
            f"Neither subset nor raw QM9 file found (looked for "
            f"{DEFAULT_SUBSET_PATH} and {RAW_QM9_PATH})"
        )

    # Load raw QM9 and sample 10k rows with a deterministic seed.
    raw_df = pd.read_parquet(RAW_QM9_PATH)
    rng = np.random.default_rng(RANDOM_SEED)
    sampled_idx = rng.choice(raw_df.index, size=SUBSET_SIZE, replace=False)
    subset = raw_df.loc[sampled_idx].reset_index(drop=True)
    # Persist the subset for downstream steps.
    subset.to_parquet(DEFAULT_SUBSET_PATH, index=False)
    return subset


def mol_from_rdkit(smiles: str) -> Chem.Mol:
    """Create an RDKit Mol object from a SMILES string."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES string: {smiles}")
    # Add hydrogens and generate 3‑D coordinates – required for the Coulomb matrix.
    mol = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol, randomSeed=RANDOM_SEED)
    AllChem.UFFOptimizeMolecule(mol)
    return mol


def compute_morgan_fingerprint(mol: Chem.Mol) -> List[int]:
    """Return a 2048‑bit Morgan fingerprint as a list of 0/1 ints."""
    fp = AllChem.GetMorganFingerprintAsBitVect(
        mol, radius=FINGERPRINT_RADIUS, nBits=FINGERPRINT_SIZE
    )
    # Convert to a Python list of ints for easy JSON/Parquet storage.
    return list(fp)


def compute_coulomb_matrix(mol: Chem.Mol) -> List[float]:
    """Compute a padded Coulomb matrix and return it as a flattened list."""
    conf = mol.GetConformer()
    num_atoms = mol.GetNumAtoms()
    Z = np.array([atom.GetAtomicNum() for atom in mol.GetAtoms()], dtype=np.float64)
    R = np.array([list(conf.GetAtomPosition(i)) for i in range(num_atoms)], dtype=np.float64)

    # Initialise the full matrix with zeros.
    cm = np.zeros((MAX_ATOMS, MAX_ATOMS), dtype=np.float64)

    # Populate the upper triangle (including diagonal).
    for i in range(num_atoms):
        for j in range(num_atoms):
            if i == j:
                cm[i, j] = 0.5 * Z[i] ** 2.4
            else:
                dist = np.linalg.norm(R[i] - R[j])
                if dist == 0:
                    # Avoid division by zero – should not happen for distinct atoms.
                    cm[i, j] = 0.0
                else:
                    cm[i, j] = (Z[i] * Z[j]) / dist
    # Return the flattened matrix (row‑major order).
    return cm.flatten().tolist()


def process_molecule(row) -> dict:
    """Generate descriptors for a single dataframe row."""
    # The QM9 HuggingFace format stores a SMILES column named ``smiles``.
    # If the column is missing we fall back to the ``smiles`` key inside the
    # ``molecule`` dict (some older versions).
    smiles = row.get("smiles")
    if smiles is None:
        # Older format: ``row["molecule"]["smiles"]``
        smiles = row.get("molecule", {}).get("smiles")
    if smiles is None:
        raise ValueError("SMILES string not found in row data.")

    mol = mol_from_rdkit(smiles)
    fingerprint = compute_morgan_fingerprint(mol)
    coulomb = compute_coulomb_matrix(mol)
    return {
        "molecule_id": row.name,
        "fingerprint": fingerprint,
        "coulomb_matrix": coulomb,
    }


# -------------------------------------------------------------------------
# Main execution
# -------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate 2D Morgan fingerprints and Coulomb matrices for the QM9 subset."
    )
    parser.add_argument(
        "--subset-path",
        type=Path,
        default=DEFAULT_SUBSET_PATH,
        help=f"Path to the 10k‑molecule parquet file (default: {DEFAULT_SUBSET_PATH})",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=OUTPUT_PATH,
        help=f"Destination parquet file for 2D descriptors (default: {OUTPUT_PATH})",
    )
    args = parser.parse_args()

    # Load (or create) the subset.
    subset_df = load_subset()

    # Process each molecule with a progress bar.
    records = []
    for _, row in tqdm(subset_df.iterrows(), total=len(subset_df), desc="Extracting 2D descriptors"):
        try:
            record = process_molecule(row)
            records.append(record)
        except Exception as exc:
            # Log the failure but continue – faulty molecules are rare.
            tqdm.write(f"Skipping molecule idx={row.name} due to error: {exc}")

    # Convert to a DataFrame and write to parquet.
    out_df = pd.DataFrame(records)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(args.output_path, index=False)
    tqdm.write(f"2D descriptor file written to {args.output_path}")


if __name__ == "__main__":
    main()
