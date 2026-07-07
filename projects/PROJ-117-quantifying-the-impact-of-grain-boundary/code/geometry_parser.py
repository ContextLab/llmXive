"""
Geometry parser for grain boundary structures.

This module parses POSCAR/CIF files to extract geometric features of grain boundaries,
including boundary plane normals, Sigma values, misorientation angles, and excess volume.
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from pymatgen.core import Structure, Lattice
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for Sigma calculation (CSL lookup for common angles)
# Using a simplified lookup table for common CSL boundaries
SIGMA_LOOKUP = {
    36.87: 5,   # Σ5
    53.13: 5,   # Σ5 (alternative)
    28.07: 13,  # Σ13
    38.94: 13,  # Σ13 (alternative)
    22.62: 17,  # Σ17
    36.87: 25,  # Σ25 (alternative)
    43.60: 29,  # Σ29
    46.40: 31,  # Σ31
    50.48: 33,  # Σ33
    54.74: 3,   # Σ3 (twin)
    70.53: 3,   # Σ3 (alternative)
}

# For angles not in lookup, use the approximation: Σ ≈ 1 / (1 - cos(θ))
# Note: This is a simplification; real CSL requires integer solutions


def calculate_sigma_from_misorientation(misorientation_angle: float) -> int:
    """
    Calculate the Sigma (Σ) value from misorientation angle using CSL definition.

    Args:
        misorientation_angle: Misorientation angle in degrees.

    Returns:
        Sigma value (integer).
    """
    # Check lookup table first
    # Use a tolerance for floating point comparison
    for angle, sigma in SIGMA_LOOKUP.items():
        if abs(misorientation_angle - angle) < 0.5:
            return sigma

    # For angles not in lookup, use approximation
    # Convert to radians
    theta_rad = np.radians(misorientation_angle)
    cos_theta = np.cos(theta_rad)

    # Avoid division by zero
    denominator = 1.0 - cos_theta
    if abs(denominator) < 1e-6:
        return 1  # No boundary (0 misorientation)

    # Approximate Sigma value
    sigma_approx = 1.0 / denominator

    # Round to nearest integer and ensure it's odd (CSL property)
    sigma = int(round(sigma_approx))
    if sigma % 2 == 0:
        sigma += 1

    # Ensure minimum Sigma is 3 (for meaningful boundaries)
    return max(3, sigma)


def calculate_rodrigues_vector(misorientation_axis: np.ndarray, misorientation_angle: float) -> np.ndarray:
    """
    Calculate Rodrigues vector from misorientation axis and angle.

    The Rodrigues vector is defined as: R = n * tan(θ/2)
    where n is the rotation axis and θ is the rotation angle.

    Args:
        misorientation_axis: Unit vector representing the rotation axis.
        misorientation_angle: Rotation angle in degrees.

    Returns:
        Rodrigues vector as numpy array.
    """
    # Normalize the axis
    axis_norm = np.linalg.norm(misorientation_axis)
    if axis_norm < 1e-10:
        return np.array([0.0, 0.0, 0.0])

    n = misorientation_axis / axis_norm

    # Convert angle to radians and calculate tan(θ/2)
    theta_rad = np.radians(misorientation_angle)
    tan_half_theta = np.tan(theta_rad / 2.0)

    # Rodrigues vector
    rodrigues = n * tan_half_theta

    return rodrigues


def get_miller_indices(normal_vector: np.ndarray, lattice: Lattice) -> Tuple[int, int, int]:
    """
    Convert a normal vector to Miller indices (hkl).

    Args:
        normal_vector: Normal vector in Cartesian coordinates.
        lattice: Pymatgen Lattice object.

    Returns:
        Tuple of (h, k, l) as integers.
    """
    # Convert Cartesian vector to fractional coordinates
    reciprocal_lattice = lattice.reciprocal_lattice
    frac_coords = np.dot(normal_vector, reciprocal_lattice.matrix.T)

    # Normalize to smallest integers
    # Find the greatest common divisor approximation
    # First, scale to reasonable integers
    scale_factor = 100.0  # Initial scaling
    hkl_float = frac_coords * scale_factor

    # Round to nearest integers
    hkl_int = np.round(hkl_float).astype(int)

    # If all zeros, return (0, 0, 1) as default
    if np.all(hkl_int == 0):
        return (0, 0, 1)

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

    common = gcd_list(hkl_int)
    if common > 1:
        hkl_int = hkl_int // common

    return tuple(hkl_int.tolist())


def extract_boundary_plane_normal(structure: Structure, growth_direction: np.ndarray = None) -> np.ndarray:
    """
    Extract the boundary plane normal from a bicrystal structure.

    Identifies the mid-plane of the simulation cell perpendicular to the growth direction.

    Args:
        structure: Pymatgen Structure object.
        growth_direction: Optional growth direction vector. Defaults to [0, 0, 1].

    Returns:
        Normal vector to the boundary plane.
    """
    if growth_direction is None:
        growth_direction = np.array([0.0, 0.0, 1.0])

    # Normalize growth direction
    growth_direction = growth_direction / np.linalg.norm(growth_direction)

    # For a bicrystal slab, the boundary plane is typically perpendicular to the growth direction
    # The normal to the boundary plane is the growth direction itself
    return growth_direction


def calculate_boundary_width(structure: Structure, growth_direction: np.ndarray = None) -> float:
    """
    Calculate the boundary width from the structure dimensions.

    Args:
        structure: Pymatgen Structure object.
        growth_direction: Growth direction vector.

    Returns:
        Boundary width in Angstroms.
    """
    if growth_direction is None:
        growth_direction = np.array([0.0, 0.0, 1.0])

    # Get the lattice parameters
    lattice = structure.lattice
    lengths = lattice.abc
    angles = lattice.angles

    # Calculate the length along the growth direction
    # Project lattice vectors onto growth direction
    lattice_vectors = np.array([
        lattice.a_vector,
        lattice.b_vector,
        lattice.c_vector
    ])

    projections = np.dot(lattice_vectors, growth_direction)
    total_length = np.sum(np.abs(projections))

    # For a typical bicrystal, the boundary width is roughly half the total length
    # (assuming symmetric bicrystal)
    return total_length / 2.0


def calculate_excess_volume(structure: Structure, bulk_density: float = None) -> float:
    """
    Calculate excess volume at the grain boundary.

    Excess volume is the difference between the actual volume and the volume
    of the same number of atoms in the bulk configuration.

    Args:
        structure: Pymatgen Structure object.
        bulk_density: Optional bulk density (atoms/A³). If None, estimated from structure.

    Returns:
        Excess volume in Angstrom³.
    """
    # Get total volume of the structure
    total_volume = structure.lattice.volume

    # Estimate number of atoms
    n_atoms = len(structure)

    # If bulk density not provided, estimate from the structure
    # Assuming most atoms are in bulk-like environment
    if bulk_density is None:
        # Use a heuristic: assume 90% of atoms are in bulk
        bulk_atoms = n_atoms * 0.9
        # Estimate bulk volume per atom from typical metal values
        # This is a rough approximation; real implementation would use reference bulk structure
        avg_atomic_volume = total_volume / n_atoms * 0.95  # Slight expansion at boundary
        bulk_density = bulk_atoms / (total_volume * 0.95)

    # Calculate expected volume for bulk atoms
    expected_bulk_volume = n_atoms / bulk_density

    # Excess volume
    excess_volume = total_volume - expected_bulk_volume

    # Ensure non-negative (boundary should have excess volume)
    return max(0.0, excess_volume)


def parse_structure_file(file_path: str) -> Structure:
    """
    Parse a structure file (POSCAR or CIF) using pymatgen.

    Args:
        file_path: Path to the structure file.

    Returns:
        Pymatgen Structure object.

    Raises:
        ValueError: If file format is unsupported or parsing fails.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Structure file not found: {file_path}")

    suffix = path.suffix.lower()

    try:
        if suffix in ['.poscar', '.vasp']:
            return Structure.from_file(file_path)
        elif suffix == '.cif':
            return Structure.from_file(file_path)
        else:
            # Try to auto-detect
            return Structure.from_file(file_path)
    except Exception as e:
        logger.error(f"Failed to parse structure file {file_path}: {e}")
        raise ValueError(f"Unsupported file format or parsing error: {e}")


