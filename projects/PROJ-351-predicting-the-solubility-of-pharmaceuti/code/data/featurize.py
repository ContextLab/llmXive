"""
Task T012a: Featurize cleaned molecules into Morgan Fingerprints for Random Forest.

Loads cleaned RDKit Mol objects from data/processed/cleaned_graphs.pkl,
generates Morgan fingerprints (radius=2, 2048 bits) for each molecule,
and saves the resulting feature matrix and targets to data/processed/fingerprints.npz.

Dependencies:
- T005: Produces data/processed/cleaned_graphs.pkl
"""
import os
import sys
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

from data.preprocess import setup_logging
from config.seeds import get_seed

# Configure logging
logger = setup_logging("featurize")

INPUT_PATH = Path("data/processed/cleaned_graphs.pkl")
OUTPUT_PATH = Path("data/processed/fingerprints.npz")
FINGERPRINT_RADIUS = 2
FINGERPRINT_BITS = 2048

def load_cleaned_data(input_path: Path) -> List[Dict[str, Any]]:
    """Load the cleaned graphs pickle file."""
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T005 (preprocess.py) has been run successfully."
        )
    
    logger.info(f"Loading cleaned data from {input_path}...")
    with open(input_path, 'rb') as f:
        data = pickle.load(f)
    
    logger.info(f"Loaded {len(data)} molecules.")
    return data

def generate_morgan_fingerprint(smiles: str, radius: int, n_bits: int) -> np.ndarray:
    """
    Generate a Morgan fingerprint for a given SMILES string.
    
    Args:
        smiles: The SMILES string of the molecule.
        radius: The radius of the fingerprint (typically 2).
        n_bits: The number of bits in the fingerprint (typically 2048).
        
    Returns:
        A numpy array of shape (n_bits,) representing the fingerprint.
        
    Raises:
        ValueError: If the SMILES string is invalid.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES string: {smiles}")
    
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    # Convert to numpy array
    arr = np.zeros((n_bits,), dtype=np.int32)
    for i in range(n_bits):
        if fp[i] == 1:
            arr[i] = 1
    return arr

def featurize_dataset(data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert a list of cleaned molecule dictionaries into a feature matrix and target vector.
    
    Args:
        data: List of dictionaries containing 'smiles' and 'logS' keys.
        
    Returns:
        Tuple of (features, targets) where features is (N, 2048) and targets is (N,).
    """
    features = []
    targets = []
    skipped = 0

    for i, item in enumerate(data):
        smiles = item.get('smiles')
        logS = item.get('logS')

        if not smiles or logS is None:
            logger.warning(f"Skipping item {i}: missing SMILES or logS")
            skipped += 1
            continue

        try:
            fp = generate_morgan_fingerprint(smiles, FINGERPRINT_RADIUS, FINGERPRINT_BITS)
            features.append(fp)
            targets.append(float(logS))
        except ValueError as e:
            logger.warning(f"Skipping item {i} (SMILES: {smiles}): {e}")
            skipped += 1
            continue

    if len(features) == 0:
        raise RuntimeError("No valid molecules found to featurize. Check input data.")

    logger.info(f"Featurized {len(features)} molecules. Skipped {skipped}.")
    return np.vstack(features), np.array(targets)

def save_featurized_data(features: np.ndarray, targets: np.ndarray, output_path: Path):
    """Save the feature matrix and targets to an NPZ file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving fingerprints to {output_path}...")
    np.savez_compressed(
        output_path,
        features=features,
        targets=targets
    )
    
    # Verify file was written and is not empty
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info(f"Successfully saved {len(features)} fingerprints to {output_path}")
    else:
        raise IOError(f"Failed to write output file: {output_path}")

def main():
    """Main entry point for the featurization task."""
    logger.info("Starting Morgan Fingerprint Featurization (T012a)...")
    
    # Load data
    data = load_cleaned_data(INPUT_PATH)
    
    # Featurize
    X, y = featurize_dataset(data)
    
    # Save
    save_featurized_data(X, y, OUTPUT_PATH)
    
    logger.info("Featurization complete.")

if __name__ == "__main__":
    main()
