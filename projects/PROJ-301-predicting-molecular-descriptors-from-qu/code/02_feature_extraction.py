"""
Module: 02_feature_extraction.py
Description:
    Generates 2‑D Morgan fingerprints and simple 3‑D graph‑based features from the
    cleaned QM9 parquet produced by ``01_data_download.py``. The resulting NumPy
    arrays and CSV label file are written to ``data/processed``.
All debug ``print`` statements have been removed and type hints are provided for
every public function.
"""
import argparse
import gc
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem

logger = logging.getLogger(__name__)


def generate_morgan_fingerprint(
    mol: Chem.Mol, n_bits: int = 2048, radius: int = 2
) -> np.ndarray:
    """
    Compute a Morgan fingerprint (circular fingerprint) for a molecule.

    Args:
        mol: RDKit molecule object.
        n_bits: Length of the fingerprint vector.
        radius: Radius of the circular substructures.

    Returns:
        NumPy array of dtype ``np.uint8`` containing the fingerprint bits.
    """
    if mol is None:
        raise ValueError("Cannot generate fingerprint for a None molecule.")
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.uint8)
    AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
    return arr


def extract_3d_features(mol: Chem.Mol) -> np.ndarray:
    """
    Extract a simple set of 3‑D features from a molecule:
        * Atomic numbers (one per atom)
        * Hybridization encoded as integers (sp, sp2, sp3, etc.)
        * Pairwise Euclidean distances binned into a fixed histogram.

    The feature vector is padded/truncated to a fixed size for compatibility with
    downstream models.

    Args:
        mol: RDKit molecule with 3‑D coordinates.

    Returns:
        1‑D NumPy array of floats.
    """
    if mol is None:
        raise ValueError("Cannot extract 3D features from a None molecule.")

    # Ensure the molecule has a conformer with 3‑D coordinates
    if not mol.GetNumConformers():
        raise ValueError("Molecule does not contain 3D coordinates.")

    conf = mol.GetConformer()
    atom_nums = np.array([atom.GetAtomicNum() for atom in mol.GetAtoms()], dtype=np.float32)

    # Hybridization encoding
    hyb_map = {
        Chem.rdchem.HybridizationType.SP: 1,
        Chem.rdchem.HybridizationType.SP2: 2,
        Chem.rdchem.HybridizationType.SP3: 3,
        Chem.rdchem.HybridizationType.SP3D: 4,
        Chem.rdchem.HybridizationType.SP3D2: 5,
    }
    hyb = np.array(
        [hyb_map.get(atom.GetHybridization(), 0) for atom in mol.GetAtoms()], dtype=np.float32
    )

    # Pairwise distances
    n = mol.GetNumAtoms()
    dists = []
    for i in range(n):
        pos_i = np.array(conf.GetAtomPosition(i))
        for j in range(i + 1, n):
            pos_j = np.array(conf.GetAtomPosition(j))
            dists.append(np.linalg.norm(pos_i - pos_j))
    dists = np.array(dists, dtype=np.float32)
    # Bin distances into a histogram of 10 bins up to 5 Å
    hist, _ = np.histogram(dists, bins=10, range=(0.0, 5.0))
    hist = hist.astype(np.float32)

    # Concatenate all parts
    feature_vec = np.concatenate([atom_nums, hyb, hist])
    # Pad/truncate to a deterministic length (e.g., 256)
    target_len = 256
    if feature_vec.size < target_len:
        feature_vec = np.pad(feature_vec, (0, target_len - feature_vec.size))
    else:
        feature_vec = feature_vec[:target_len]
    return feature_vec


def load_and_process_data(
    cleaned_parquet: Path,
    fingerprint_bits: int = 2048,
) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """
    Load the cleaned QM9 parquet, generate 2‑D fingerprints and 3‑D features,
    and return the feature matrices together with the label dataframe.

    Args:
        cleaned_parquet: Path to ``molecules_cleaned.parquet``.
        fingerprint_bits: Length of the Morgan fingerprint.

    Returns:
        Tuple containing:
            * 2‑D feature matrix (shape: N × fingerprint_bits)
            * 3‑D feature matrix (shape: N × 256)
            * DataFrame of labels (dipole, HOMO, LUMO)
    """
    logger.info("Loading cleaned data from %s", cleaned_parquet)
    df = pd.read_parquet(cleaned_parquet)

    # Expected label columns
    label_cols = ["dipole_moment", "homo", "lumo"]
    labels = df[label_cols].reset_index(drop=True)

    # Convert SMILES to RDKit molecules
    mols = []
    for idx, smi in enumerate(df["smiles"]):
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            logger.warning("Failed to parse SMILES at index %d: %s", idx, smi)
            continue
        # Add explicit hydrogens and generate a 3‑D conformer
        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, AllChem.ETKDG())
        AllChem.UFFOptimizeMolecule(mol)
        mols.append(mol)

    logger.info("Generated %d RDKit molecules.", len(mols))

    # 2‑D fingerprints
    fp_array = np.vstack([generate_morgan_fingerprint(m, n_bits=fingerprint_bits) for m in mols])
    logger.info("2D feature matrix shape: %s", fp_array.shape)

    # 3‑D features
    feat3d_array = np.vstack([extract_3d_features(m) for m in mols])
    logger.info("3D feature matrix shape: %s", feat3d_array.shape)

    # Align labels with the molecules we successfully processed
    aligned_labels = labels.iloc[: len(mols)].reset_index(drop=True)

    # Explicit garbage collection to keep memory footprint low
    gc.collect()

    return fp_array, feat3d_array, aligned_labels


def main() -> None:
    """
    Execute the feature‑extraction pipeline:
        1. Load cleaned QM9 data.
        2. Generate 2‑D Morgan fingerprints.
        3. Generate simple 3‑D graph features.
        4. Write NumPy arrays and CSV labels to ``data/processed``.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s – %(message)s",
    )

    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    cleaned_path = processed_dir / "molecules_cleaned.parquet"
    fp_path = processed_dir / "features_2d.npy"
    feat3d_path = processed_dir / "features_3d.npy"
    labels_path = processed_dir / "labels.csv"

    fp_matrix, feat3d_matrix, labels_df = load_and_process_data(cleaned_path)

    np.save(fp_path, fp_matrix)
    logger.info("Saved 2D features to %s", fp_path)
    np.save(feat3d_path, feat3d_matrix)
    logger.info("Saved 3D features to %s", feat3d_path)
    labels_df.to_csv(labels_path, index=False)
    logger.info("Saved labels to %s", labels_path)


if __name__ == "__main__":
    main()
