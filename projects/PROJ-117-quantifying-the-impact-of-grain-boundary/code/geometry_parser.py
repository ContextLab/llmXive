"""
Geometry parser for grain boundary structures.

This module handles the parsing of POSCAR/CIF files to extract geometric features
relevant to grain boundary character, including:
- Boundary plane normal (Miller indices)
- Sigma (Σ) value from misorientation
- Boundary width and excess volume
- Rodrigues vector encoding
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from pymatgen.core import Structure, Lattice
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.analysis.structure_matcher import StructureMatcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_sigma_from_misorientation(misorientation_angle_deg: float) -> int:
    """
    Calculate the Sigma (Σ) value from misorientation angle using CSL definition.

    For cubic systems, common Σ values are derived from specific misorientation
    angles. This function uses a lookup table for common angles and an
    approximation for others.

    Args:
        misorientation_angle_deg: Misorientation angle in degrees.

    Returns:
        Sigma value (integer). Returns -1 if no common CSL match is found.
    """
    # Common CSL misorientation angles for cubic systems (approximate)
    # Format: (angle, sigma)
    csl_table = [
        (38.94, 3),   # Σ3
        (50.48, 9),   # Σ9
        (60.00, 3),   # Σ3 (twin)
        (70.53, 3),   # Σ3 (another variant)
        (28.95, 27),  # Σ27
        (31.60, 27),  # Σ27
        (36.87, 5),   # Σ5
        (53.13, 5),   # Σ5
        (21.80, 13),  # Σ13
        (27.80, 13),  # Σ13
        (43.60, 13),  # Σ13
        (46.40, 13),  # Σ13
    ]

    # Find closest match in table
    best_sigma = -1
    min_diff = float('inf')

    for angle, sigma in csl_table:
        diff = abs(misorientation_angle_deg - angle)
        if diff < min_diff:
            min_diff = diff
            best_sigma = sigma

    # If within tolerance, return the match
    if min_diff < 2.0:  # 2 degree tolerance
        return best_sigma

    # For non-standard angles, use approximation: Σ ≈ 1 / (1 - cos(θ))
    # This is a rough approximation and may not yield integer Σ
    theta_rad = np.radians(misorientation_angle_deg)
    if np.abs(1 - np.cos(theta_rad)) < 1e-6:
        return -1  # Avoid division by zero

    sigma_approx = 1.0 / (1 - np.cos(theta_rad))

    # Round to nearest integer and check if it's a valid CSL (odd integer for cubic)
    sigma_rounded = int(round(sigma_approx))
    if sigma_rounded > 0 and sigma_rounded % 2 == 1:
        return sigma_rounded

    return -1  # No valid CSL match


def calculate_rodrigues_vector(rotation_matrix: np.ndarray) -> np.ndarray:
    """
    Calculate Rodrigues vector from rotation matrix.

    The Rodrigues vector is a compact representation of 3D rotations.

    Args:
        rotation_matrix: 3x3 rotation matrix.

    Returns:
        Rodrigues vector (3-element array).
    """
    # Extract rotation angle from trace of rotation matrix
    trace = np.trace(rotation_matrix)
    theta = np.arccos(np.clip((trace - 1) / 2, -1, 1))

    if np.abs(theta) < 1e-6:
        return np.zeros(3)

    # Extract rotation axis
    axis = np.array([
        rotation_matrix[2, 1] - rotation_matrix[1, 2],
        rotation_matrix[0, 2] - rotation_matrix[2, 0],
        rotation_matrix[1, 0] - rotation_matrix[0, 1]
    ]) / (2 * np.sin(theta))

    # Rodrigues vector = axis * tan(theta/2)
    rod = axis * np.tan(theta / 2)
    return rod


def get_miller_indices(normal_vector: np.ndarray, lattice: Lattice) -> Tuple[int, int, int]:
    """
    Convert a normal vector to Miller indices (hkl).

    Args:
        normal_vector: Normal vector in Cartesian coordinates.
        lattice: Pymatgen Lattice object.

    Returns:
        Tuple of (h, k, l) Miller indices.
    """
    # Convert Cartesian to fractional coordinates
    frac_coords = lattice.get_fractional_coords(normal_vector)

    # Normalize to smallest integer ratio
    # Multiply by a large factor to avoid floating point issues
    scaled = frac_coords * 1000
    rounded = np.round(scaled)

    # Find GCD to reduce to smallest integers
    gcd_val = np.gcd.reduce(np.abs(rounded.astype(int)))
    if gcd_val > 0:
        hkl = (rounded / gcd_val).astype(int)
    else:
        hkl = rounded.astype(int)

    # Ensure at least one non-zero component
    if np.all(hkl == 0):
        hkl = np.array([1, 0, 0])

    return tuple(hkl)


def extract_boundary_plane_normal(structure: Structure, growth_direction: str = 'z') -> np.ndarray:
    """
    Extract the boundary plane normal from a bicrystal structure.

    Identifies the interface plane by locating the mid-plane of the simulation
    cell perpendicular to the growth direction.

    Args:
        structure: Pymatgen Structure object.
        growth_direction: Direction of the simulation cell growth ('x', 'y', or 'z').

    Returns:
        Normal vector to the boundary plane in Cartesian coordinates.
    """
    lattice = structure.lattice

    # Determine which axis corresponds to growth direction
    if growth_direction.lower() == 'x':
        axis_idx = 0
    elif growth_direction.lower() == 'y':
        axis_idx = 1
    elif growth_direction.lower() == 'z':
        axis_idx = 2
    else:
        raise ValueError(f"Invalid growth direction: {growth_direction}")

    # Get lattice vectors
    lattice_vectors = lattice.matrix

    # The normal to the plane perpendicular to growth direction
    # is simply the lattice vector in that direction (normalized)
    normal = lattice_vectors[axis_idx]
    normal = normal / np.linalg.norm(normal)

    return normal


def calculate_boundary_width(structure: Structure, growth_direction: str = 'z') -> float:
    """
    Calculate the boundary width from the structure dimensions.

    Args:
        structure: Pymatgen Structure object.
        growth_direction: Direction of the simulation cell growth.

    Returns:
        Boundary width in Angstroms.
    """
    lattice = structure.lattice

    if growth_direction.lower() == 'x':
        return lattice.a
    elif growth_direction.lower() == 'y':
        return lattice.b
    elif growth_direction.lower() == 'z':
        return lattice.c
    else:
        raise ValueError(f"Invalid growth direction: {growth_direction}")


def calculate_excess_volume(structure: Structure, bulk_density: float, boundary_width: float) -> float:
    """
    Calculate excess volume at the grain boundary.

    Excess volume is the additional volume per unit area due to the grain boundary.

    Args:
        structure: Pymatgen Structure object.
        bulk_density: Density of the bulk material (atoms/Angstrom^3).
        boundary_width: Width of the boundary region (Angstroms).

    Returns:
        Excess volume per unit area (Angstrom).
    """
    # Calculate total volume of the structure
    total_volume = structure.volume

    # Calculate number of atoms
    n_atoms = len(structure)

    # Expected volume for bulk material
    expected_volume = n_atoms / bulk_density

    # Excess volume
    excess_vol_total = total_volume - expected_volume

    # Excess volume per unit area (assuming the boundary spans the cross-section)
    # Cross-sectional area perpendicular to growth direction
    lattice = structure.lattice
    if boundary_width == lattice.a:  # Growth in x
        cross_section_area = lattice.b * lattice.c
    elif boundary_width == lattice.b:  # Growth in y
        cross_section_area = lattice.a * lattice.c
    else:  # Growth in z
        cross_section_area = lattice.a * lattice.b

    if cross_section_area == 0:
        return 0.0

    excess_vol_per_area = excess_vol_total / cross_section_area

    return excess_vol_per_area


def parse_structure_file(file_path: str) -> Optional[Structure]:
    """
    Parse a structure file (POSCAR or CIF).

    Args:
        file_path: Path to the structure file.

    Returns:
        Pymatgen Structure object, or None if parsing fails.
    """
    path = Path(file_path)

    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    try:
        if path.suffix.lower() in ['.vasp', '.poscar', '.car']:
            structure = Structure.from_file(file_path, fmt='vasp')
        elif path.suffix.lower() == '.cif':
            structure = Structure.from_file(file_path, fmt='cif')
        else:
            # Try to detect format
            structure = Structure.from_file(file_path)

        logger.info(f"Successfully parsed structure from {file_path}")
        return structure

    except Exception as e:
        logger.error(f"Failed to parse structure from {file_path}: {e}")
        return None


def extract_geometry_features(structure: Structure, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all geometric features from a structure.

    Args:
        structure: Pymatgen Structure object.
        metadata: Dictionary containing metadata like misorientation angle,
                 growth direction, bulk density, etc.

    Returns:
        Dictionary of extracted geometric features.
    """
    features = {}

    # Get misorientation angle from metadata
    misorientation_angle = metadata.get('misorientation_angle', 0.0)

    # Calculate Sigma value
    sigma = calculate_sigma_from_misorientation(misorientation_angle)
    features['sigma_value'] = sigma

    # Get growth direction from metadata
    growth_direction = metadata.get('growth_direction', 'z')

    # Extract boundary plane normal
    normal_vector = extract_boundary_plane_normal(structure, growth_direction)
    features['boundary_plane_normal_cartesian'] = normal_vector.tolist()

    # Convert to Miller indices
    lattice = structure.lattice
    miller_indices = get_miller_indices(normal_vector, lattice)
    features['boundary_plane_miller_indices'] = list(miller_indices)

    # Calculate boundary width
    boundary_width = calculate_boundary_width(structure, growth_direction)
    features['boundary_width'] = boundary_width

    # Get bulk density from metadata
    bulk_density = metadata.get('bulk_density', 0.1)  # Default fallback

    # Calculate excess volume
    excess_volume = calculate_excess_volume(structure, bulk_density, boundary_width)
    features['excess_volume_per_area'] = excess_volume

    # Calculate Rodrigues vector
    # For simplicity, we assume the rotation is around the growth direction
    # In a real implementation, this would use the actual rotation matrix
    rotation_angle_rad = np.radians(misorientation_angle)
    if growth_direction.lower() == 'x':
        rotation_axis = np.array([1, 0, 0])
    elif growth_direction.lower() == 'y':
        rotation_axis = np.array([0, 1, 0])
    else:  # z
        rotation_axis = np.array([0, 0, 1])

    # Create rotation matrix from axis-angle
    cos_theta = np.cos(rotation_angle_rad)
    sin_theta = np.sin(rotation_angle_rad)
    ux, uy, uz = rotation_axis

    rotation_matrix = np.array([
        [cos_theta + ux**2 * (1 - cos_theta), ux * uy * (1 - cos_theta) - uz * sin_theta, ux * uz * (1 - cos_theta) + uy * sin_theta],
        [uy * ux * (1 - cos_theta) + uz * sin_theta, cos_theta + uy**2 * (1 - cos_theta), uy * uz * (1 - cos_theta) - ux * sin_theta],
        [uz * ux * (1 - cos_theta) - uy * sin_theta, uz * uy * (1 - cos_theta) + ux * sin_theta, cos_theta + uz**2 * (1 - cos_theta)]
    ])

    rodrigues_vector = calculate_rodrigues_vector(rotation_matrix)
    features['rodrigues_vector'] = rodrigues_vector.tolist()

    # Additional structure info
    features['num_atoms'] = len(structure)
    features['volume'] = structure.volume
    features['density'] = len(structure) / structure.volume

    return features


def parse_all_structures(structure_files: List[str], metadata_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse multiple structure files and extract geometry features.

    Args:
        structure_files: List of paths to structure files.
        metadata_list: List of metadata dictionaries corresponding to each file.

    Returns:
        List of dictionaries containing extracted features.
    """
    results = []

    for i, (file_path, metadata) in enumerate(zip(structure_files, metadata_list)):
        logger.info(f"Processing file {i+1}/{len(structure_files)}: {file_path}")

        structure = parse_structure_file(file_path)
        if structure is None:
            logger.warning(f"Skipping {file_path} due to parsing failure")
            continue

        try:
            features = extract_geometry_features(structure, metadata)
            features['source_file'] = file_path
            results.append(features)
        except Exception as e:
            logger.error(f"Failed to extract features from {file_path}: {e}")
            continue

    logger.info(f"Successfully processed {len(results)} out of {len(structure_files)} files")
    return results


def main():
    """
    Main function to demonstrate geometry parsing.
    """
    # This would typically be called by a pipeline
    # For now, just log that the module is ready
    logger.info("Geometry parser module loaded successfully")


if __name__ == "__main__":
    main()
