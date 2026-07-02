"""
Extract physics-based features from CIF files.

This module calculates H-bond capacity, aromatic fraction, and thermodynamic
confounders from CIF metadata and 3D geometry.
"""
import os
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np

# Import from project modules
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import setup_logging, fix_seed
from error_handling import CIFParseError, MissingMetadataError, safe_cif_read, get_cif_metadata_summary
from config import ensure_directories

logger = setup_logging(__name__)

def parse_cif_metadata(cif_content: str) -> Dict[str, Any]:
    """
    Parse metadata from CIF content.
    
    Args:
        cif_content: Content of the CIF file
        
    Returns:
        Dictionary of parsed metadata
    """
    metadata = {}
    
    # Common metadata fields
    field_patterns = {
        'cell_a': r'_cell_length_a\s+(\S+)',
        'cell_b': r'_cell_length_b\s+(\S+)',
        'cell_c': r'_cell_length_c\s+(\S+)',
        'alpha': r'_cell_angle_alpha\s+(\S+)',
        'beta': r'_cell_angle_beta\s+(\S+)',
        'gamma': r'_cell_angle_gamma\s+(\S+)',
        'formula': r'_chemical_formula_sum\s+(\S+)',
        'space_group': r'_space_group_name_H-M_alt\s+(\S+)',
        'density': r'_exptl_crystal_density_diffrn\s+(\S+)',
        'temperature': r'_diffrn_ambient_temperature\s+(\S+)',
        'pressure': r'_diffrn_ambient_pressure\s+(\S+)',
    }
    
    for key, pattern in field_patterns.items():
        match = re.search(pattern, cif_content)
        if match:
            try:
                metadata[key] = float(match.group(1))
            except ValueError:
                metadata[key] = match.group(1)
    
    return metadata

def extract_atomic_coordinates(cif_content: str) -> List[Tuple[str, float, float, float]]:
    """
    Extract atomic coordinates from CIF content.
    
    Args:
        cif_content: Content of the CIF file
        
    Returns:
        List of (atom_type, x, y, z) tuples
    """
    atoms = []
    
    # Find atom site loop
    lines = cif_content.split('\n')
    in_atom_loop = False
    atom_data = []
    
    for i, line in enumerate(lines):
        if '_atom_site_label' in line:
            in_atom_loop = True
            continue
        
        if in_atom_loop:
            if line.startswith('_') or line.startswith('loop_'):
                in_atom_loop = False
                continue
            if line.strip() and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 4:
                    label = parts[0]
                    x, y, z = parts[1], parts[2], parts[3]
                    try:
                        # Extract atom type from label (e.g., C1 -> C)
                        atom_type = re.match(r'^([A-Z][a-z]?)', label)
                        if atom_type:
                            atom_type = atom_type.group(1)
                            atoms.append((atom_type, float(x), float(y), float(z)))
                    except ValueError:
                        continue
    
    return atoms

def calculate_h_bond_capacity(atoms: List[Tuple[str, float, float, float]]) -> Dict[str, int]:
    """
    Calculate hydrogen bond capacity (donors and acceptors).
    
    Args:
        atoms: List of (atom_type, x, y, z) tuples
        
    Returns:
        Dictionary with 'donors' and 'acceptors' counts
    """
    # Simplified H-bond capacity calculation
    # Donors: N-H, O-H groups
    # Acceptors: N, O, F atoms with lone pairs
    
    donors = 0
    acceptors = 0
    
    atom_types = [atom[0] for atom in atoms]
    
    # Count potential donors (N, O atoms that could be in H-bonding groups)
    # This is a simplified heuristic
    n_count = atom_types.count('N')
    o_count = atom_types.count('O')
    
    # Simplified: assume each N and O could be a donor/acceptor
    # In reality, this depends on the molecular structure
    donors = min(n_count + o_count, 10)  # Cap at 10 for simplicity
    acceptors = n_count + o_count
    
    return {'donors': donors, 'acceptors': acceptors}

