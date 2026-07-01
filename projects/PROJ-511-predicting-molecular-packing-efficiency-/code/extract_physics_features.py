"""
extract_physics_features.py

Calculates H-bond capacity (donor/acceptor counts), aromatic ring fraction,
and thermodynamic confounders (temperature, solvent presence) from CIF metadata
and 3D geometry.

Reads raw CIFs from data/raw_cif/ and produces data/physics_features.csv.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np

# Import from local project modules
from utils import fix_seed, setup_logging
from error_handling import (
    CIFParseError,
    MissingMetadataError,
    handle_corrupt_cif,
    validate_required_metadata,
    safe_cif_read,
    get_cif_metadata_summary,
    log_processing_statistics
)
from config import ensure_directories

# Ensure we have a random seed for reproducibility if needed later
fix_seed(42)

logger = logging.getLogger(__name__)

# Constants for H-bond detection (approximate van der Waals radii in Angstroms)
# Based on Bondi radii (T006 reference)
R_VDW = {
    'H': 1.20,
    'C': 1.70,
    'N': 1.55,
    'O': 1.52,
    'F': 1.47,
    'S': 1.80,
    'P': 1.80,
    'Cl': 1.75,
    'Br': 1.85,
    'I': 1.98
}

# H-bond donor atoms (typically N, O, S with H attached)
# H-bond acceptor atoms (typically N, O, S with lone pairs)
H_BOND_DONOR_ATOMS = {'N', 'O', 'S'}
H_BOND_ACCEPTOR_ATOMS = {'N', 'O', 'S', 'F', 'Cl', 'Br', 'I'}

# Threshold for H-bond distance (sum of van der Waals radii * factor)
H_BOND_DISTANCE_THRESHOLD = 0.6  # 0.6 * (r1 + r2) is a common cutoff for H-bonds

def parse_cif_metadata(cif_content: str) -> Dict[str, Any]:
    """
    Extract metadata from CIF content.

    Args:
        cif_content: Raw CIF file content as string

    Returns:
        Dictionary of metadata fields
    """
    metadata = {}

    # Common CIF metadata keys
    key_mappings = {
        '_chemical_formula_sum': 'formula',
        '_chemical_name_systematic': 'name',
        '_cell_length_a': 'a',
        '_cell_length_b': 'b',
        '_cell_length_c': 'c',
        '_cell_angle_alpha': 'alpha',
        '_cell_angle_beta': 'beta',
        '_cell_angle_gamma': 'gamma',
        '_cell_volume': 'volume',
        '_symmetry_space_group_name_H-M': 'space_group',
        '_exptl_crystal_growth_temperature': 'temp_growth',
        '_exptl_crystal_growth_method': 'growth_method',
        '_exptl_solvent': 'solvent',
        '_diffrn_ambient_temperature': 'temp_ambient',
        '_reflns_number_total': 'num_reflections'
    }

    lines = cif_content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('_') and not line.startswith('_atom_site'):
            # Parse key-value pair
            parts = line.split(None, 1)
            if len(parts) == 2:
                key, value = parts
                # Remove quotes if present
                value = value.strip("'\"")
                # Map to our internal keys
                if key in key_mappings:
                    metadata[key_mappings[key]] = value

    # Try to extract temperature from various fields
    temp = None
    if 'temp_growth' in metadata:
        try:
            temp = float(metadata['temp_growth'])
        except (ValueError, TypeError):
            pass
    elif 'temp_ambient' in metadata:
        try:
            temp = float(metadata['temp_ambient'])
        except (ValueError, TypeError):
            pass

    if temp is not None:
        metadata['temperature'] = temp

    # Check for solvent presence
    metadata['has_solvent'] = False
    if 'solvent' in metadata and metadata['solvent']:
        # Simple heuristic: if solvent field is not empty or contains common solvent names
        solvent_val = str(metadata['solvent']).lower()
        if solvent_val and solvent_val not in ['.', '?', 'none', 'null', '']:
            metadata['has_solvent'] = True

    return metadata

def extract_atomic_coordinates(cif_content: str) -> List[Tuple[str, float, float, float]]:
    """
    Extract atomic coordinates from CIF content.

    Args:
        cif_content: Raw CIF file content as string

    Returns:
        List of tuples (element, x, y, z)
    """
    atoms = []
    lines = cif_content.split('\n')

    in_atom_site = False
    element_idx = None
    x_idx = None
    y_idx = None
    z_idx = None

    for line in lines:
        line = line.strip()

        if line.startswith('loop_'):
            in_atom_site = False
            element_idx = None
            x_idx = None
            y_idx = None
            z_idx = None
            continue

        if line.startswith('_atom_site'):
            in_atom_site = True
            # Parse column headers
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0]
                if key == '_atom_site_label':
                    pass  # label
                elif key == '_atom_site_type_symbol':
                    element_idx = len(atoms)  # Will be updated later
                elif key == '_atom_site_fract_x':
                    x_idx = len(atoms)
                elif key == '_atom_site_fract_y':
                    y_idx = len(atoms)
                elif key == '_atom_site_fract_z':
                    z_idx = len(atoms)
            continue

        if in_atom_site and line and not line.startswith('#'):
            parts = line.split()
            if len(parts) >= 4:
                # We need to map indices properly
                # This is a simplified parser; real CIFs may have different formats
                try:
                    element = parts[0] if element_idx is None else parts[element_idx] if element_idx < len(parts) else None
                    x = float(parts[1] if x_idx is None else parts[x_idx] if x_idx < len(parts) else 0)
                    y = float(parts[2] if y_idx is None else parts[y_idx] if y_idx < len(parts) else 0)
                    z = float(parts[3] if z_idx is None else parts[z_idx] if z_idx < len(parts) else 0)

                    # Extract element symbol (first letters)
                    element = re.match(r'^([A-Z][a-z]?)', parts[0])
                    if element:
                        atoms.append((element.group(1), x, y, z))
                except (ValueError, IndexError):
                    continue

    return atoms

def calculate_h_bond_capacity(atoms: List[Tuple[str, float, float, float]], 
                             cell_params: Dict[str, float]) -> Tuple[int, int]:
    """
    Calculate H-bond donor and acceptor counts based on atomic positions.

    This is a simplified geometric estimation based on proximity of H-bond
    capable atoms.

    Args:
        atoms: List of (element, x, y, z) tuples
        cell_params: Dictionary with cell dimensions (a, b, c, alpha, beta, gamma)

    Returns:
        Tuple of (donor_count, acceptor_count)
    """
    if not atoms:
        return 0, 0

    # Convert fractional to Cartesian coordinates
    a = cell_params.get('a', 10.0)
    b = cell_params.get('b', 10.0)
    c = cell_params.get('c', 10.0)
    alpha = cell_params.get('alpha', 90.0)
    beta = cell_params.get('beta', 90.0)
    gamma = cell_params.get('gamma', 90.0)

    # Convert angles to radians
    alpha_rad = np.radians(alpha)
    beta_rad = np.radians(beta)
    gamma_rad = np.radians(gamma)

    # Volume calculation
    vol = a * b * c * np.sqrt(
        1 - np.cos(alpha_rad)**2 - np.cos(beta_rad)**2 - np.cos(gamma_rad)**2
        + 2 * np.cos(alpha_rad) * np.cos(beta_rad) * np.cos(gamma_rad)
    )

    # Simple Cartesian conversion (assuming orthorhombic for simplicity)
    # For more accurate conversion, full matrix transformation is needed
    cartesian_atoms = []
    for element, x, y, z in atoms:
        # Simplified: assume orthogonal cell
        cx = x * a
        cy = y * b
        cz = z * c
        cartesian_atoms.append((element, cx, cy, cz))

    donors = 0
    acceptors = 0

    # Count atoms that can act as donors or acceptors
    for element, x, y, z in cartesian_atoms:
        if element in H_BOND_DONOR_ATOMS:
            donors += 1
        if element in H_BOND_ACCEPTOR_ATOMS:
            acceptors += 1

    # In a real implementation, we would check distances between H and acceptor atoms
    # For now, we use a simplified count based on atom types
    # This is a proxy that can be refined with full geometry analysis

    return donors, acceptors

def calculate_aromatic_fraction(atoms: List[Tuple[str, float, float, float]]) -> float:
    """
    Calculate the fraction of atoms that are part of aromatic systems.

    This is a simplified estimation based on the presence of C, N, O atoms
    in typical aromatic configurations.

    Args:
        atoms: List of (element, x, y, z) tuples

    Returns:
        Fraction of aromatic atoms (0.0 to 1.0)
    """
    if not atoms:
        return 0.0

    # Count carbon and nitrogen atoms (common in aromatic rings)
    aromatic_candidates = sum(1 for elem, _, _, _ in atoms if elem in ['C', 'N'])
    total_atoms = len(atoms)

    # This is a heuristic; a real implementation would use RDKit or similar
    # to detect aromatic rings from 3D geometry
    # For now, we assume ~30-50% of C/N atoms are aromatic in organic crystals
    aromatic_ratio = 0.4 if total_atoms > 0 else 0.0
    aromatic_count = int(aromatic_candidates * aromatic_ratio)

    return aromatic_count / total_atoms if total_atoms > 0 else 0.0

def extract_physics_features(cif_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract physics features from a single CIF file.

    Args:
        cif_path: Path to CIF file

    Returns:
        Dictionary of extracted features or None if extraction fails
    """
    try:
        # Read CIF content
        cif_content = safe_cif_read(cif_path)
        if not cif_content:
            logger.warning(f"Failed to read CIF file: {cif_path}")
            return None

        # Parse metadata
        metadata = parse_cif_metadata(cif_content)

        # Extract atomic coordinates
        atoms = extract_atomic_coordinates(cif_content)

        # Calculate cell parameters for coordinate conversion
        cell_params = {
            'a': float(metadata.get('a', 10.0)),
            'b': float(metadata.get('b', 10.0)),
            'c': float(metadata.get('c', 10.0)),
            'alpha': float(metadata.get('alpha', 90.0)),
            'beta': float(metadata.get('beta', 90.0)),
            'gamma': float(metadata.get('gamma', 90.0))
        }

        # Calculate H-bond capacity
        donor_count, acceptor_count = calculate_h_bond_capacity(atoms, cell_params)

        # Calculate aromatic fraction
        aromatic_fraction = calculate_aromatic_fraction(atoms)

        # Extract thermodynamic confounders
        temperature = metadata.get('temperature', None)
        has_solvent = metadata.get('has_solvent', False)

        # Build feature dictionary
        features = {
            'cif_file': os.path.basename(cif_path),
            'h_bond_donors': donor_count,
            'h_bond_acceptors': acceptor_count,
            'h_bond_capacity': donor_count + acceptor_count,
            'aromatic_fraction': aromatic_fraction,
            'temperature': temperature,
            'has_solvent': has_solvent,
            'num_atoms': len(atoms),
            'cell_volume': cell_params['a'] * cell_params['b'] * cell_params['c'] if all([cell_params['a'], cell_params['b'], cell_params['c']]) else None
        }

        return features

    except Exception as e:
        logger.error(f"Error extracting features from {cif_path}: {e}")
        handle_corrupt_cif(cif_path, str(e))
        return None

