"""
T023a: ECFP Collinearity Check

Calculates Pearson correlation for ECFP bits on the training set.
Flags bits with r >= 0.9.
Outputs: data/processed/collinearity_flags.json
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem

# Configure logging to match project standard
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
INPUT_FILE = DATA_PROCESSED / "train_val_test.csv"
OUTPUT_FILE = DATA_PROCESSED / "collinearity_flags.json"

# Parameters
RADIUS = 2
N_BITS = 2048
THRESHOLD = 0.9

def load_processed_data() -> pd.DataFrame:
    """Load the split dataset containing training molecules."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}. "
            "Run code/split.py and code/merge_split.py first."
        )
    df = pd.read_csv(INPUT_FILE)
    # Filter for training set only as per task description
    if 'split' in df.columns:
        train_df = df[df['split'] == 'train'].reset_index(drop=True)
    else:
        # Fallback if split column missing, assume all are training
        train_df = df.copy()
        logger.warning("No 'split' column found. Assuming all data is training set.")
    
    if 'smi' not in train_df.columns:
        raise ValueError("Input file missing 'smi' column.")
    
    logger.info(f"Loaded {len(train_df)} molecules for collinearity check.")
    return train_df

def smiles_to_ecfp_bitvec(smiles: str) -> np.ndarray:
    """
    Convert SMILES to ECFP4 bit vector (2048 bits).
    Returns a numpy array of 0s and 1s.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    # Get Morgan fingerprint as bit vector
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=RADIUS, nBits=N_BITS)
    
    # Convert to numpy array
    arr = np.zeros(N_BITS, dtype=int)
    for idx in fp.GetOnBits():
        arr[idx] = 1
    return arr

def calculate_correlation_matrix(bit_vectors: List[np.ndarray]) -> np.ndarray:
    """
    Calculate the Pearson correlation matrix of the bit vectors.
    Shape: (N_BITS, N_BITS)
    """
    # Stack into a matrix: (N_BITS, N_SAMPLES)
    # Transpose to (N_SAMPLES, N_BITS) for corrcoef
    data_matrix = np.array(bit_vectors).T  # Shape: (N_BITS, N_SAMPLES)
    
    # Calculate Pearson correlation
    # corrcoef returns correlation matrix of variables (rows)
    corr_matrix = np.corrcoef(data_matrix)
    
    return corr_matrix

def identify_flagged_bits(corr_matrix: np.ndarray) -> Dict[str, Any]:
    """
    Identify bits that have correlation >= 0.9 with any other bit.
    Returns a dictionary with flagged bits and max correlation.
    """
    n_bits = corr_matrix.shape[0]
    flagged_bits = set()
    max_corr = 0.0

    # Iterate upper triangle (excluding diagonal)
    # We only care if a bit is highly correlated with ANY other bit
    for i in range(n_bits):
        for j in range(i + 1, n_bits):
            r = corr_matrix[i, j]
            if np.isnan(r):
                continue
            if abs(r) > max_corr:
                max_corr = abs(r)
            if abs(r) >= THRESHOLD:
                flagged_bits.add(i)
                flagged_bits.add(j)

    logger.info(f"Total bits: {n_bits}")
    logger.info(f"Flagged bits (|r| >= {THRESHOLD}): {len(flagged_bits)}")
    logger.info(f"Max correlation observed: {max_corr:.4f}")

    return {
        "flagged_bits": sorted(list(flagged_bits)),
        "max_correlation": float(max_corr),
        "threshold_used": THRESHOLD,
        "n_bits_total": n_bits,
        "n_samples": corr_matrix.shape[1]
    }

def main():
    logger.info("Starting T023a: ECFP Collinearity Check")
    
    # Ensure output directory exists
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    try:
        df = load_processed_data()
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)

    if len(df) == 0:
        logger.error("No training data found. Cannot compute correlations.")
        sys.exit(1)

    # 2. Generate ECFP Bit Vectors
    logger.info(f"Generating ECFP4 fingerprints for {len(df)} molecules...")
    bit_vectors = []
    skipped = 0
    
    for idx, row in df.iterrows():
        smi = row['smi']
        bv = smiles_to_ecfp_bitvec(smi)
        if bv is None:
            skipped += 1
            if skipped % 1000 == 0:
                logger.debug(f"Skipped {skipped} invalid SMILES so far...")
        else:
            bit_vectors.append(bv)
    
    if len(bit_vectors) < 2:
        logger.error("Insufficient valid molecules to calculate correlation matrix.")
        sys.exit(1)
    
    logger.info(f"Successfully generated fingerprints for {len(bit_vectors)} molecules.")

    # 3. Calculate Correlation Matrix
    logger.info("Calculating Pearson correlation matrix...")
    # Note: For 2048x2048, this is computationally feasible in RAM
    try:
        corr_matrix = calculate_correlation_matrix(bit_vectors)
    except Exception as e:
        logger.error(f"Failed to calculate correlation matrix: {e}")
        sys.exit(1)

    # 4. Identify Flagged Bits
    result = identify_flagged_bits(corr_matrix)

    # 5. Save Output
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Collinearity flags written to {OUTPUT_FILE}")
    logger.info("T023a completed successfully.")

if __name__ == "__main__":
    main()
