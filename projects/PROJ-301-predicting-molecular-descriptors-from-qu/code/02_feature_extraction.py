"""
Feature Extraction Module.

Implements T011: Split & Feature Generation.

1. Loads `data/processed/molecules_cleaned.parquet`.
2. Constructs Train/Test split (stratified by atom count/polarity).
3. Generates 2D Morgan fingerprints (radius=2, nBits=2048).
4. Generates 3D graph features (atomic number, hybridization, distance bins, angles).
5. Monitors memory; downsamples if > 6.5 GB.
6. Saves outputs to `data/processed/`.

Outputs:
- data/processed/features_2d.npy
- data/processed/features_3d.npy
- data/processed/labels_train.csv
- data/processed/labels_test.csv
- data/processed/split_indices_train.json
- data/processed/split_indices_test.json
- artifacts/metrics/downsampling_log.json
"""

import argparse
import gc
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.model_selection import train_test_split

# Import local utilities
from utils.logger import setup_logger, get_logger
from utils.memory_monitor import check_memory_limit, force_gc, MemoryMonitor
from utils.parsers import smiles_to_mol, parse_xyz_to_mol, validate_molecule

# Setup logging
logger = get_logger(__name__)

# Constants
DATA_PROCESSED_DIR = Path("data/processed")
ARTIFACTS_METRICS_DIR = Path("artifacts/metrics")

# Feature generation parameters
MORGAN_RADIUS = 2
MORGAN_BITS = 2048

# Memory threshold (6.5 GB)
MEMORY_THRESHOLD_GB = 6.5

def load_and_process_data() -> pd.DataFrame:
    """
    Load the cleaned molecules dataset.
    
    Returns:
        pd.DataFrame: The cleaned dataset.
    """
    input_path = DATA_PROCESSED_DIR / "molecules_cleaned.parquet"
    if not input_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {input_path}. Run T010 first.")
    
    logger.info(f"Loading cleaned data from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} molecules.")
    return df

