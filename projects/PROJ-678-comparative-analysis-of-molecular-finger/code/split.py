"""
Greedy Maximal Dissimilarity Split Implementation.

This module implements the Greedy Maximal Dissimilarity Split algorithm
for generating 5 folds with Tanimoto similarity < 0.85.
"""

import numpy as np
import pandas as pd
import logging
import os
from pathlib import Path
from typing import List, Tuple, Dict, Optional

from rdkit import DataStructs
from rdkit import Chem

# Import from project utilities and constants
from utils import init_random_seed, get_logger
from constants import TANIMOTO_THRESHOLD, N_FOLDS, MORGAN_RADIUS, MORGAN_BITS
from fingerprints import generate_morgan_fingerprint, calculate_tanimoto_similarity

# Setup logging
logger = get_logger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/split_log.txt'),
        logging.StreamHandler()
    ]
)

def load_fingerprints(csv_path: str) -> Tuple[pd.DataFrame, List]:
    """
    Load compounds and generate Morgan fingerprints.

    Args:
        csv_path: Path to the filtered compounds CSV.

    Returns:
        Tuple of (DataFrame with compounds, list of RDKit fingerprints).
    """
    logger.info(f"Loading compounds from {csv_path}")
    df = pd.read_csv(csv_path)

    if 'smiles' not in df.columns:
        raise ValueError("CSV must contain a 'smiles' column")

    fingerprints = []
    valid_indices = []

    for idx, row in df.iterrows():
        mol = Chem.MolFromSmiles(row['smiles'])
        if mol is None:
            logger.warning(f"Invalid SMILES at index {idx}, skipping")
            continue

        fp = generate_morgan_fingerprint(mol, radius=MORGAN_RADIUS, n_bits=MORGAN_BITS)
        fingerprints.append(fp)
        valid_indices.append(idx)

    logger.info(f"Generated {len(fingerprints)} valid fingerprints from {len(df)} rows")
    return df.iloc[valid_indices].reset_index(drop=True), fingerprints

def greedy_maximal_dissimilarity_split(
    fingerprints: List,
    n_folds: int = 5,
    threshold: float = TANIMOTO_THRESHOLD,
    min_test_size: int = 20
) -> Tuple[List[Dict], bool]:
    """
    Execute Greedy Maximal Dissimilarity Split for multiple folds.

    Algorithm:
    1. Initialize test set with the compound furthest from the mean.
    2. Iterate through remaining compounds, selecting the one with max min-distance
       to current test set.
    3. Add to test set if distance > threshold (similarity < threshold).
    4. Verify test set size >= min_test_size.
    5. Halt if split cannot achieve min_test_size with valid similarity.

    Args:
        fingerprints: List of RDKit fingerprints.
        n_folds: Number of folds to generate.
        threshold: Maximum Tanimoto similarity allowed (default 0.85).
        min_test_size: Minimum required size for test set (default 20).

    Returns:
        Tuple of (list of split dicts, success boolean).
    """
    n_compounds = len(fingerprints)
    logger.info(f"Starting greedy split for {n_folds} folds on {n_compounds} compounds")

    if n_compounds < min_test_size:
        logger.error(f"Insufficient compounds: {n_compounds} < {min_test_size}")
        return [], False

    # Convert fingerprints to bit vectors for efficient calculation
    bit_vectors = []
    for fp in fingerprints:
        bv = np.zeros(MORGAN_BITS, dtype=np.int8)
        fp.ToBitString()  # Ensure internal representation is ready
        DataStructs.ConvertToBitVector(fp, bv)
        bit_vectors.append(bv)

    all_splits = []
    remaining_indices = list(range(n_compounds))

    for fold in range(n_folds):
        logger.info(f"Processing fold {fold + 1}/{n_folds}")
        test_set_indices = []
        train_set_indices = remaining_indices.copy()

        if len(train_set_indices) < min_test_size:
            logger.error(f"Fold {fold + 1}: Insufficient compounds remaining ({len(train_set_indices)})")
            return [], False

        # Step 1: Initialize test set with compound furthest from the mean
        logger.info("Initializing test set with furthest compound from mean")

        # Calculate mean fingerprint (approximate by averaging bit vectors)
        mean_fp = np.mean(bit_vectors, axis=0)

        # Find compound furthest from mean (lowest similarity to mean)
        max_distance = -1.0
        furthest_idx = -1

        for idx in train_set_indices:
            # Calculate similarity to mean (using Tanimoto)
            # Note: We use a simplified distance metric here as exact Tanimoto to mean is complex
            # We'll use the bit count difference as a proxy for distance
            distance = 1.0 - (np.sum(np.bitwise_and(bit_vectors[idx], mean_fp.astype(int))) /
                             (np.sum(bit_vectors[idx]) + np.sum(mean_fp.astype(int)) -
                              np.sum(np.bitwise_and(bit_vectors[idx], mean_fp.astype(int))) + 1e-10))

            if distance > max_distance:
                max_distance = distance
                furthest_idx = idx

        if furthest_idx == -1:
            logger.error("Could not find furthest compound")
            return [], False

        # Remove from train, add to test
        train_set_indices.remove(furthest_idx)
        test_set_indices.append(furthest_idx)
        logger.info(f"Initial test set member: index {furthest_idx}")

        # Step 2 & 3: Iterate and select compounds with max min-distance
        logger.info("Selecting additional test set members via greedy max min-distance")

        while len(test_set_indices) < min_test_size and len(train_set_indices) > 0:
            best_idx = -1
            best_min_distance = -1.0

            # Find compound with max min-distance to current test set
            for idx in train_set_indices:
                min_dist = 1.0  # Start with max possible distance
                for test_idx in test_set_indices:
                    # Calculate Tanimoto similarity
                    sim = DataStructs.TanimotoSimilarity(fingerprints[idx], fingerprints[test_idx])
                    dist = 1.0 - sim
                    if dist < min_dist:
                        min_dist = dist

                if min_dist > best_min_distance:
                    best_min_distance = min_dist
                    best_idx = idx

            if best_idx == -1 or best_min_distance <= 1.0 - threshold:
                # No compound meets the threshold
                logger.warning(f"Cannot find compound with min-distance > {1.0 - threshold}")
                break

            # Add to test set
            train_set_indices.remove(best_idx)
            test_set_indices.append(best_idx)
            logger.debug(f"Added index {best_idx} to test set (min-distance: {best_min_distance:.4f})")

        # Step 4: Verify test set size
        if len(test_set_indices) < min_test_size:
            logger.error(f"Fold {fold + 1}: Test set size {len(test_set_indices)} < {min_test_size}")
            logger.error("Insufficient Structural Diversity: Cannot achieve valid split")
            return [], False

        # Verify all test set pairs have Tanimoto < threshold
        logger.info(f"Verifying test set diversity for fold {fold + 1}")
        valid = True
        for i in range(len(test_set_indices)):
            for j in range(i + 1, len(test_set_indices)):
                sim = DataStructs.TanimotoSimilarity(
                    fingerprints[test_set_indices[i]],
                    fingerprints[test_set_indices[j]]
                )
                if sim >= threshold:
                    logger.warning(f"Fold {fold + 1}: Pair ({test_set_indices[i]}, {test_set_indices[j]}) has similarity {sim:.4f} >= {threshold}")
                    valid = False

        if not valid:
            logger.error(f"Fold {fold + 1}: Validation failed - some pairs exceed threshold")
            return [], False

        all_splits.append({
            'fold': fold + 1,
            'test_indices': test_set_indices,
            'train_indices': train_set_indices,
            'test_size': len(test_set_indices),
            'train_size': len(train_set_indices)
        })

        # Update remaining indices for next fold (remove test set)
        remaining_indices = train_set_indices

        logger.info(f"Fold {fold + 1}: Test set size = {len(test_set_indices)}, Train set size = {len(train_set_indices)}")

    return all_splits, True