def calculate_aromatic_fraction(atoms: List[Tuple[str, float, float, float]]) -> float:
    """
    Calculate aromatic ring fraction.
    
    Args:
        atoms: List of (atom_type, x, y, z) tuples
        
    Returns:
        Fraction of atoms in aromatic rings (simplified)
    """
    # Simplified: count carbon atoms as potentially aromatic
    # In reality, this requires structural analysis
    c_count = sum(1 for atom in atoms if atom[0] == 'C')
    total_atoms = len(atoms)
    
    if total_atoms == 0:
        return 0.0
    
    # Heuristic: assume ~30% of carbons are in aromatic rings
    aromatic_carbons = int(c_count * 0.3)
    return aromatic_carbons / total_atoms if total_atoms > 0 else 0.0

def extract_physics_features(cif_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract all physics features from a CIF file.
    
    Args:
        cif_path: Path to the CIF file
        
    Returns:
        Dictionary of physics features, or None if extraction fails
    """
    cif_content = safe_cif_read(cif_path)
    if cif_content is None:
        return None
    
    try:
        # Parse metadata
        metadata = parse_cif_metadata(cif_content)
        
        # Extract coordinates
        atoms = extract_atomic_coordinates(cif_content)
        if not atoms:
            logger.warning(f"No atoms found in {cif_path}")
            return None
        
        # Calculate H-bond capacity
        h_bond_capacity = calculate_h_bond_capacity(atoms)
        
        # Calculate aromatic fraction
        aromatic_fraction = calculate_aromatic_fraction(atoms)
        
        # Extract confounders
        confounders = {
            'temperature': metadata.get('temperature', 298.0),  # Default to room temp
            'pressure': metadata.get('pressure', 1.0),  # Default to 1 atm
            'cell_volume': None
        }
        
        # Calculate cell volume if cell parameters are available
        if all(k in metadata for k in ['cell_a', 'cell_b', 'cell_c', 'alpha', 'beta', 'gamma']):
            a, b, c = metadata['cell_a'], metadata['cell_b'], metadata['cell_c']
            alpha, beta, gamma = np.radians(metadata['alpha']), np.radians(metadata['beta']), np.radians(metadata['gamma'])
            volume = a * b * c * np.sqrt(
                1 - np.cos(alpha)**2 - np.cos(beta)**2 - np.cos(gamma)**2 +
                2 * np.cos(alpha) * np.cos(beta) * np.cos(gamma)
            )
            confounders['cell_volume'] = volume
        
        return {
            'h_bond_donors': h_bond_capacity['donors'],
            'h_bond_acceptors': h_bond_capacity['acceptors'],
            'aromatic_fraction': aromatic_fraction,
            'confounders': confounders,
            'atom_count': len(atoms)
        }
        
    except Exception as e:
        logger.error(f"Failed to extract physics features from {cif_path}: {e}")
        return None

def main():
    """
    Main function to extract physics features from all CIFs in data/raw_cif/.
    """
    fix_seed()
    
    # Ensure directories exist
    project_root = ensure_directories()
    raw_cif_dir = os.path.join(project_root, "data", "raw_cif")
    
    if not os.path.exists(raw_cif_dir):
        logger.error(f"Raw CIF directory not found: {raw_cif_dir}")
        return
    
    # Find all CIF files
    cif_files = [f for f in os.listdir(raw_cif_dir) if f.endswith('.cif')]
    
    if not cif_files:
        logger.warning("No CIF files found in data/raw_cif/")
        return
    
    logger.info(f"Found {len(cif_files)} CIF files to process")
    
    # Extract features for each CIF
    results = []
    for cif_file in cif_files:
        cif_path = os.path.join(raw_cif_dir, cif_file)
        features = extract_physics_features(cif_path)
        
        if features:
            results.append({
                'cif_id': cif_file.replace('.cif', ''),
                **features
            })
    
    # Create DataFrame
    if results:
        df = pd.DataFrame(results)
        output_path = os.path.join(project_root, "data", "physics_features.csv")
        df.to_csv(output_path, index=False)
        logger.info(f"Saved physics features to {output_path}")
    else:
        logger.warning("No valid physics features extracted")

if __name__ == "__main__":
    main()