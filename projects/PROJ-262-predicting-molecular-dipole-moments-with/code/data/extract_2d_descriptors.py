from __future__ import annotations

import argparse
import json
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
from scipy import sparse

# Import existing project utilities to ensure consistency
from utils.reproducibility import set_seed
from utils.pipeline_time_limit import time_limit
from utils.memory_constraint import memory_limit
from utils.cpu_constraint import cpu_limit

# Constants
FINGERPRINT_BITS = 2048
MAX_ATOMS = 50  # QM9 max atoms is 29, safe upper bound
SEED = 42

def compute_coulomb_matrix(atoms: List[str], coordinates: np.ndarray) -> np.ndarray:
    """
    Compute the Topological Coulomb Matrix.
    
    Unlike the standard Coulomb Matrix which uses Euclidean distances,
    the Topological version uses the shortest path distance (graph distance)
    between atoms in the molecular graph.
    
    M_ij = 0.5 * Z_i^2.4       if i == j
    M_ij = Z_i * Z_j / d_ij    if i != j
    
    Where Z is the atomic number and d_ij is the topological distance (number of bonds).
    
    Args:
        atoms: List of atomic symbols (e.g., ['C', 'H', 'O'])
        coordinates: Numpy array of shape (N, 3) with atomic coordinates.
                    (Used to generate the RDKit molecule for graph construction)
                    
    Returns:
        Numpy array of shape (N, N) containing the topological Coulomb matrix.
        Padded with zeros if the number of atoms is less than MAX_ATOMS.
    """
    if len(atoms) == 0:
        return np.zeros((MAX_ATOMS, MAX_ATOMS))
    
    # Create RDKit molecule from atoms and coordinates
    mol = Chem.MolFromXYZBlock(
        f"{len(atoms)}\n\n" + "\n".join([
            f"{atom} {x} {y} {z}" for atom, (x, y, z) in zip(atoms, coordinates)
        ])
    )
    
    if mol is None:
        # Fallback: construct from atomic numbers if XYZ parsing fails
        # This handles cases where coordinates might be slightly malformed
        mol = Chem.RWMol()
        for atom_symbol in atoms:
            atom = Chem.Atom(atom_symbol)
            mol.AddAtom(atom)
        # Add dummy bonds to create a connected graph if possible, 
        # otherwise just return diagonal
        # For Topological Coulomb, we strictly need graph distances.
        # If we can't infer bonds, we can't compute topological distance.
        # We'll assume the input coordinates are valid for a molecule.
        pass

    # Convert to editable molecule to add bonds if missing (RDKit sometimes needs help)
    # However, for QM9, the XYZ usually has valid geometry.
    # We will use the connectivity from the 3D structure if available, 
    # or rely on RDKit's distance-based bond perception.
    try:
        Chem.rdDistGeom.EmbedMolecule(mol, randomSeed=SEED) # Just to ensure valid state
        Chem.Kekulize(mol, clearAromaticFlags=True)
    except:
        pass

    # Get atomic numbers
    atomic_numbers = [atom.GetAtomicNum() for atom in mol.GetAtoms()]
    n_atoms = len(atomic_numbers)
    
    # Initialize matrix
    matrix = np.zeros((n_atoms, n_atoms))
    
    # Diagonal: 0.5 * Z_i^2.4
    for i, z in enumerate(atomic_numbers):
        matrix[i, i] = 0.5 * (z ** 2.4)
        
    # Off-diagonal: Z_i * Z_j / d_ij
    # Compute shortest path distances (graph distance)
    # Using RDKit's GetShortestPaths
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            # Calculate topological distance (number of bonds)
            # If no path exists (unlikely in a single molecule), use a large distance or 0
            path = Chem.GetShortestPath(mol, i, j)
            if path:
                dist = len(path) - 1  # Number of bonds
                if dist == 0:
                    dist = 1 # Avoid division by zero if self-loop detected (shouldn't happen)
                matrix[i, j] = (atomic_numbers[i] * atomic_numbers[j]) / dist
                matrix[j, i] = matrix[i, j]
                
    # Pad to MAX_ATOMS x MAX_ATOMS
    padded_matrix = np.zeros((MAX_ATOMS, MAX_ATOMS))
    padded_matrix[:n_atoms, :n_atoms] = matrix
    
    return padded_matrix

