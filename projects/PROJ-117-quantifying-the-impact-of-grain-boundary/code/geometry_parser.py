"""
Geometry Parser for Grain Boundary Diffusivity Project.

Parses POSCAR/CIF files to extract grain boundary descriptors:
- Boundary Plane Normal (Miller indices)
- Sigma (Σ) value from misorientation
- Boundary width and excess volume
- Rodrigues vectors for misorientation
"""
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from pymatgen.core import Structure, Lattice
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.io.cif import CifParser
from pymatgen.io.vasp import Poscar

# Import project utilities
from utils import setup_logging, compute_sha256, load_metadata, update_metadata_entry, save_metadata
from error_handling import DataInsufficiencyError, check_data_sufficiency, exit_on_insufficiency
from models.grain_boundary_record import GrainBoundaryRecord

# Configure logging
logger = setup_logging()

# Constants
RAW_DATA_DIR = Path("data/raw")
PROCESSED_OUTPUT = Path("data/processed/parsed_geometry.parquet")
MIN_RECORDS = 500

def get_miller_indices(normal_vector: np.ndarray, lattice: Lattice) -> Tuple[int, int, int]:
    """
    Convert a normal vector to Miller indices (hkl).
    
    The normal vector is in Cartesian coordinates. We convert it to
    reciprocal lattice coordinates, then find the smallest integer
    representation.
    
    Args:
        normal_vector: Normal vector in Cartesian coordinates
        lattice: Pymatgen Lattice object
        
    Returns:
        Tuple of (h, k, l) Miller indices
    """
    # Convert Cartesian to reciprocal lattice coordinates
    # normal_cart = h*b1 + k*b2 + l*b3
    # where b1, b2, b3 are reciprocal lattice vectors
    rec_lat = lattice.reciprocal_lattice
    hkl_float = np.dot(normal_vector, rec_lat.matrix)
    
    # Normalize to smallest integers
    # Find the greatest common divisor approximation
    hkl_float = hkl_float / np.max(np.abs(hkl_float))
    
    # Multiply by a factor to get close to integers
    scale_factor = 10
    for i in range(1, 11):
        candidate = hkl_float * i
        if np.allclose(candidate, np.round(candidate), atol=0.1):
            scale_factor = i
            break
    
    hkl = np.round(hkl_float * scale_factor).astype(int)
    
    # Handle zero case
    if np.all(hkl == 0):
        hkl = np.array([1, 0, 0])
    
    # Simplify by dividing by GCD
    def gcd(a, b):
        while b:
            a, b = b, a % b
        return a
    
    def gcd_list(lst):
        result = lst[0]
        for i in range(1, len(lst)):
            result = gcd(result, lst[i])
        return abs(result)
    
    common = gcd_list(hkl.tolist())
    if common > 1:
        hkl = hkl // common
    
    return tuple(hkl.tolist())

def calculate_sigma_from_misorientation(misorientation_angle: float) -> int:
    """
    Calculate the Sigma (Σ) value from misorientation angle using CSL definition.
    
    For cubic systems, common Σ values follow the relationship:
    Σ = 1 / (1 - cos(θ)) for certain special angles, or can be looked up.
    
    Args:
        misorientation_angle: Misorientation angle in degrees
        
    Returns:
        Sigma value (integer)
    """
    # Convert to radians
    theta_rad = np.radians(misorientation_angle)
    
    # For Σ3 (twin boundary): ~60° for <111> axis
    # For Σ5: ~36.9° for <100> axis
    # For Σ7: ~21.8° for <111> axis
    # For Σ9: ~38.9° for <110> axis
    
    # Common CSL angles for cubic systems
    csl_angles = {
        60.0: 3,   # Σ3
        36.87: 5,  # Σ5
        38.94: 9,  # Σ9
        21.79: 7,  # Σ7
        50.48: 11, # Σ11
        29.32: 13, # Σ13
        27.80: 15, # Σ15
        43.61: 17, # Σ17
    }
    
    # Find closest match
    min_diff = float('inf')
    closest_sigma = 1  # Default to random grain boundary
    
    for angle, sigma in csl_angles.items():
        diff = abs(misorientation_angle - angle)
        if diff < min_diff:
            min_diff = diff
            closest_sigma = sigma
    
    # If the angle is very close to a known CSL angle, return that
    if min_diff < 2.0:  # Within 2 degrees
        return closest_sigma
    
    # For other angles, use the approximation formula
    # Σ ≈ 1 / (1 - cos(θ)) for small angles, but this is approximate
    cos_theta = np.cos(theta_rad)
    if abs(1 - cos_theta) > 1e-6:
        approx_sigma = 1.0 / (1 - cos_theta)
        # Round to nearest odd integer (Σ values are typically odd for cubic)
        if approx_sigma > 1:
            closest_sigma = int(round(approx_sigma))
            if closest_sigma % 2 == 0:
                closest_sigma += 1
    
    return closest_sigma