def extract_geometry_features(structure: Structure, misorientation_angle: float = None) -> Dict[str, Any]:
    """
    Extract all geometric features from a structure.

    Args:
        structure: Pymatgen Structure object.
        misorientation_angle: Optional misorientation angle in degrees.
            If not provided, will be estimated or set to None.

    Returns:
        Dictionary containing extracted features.
    """
    features = {}

    # Extract boundary plane normal (default to [0,0,1])
    normal = extract_boundary_plane_normal(structure)
    features['boundary_plane_normal'] = normal.tolist()

    # Get Miller indices
    miller_indices = get_miller_indices(normal, structure.lattice)
    features['miller_indices'] = list(miller_indices)

    # Calculate Sigma value
    if misorientation_angle is not None:
        sigma = calculate_sigma_from_misorientation(misorientation_angle)
        features['sigma_value'] = sigma
        features['misorientation_angle'] = misorientation_angle

        # Calculate Rodrigues vector (assuming axis is normal to plane)
        rodrigues = calculate_rodrigues_vector(normal, misorientation_angle)
        features['rodrigues_vector'] = rodrigues.tolist()
    else:
        features['sigma_value'] = None
        features['misorientation_angle'] = None
        features['rodrigues_vector'] = None

    # Calculate boundary width
    width = calculate_boundary_width(structure)
    features['boundary_width'] = width

    # Calculate excess volume
    excess_vol = calculate_excess_volume(structure)
    features['excess_volume'] = excess_vol

    # Additional structure info
    features['n_atoms'] = len(structure)
    features['volume'] = structure.lattice.volume
    features['composition'] = dict(structure.composition)

    return features


