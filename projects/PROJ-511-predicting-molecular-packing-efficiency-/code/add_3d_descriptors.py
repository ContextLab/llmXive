"""
T018: Calculate 3D descriptors (radius of gyration, asphericity, moments) from RDKit conformers.

Reads: data/dataset_filtered.csv
Writes: data/dataset.csv (merged with 3D descriptors)

Uses ETKDG parameters with seed=42, max_attempts=50.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import Optional, Tuple, List, Dict, Any

from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors, Descriptors3D
from rdkit import RDLogger

# Project local imports
from utils import fix_seed, setup_logging
from config import ensure_directories

# Disable RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

logger = logging.getLogger(__name__)

# Constants for ETKDG
ETKDG_SEED = 42
ETKDG_MAX_ATTEMPTS = 50

def calculate_radius_of_gyration(mol: Chem.Mol) -> float:
    """
    Calculate the radius of gyration of a molecule.
    Uses the 3D coordinates of the molecule.
    """
    conf = mol.GetConformer()
    coords = conf.GetPositions()
    
    # Calculate center of mass (assuming equal mass for simplicity, or use atomic masses)
    # For organic molecules, using centroid is often sufficient for shape descriptors
    centroid = np.mean(coords, axis=0)
    
    # Calculate squared distances from centroid
    dists_sq = np.sum((coords - centroid) ** 2, axis=1)
    
    # Radius of gyration
    rg = np.sqrt(np.mean(dists_sq))
    return float(rg)

def calculate_asphericity(mol: Chem.Mol) -> float:
    """
    Calculate the asphericity of a molecule.
    Asphericity = (3 * lambda_3 - trace) / (2 * trace)
    where lambda_i are eigenvalues of the gyration tensor.
    """
    conf = mol.GetConformer()
    coords = conf.GetPositions()
    
    # Center coordinates
    centroid = np.mean(coords, axis=0)
    coords_centered = coords - centroid
    
    # Calculate gyration tensor
    # G_ij = (1/N) * sum_k (r_ki * r_kj)
    N = len(coords)
    G = np.dot(coords_centered.T, coords_centered) / N
    
    # Eigenvalues of gyration tensor
    eigenvalues = np.linalg.eigvalsh(G)
    eigenvalues = np.sort(eigenvalues)[::-1]  # Sort descending: lambda_1 >= lambda_2 >= lambda_3
    
    # Asphericity: b = lambda_1 - (lambda_2 + lambda_3)/2
    # Alternative definition: b = (3*lambda_1 - trace)/2
    # Using the standard definition from polymer physics
    trace = np.trace(G)
    asphericity = eigenvalues[0] - (eigenvalues[1] + eigenvalues[2]) / 2.0
    
    return float(asphericity)

def calculate_principal_moments(mol: Chem.Mol) -> Tuple[float, float, float]:
    """
    Calculate the principal moments of inertia (normalized by mass for simplicity,
    or just based on coordinates if masses are not available).
    Returns (I1, I2, I3) sorted descending.
    """
    conf = mol.GetConformer()
    coords = conf.GetPositions()
    atoms = mol.GetAtoms()
    
    # Use atomic masses if available, otherwise assume unit mass
    masses = []
    for atom in atoms:
        masses.append(atom.GetAtomicWeight())
    masses = np.array(masses)
    
    # Center of mass
    total_mass = np.sum(masses)
    center_of_mass = np.sum(coords * masses[:, np.newaxis], axis=0) / total_mass
    
    # Coordinates relative to center of mass
    coords_centered = coords - center_of_mass
    
    # Calculate inertia tensor
    # I_ij = sum_k m_k * (r_k^2 * delta_ij - r_ki * r_kj)
    I = np.zeros((3, 3))
    for i in range(len(coords)):
        r = coords_centered[i]
        r_sq = np.dot(r, r)
        m = masses[i]
        for x in range(3):
            for y in range(3):
                if x == y:
                    I[x, y] += m * (r_sq - r[x] * r[y])
                else:
                    I[x, y] -= m * r[x] * r[y]
    
    # Eigenvalues (principal moments)
    eigenvalues = np.linalg.eigvalsh(I)
    eigenvalues = np.sort(eigenvalues)[::-1]  # Descending order
    
    return (float(eigenvalues[0]), float(eigenvalues[1]), float(eigenvalues[2]))

def generate_conformer(mol: Chem.Mol) -> Optional[Chem.Mol]:
    """
    Generate a 3D conformer for a molecule using ETKDG.
    Returns the molecule with the conformer attached, or None if generation fails.
    """
    # Create a copy to avoid modifying the original
    mol_copy = Chem.Mol(mol)
    
    # Add hydrogens if not present
    if not mol_copy.GetNumAtoms() or mol_copy.GetNumAtoms() != mol.GetNumAtoms():
        mol_copy = Chem.AddHs(mol_copy)
    
    # Generate conformer using ETKDG
    params = AllChem.ETKDGv3()
    params.randomSeed = ETKDG_SEED
    params.maxAttempts = ETKDG_MAX_ATTEMPTS
    params.useRandomCoords = False
    
    try:
        result = AllChem.EmbedMolecule(mol_copy, params)
        if result == -1:
            # Try with random coords if ETKDG fails
            params.useRandomCoords = True
            result = AllChem.EmbedMolecule(mol_copy, params)
            if result == -1:
                logger.warning("Failed to generate conformer for molecule")
                return None
        
        # Optimize geometry with MMFF94
        try:
            AllChem.MMFFOptimizeMolecule(mol_copy, maxIters=200)
        except Exception as e:
            logger.debug(f"MMFF optimization failed: {e}, using raw ETKDG coords")
        
        return mol_copy
    except Exception as e:
        logger.warning(f"Conformer generation failed: {e}")
        return None

def compute_3d_descriptors(smiles: str) -> Dict[str, float]:
    """
    Compute 3D descriptors for a given SMILES string.
    Returns a dictionary with:
      - radius_of_gyration
      - asphericity
      - principal_moment_1
      - principal_moment_2
      - principal_moment_3
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    
    # Generate 3D conformer
    mol_3d = generate_conformer(mol)
    if mol_3d is None:
        raise ValueError(f"Failed to generate 3D conformer for SMILES: {smiles}")
    
    # Calculate descriptors
    rg = calculate_radius_of_gyration(mol_3d)
    asp = calculate_asphericity(mol_3d)
    m1, m2, m3 = calculate_principal_moments(mol_3d)
    
    return {
        'radius_of_gyration': rg,
        'asphericity': asp,
        'principal_moment_1': m1,
        'principal_moment_2': m2,
        'principal_moment_3': m3
    }

