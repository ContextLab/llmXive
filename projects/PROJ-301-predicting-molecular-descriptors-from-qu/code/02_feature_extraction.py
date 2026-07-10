"""
Feature Extraction Pipeline for Molecular Descriptors.

This script loads cleaned molecular data, splits it into train/test sets,
and generates 2D Morgan fingerprints and 3D graph features (atomic number,
hybridization, distance bins, bond angles, dihedral angles).

It includes a memory monitoring loop that performs stratified downsampling
if memory usage exceeds 6.5 GB.

Outputs:
  - data/processed/features_2d.npy
  - data/processed/features_3d.npy
  - data/processed/labels.csv
"""

import os
import gc
import logging
import argparse
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors
from sklearn.model_selection import train_test_split
from scipy.spatial.distance import pdist, squareform

# Project imports
from config import set_seeds
from utils.logger import get_logger, configure_logging_for_pipeline
from utils.memory_monitor import check_memory_limit, force_gc, get_memory_usage_gb
from utils.parsers import smiles_to_mol, validate_molecule

# Constants
MEMORY_LIMIT_GB = 6.5
RANDOM_STATE = 42
N_BITS = 2048
FINGERPRINT_RADIUS = 2
TARGET_OUTPUT_2D = "data/processed/features_2d.npy"
TARGET_OUTPUT_3D = "data/processed/features_3d.npy"
TARGET_OUTPUT_LABELS = "data/processed/labels.csv"
INPUT_CLEANED_DATA = "data/processed/molecules_cleaned.parquet"

# Initialize logger
configure_logging_for_pipeline()
logger = get_logger(__name__)


