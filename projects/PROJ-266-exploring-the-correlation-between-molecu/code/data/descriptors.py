"""
code/data/descriptors.py

Module for computing molecular flexibility descriptors (bond, angle, dihedral variances)
from 3D conformer ensembles generated via RDKit. Includes outlier detection and
formatted output generation.

Implements US2 tasks: T013a, T013b, T013c, T014a, T014b, T014c.
"""
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolTransforms
from scipy.spatial.distance import pdist, squareform

# Local imports
from utils.logging import get_logger, setup_logging_for_script
from utils.config import get_project_root, get_data_path, set_seed

# Configure logger for this module
logger = setup_logging_for_script(__name__)

# Constants
CONFORMER_COUNT = 20  # Per DEV-001 (CPU feasibility)
RANDOM_SEED = 42
IQR_MULTIPLIER = 1.5

def load_processed_data() -> pd.DataFrame:
    """
    Load the preprocessed Caco-2 dataset from data/processed/caco2_cleaned.csv.

    Returns:
        pd.DataFrame: DataFrame with columns including 'smiles' and 'logPapp'.
    """
    data_path = get_data_path()
    input_file = data_path / "processed" / "caco2_cleaned.csv"
    
    if not input_file.exists():
        raise FileNotFoundError(
            f"Processed data file not found: {input_file}. "
            "Please run code/data/preprocessing.py first."
        )
    
    logger.info(f"Loading processed data from {input_file}")
    df = pd.read_csv(input_file)
    
    required_cols = ['smiles', 'logPapp']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in input data: {missing}")
    
    logger.info(f"Loaded {len(df)} records")
    return df

