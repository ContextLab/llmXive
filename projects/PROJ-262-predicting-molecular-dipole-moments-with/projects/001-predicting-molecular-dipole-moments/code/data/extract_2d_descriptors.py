"""extract_2d_descriptors.py
-------------------------------------------------
Implements 2‑D molecular descriptors required for US1:
* Morgan (ECFP) fingerprints (radius=2, 2048 bits)
* Coulomb matrix (upper‑triangular flattened) derived from 3‑D
  coordinates (generated on‑the‑fly if missing).

The script reads the 10 k molecule subset created by
`create_subset.py` (expected at
``data/processed/molecules_10k.parquet``) which must contain at
least a ``smiles`` column.  For each molecule it computes the
descriptors and writes a parquet file
``data/processed/features_2d.parquet`` with three columns:

* ``molecule_id`` – integer index (0‑based)
* ``fingerprint`` – list of 0/1 ints (length 2048)
* ``coulomb_matrix`` – list of floats (upper‑triangular of the
  Coulomb matrix)

The module can be executed directly:
    python extract_2d_descriptors.py
and will produce the output file in the repository’s ``data/processed``
directory.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

# RDKit imports – the rdkit‑pypi wheel is listed in requirements.txt
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_subset() -> pd.DataFrame:
    """
    Load the 10 k molecule subset created by ``create_subset.py``.
    The expected location is ``data/processed/molecules_10k.parquet``.
    """
    subset_path = (
        Path(__file__).resolve().parents[2] / "data" / "processed" / "molecules_10k.parquet"
    )
    if not subset_path.is_file():
        raise FileNotFoundError(f"Subset file not found at {subset_path}")
    return pd.read_parquet(subset_path)


def _smiles_to_mol(smiles: str) -> Chem.Mol:
    """
    Convert a SMILES string to an RDKit Mol object.  If the conversion
    fails, a ``ValueError`` is raised.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES string: {smiles}")
    # Add hydrogens – required for a realistic 3‑D geometry later.
    mol = Chem.AddHs(mol)
    return mol


def _ensure_3d_coordinates(mol: Chem.Mol) -> Chem.Mol:
    """
    Ensure that the molecule has a 3‑D conformer.  If none exists, an
    embedding is performed (with a fixed random seed for reproducibility).
    """
    if mol.GetNumConformers() == 0:
        # Use a deterministic seed for reproducibility
        params = AllChem.ETKDGv3()
        params.randomSeed = 42
        AllChem.EmbedMolecule(mol, params=params)
        AllChem.UFFOptimizeMolecule(mol)
    return mol


def compute_morgan_fingerprint(mol: Chem.Mol, radius: int = 2, n_bits: int = 2048) -> List[int]:
    """
    Compute a binary Morgan (ECFP) fingerprint and return it as a list of ints.
    """
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.int8)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr.tolist()


def compute_coulomb_matrix(mol: Chem.Mol) -> List[float]:
    """
    Compute the Coulomb matrix for a molecule using its 3‑D coordinates.
    The matrix is flattened by taking the upper‑triangular (including diagonal)
    elements, which is a common fixed‑size representation for variable‑size
    molecules.

    Reference for diagonal term: 0.5 * Z_i ^ 2.4
    """
    mol = _ensure_3d_coordinates(mol)
    conf = mol.GetConformer()
    n_atoms = mol.GetNumAtoms()
    if n_atoms == 0:
        return []

    # Atomic numbers (Z) vector
    Z = np.array([atom.GetAtomicNum() for atom in mol.GetAtoms()], dtype=float)

    # Positions matrix (R)
    R = np.array([conf.GetAtomPosition(i) for i in range(n_atoms)], dtype=float)

    # Initialize Coulomb matrix
    M = np.zeros((n_atoms, n_atoms), dtype=float)

    for i in range(n_atoms):
        for j in range(i, n_atoms):
            if i == j:
                M[i, j] = 0.5 * (Z[i] ** 2.4)
            else:
                dist = np.linalg.norm(R[i] - R[j])
                if dist > 0:
                    val = (Z[i] * Z[j]) / dist
                else:
                    val = 0.0
                M[i, j] = M[j, i] = val

    # Flatten upper‑triangular part
    triu_idx = np.triu_indices(n_atoms)
    return M[triu_idx].tolist()


# ----------------------------------------------------------------------
# Main processing routine
# ----------------------------------------------------------------------


def generate_2d_features() -> pd.DataFrame:
    """
    Load the subset, compute fingerprints and Coulomb matrices,
    and return a DataFrame ready to be written to disk.
    """
    df = _load_subset()

    # Expect a column named 'smiles'; raise a clear error otherwise.
    if "smiles" not in df.columns:
        raise KeyError("Input dataframe must contain a 'smiles' column.")

    records = []
    for idx, smiles in enumerate(df["smiles"]):
        try:
            mol = _smiles_to_mol(smiles)
            fp = compute_morgan_fingerprint(mol)
            cm = compute_coulomb_matrix(mol)
            records.append(
                {
                    "molecule_id": idx,
                    "fingerprint": fp,
                    "coulomb_matrix": cm,
                }
            )
        except Exception as exc:
            # Log the problem but continue processing other molecules.
            print(f"[WARN] Skipping molecule {idx} ({smiles}): {exc}", file=sys.stderr)

    return pd.DataFrame.from_records(records)


def write_features(df: pd.DataFrame) -> None:
    """
    Write the DataFrame to ``data/processed/features_2d.parquet``.
    """
    out_path = (
        Path(__file__).resolve().parents[2] / "data" / "processed" / "features_2d.parquet"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    print(f"[INFO] 2‑D feature file written to {out_path}")


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------


if __name__ == "__main__":
    features_df = generate_2d_features()
    write_features(features_df)