def _calculate_3d_features(mol: Chem.Mol) -> Optional[np.ndarray]:
    """
    Extract 3D graph features for a single molecule.
    Features: Atomic numbers, Hybridization, Distance bins, Bond angles, Dihedral angles.
    Returns a flattened 1D numpy array or None if calculation fails.
    """
    try:
        if mol.GetNumAtoms() < 4:
            # Need at least 4 atoms for dihedrals
            return None

        conformer = mol.GetConformer(0)
        atoms = mol.GetAtoms()
        n_atoms = mol.GetNumAtoms()

        # 1. Atomic Numbers (one-hot or raw? Raw for simplicity, normalized later if needed)
        # Using raw atomic numbers for now, shape (N, 1)
        atomic_numbers = np.array([a.GetAtomicNum() for a in atoms], dtype=np.float32)

        # 2. Hybridization
        hybrid_map = {
            Chem.HybridizationType.UNSPECIFIED: 0,
            Chem.HybridizationType.S: 1,
            Chem.HybridizationType.SP: 2,
            Chem.HybridizationType.SP2: 3,
            Chem.HybridizationType.SP3: 4,
            Chem.HybridizationType.SP3D: 5,
            Chem.HybridizationType.SP3D2: 6,
        }
        hybridizations = np.array([hybrid_map.get(a.GetHybridization(), 0) for a in atoms], dtype=np.float32)

        # 3. Distance Matrix (Binned)
        coords = conformer.GetPositions()
        dist_matrix = squareform(pdist(coords))
        # Bin distances: 0-1, 1-2, 2-3, 3-4, >4 Angstroms
        bins = [0, 1, 2, 3, 4, np.inf]
        dist_binned = np.digitize(dist_matrix, bins) - 1 # 0 to 5
        # Flatten upper triangle only to avoid redundancy and self-dist
        # Upper triangle indices
        upper_tri_idx = np.triu_indices(n_atoms, k=1)
        dist_features = dist_binned[upper_tri_idx]

        # 4. Bond Angles
        # Iterate over all triplets (i, j, k) where j is central
        # This is O(N^3), so we might need to sample or limit if N is large.
        # For QM9, N <= 29. N^3 is manageable (~24k triplets).
        angles = []
        for i in range(n_atoms):
            for j in range(n_atoms):
                if i == j: continue
                for k in range(n_atoms):
                    if k == i or k == j: continue
                    # Vector ji
                    v1 = coords[i] - coords[j]
                    # Vector jk
                    v2 = coords[k] - coords[j]
                    norm1 = np.linalg.norm(v1)
                    norm2 = np.linalg.norm(v2)
                    if norm1 < 1e-6 or norm2 < 1e-6: continue
                    cos_angle = np.dot(v1, v2) / (norm1 * norm2)
                    cos_angle = np.clip(cos_angle, -1.0, 1.0)
                    angles.append(cos_angle)
        
        if len(angles) == 0:
            return None
        
        angle_features = np.array(angles, dtype=np.float32)

        # 5. Dihedral Angles
        dihedrals = []
        # Iterate over quadruplets (i, j, k, l)
        for i in range(n_atoms):
            for j in range(n_atoms):
                if i == j: continue
                for k in range(n_atoms):
                    if k == i or k == j: continue
                    for l in range(n_atoms):
                        if l == i or l == j or l == k: continue
                        # Calculate dihedral
                        b1 = coords[j] - coords[i]
                        b2 = coords[k] - coords[j]
                        b3 = coords[l] - coords[k]

                        n1 = np.cross(b1, b2)
                        n2 = np.cross(b2, b3)

                        m1 = np.cross(n1, b2 / np.linalg.norm(b2))

                        x = np.dot(n1, n2)
                        y = np.dot(m1, n2)
                        angle = np.arctan2(y, x)
                        # Normalize to [-1, 1] via sin or just keep raw?
                        # Using sin/cos to make it periodic-friendly or just raw angle
                        # Let's use raw angle in radians for now, but it's unbounded.
                        # Better: use cos and sin of the angle.
                        dihedrals.append(np.cos(angle))
                        dihedrals.append(np.sin(angle))

        if len(dihedrals) == 0:
            return None

        dihedral_features = np.array(dihedrals, dtype=np.float32)

        # Concatenate all features into a single vector
        # Note: The length of angle_features and dihedral_features depends on N.
        # To make this a fixed-size vector for ML, we usually need a pooling strategy
        # (e.g., mean, max) or a graph neural network approach.
        # However, the task asks to "Generate 3D graph features".
        # Since we are using Random Forest (as per T015), we need fixed-size vectors.
        # Strategy: Compute statistics (mean, std, min, max) of the angle and distance distributions.
        
        # Distance stats (from upper triangle)
        dist_stats = [np.mean(dist_features), np.std(dist_features), np.min(dist_features), np.max(dist_features)]
        
        # Angle stats
        angle_stats = [np.mean(angle_features), np.std(angle_features), np.min(angle_features), np.max(angle_features)]
        
        # Dihedral stats
        dihedral_stats = [np.mean(dihedral_features), np.std(dihedral_features), np.min(dihedral_features), np.max(dihedral_features)]

        # Atomic number stats
        atom_stats = [np.mean(atomic_numbers), np.std(atomic_numbers)]
        
        # Hybridization stats
        hybrid_stats = [np.mean(hybridizations), np.std(hybridizations)]

        feature_vector = np.concatenate([
            atom_stats,
            hybrid_stats,
            dist_stats,
            angle_stats,
            dihedral_stats
        ])

        return feature_vector

    except Exception as e:
        logger.warning(f"Failed to compute 3D features for molecule: {e}")
        return None


def _generate_2d_features(smiles_list: List[str]) -> np.ndarray:
    """
    Generate 2D Morgan fingerprints for a list of SMILES strings.
    Returns a numpy array of shape (N, N_BITS).
    """
    fps = []
    for smiles in smiles_list:
        mol = smiles_to_mol(smiles)
        if mol is None:
            fps.append(np.zeros(N_BITS, dtype=np.uint8))
            continue
        
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=FINGERPRINT_RADIUS, nBits=N_BITS)
        arr = np.zeros((N_BITS,), dtype=np.uint8)
        AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
        fps.append(arr)
    
    return np.array(fps, dtype=np.float32)


def _generate_3d_features_batch(df: pd.DataFrame) -> np.ndarray:
    """
    Generate 3D features for the dataframe.
    Returns a numpy array. Rows with invalid 3D data will be dropped.
    """
    features = []
    valid_indices = []
    
    logger.info(f"Computing 3D features for {len(df)} molecules...")
    
    # We need to process one by one to handle errors gracefully
    for idx, row in df.iterrows():
        mol = smiles_to_mol(row['smiles'])
        if mol is None or not validate_molecule(mol):
            continue
        
        # Ensure 3D coordinates exist
        if not mol.GetNumConformers():
            continue
        
        # Try to get 3D features
        feat = _calculate_3d_features(mol)
        if feat is not None:
            features.append(feat)
            valid_indices.append(idx)
        
        if len(features) % 1000 == 0:
            logger.info(f"Processed {len(features)} valid 3D molecules...")
    
    if len(features) == 0:
        logger.error("No valid 3D features computed.")
        return np.array([]).reshape(0, 0), []
        
    return np.array(features, dtype=np.float32), valid_indices


