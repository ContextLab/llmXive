from __future__ import annotations

import numpy as np
import pandas as pd
from typing import List, Dict, Any
import sys
from pathlib import Path

# Add project root to path to resolve relative imports if run as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the real data loader used in the pipeline
from data.download_qm9 import download_qm9
from data.create_subset import create_reproducible_subset

# Atom type mapping based on QM9 element indices (0: H, 1: C, 2: N, 3: O, 4: F)
ATOM_TYPES = {0: 'H', 1: 'C', 2: 'N', 3: 'O', 4: 'F'}
ATOM_ELECTRONEGATIVITY = {
    'H': 2.20, 'C': 2.55, 'N': 3.04, 'O': 3.44, 'F': 3.98
}

def extract_3d_features(
    subset_path: str | Path,
    output_path: str | Path,
    raw_data_dir: str | Path = "data/raw"
) -> Path:
    """
    Extract 3D coordinates, atom types, and bond connectivity from the QM9 subset.
    
    This function:
    1. Loads the molecule subset from the parquet file created by T016b.
    2. Downloads the QM9 dataset if not present.
    3. Parses the .xyz files for each molecule in the subset.
    4. Extracts atom types, 3D coordinates, and bond connectivity (distance-based).
    5. Computes derived features: bond lengths, bond angles, and electronegativity differences.
    6. Validates for NaN values and missing coordinates.
    7. Saves the processed features to a Parquet file.
    
    Args:
        subset_path: Path to the molecule subset parquet file.
        output_path: Path to save the processed 3D features.
        raw_data_dir: Directory where QM9 raw data is stored.
        
    Returns:
        Path to the output file.
    """
    subset_path = Path(subset_path)
    output_path = Path(output_path)
    raw_data_dir = Path(raw_data_dir)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load subset
    if not subset_path.exists():
        raise FileNotFoundError(f"Subset file not found: {subset_path}")
    
    subset_df = pd.read_parquet(subset_path)
    molecule_ids = subset_df['molecule_id'].tolist()
    
    # Download QM9 if necessary
    qm9_dir = download_qm9(raw_data_dir)
    molecules_path = qm9_dir / "molecules"
    
    if not molecules_path.exists():
        raise FileNotFoundError(f"QM9 molecules directory not found: {molecules_path}")
    
    processed_features = []
    excluded_molecules = []
    
    for mol_id in molecule_ids:
        # Construct filename for the molecule
        # QM9 molecules are stored as <molecule_id>.xyz
        xyz_file = molecules_path / f"{mol_id}.xyz"
        
        if not xyz_file.exists():
            excluded_molecules.append({
                'molecule_id': mol_id,
                'exclusion_reason': 'missing_3d',
                'exclusion_timestamp': pd.Timestamp.now().isoformat()
            })
            continue
        
        try:
            # Parse XYZ file
            atoms, coords, connectivity = parse_xyz_file(xyz_file)
            
            # Check for NaN or missing coordinates
            if np.any(np.isnan(coords)):
                excluded_molecules.append({
                    'molecule_id': mol_id,
                    'exclusion_reason': 'invalid_structure',
                    'exclusion_timestamp': pd.Timestamp.now().isoformat()
                })
                continue
            
            # Extract features
            features = extract_molecule_features(atoms, coords, connectivity)
            features['molecule_id'] = mol_id
            processed_features.append(features)
            
        except Exception as e:
            excluded_molecules.append({
                'molecule_id': mol_id,
                'exclusion_reason': f'invalid_structure: {str(e)}',
                'exclusion_timestamp': pd.Timestamp.now().isoformat()
            })
            continue
    
    # Save excluded molecules report
    if excluded_molecules:
        excluded_df = pd.DataFrame(excluded_molecules)
        excluded_report_path = output_path.parent / "excluded_molecules.csv"
        excluded_df.to_csv(excluded_report_path, index=False)
        print(f"Excluded {len(excluded_molecules)} molecules. Report saved to {excluded_report_path}")
    
    if not processed_features:
        raise RuntimeError("No molecules successfully processed. Check QM9 data availability and format.")
    
    # Create DataFrame from processed features
    features_df = pd.DataFrame(processed_features)
    
    # Validate no NaN values in feature vectors
    if features_df.isnull().any().any():
        nan_cols = features_df.columns[features_df.isnull().any()]
        raise ValueError(f"NaN values found in features for columns: {list(nan_cols)}")
    
    # Save to Parquet
    features_df.to_parquet(output_path, index=False)
    print(f"Successfully extracted 3D features for {len(processed_features)} molecules.")
    print(f"Output saved to: {output_path}")
    
    return output_path