def main():
    """
    Main function to process all CIF files and generate physics features CSV.
    """
    # Setup logging
    logger = setup_logging("extract_physics_features")
    logger.info("Starting physics feature extraction")

    # Ensure output directories exist
    ensure_directories()

    # Input and output paths
    cif_dir = "data/raw_cif"
    output_path = "data/physics_features.csv"

    if not os.path.exists(cif_dir):
        logger.error(f"CIF directory not found: {cif_dir}")
        logger.error("Please run T012 (download_cif.py) first to populate data/raw_cif/")
        return

    # Find all CIF files
    cif_files = [f for f in os.listdir(cif_dir) if f.lower().endswith('.cif')]

    if not cif_files:
        logger.warning(f"No CIF files found in {cif_dir}")
        # Create empty CSV with headers
        df = pd.DataFrame(columns=[
            'cif_file', 'h_bond_donors', 'h_bond_acceptors', 'h_bond_capacity',
            'aromatic_fraction', 'temperature', 'has_solvent', 'num_atoms', 'cell_volume'
        ])
        df.to_csv(output_path, index=False)
        logger.info(f"Created empty output file: {output_path}")
        return

    logger.info(f"Found {len(cif_files)} CIF files to process")

    # Process each CIF file
    all_features = []
    successful = 0
    failed = 0

    for cif_file in cif_files:
        cif_path = os.path.join(cif_dir, cif_file)
        logger.info(f"Processing: {cif_file}")

        features = extract_physics_features(cif_path)
        if features:
            all_features.append(features)
            successful += 1
        else:
            failed += 1

    # Create DataFrame and save
    if all_features:
        df = pd.DataFrame(all_features)
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully extracted features for {successful} files")
        logger.info(f"Failed to process {failed} files")
        logger.info(f"Output saved to: {output_path}")

        # Log processing statistics
        log_processing_statistics(
            total=len(cif_files),
            successful=successful,
            failed=failed,
            output_file=output_path
        )
    else:
        logger.warning("No features extracted. Creating empty output file.")
        df = pd.DataFrame(columns=[
            'cif_file', 'h_bond_donors', 'h_bond_acceptors', 'h_bond_capacity',
            'aromatic_fraction', 'temperature', 'has_solvent', 'num_atoms', 'cell_volume'
        ])
        df.to_csv(output_path, index=False)
        logger.info(f"Created empty output file: {output_path}")

if __name__ == "__main__":
    main()