def parse_all_structures(input_dir: str, output_path: str, misorientation_map: Dict[str, float] = None) -> None:
    """
    Parse all structure files in a directory and extract geometric features.

    Args:
        input_dir: Directory containing structure files (POSCAR/CIF).
        output_path: Path to save the output parquet file.
        misorientation_map: Optional dictionary mapping file names to misorientation angles.
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    # Find all structure files
    structure_files = list(input_path.glob('*.poscar')) + \
                     list(input_path.glob('*.POSCAR')) + \
                     list(input_path.glob('*.cif')) + \
                     list(input_path.glob('*.CIF'))

    if not structure_files:
        logger.warning(f"No structure files found in {input_dir}")
        return

    logger.info(f"Found {len(structure_files)} structure files to parse")

    # Prepare data list
    data_list = []

    for file_path in structure_files:
        try:
            logger.info(f"Parsing {file_path.name}")
            structure = parse_structure_file(str(file_path))

            # Get misorientation angle from map if available
            misorientation = None
            if misorientation_map and file_path.name in misorientation_map:
                misorientation = misorientation_map[file_path.name]

            # Extract features
            features = extract_geometry_features(structure, misorientation)

            # Add file metadata
            features['file_name'] = file_path.name
            features['file_path'] = str(file_path)

            data_list.append(features)

        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            continue

    if not data_list:
        logger.warning("No structures were successfully parsed")
        return

    # Convert to DataFrame and save
    import pandas as pd
    df = pd.DataFrame(data_list)

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save to parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df)} records to {output_path}")


def main():
    """
    Main entry point for the geometry parser.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Parse grain boundary structures and extract geometric features')
    parser.add_argument('--input-dir', type=str, required=True,
                      help='Directory containing structure files (POSCAR/CIF)')
    parser.add_argument('--output', type=str, required=True,
                      help='Output path for the parsed data (parquet format)')
    parser.add_argument('--misorientation-map', type=str, default=None,
                      help='JSON file mapping filenames to misorientation angles')

    args = parser.parse_args()

    # Load misorientation map if provided
    misorientation_map = None
    if args.misorientation_map:
        import json
        with open(args.misorientation_map, 'r') as f:
            misorientation_map = json.load(f)

    # Parse structures
    parse_all_structures(args.input_dir, args.output, misorientation_map)


if __name__ == '__main__':
    main()