def _downsample_stratified(df: pd.DataFrame, target_size: int) -> pd.DataFrame:
    """
    Perform stratified random sampling to reduce dataset size.
    Strata: atom count, polarity (dipole magnitude).
    """
    logger.info(f"Performing stratified downsampling from {len(df)} to {target_size}...")
    
    # Create strata keys
    # Atom count
    df['_atom_count'] = df['smiles'].apply(lambda s: len(Chem.MolFromSmiles(s).GetAtoms()) if Chem.MolFromSmiles(s) else 0)
    
    # Polarity (Dipole moment magnitude) - binning
    if 'dipole' in df.columns:
        df['_dipole_mag'] = df['dipole'].apply(lambda x: np.linalg.norm(x) if isinstance(x, (list, np.ndarray)) else 0.0)
        # Create bins for dipole
        n_bins = min(10, target_size // 10) # Ensure enough bins
        if n_bins < 2: n_bins = 2
        df['_dipole_bin'] = pd.qcut(df['_dipole_mag'], q=n_bins, labels=False, duplicates='drop')
    else:
        df['_dipole_bin'] = 0 # Fallback

    strata_cols = ['_atom_count', '_dipole_bin']
    
    # Ensure target_size is not larger than min strata count
    min_count = df.groupby(strata_cols).size().min()
    if min_count == 0:
        # If a stratum is empty or too small, we might need to adjust strategy
        # Fallback to simple random sample if stratification fails
        logger.warning("Stratification failed due to empty strata. Falling back to random sampling.")
        return df.sample(n=target_size, random_state=RANDOM_STATE)

    # Calculate sample size per group
    # Proportional sampling
    group_sizes = df.groupby(strata_cols).size()
    total = group_sizes.sum()
    sample_counts = (group_sizes / total * target_size).round().astype(int)
    
    # Ensure we don't sample more than available
    sample_counts = sample_counts.clip(upper=group_sizes)
    
    # Adjust if sum is not target_size (due to rounding)
    current_sum = sample_counts.sum()
    diff = target_size - current_sum
    
    if diff != 0:
        # Add/remove from largest groups
        sorted_groups = group_sizes.sort_values(ascending=False).index
        for i, group in enumerate(sorted_groups):
            if diff > 0 and sample_counts[group] < group_sizes[group]:
                sample_counts[group] += 1
                diff -= 1
            elif diff < 0 and sample_counts[group] > 0:
                sample_counts[group] -= 1
                diff += 1
            if diff == 0: break
    
    sampled_dfs = []
    for group, size in sample_counts.items():
        if size > 0:
            group_df = df[df[strata_cols] == group]
            sampled = group_df.sample(n=size, random_state=RANDOM_STATE)
            sampled_dfs.append(sampled)
    
    if not sampled_dfs:
        return df.sample(n=target_size, random_state=RANDOM_STATE)
        
    result = pd.concat(sampled_dfs)
    # Drop helper columns
    result = result.drop(columns=['_atom_count', '_dipole_mag', '_dipole_bin'])
    
    logger.info(f"Downsampling complete. New size: {len(result)}")
    return result


def main():
    """Main entry point for feature extraction."""
    logger.info("Starting Feature Extraction Pipeline (T011)")
    set_seeds(RANDOM_STATE)
    
    # 1. Load Cleaned Data
    if not os.path.exists(INPUT_CLEANED_DATA):
        logger.error(f"Input file not found: {INPUT_CLEANED_DATA}")
        logger.error("Please ensure T010 has been completed successfully.")
        return
    
    logger.info(f"Loading data from {INPUT_CLEANED_DATA}")
    df = pd.read_parquet(INPUT_CLEANED_DATA)
    logger.info(f"Loaded {len(df)} molecules")
    
    # 2. Split Construction (Train/Test)
    # Assuming we split before feature generation to avoid leakage, 
    # but T011 says "Generate 2D/3D features" then "Monitor memory".
    # Usually, we generate features for the whole set, then split?
    # No, splitting first is better for memory if we only need test features for evaluation later.
    # However, the task says "Split & Feature Generation" and "Output: features_2d.npy, features_3d.npy, labels.csv".
    # It implies we produce the full dataset's features, then maybe split?
    # But the "Downsampling Logic" suggests we might need to reduce the whole dataset if it's too big.
    # Let's interpret: Split the data, then generate features for the TRAIN set?
    # Or generate for all, then split?
    # Given the memory limit constraint, it's safer to split first, then generate features for the training set (which is usually larger).
    # But the output file names are generic "features_2d.npy".
    # Let's follow the standard pipeline: Split -> Generate Features for both (or just train for training, test for evaluation).
    # The task says "Construct the final Train/Test split".
    # Let's split the dataframe first.
    
    # Determine labels
    label_cols = ['dipole', 'HOMO', 'LUMO']
    # Check if all labels exist
    if not all(col in df.columns for col in label_cols):
        logger.error(f"Missing required label columns: {label_cols}")
        return
    
    # Split 80/20
    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=RANDOM_STATE, shuffle=True
    )
    logger.info(f"Split: Train={len(train_df)}, Test={len(test_df)}")
    
    # Combine for processing if we need to check memory on the whole batch
    # But we can process train and test separately.
    # The task says "Monitor memory... reduce sample size".
    # This implies we might need to reduce the TRAIN set size if it's too big.
    
    # 3. Generate 2D Features (Fast)
    logger.info("Generating 2D Morgan fingerprints...")
    train_2d = _generate_2d_features(train_df['smiles'].tolist())
    test_2d = _generate_2d_features(test_df['smiles'].tolist())
    
    # 4. Generate 3D Features (Slow, Memory Intensive)
    logger.info("Generating 3D graph features...")
    # Process train
    train_3d, train_valid_idx = _generate_3d_features_batch(train_df)
    # Process test
    test_3d, test_valid_idx = _generate_3d_features_batch(test_df)
    
    # Filter train_df and test_df to only keep valid 3D molecules
    # We need to map valid indices back to the dataframe
    # Note: iterrows() index is the original index
    train_df = train_df.loc[train_valid_idx].reset_index(drop=True)
    test_df = test_df.loc[test_valid_idx].reset_index(drop=True)
    
    logger.info(f"3D Features Valid: Train={len(train_3d)}, Test={len(test_3d)}")
    
    # 5. Memory Monitoring & Downsampling
    # Check memory usage. If > 6.5 GB, downsample the TRAIN set.
    current_mem_gb = get_memory_usage_gb()
    logger.info(f"Current memory usage: {current_mem_gb:.2f} GB")
    
    if current_mem_gb >= MEMORY_LIMIT_GB:
        logger.warning(f"Memory usage ({current_mem_gb:.2f} GB) exceeds limit ({MEMORY_LIMIT_GB} GB). Downsampling...")
        
        # Calculate target size
        # Heuristic: Reduce by 20% increments until under limit
        target_size = len(train_df)
        while target_size > 1000 and current_mem_gb >= MEMORY_LIMIT_GB:
            target_size = int(target_size * 0.8)
            logger.info(f"Attempting to downsample to {target_size}...")
            
            # Downsample
            train_df = _downsample_stratified(train_df, target_size)
            
            # Re-generate 2D features for the downsampled set
            train_2d = _generate_2d_features(train_df['smiles'].tolist())
            
            # Re-generate 3D features for the downsampled set
            # Note: This is expensive. In a real pipeline, we might cache 3D features.
            # But for this task, we re-calculate to ensure consistency.
            train_3d, _ = _generate_3d_features_batch(train_df)
            
            # Force GC
            force_gc()
            current_mem_gb = get_memory_usage_gb()
            logger.info(f"Memory after downsample: {current_mem_gb:.2f} GB")
            
            if len(train_3d) == 0:
                logger.error("Downsampling resulted in no valid 3D features. Stopping.")
                break
    else:
        logger.info("Memory usage within limits. No downsampling required.")
    
    # 6. Prepare Labels
    # Align labels with the processed dataframes
    train_labels = train_df[label_cols].copy()
    test_labels = test_df[label_cols].copy()
    
    # Combine train and test for saving? 
    # The task says "Output: Save outputs to ... features_2d.npy, features_3d.npy, labels.csv"
    # It doesn't explicitly say separate train/test files.
    # Usually, we save the full processed dataset for the next stage (Training) to split again?
    # Or we save the split?
    # T015 (Training) expects to load features.
    # Let's save the TRAIN features and labels, as that's what the model trains on.
    # And maybe the test set for evaluation?
    # The task says "Construct the final Train/Test split".
    # Let's save the TRAIN set as the primary output for training, and maybe a separate file for test?
    # But the output spec is specific: `data/processed/features_2d.npy`, etc.
    # It implies a single file.
    # Let's assume the output files contain the TRAIN data, as that is the primary artifact for training.
    # However, to be safe and consistent with "Split & Feature Generation", maybe we save the combined set?
    # No, T015 says "Train the final Random Forest... on the full training set".
    # So T011 should produce the training set features.
    # Let's save the TRAIN set.
    
    # Wait, T022 (Analysis) needs test labels and predictions.
    # If we only save train, where does test go?
    # Maybe we save BOTH? Or maybe the "labels.csv" is the full set?
    # Let's look at the dependency: T011 -> T015 (Train), T022 (Analysis).
    # T022 loads "labels.csv".
    # If we only save train labels, T022 fails.
    # So we must save the FULL set (Train + Test) or separate files.
    # The task says "Save outputs to ... labels.csv". Singular.
    # Let's save the FULL dataset (Train + Test) to the specified paths.
    # The split information (indices) might be needed, or the next step re-splits?
    # T015 says "Train ... on the full training set". It might re-split or expect a specific split.
    # Given the ambiguity, the safest interpretation for a "Feature Extraction" task is to produce the features for the data it processed.
    # Since we split internally, let's save the TRAIN set as the main artifact for T015,
    # AND save the TEST set as a separate artifact if needed?
    # But the task only lists ONE set of output files.
    # Let's assume the output files are the TRAIN set, and the test set is kept in memory or saved elsewhere?
    # No, that's bad practice.
    # Let's re-read: "Construct the final Train/Test split... Output: Save outputs to..."
    # Maybe the output files are the combined features, and the split is stored in a separate file?
    # Or maybe the "labels.csv" is the full set, and the features are the full set?
    # Let's save the FULL dataset (Train + Test) to the specified paths.
    # This ensures T022 can load labels. T015 can load features and re-split or use a split file.
    # But T015 says "Train ... on the full training set". It implies it knows what the training set is.
    # If we save the full set, T015 must re-split.
    # But we already split!
    # Let's save the TRAIN set to the specified paths, and save the TEST set to `data/processed/features_test_2d.npy`?
    # The task doesn't specify test files.
    # Let's assume the task wants the TRAIN set features and labels, and the test set is handled differently?
    # Actually, T011 says "Construct the final Train/Test split".
    # Maybe the output is the TRAIN set, and the test set is saved to `data/processed/test_...`?
    # Let's look at the "Output" section again: "Save outputs to `data/processed/features_2d.npy`, `data/processed/features_3d.npy`, and `data/processed/labels.csv`."
    # It does not mention test files.
    # This suggests the output is the TRAIN set.
    # But then how does T022 get test labels?
    # Maybe T022 loads the same file and splits?
    # Or maybe the "labels.csv" contains the full set?
    # Let's save the FULL set to the specified paths.
    # And save a `split_indices.json` to indicate which rows are train/test.
    # This is the most robust approach.
    
    # Combine back
    full_2d = np.vstack([train_2d, test_2d])
    full_3d = np.vstack([train_3d, test_3d])
    full_labels = pd.concat([train_labels, test_labels]).reset_index(drop=True)
    
    # Save split indices
    split_info = {
        "train_size": len(train_df),
        "test_size": len(test_df),
        "random_state": RANDOM_STATE
    }
    # We need to know which rows are train/test.
    # Since we concatenated, the first N rows are train, next M are test.
    split_info["train_indices"] = list(range(len(train_df)))
    split_info["test_indices"] = list(range(len(train_df), len(full_labels)))
    
    # Save artifacts
    logger.info(f"Saving 2D features: {full_2d.shape}")
    np.save(TARGET_OUTPUT_2D, full_2d)
    
    logger.info(f"Saving 3D features: {full_3d.shape}")
    np.save(TARGET_OUTPUT_3D, full_3d)
    
    logger.info(f"Saving labels: {full_labels.shape}")
    full_labels.to_csv(TARGET_OUTPUT_LABELS, index=False)
    
    # Save split info
    split_path = "data/processed/split_info.json"
    with open(split_path, 'w') as f:
        import json
        json.dump(split_info, f)
    
    logger.info(f"Feature extraction complete. Outputs saved to {TARGET_OUTPUT_2D}, {TARGET_OUTPUT_3D}, {TARGET_OUTPUT_LABELS}")
    logger.info(f"Split info saved to {split_path}")


if __name__ == "__main__":
    main()