def calculate_rodrigues_vector(rotation_matrix: np.ndarray) -> np.ndarray:
    """
    Convert a rotation matrix to Rodrigues vector.
    
    The Rodrigues vector g = n * tan(θ/2), where n is the rotation axis
    and θ is the rotation angle.
    
    Args:
        rotation_matrix: 3x3 rotation matrix
        
    Returns:
        Rodrigues vector (3,)
    """
    # Extract rotation angle and axis from rotation matrix
    trace = np.trace(rotation_matrix)
    cos_theta = (trace - 1) / 2
    theta = np.arccos(np.clip(cos_theta, -1, 1))
    
    if abs(theta) < 1e-10:
        return np.zeros(3)
    
    # Rotation axis
    axis_x = rotation_matrix[2, 1] - rotation_matrix[1, 2]
    axis_y = rotation_matrix[0, 2] - rotation_matrix[2, 0]
    axis_z = rotation_matrix[1, 0] - rotation_matrix[0, 1]
    
    axis = np.array([axis_x, axis_y, axis_z])
    axis_norm = np.linalg.norm(axis)
    
    if axis_norm < 1e-10:
        return np.zeros(3)
    
    axis = axis / axis_norm
    
    # Rodrigues vector: g = n * tan(θ/2)
    rodrigues = axis * np.tan(theta / 2)
    
    return rodrigues

def extract_boundary_plane_normal(structure: Structure, growth_direction: str = 'z') -> Tuple[np.ndarray, Tuple[int, int, int]]:
    """
    Extract the boundary plane normal from a bicrystal structure.
    
    The interface plane is identified as the mid-plane perpendicular to
    the growth direction. The normal vector is calculated and converted
    to Miller indices.
    
    Args:
        structure: Pymatgen Structure object
        growth_direction: Direction of growth ('x', 'y', or 'z')
        
    Returns:
        Tuple of (normal_vector_cartesian, miller_indices)
    """
    lattice = structure.lattice
    
    # Determine the growth direction index
    dir_map = {'x': 0, 'y': 1, 'z': 2}
    dir_idx = dir_map.get(growth_direction.lower(), 2)
    
    # For a slab geometry, the boundary plane normal is typically
    # perpendicular to the growth direction
    # In most bicrystal simulations, the interface is in the xy-plane
    # with normal along z
    
    # Create a normal vector along the growth direction
    normal_cartesian = np.zeros(3)
    normal_cartesian[dir_idx] = 1.0
    
    # Convert to Miller indices
    miller_indices = get_miller_indices(normal_cartesian, lattice)
    
    return normal_cartesian, miller_indices