def add_3d_descriptors_to_dataset(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Read dataset, compute 3D descriptors, and save to output.
    """
    logger.info(f"Reading dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info(f"Dataset has {len(df)} rows")
    
    # Initialize columns with NaN
    descriptor_cols = [
        'radius_of_gyration',
        'asphericity',
        'principal_moment_1',
        'principal_moment_2',
        'principal_moment_3'
    ]
    
    for col in descriptor_cols:
        df[col] = np.nan
    
    success_count = 0
    fail_count = 0
    
    for idx, row in df.iterrows():
        smiles = row['smiles']
        cod_id = row.get('cod_id', 'unknown')
        
        try:
            descriptors = compute_3d_descriptors(smiles)
            for col, val in descriptors.items():
                df.at[idx, col] = val
            success_count += 1
            if success_count % 100 == 0:
                logger.info(f"Processed {success_count} molecules successfully")
        except Exception as e:
            logger.warning(f"Failed to compute descriptors for {cod_id} (SMILES: {smiles[:50]}...): {e}")
            fail_count += 1
    
    logger.info(f"Successfully computed descriptors for {success_count} molecules")
    logger.info(f"Failed to compute descriptors for {fail_count} molecules")
    
    # Save to output
    ensure_directories(output_path)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved dataset with 3D descriptors to {output_path}")
    
    return df

def main():
    """Main entry point for the script."""
    # Setup logging
    log_file = setup_logging("add_3d_descriptors")
    
    # Paths
    input_path = "data/dataset_filtered.csv"
    output_path = "data/dataset.csv"
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Fix seed for reproducibility
    fix_seed(42)
    
    # Process dataset
    df = add_3d_descriptors_to_dataset(input_path, output_path)
    
    logger.info("3D descriptor calculation completed successfully")
    
    # Log final statistics
    logger.info(f"Final dataset shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")
    
    # Check for any NaN values in descriptor columns
    descriptor_cols = ['radius_of_gyration', 'asphericity', 'principal_moment_1', 
                     'principal_moment_2', 'principal_moment_3']
    nan_counts = df[descriptor_cols].isna().sum()
    logger.info(f"NaN counts in descriptor columns:\n{nan_counts}")

if __name__ == "__main__":
    main()