def parse_xyz_file(xyz_path: Path) -> tuple[List[str], np.ndarray, List[tuple[int, int, float]]]:
    """
    Parse an XYZ file and extract atoms, coordinates, and connectivity.
    
    Args:
        xyz_path: Path to the XYZ file.
        
    Returns:
        Tuple of (atoms, coords, connectivity)
        - atoms: List of atom type strings (e.g., 'C', 'H')
        - coords: NumPy array of shape (n_atoms, 3) with coordinates
        - connectivity: List of (atom_idx1, atom_idx2, bond_length) tuples
    """
    with open(xyz_path, 'r') as f:
        lines = f.readlines()
    
    if len(lines) < 2:
        raise ValueError(f"Invalid XYZ file: {xyz_path}")
    
    # First line: number of atoms
    n_atoms = int(lines[0].strip())
    
    # Second line: comment (can be ignored for our purposes)
    # Remaining lines: atom type and coordinates
    atoms = []
    coords = []
    
    for line in lines[2:2+n_atoms]:
        parts = line.strip().split()
        if len(parts) < 4:
            continue
        
        atom_type = parts[0]
        x, y, z = map(float, parts[1:4])
        
        atoms.append(atom_type)
        coords.append([x, y, z])
    
    if len(atoms) != n_atoms:
        raise ValueError(f"Mismatch in atom count for {xyz_path}: expected {n_atoms}, got {len(atoms)}")
    
    coords = np.array(coords)
    
    # Compute connectivity based on distance threshold
    connectivity = compute_connectivity(coords)
    
    return atoms, coords, connectivity

def compute_connectivity(coords: np.ndarray, bond_threshold: float = 1.7) -> List[tuple[int, int, float]]:
    """
    Compute bond connectivity based on interatomic distances.
    
    Args:
        coords: NumPy array of shape (n_atoms, 3)
        bond_threshold: Maximum distance for a bond to exist (in Angstroms)
        
    Returns:
        List of (atom_idx1, atom_idx2, bond_length) tuples
    """
    n_atoms = len(coords)
    connectivity = []
    
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            dist = np.linalg.norm(coords[i] - coords[j])
            if dist < bond_threshold:
                connectivity.append((i, j, dist))
    
    return connectivity

def extract_molecule_features(
    atoms: List[str],
    coords: np.ndarray,
    connectivity: List[tuple[int, int, float]]
) -> Dict[str, Any]:
    """
    Extract features for a single molecule.
    
    Args:
        atoms: List of atom type strings
        coords: NumPy array of shape (n_atoms, 3)
        connectivity: List of (atom_idx1, atom_idx2, bond_length) tuples
        
    Returns:
        Dictionary of features
    """
    n_atoms = len(atoms)
    
    # Basic molecular properties
    atom_types_encoded = [list(ATOM_TYPES.values()).index(atom) for atom in atoms]
    electronegativity_values = [ATOM_ELECTRONEGATIVITY[atom] for atom in atoms]
    
    # Bond features
    bond_lengths = [bond[2] for bond in connectivity]
    n_bonds = len(connectivity)
    avg_bond_length = np.mean(bond_lengths) if bond_lengths else 0.0
    min_bond_length = np.min(bond_lengths) if bond_lengths else 0.0
    max_bond_length = np.max(bond_lengths) if bond_lengths else 0.0
    
    # Electronegativity differences along bonds
    if connectivity:
        electronegativity_diffs = []
        for i, j, _ in connectivity:
            diff = abs(electronegativity_values[i] - electronegativity_values[j])
            electronegativity_diffs.append(diff)
        avg_electronegativity_diff = np.mean(electronegativity_diffs)
        max_electronegativity_diff = np.max(electronegativity_diffs)
    else:
        avg_electronegativity_diff = 0.0
        max_electronegativity_diff = 0.0
    
    # 3D geometric features
    center_of_mass = np.mean(coords, axis=0)
    coords_centered = coords - center_of_mass
    radius_of_gyration = np.sqrt(np.mean(np.sum(coords_centered**2, axis=1)))
    
    # Dipole moment vector (simplified: based on electronegativity and geometry)
    # In reality, this would come from QM calculations, but we can compute a proxy
    # for feature extraction purposes.
    # Note: The actual dipole moment is in the QM9 data and will be used as the target.
    
    # Compile features
    features = {
        'n_atoms': n_atoms,
        'n_bonds': n_bonds,
        'avg_bond_length': avg_bond_length,
        'min_bond_length': min_bond_length,
        'max_bond_length': max_bond_length,
        'avg_electronegativity_diff': avg_electronegativity_diff,
        'max_electronegativity_diff': max_electronegativity_diff,
        'radius_of_gyration': radius_of_gyration,
        # Store atom types as a string for simplicity
        'atom_types': ','.join(atoms),
        # Store coordinates as a flattened list (can be reshaped later)
        'coordinates': coords.flatten().tolist(),
        # Store connectivity as a list of tuples (flattened for storage)
        'connectivity': [(i, j, round(d, 4)) for i, j, d in connectivity],
    }
    
    return features

def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract 3D features from QM9 subset")
    parser.add_argument(
        "--subset-path",
        type=str,
        default="data/processed/subset_final.parquet",
        help="Path to the molecule subset parquet file"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/processed/features_3d.parquet",
        help="Path to save the processed 3D features"
    )
    parser.add_argument(
        "--raw-data-dir",
        type=str,
        default="data/raw",
        help="Directory where QM9 raw data is stored"
    )
    
    args = parser.parse_args()
    
    extract_3d_features(
        subset_path=args.subset_path,
        output_path=args.output_path,
        raw_data_dir=args.raw_data_dir
    )

if __name__ == "__main__":
    main()