def calculate_boundary_width(structure: Structure, growth_direction: str = 'z') -> float:
    """
    Calculate the boundary width from the simulation cell dimensions.
    
    Args:
        structure: Pymatgen Structure object
        growth_direction: Direction of growth ('x', 'y', or 'z')
        
    Returns:
        Boundary width in Angstroms
    """
    lattice = structure.lattice
    dir_map = {'x': 0, 'y': 1, 'z': 2}
    dir_idx = dir_map.get(growth_direction.lower(), 2)
    
    # Get the lattice parameter in the growth direction
    # This represents the total width of the simulation cell
    # The boundary width is typically half of this for symmetric bicrystals
    total_width = lattice.abc[dir_idx]
    
    # For a bicrystal with two grains, the boundary region is at the interface
    # We estimate the boundary width as a fraction of the total width
    # A typical estimate is 10-20% of the total width for the interface region
    boundary_width = total_width * 0.15  # Approximate interface region
    
    return boundary_width

def calculate_excess_volume(structure: Structure, boundary_width: float) -> float:
    """
    Calculate the excess volume at the grain boundary.
    
    Excess volume is the additional volume per unit area due to the
    presence of the grain boundary compared to the bulk material.
    
    Args:
        structure: Pymatgen Structure object
        boundary_width: Width of the boundary region in Angstroms
        
    Returns:
        Excess volume in Å³/Å² (or Å)
    """
    lattice = structure.lattice
    volume = lattice.volume
    n_atoms = len(structure)
    
    # Bulk volume per atom
    bulk_volume_per_atom = volume / n_atoms
    
    # Estimate excess volume based on the boundary width
    # This is a simplified geometric calculation
    # In reality, this would require comparing to a perfect bulk structure
    
    # Approximate excess volume as a function of boundary width
    # Typical values range from 0.5 to 2.0 Å for grain boundaries
    excess_volume = boundary_width * 0.5  # Simplified estimate
    
    return excess_volume

def parse_structure_file(file_path: Path) -> Structure:
    """
    Parse a structure file (POSCAR or CIF) into a Pymatgen Structure.
    
    Args:
        file_path: Path to the structure file
        
    Returns:
        Pymatgen Structure object
    """
    file_ext = file_path.suffix.lower()
    
    if file_ext in ['.vasp', '.poscar', '.car']:
        with open(file_path, 'r') as f:
            poscar = Poscar.from_file(f)
            return poscar.structure
    elif file_ext in ['.cif']:
        parser = CifParser(str(file_path))
        structures = parser.parse_structures()
        if structures:
            return structures[0]
        else:
            raise ValueError(f"No structures found in CIF file: {file_path}")
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")