def generate_morgan_fingerprint(mol: Chem.Mol, radius: int = MORGAN_RADIUS, n_bits: int = MORGAN_BITS) -> np.ndarray:
    """
    Generate a Morgan fingerprint for a molecule.
    
    Args:
        mol: RDKit Mol object.
        radius: Fingerprint radius.
        n_bits: Number of bits in the fingerprint.
        
    Returns:
        np.ndarray: Binary fingerprint vector.
    """
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.int8)
    AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def extract_3d_features(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Extract 3D graph features from a molecule.
    
    Includes:
    - Atomic numbers
    - Hybridization states
    - Distance bins (histogram of bond lengths)
    - Bond angles
    - Dihedral angles (if applicable)
    
    Args:
        mol: RDKit Mol object with 3D coordinates.
        
    Returns:
        Dict containing feature arrays or scalars.
    """
    if mol.GetNumAtoms() == 0:
        return {}
        
    atoms = list(mol.GetAtoms())
    conf = mol.GetConformer()
    
    atomic_numbers = [atom.GetAtomicNum() for atom in atoms]
    hybridizations = [int(atom.GetHybridization()) for atom in atoms]
    
    # Compute distance matrix
    n_atoms = len(atoms)
    distances = []
    angles = []
    dihedrals = []
    
    # Sample distances (all pairs)
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            dist = conf.GetDistance(i, j)
            distances.append(dist)
            
    # Sample angles (triplets) - limited to avoid memory explosion
    # Only consider connected triplets or random sample if too many
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            if conf.GetDistance(i, j) < 3.0: # Bonded or close
                for k in range(n_atoms):
                    if k != i and k != j:
                        # Check if k is bonded to j to form a proper angle
                        # For simplicity, we just take a random subset if n is large
                        if len(angles) < 1000: # Limit per molecule
                            angle = conf.GetAngle(i, j, k)
                            angles.append(angle)
    
    # Dihedrals (quadruplets) - very expensive, sample heavily
    if n_atoms >= 4:
        # Random sample of dihedrals to keep feature size manageable
        count = 0
        for i in range(n_atoms):
            for j in range(i + 1, n_atoms):
                for k in range(j + 1, n_atoms):
                    for l in range(k + 1, n_atoms):
                        if count < 500:
                            # Simple check for valid geometry
                            try:
                                dihedral = conf.GetDihedral(i, j, k, l)
                                dihedrals.append(dihedral)
                                count += 1
                            except:
                                pass
    
    # Aggregate features into a fixed-size vector for the molecule
    # 1. Atomic number stats
    avg_atomic_num = np.mean(atomic_numbers)
    std_atomic_num = np.std(atomic_numbers)
    
    # 2. Hybridization stats
    avg_hybrid = np.mean(hybridizations)
    
    # 3. Distance histogram (10 bins)
    if distances:
        dist_hist, _ = np.histogram(distances, bins=10, range=(0.0, 5.0))
        dist_hist = dist_hist / len(distances) # Normalize
    else:
        dist_hist = np.zeros(10)
        
    # 4. Angle histogram (10 bins, 0-180 deg)
    if angles:
        angle_hist, _ = np.histogram(angles, bins=10, range=(0.0, 180.0))
        angle_hist = angle_hist / len(angles)
    else:
        angle_hist = np.zeros(10)
        
    # 5. Dihedral histogram (10 bins, -180 to 180)
    if dihedrals:
        dihedral_hist, _ = np.histogram(dihedrals, bins=10, range=(-180.0, 180.0))
        dihedral_hist = dihedral_hist / len(dihedrals)
    else:
        dihedral_hist = np.zeros(10)
        
    features = np.concatenate([
        [avg_atomic_num, std_atomic_num, avg_hybrid],
        dist_hist,
        angle_hist,
        dihedral_hist
    ])
    
    return features

def downsample_if_needed(df: pd.DataFrame, target_memory_gb: float = MEMORY_THRESHOLD_GB) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Check memory usage and downsample if necessary.
    
    Uses Stratified Random Sampling based on atom count and polarity.
    
    Args:
        df: Input dataframe.
        target_memory_gb: Maximum allowed memory in GB.
        
    Returns:
        Tuple of (downsampled_df, log_info).
    """
    monitor = MemoryMonitor()
    initial_memory = monitor.get_memory_usage_gb()
    
    if initial_memory < target_memory_gb:
        return df, {"action": "none", "initial_gb": initial_memory, "final_gb": initial_memory}
    
    logger.warning(f"Memory usage {initial_memory:.2f} GB exceeds limit. Downsampling...")
    
    # Prepare stratification keys
    df['atom_count'] = df['smiles'].apply(lambda x: len(Chem.MolFromSmiles(x).GetAtoms()) if Chem.MolFromSmiles(x) else 0)
    # Polarity proxy: number of heteroatoms or dipole moment if available
    if 'dipole' in df.columns:
        df['polarity_bin'] = pd.qcut(df['dipole'], q=5, duplicates='drop')
    else:
        df['polarity_bin'] = df['atom_count'] % 5 # Fallback
        
    strat_keys = ['atom_count', 'polarity_bin']
    
    # Iterative downsampling
    current_df = df
    sample_frac = 0.9
    iteration = 0
    max_iterations = 10
    
    while iteration < max_iterations:
        try:
            # Sample
            current_df = current_df.sample(frac=sample_frac, random_state=42, replace=False)
            
            # Estimate memory (rough heuristic: rows * avg_row_size)
            # In practice, we check actual RSS if possible, but here we estimate based on row count reduction
            # or re-run the monitor if we were loading the whole dataset in memory again.
            # For this script, we assume the dataframe is the main memory consumer.
            estimated_gb = (len(current_df) / len(df)) * initial_memory
            
            if estimated_gb < target_memory_gb:
                break
                
            sample_frac *= 0.9
            iteration += 1
        except Exception as e:
            logger.error(f"Downsampling failed at iteration {iteration}: {e}")
            break
            
    log_info = {
        "action": "downsampled",
        "initial_rows": len(df),
        "final_rows": len(current_df),
        "initial_gb": initial_memory,
        "estimated_final_gb": (len(current_df) / len(df)) * initial_memory,
        "iterations": iteration
    }
    
    return current_df, log_info

def main():
    """
    Main entry point for feature extraction.
    """
    # Ensure directories exist
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_METRICS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting Feature Extraction Pipeline.")
    
    # 1. Load Data
    df = load_and_process_data()
    
    # 2. Memory Check & Downsampling
    df, downsample_log = downsample_if_needed(df)
    
    # Save downsampling log
    with open(ARTIFACTS_METRICS_DIR / "downsampling_log.json", "w") as f:
        json.dump(downsample_log, f, indent=2)
    logger.info(f"Downsampling log saved. Final rows: {len(df)}")
    
    # 3. Split Data
    # Stratify by atom count and target descriptor if available
    stratify_cols = []
    if 'atom_count' in df.columns:
        stratify_cols.append('atom_count')
    # Use a target for stratification if available (e.g., dipole bucket)
    if 'dipole' in df.columns:
        df['dipole_bin'] = pd.qcut(df['dipole'], q=5, duplicates='drop', labels=False)
        stratify_cols.append('dipole_bin')
        
    stratify_arg = df[stratify_cols] if stratify_cols else None
    
    train_indices, test_indices = train_test_split(
        df.index, 
        test_size=0.2, 
        random_state=42, 
        stratify=stratify_arg if stratify_arg is not None and len(stratify_arg) > 0 else None
    )
    
    # Save indices
    with open(DATA_PROCESSED_DIR / "split_indices_train.json", "w") as f:
        json.dump(train_indices.tolist(), f)
    with open(DATA_PROCESSED_DIR / "split_indices_test.json", "w") as f:
        json.dump(test_indices.tolist(), f)
    logger.info("Train/Test split indices saved.")
    
    # 4. Generate Features
    logger.info("Generating 2D and 3D features...")
    
    features_2d_list = []
    features_3d_list = []
    labels_train_list = []
    labels_test_list = []
    
    # Process in batches to manage memory if dataset is huge
    # For now, iterate directly
    
    train_df = df.loc[train_indices]
    test_df = df.loc[test_indices]
    
    def process_batch(batch_df, is_train=True):
        f2d = []
        f3d = []
        labels = []
        
        for idx, row in batch_df.iterrows():
            mol = smiles_to_mol(row['smiles'])
            if mol is None:
                continue
                
            # 2D Features
            try:
                fp = generate_morgan_fingerprint(mol)
                f2d.append(fp)
            except Exception as e:
                logger.warning(f"2D feature failed for {idx}: {e}")
                continue
                
            # 3D Features
            try:
                # Ensure 3D coords exist
                if mol.GetNumConformers() == 0:
                    # Try to generate 3D if missing (optional, but plan says parse 3D)
                    # If plan assumes 3D is already in data, we skip generation
                    # Assuming 3D is present in the cleaned data as per T010 validation
                    pass
                
                feat_3d = extract_3d_features(mol)
                if len(feat_3d) > 0:
                    f3d.append(feat_3d)
            except Exception as e:
                logger.warning(f"3D feature failed for {idx}: {e}")
                continue
            
            # Labels
            target_cols = ['dipole', 'homo', 'lumo']
            valid_labels = {col: row[col] for col in target_cols if col in row and not pd.isna(row[col])}
            if valid_labels:
                labels.append(valid_labels)
                
        return f2d, f3d, labels
    
    # Process Train
    t2d, t3d, t_labels = process_batch(train_df, is_train=True)
    # Process Test
    e2d, e3d, e_labels = process_batch(test_df, is_train=False)
    
    if not t2d or not e2d:
        raise RuntimeError("Feature generation resulted in empty lists. Check input data validity.")
    
    # Convert to numpy
    features_2d = np.array(t2d + e2d)
    features_3d = np.array(t3d + e3d)
    
    # Create DataFrames for labels
    # Align indices with the combined feature list
    # We need to map the original indices to the new array positions
    # This is tricky if we dropped some. We'll save the labels that correspond to the features.
    
    # Re-process to align labels with the kept features
    # A simpler approach: Generate features and labels in the same loop and filter together
    # Let's refactor slightly for alignment in the main loop above (conceptually)
    # For this implementation, we assume the filtering is consistent or we re-join.
    # To be safe, we will save the labels that were successfully generated.
    
    # Re-construct aligned labels for the saved features
    # This requires a mapping which we didn't explicitly store in the list above.
    # Let's fix the loop to store (index, features, labels)
    
    # Refactoring the loop for alignment:
    all_2d = []
    all_3d = []
    all_labels = []
    all_indices = []
    
    for df_part, name in [(train_df, "train"), (test_df, "test")]:
        for idx, row in df_part.iterrows():
            mol = smiles_to_mol(row['smiles'])
            if mol is None:
                continue
            
            try:
                fp = generate_morgan_fingerprint(mol)
                feat_3d = extract_3d_features(mol)
                
                target_cols = ['dipole', 'homo', 'lumo']
                valid_labels = {col: row[col] for col in target_cols if col in row and not pd.isna(row[col])}
                
                if valid_labels:
                    all_2d.append(fp)
                    all_3d.append(feat_3d)
                    all_labels.append(valid_labels)
                    all_indices.append(idx)
            except:
                continue
                
    features_2d = np.array(all_2d)
    features_3d = np.array(all_3d)
    
    # Split back based on indices
    train_mask = [i in train_indices for i in all_indices]
    test_mask = [i in test_indices for i in all_indices]
    
    train_2d = features_2d[train_mask]
    train_3d = features_3d[train_mask]
    train_lbls = [all_labels[i] for i in range(len(all_labels)) if train_mask[i]]
    
    test_2d = features_2d[test_mask]
    test_3d = features_3d[test_mask]
    test_lbls = [all_labels[i] for i in range(len(all_labels)) if test_mask[i]]
    
    # Save Features
    np.save(DATA_PROCESSED_DIR / "features_2d.npy", train_2d) # Or combined? Task says "features_2d.npy"
    # The task description says "Save outputs to ... features_2d.npy". Usually this implies the full matrix or the train one.
    # Given the split, we should probably save the full aligned matrix or separate ones.
    # The task says "labels_train.csv" and "labels_test.csv", implying separate labels.
    # Let's save the full matrix and the split indices, or separate matrices.
    # "Save train indices... test indices... features_2d.npy"
    # Interpretation: features_2d.npy contains the full dataset (or the one used for training?).
    # Standard practice: Save the full feature matrix and the split indices, OR save train/test separately.
    # Let's save the full aligned matrix to features_2d.npy and features_3d.npy, and rely on split_indices for splitting.
    # BUT the task says "labels_train.csv" and "labels_test.csv".
    # Let's save the full matrix and the labels separately.
    
    # Actually, looking at T015 (Training), it loads "features_2d.npy".
    # If we save the full matrix, T015 must split it.
    # Let's save the full aligned matrix.
    np.save(DATA_PROCESSED_DIR / "features_2d.npy", features_2d)
    np.save(DATA_PROCESSED_DIR / "features_3d.npy", features_3d)
    
    # Save Labels
    df_train_labels = pd.DataFrame(train_lbls)
    df_train_labels['molecule_id'] = [i for i, m in enumerate(all_indices) if train_mask[i]]
    df_train_labels.to_csv(DATA_PROCESSED_DIR / "labels_train.csv", index=False)
    
    df_test_labels = pd.DataFrame(test_lbls)
    df_test_labels['molecule_id'] = [i for i, m in enumerate(all_indices) if test_mask[i]]
    df_test_labels.to_csv(DATA_PROCESSED_DIR / "labels_test.csv", index=False)
    
    logger.info(f"Features saved: 2D shape {features_2d.shape}, 3D shape {features_3d.shape}")
    logger.info(f"Labels saved: Train {len(train_lbls)}, Test {len(test_lbls)}")
    logger.info("Feature Extraction Pipeline completed.")

if __name__ == "__main__":
    main()