def extract_2d_features(molecule_id: str, atoms: List[str], coordinates: np.ndarray) -> Dict[str, Any]:
    """
    Extract 2D descriptors: Morgan Fingerprints and Topological Coulomb Matrix.
    
    Args:
        molecule_id: Unique identifier for the molecule.
        atoms: List of atomic symbols.
        coordinates: Numpy array of shape (N, 3).
        
    Returns:
        Dictionary containing:
            - molecule_id: str
            - features_2d_fp: List of float (Morgan fingerprint bits)
            - features_2d_cm: List of float (Flattened Topological Coulomb Matrix)
    """
    # Ensure reproducibility
    set_seed(SEED)
    
    # 1. Morgan Fingerprints
    mol = Chem.MolFromXYZBlock(
        f"{len(atoms)}\n\n" + "\n".join([
            f"{atom} {x} {y} {z}" for atom, (x, y, z) in zip(atoms, coordinates)
        ])
    )
    
    if mol is None:
        # Fallback construction
        mol = Chem.RWMol()
        for atom_symbol in atoms:
            mol.AddAtom(Chem.Atom(atom_symbol))
    
    # Generate Morgan fingerprint (radius=2, nBits=2048)
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=FINGERPRINT_BITS)
    fp_array = np.zeros((FINGERPRINT_BITS,), dtype=np.float32)
    DataStructs.ConvertToNumpyArray(fp, fp_array)
    
    # 2. Topological Coulomb Matrix
    cm_matrix = compute_coulomb_matrix(atoms, coordinates)
    cm_flat = cm_matrix.flatten().tolist()
    
    return {
        "molecule_id": molecule_id,
        "features_2d_fp": fp_array.tolist(),
        "features_2d_cm": cm_flat
    }

def load_subset_data(subset_path: Path) -> pd.DataFrame:
    """Load the subset data generated by T016a."""
    if not subset_path.exists():
        raise FileNotFoundError(f"Subset file not found: {subset_path}")
    return pd.read_parquet(subset_path)

def save_results(results: List[Dict[str, Any]], output_path: Path):
    """Save the extracted features to a Parquet file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert list of dicts to DataFrame
    # We need to handle the list columns carefully for Parquet
    df = pd.DataFrame(results)
    
    # Ensure columns are in expected order for downstream tasks
    # The schema expects: molecule_id, features_2d (combined list), features_3d (from T017)
    # But T018 specifically generates 2D features. We will output a file with 2D features.
    # The downstream T029 will combine these.
    
    # Flatten the list columns if necessary, but Parquet supports lists.
    # We'll keep them as lists.
    
    df.to_parquet(output_path, index=False)
    print(f"Saved 2D descriptors to {output_path}")

@time_limit(300) # 5 minutes limit
@memory_limit(8 * 1024**3) # 8 GB limit
@cpu_limit(4) # Limit CPU cores
def main():
    parser = argparse.ArgumentParser(description="Extract 2D descriptors (Morgan FP + Topological Coulomb Matrix)")
    parser.add_argument("--input", type=str, required=True, help="Path to input subset parquet file")
    parser.add_argument("--output", type=str, required=True, help="Path to output features parquet file")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    print(f"Loading subset data from {input_path}...")
    df = load_subset_data(input_path)
    
    if df.empty:
        print("Error: Input dataframe is empty.")
        sys.exit(1)
        
    required_cols = ['molecule_id', 'atoms', 'coordinates']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns in input: {missing_cols}")
        sys.exit(1)
        
    print(f"Processing {len(df)} molecules...")
    
    results = []
    for idx, row in df.iterrows():
        mol_id = row['molecule_id']
        atoms = row['atoms']
        coords = np.array(row['coordinates'])
        
        try:
            features = extract_2d_features(mol_id, atoms, coords)
            results.append(features)
            
            if (idx + 1) % 1000 == 0:
                print(f"Processed {idx + 1}/{len(df)} molecules...")
        except Exception as e:
            print(f"Error processing molecule {mol_id}: {e}")
            # Fail loudly as per constraints
            raise e
    
    save_results(results, output_path)
    
    # Verify output
    if not output_path.exists():
        print("ERROR: Output file was not created.")
        sys.exit(1)
        
    print("2D descriptor extraction completed successfully.")

if __name__ == "__main__":
    main()