def save_splits(splits: List[Dict], output_dir: str) -> None:
    """
    Save split indices to CSV files.

    Args:
        splits: List of split dictionaries.
        output_dir: Directory to save split files.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for split in splits:
        fold = split['fold']
        output_path = Path(output_dir) / f"split_fold_{fold}.csv"

        df = pd.DataFrame({
            'index': split['train_indices'] + split['test_indices'],
            'set': ['train'] * len(split['train_indices']) + ['test'] * len(split['test_indices']),
            'fold': [fold] * len(split['train_indices'] + split['test_indices'])
        })

        df.to_csv(output_path, index=False)
        logger.info(f"Saved split {fold} to {output_path}")

def main():
    """Main entry point for split generation."""
    logger.info("Starting Greedy Maximal Dissimilarity Split")

    # Initialize random seed
    init_random_seed(42)

    # Load data
    input_path = 'data/processed/organophosphates_filtered.csv'
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df, fingerprints = load_fingerprints(input_path)

    if len(fingerprints) < 20:
        logger.error(f"Insufficient data: only {len(fingerprints)} compounds available")
        return

    # Execute split
    splits, success = greedy_maximal_dissimilarity_split(
        fingerprints=fingerprints,
        n_folds=N_FOLDS,
        threshold=TANIMOTO_THRESHOLD,
        min_test_size=20
    )

    if not success:
        logger.error("Split generation failed: Insufficient Structural Diversity")
        # Generate invalid split report
        report_path = 'data/processed/invalid_split_report.md'
        with open(report_path, 'w') as f:
            f.write("# Invalid Split Report\n\n")
            f.write("## Error: Insufficient Structural Diversity\n\n")
            f.write("Cannot achieve valid split with Tanimoto < 0.85 and minimum 20 test samples.\n\n")
            f.write(f"## Details\n\n")
            f.write(f"- Total compounds: {len(df)}\n")
            f.write(f"- Required test size: 20\n")
            f.write(f"- Tanimoto threshold: {TANIMOTO_THRESHOLD}\n")
            f.write(f"- Number of folds: {N_FOLDS}\n")
        logger.info(f"Generated invalid split report at {report_path}")
        return

    # Save splits
    save_splits(splits, 'data/processed/splits')

    logger.info("Split generation completed successfully")
    logger.info(f"Generated {len(splits)} valid splits")

if __name__ == "__main__":
    main()