def generate_conformers(smiles: str, max_conformers: int = CONFORMER_COUNT) -> Optional[List[Chem.Mol]]:
    """
    Generate a 3D conformer ensemble for a given SMILES string.

    Args:
        smiles: SMILES string of the molecule.
        max_conformers: Number of conformers to generate (default 20 per DEV-001).

    Returns:
        List of RDKit Mol objects with 3D coordinates, or None if generation fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Invalid SMILES: {smiles}")
            return None

        mol = Chem.AddHs(mol)
        
        # Embed conformers
        params = AllChem.ETKDGv3()
        params.randomSeed = RANDOM_SEED
        params.maxAttempts = 500
        
        success = AllChem.EmbedMultipleConfs(mol, numConfs=max_conformers, params=params)
        
        if not success:
            logger.warning(f"Failed to generate conformers for SMILES: {smiles}")
            return None

        # Optimize conformers
        for cid in success:
            AllChem.UFFOptimizeMolecule(mol, confId=cid, maxIters=200)

        return [mol]  # Return list containing the single optimized molecule with multiple conformers
    
    except Exception as e:
        logger.warning(f"Conformer generation failed for {smiles}: {e}")
        return None

def calculate_variance_metrics(mol: Chem.Mol) -> Dict[str, float]:
    """
    Calculate bond length, bond angle, and dihedral angle variances from the conformer ensemble.

    Args:
        mol: RDKit Mol object containing multiple conformers.

    Returns:
        Dictionary with keys: 'bond_variance', 'angle_variance', 'dihedral_variance'.
    """
    confs = [mol.GetConformer(i) for i in range(mol.GetNumConformers())]
    if len(confs) < 2:
        return {'bond_variance': 0.0, 'angle_variance': 0.0, 'dihedral_variance': 0.0}

    # Collect bond lengths
    bond_lengths = []
    # Collect bond angles
    bond_angles = []
    # Collect dihedral angles
    dihedral_angles = []

    # Helper to get all unique bonds
    bonds = list(mol.GetBonds())
    atoms = list(mol.GetAtoms())
    n_atoms = mol.GetNumAtoms()

    # 1. Bond Lengths (distances between bonded atoms)
    for conf in confs:
        for bond in bonds:
            idx1 = bond.GetBeginAtomIdx()
            idx2 = bond.GetEndAtomIdx()
            pos1 = conf.GetAtomPosition(idx1)
            pos2 = conf.GetAtomPosition(idx2)
            dist = pos1.Distance(pos2)
            bond_lengths.append(dist)

    # 2. Bond Angles (angle between two bonds sharing an atom)
    # Iterate over atoms and their neighbors
    for conf in confs:
        for atom in atoms:
            idx = atom.GetIdx()
            neighbors = [bond.GetOtherAtomIdx(idx) for bond in atom.GetBonds()]
            if len(neighbors) >= 2:
                # Check all pairs of neighbors
                for i in range(len(neighbors)):
                    for j in range(i + 1, len(neighbors)):
                        idx1 = neighbors[i]
                        idx2 = neighbors[j]
                        pos_center = conf.GetAtomPosition(idx)
                        pos1 = conf.GetAtomPosition(idx1)
                        pos2 = conf.GetAtomPosition(idx2)
                        
                        # Vector math for angle
                        v1 = pos1 - pos_center
                        v2 = pos2 - pos_center
                        
                        # Normalize
                        len1 = v1.Length()
                        len2 = v2.Length()
                        if len1 > 0 and len2 > 0:
                            dot = v1.Dot(v2) / (len1 * len2)
                            # Clamp for numerical stability
                            dot = max(-1.0, min(1.0, dot))
                            angle = np.arccos(dot)
                            bond_angles.append(angle)

    # 3. Dihedral Angles (angle between planes defined by 4 atoms)
    # We look for paths of 3 bonds: A-B-C-D
    # This is computationally expensive, so we sample or use a specific set if needed.
    # For robustness, we iterate over all valid 4-atom chains in the molecule.
    for conf in confs:
        # Get all bonds as tuples (u, v)
        bond_pairs = [(b.GetBeginAtomIdx(), b.GetEndAtomIdx()) for b in bonds]
        # Build adjacency
        adj = {i: [] for i in range(n_atoms)}
        for u, v in bond_pairs:
            adj[u].append(v)
            adj[v].append(u)
        
        # Find paths of length 3 (4 atoms)
        visited_paths = set()
        for start in range(n_atoms):
            for mid1 in adj[start]:
                if mid1 == start: continue
                for mid2 in adj[mid1]:
                    if mid2 == start or mid2 == mid1: continue
                    for end in adj[mid2]:
                        if end == start or end == mid1 or end == mid2: continue
                        
                        path = (start, mid1, mid2, end)
                        # Canonicalize to avoid duplicates (reverse path)
                        if path in visited_paths or path[::-1] in visited_paths:
                            continue
                        visited_paths.add(path)
                        
                        p1 = conf.GetAtomPosition(start)
                        p2 = conf.GetAtomPosition(mid1)
                        p3 = conf.GetAtomPosition(mid2)
                        p4 = conf.GetAtomPosition(end)
                        
                        # Calculate dihedral
                        b1 = p2 - p1
                        b2 = p3 - p2
                        b3 = p4 - p3
                        
                        n1 = np.cross(b1, b2)
                        n2 = np.cross(b2, b3)
                        
                        n1 /= np.linalg.norm(n1)
                        n2 /= np.linalg.norm(n2)
                        
                        m1 = np.cross(n1, b2 / np.linalg.norm(b2))
                        
                        x = np.dot(n1, n2)
                        y = np.dot(m1, n2)
                        angle = np.arctan2(y, x)
                        
                        dihedral_angles.append(angle)

    # Calculate variances
    def safe_variance(values):
        if len(values) == 0:
            return 0.0
        return float(np.var(values))

    bond_var = safe_variance(bond_lengths)
    angle_var = safe_variance(bond_angles)
    dihedral_var = safe_variance(dihedral_angles)

    return {
        'bond_variance': bond_var,
        'angle_variance': angle_var,
        'dihedral_variance': dihedral_var
    }

def flag_outliers(df: pd.DataFrame, cols: List[str] = None) -> pd.Series:
    """
    Flag outliers using the Interquartile Range (IQR) method.
    A value is an outlier if it is > Q3 + 1.5*IQR or < Q1 - 1.5*IQR.
    
    Args:
        df: DataFrame containing the variance columns.
        cols: List of column names to check (default: all variance columns).
    
    Returns:
        pd.Series: Boolean mask where True indicates an outlier.
    """
    if cols is None:
        cols = ['bond_variance', 'angle_variance', 'dihedral_variance']
    
    outlier_flags = pd.Series(False, index=df.index)
    
    for col in cols:
        if col not in df.columns:
            logger.warning(f"Column {col} not found in dataframe for outlier detection.")
            continue
        
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - IQR_MULTIPLIER * IQR
        upper_bound = Q3 + IQR_MULTIPLIER * IQR
        
        col_outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
        outlier_flags |= col_outliers
    
    return outlier_flags

def process_molecules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process molecules: generate conformers, calculate variances, and flag outliers.
    
    Args:
        df: Input DataFrame with 'smiles' and 'logPapp'.
    
    Returns:
        DataFrame with added variance columns and outlier flag.
    """
    set_seed(RANDOM_SEED)
    
    results = []
    success_count = 0
    fail_count = 0
    
    logger.info(f"Starting processing of {len(df)} molecules...")
    
    for idx, row in df.iterrows():
        smiles = row['smiles']
        logpapp = row['logPapp']
        
        conformers = generate_conformers(smiles)
        
        if conformers is None:
            fail_count += 1
            continue
        
        metrics = calculate_variance_metrics(conformers[0])
        
        results.append({
            'smiles': smiles,
            'logPapp': logpapp,
            'bond_variance': metrics['bond_variance'],
            'angle_variance': metrics['angle_variance'],
            'dihedral_variance': metrics['dihedral_variance']
        })
        success_count += 1
        
        if success_count % 50 == 0:
            logger.info(f"Processed {success_count} molecules successfully, {fail_count} failed.")
    
    logger.info(f"Processing complete. Success: {success_count}, Failed: {fail_count}")
    
    if not results:
        raise RuntimeError("No molecules were successfully processed.")
    
    output_df = pd.DataFrame(results)
    output_df['is_outlier'] = flag_outliers(output_df)
    
    return output_df

def write_descriptors(df: pd.DataFrame, output_filename: str = "descriptors.csv") -> Path:
    """
    Write the computed descriptors to a CSV file.
    
    Args:
        df: DataFrame with descriptor data.
        output_filename: Name of the output file.
    
    Returns:
        Path to the written file.
    """
    data_path = get_data_path()
    output_dir = data_path / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / output_filename
    
    # Ensure required columns exist
    required_cols = ['smiles', 'bond_variance', 'angle_variance', 'dihedral_variance', 'is_outlier']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required output columns: {missing_cols}")
    
    # Select and order columns
    output_df = df[required_cols]
    
    output_df.to_csv(output_file, index=False)
    logger.info(f"Wrote descriptors to {output_file}")
    
    return output_file

def main():
    """Main entry point for the descriptor generation pipeline."""
    logger.info("Starting molecular flexibility descriptor calculation (T014c)...")
    
    try:
        # 1. Load data
        df = load_processed_data()
        
        # 2. Process molecules
        result_df = process_molecules(df)
        
        # 3. Write output
        write_descriptors(result_df)
        
        logger.info("Descriptor calculation completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()