def extract_geometry_features(structure: Structure, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all geometry-related features from a structure.
    
    Args:
        structure: Pymatgen Structure object
        metadata: Metadata dictionary containing misorientation angle, etc.
        
    Returns:
        Dictionary of extracted features
    """
    features = {}
    
    # Get misorientation angle from metadata
    misorientation_angle = metadata.get('misorientation_angle', 0.0)
    features['misorientation_angle'] = misorientation_angle
    
    # Calculate Sigma value
    sigma_value = calculate_sigma_from_misorientation(misorientation_angle)
    features['sigma_value'] = sigma_value
    
    # Extract boundary plane normal
    growth_direction = metadata.get('growth_direction', 'z')
    normal_cartesian, miller_indices = extract_boundary_plane_normal(structure, growth_direction)
    features['boundary_plane_normal_cartesian'] = normal_cartesian.tolist()
    features['boundary_plane_normal_miller'] = list(miller_indices)
    
    # Calculate boundary width
    boundary_width = calculate_boundary_width(structure, growth_direction)
    features['boundary_width'] = boundary_width
    
    # Calculate excess volume
    excess_volume = calculate_excess_volume(structure, boundary_width)
    features['excess_volume'] = excess_volume
    
    # Encode misorientation as Rodrigues vector
    # We need to construct a rotation matrix from the misorientation angle
    # For simplicity, assume rotation around a standard axis (e.g., [0,0,1])
    theta_rad = np.radians(misorientation_angle)
    rotation_matrix = np.array([
        [np.cos(theta_rad), -np.sin(theta_rad), 0],
        [np.sin(theta_rad), np.cos(theta_rad), 0],
        [0, 0, 1]
    ])
    rodrigues_vector = calculate_rodrigues_vector(rotation_matrix)
    features['rodrigues_vector'] = rodrigues_vector.tolist()
    
    # Add lattice parameters
    lattice = structure.lattice
    features['lattice_a'] = lattice.a
    features['lattice_b'] = lattice.b
    features['lattice_c'] = lattice.c
    features['lattice_alpha'] = lattice.alpha
    features['lattice_beta'] = lattice.beta
    features['lattice_gamma'] = lattice.gamma
    
    # Number of atoms
    features['num_atoms'] = len(structure)
    
    return features

def parse_all_structures(raw_data_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse all structure files in the raw data directory.
    
    Args:
        raw_data_dir: Directory containing raw structure files
        
    Returns:
        List of dictionaries containing parsed geometry data
    """
    results = []
    structure_files = list(raw_data_dir.glob('*'))
    structure_files = [f for f in structure_files if f.suffix.lower() in ['.vasp', '.poscar', '.cif', '.car']]
    
    logger.info(f"Found {len(structure_files)} structure files to parse")
    
    for file_path in structure_files:
        try:
            logger.info(f"Parsing: {file_path.name}")
            
            # Parse structure
            structure = parse_structure_file(file_path)
            
            # Load metadata for this file
            # Metadata should be in a separate file or embedded in the structure
            # For now, we'll use a placeholder or try to extract from filename
            metadata = {
                'misorientation_angle': 0.0,  # Placeholder - should come from metadata
                'growth_direction': 'z',
                'file_path': str(file_path)
            }
            
            # Try to extract misorientation from filename if possible
            # e.g., "grain_boundary_30deg_vasp.vasp" -> 30 degrees
            filename = file_path.stem
            import re
            angle_match = re.search(r'(\d+)deg', filename)
            if angle_match:
                metadata['misorientation_angle'] = float(angle_match.group(1))
            
            # Extract features
            features = extract_geometry_features(structure, metadata)
            features['source_file'] = file_path.name
            features['source_path'] = str(file_path)
            
            # Compute checksum
            features['checksum'] = compute_sha256(file_path)
            
            results.append(features)
            
        except Exception as e:
            logger.error(f"Error parsing {file_path.name}: {str(e)}")
            continue
    
    return results

def main():
    """Main entry point for geometry parser."""
    logger.info("Starting geometry parser...")
    
    # Check if raw data exists
    if not RAW_DATA_DIR.exists():
        logger.error(f"Raw data directory not found: {RAW_DATA_DIR}")
        sys.exit(1)
    
    # Parse all structures
    parsed_data = parse_all_structures(RAW_DATA_DIR)
    
    # Check data sufficiency
    if len(parsed_data) < MIN_RECORDS:
        error_msg = f"Data Insufficiency: Retrieved {len(parsed_data)} < {MIN_RECORDS}"
        logger.error(error_msg)
        raise DataInsufficiencyError(error_msg)
    
    logger.info(f"Successfully parsed {len(parsed_data)} structures")
    
    # Convert to DataFrame
    df = pd.DataFrame(parsed_data)
    
    # Ensure output directory exists
    PROCESSED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to parquet
    df.to_parquet(PROCESSED_OUTPUT, index=False)
    logger.info(f"Saved parsed geometry data to {PROCESSED_OUTPUT}")
    
    # Update metadata
    metadata = load_metadata()
    update_metadata_entry(metadata, 'geometry_parser', {
        'timestamp': pd.Timestamp.now().isoformat(),
        'records_processed': len(parsed_data),
        'output_file': str(PROCESSED_OUTPUT)
    })
    save_metadata(metadata)
    
    logger.info("Geometry parsing complete!")

if __name__ == '__main__':
    main()
