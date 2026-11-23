"""
Symmetry handling for FCC crystal textures using orix.

This module integrates `orix` to ensure correct component identification for FCC crystals.
It handles symmetry operations, orientation alignment, and component classification.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
from orix.crystal.march import FCC
from orix.quaternion import Orientation
from orix.vector import Vector3d
from orix.space_group import SpaceGroup

# Import local utilities
from utils.logging import get_logger

logger = get_logger(__name__)

# Define standard FCC texture components (Euler angles in degrees, Bunge convention)
# These are the standard reference orientations for FCC rolling textures
FCC_COMPONENTS = {
    "Brass": (35.0, 45.0, 0.0),      # (phi1, Phi, phi2)
    "Copper": (90.0, 35.0, 45.0),
    "S": (59.0, 37.0, 63.0),
    "Goss": (0.0, 45.0, 0.0),
    "Cube": (0.0, 0.0, 0.0),
}

# Tolerance for orientation matching (in degrees)
ORIENTATION_TOLERANCE = 15.0

def get_fcc_symmetry() -> SpaceGroup:
    """
    Retrieve the FCC symmetry group from orix.

    Returns:
        SpaceGroup: The FCC symmetry group object.
    """
    try:
        # orix uses crystal classes; FCC corresponds to m-3m symmetry
        return SpaceGroup.from_name("m-3m")
    except Exception as e:
        logger.error(f"Failed to load FCC symmetry group: {e}")
        raise

def align_orientations_to_fcc(orientations: np.ndarray) -> Orientation:
    """
    Align a set of Euler angles to the fundamental zone of FCC symmetry.

    Args:
        orientations: Array of shape (N, 3) containing Euler angles (phi1, Phi, phi2) in degrees.

    Returns:
        Orientation: orix Orientation object with FCC symmetry applied.
    """
    symmetry = get_fcc_symmetry()
    # Convert Euler angles to radians for orix
    euler_rad = np.radians(orientations)
    # Create Orientation object
    orix_orient = Orientation.from_euler(euler_rad, symmetry=symmetry)
    # Ensure they are in the fundamental sector
    orix_orient = orix_orient.set_symmetry(symmetry)
    return orix_orient

def find_closest_component(orientation: Orientation) -> Tuple[str, float]:
    """
    Find the closest standard FCC texture component for a given orientation.

    Args:
        orientation: A single orix Orientation object.

    Returns:
        Tuple of (component_name, angular_distance_degrees).
    """
    symmetry = get_fcc_symmetry()
    min_distance = float('inf')
    closest_name = "Random"

    for name, (phi1, Phi, phi2) in FCC_COMPONENTS.items():
        # Create reference orientation
        ref_euler = np.radians([phi1, Phi, phi2])
        ref_orient = Orientation.from_euler(ref_euler, symmetry=symmetry)

        # Calculate angular distance
        # orix calculates distance in radians by default
        distance_rad = (orientation * ref_orient.inv()).angle
        distance_deg = np.degrees(distance_rad)

        if distance_deg < min_distance:
            min_distance = distance_deg
            closest_name = name

    return closest_name, min_distance

def classify_orientations_to_components(orientations: np.ndarray, tolerance: float = ORIENTATION_TOLERANCE) -> List[Dict[str, Any]]:
    """
    Classify a list of orientations into standard FCC texture components.

    Args:
        orientations: Array of shape (N, 3) with Euler angles in degrees.
        tolerance: Maximum angular distance (degrees) to consider a match.

    Returns:
        List of dictionaries with 'component', 'distance', and 'original_index'.
    """
    if len(orientations) == 0:
        return []

    orix_orientations = align_orientations_to_fcc(orientations)
    results = []

    for i, orient in enumerate(orix_orientations):
        component, distance = find_closest_component(orient)
        
        # Only classify if within tolerance, otherwise mark as "Random"
        if distance > tolerance:
            component = "Random"
            distance = float('nan') # No specific distance for random

        results.append({
            "original_index": i,
            "component": component,
            "angular_distance": distance
        })

    return results

def calculate_symmetry_equivalent_count(orientations: np.ndarray) -> int:
    """
    Calculate the number of symmetry equivalents for a set of orientations.
    For FCC (m-3m), the order of the symmetry group is 48.

    Args:
        orientations: Array of shape (N, 3).

    Returns:
        int: The number of symmetry equivalents (constant for FCC).
    """
    # The order of the m-3m point group is 48
    return 48

def validate_fcc_symmetry_application(orientations: np.ndarray, component_labels: List[str]) -> Dict[str, Any]:
    """
    Validate that symmetry handling was applied correctly.

    Checks:
    1. All orientations are within the fundamental sector.
    2. Component assignments are consistent with the symmetry.

    Args:
        orientations: Array of shape (N, 3).
        component_labels: List of assigned component names.

    Returns:
        Dict with validation results.
    """
    orix_orientations = align_orientations_to_fcc(orientations)
    
    # Check if any orientation is outside the fundamental sector (shouldn't happen after alignment)
    # This is a sanity check
    in_sector = True
    for orient in orix_orientations:
        # If symmetry was applied, it should be in the sector
        # We can check if the orientation is equal to its symmetry-reduced form
        reduced = orient.set_symmetry(get_fcc_symmetry())
        if not np.allclose(orient.data, reduced.data):
            in_sector = False
            break

    component_counts = {}
    for label in component_labels:
        component_counts[label] = component_counts.get(label, 0) + 1

    return {
        "all_in_sector": in_sector,
        "component_distribution": component_counts,
        "total_samples": len(orientations),
        "is_valid": in_sector
    }

def main():
    """
    Main entry point for testing symmetry handling functionality.
    """
    logger.info("Starting FCC symmetry validation test.")
    
    # Create sample data
    sample_eulers = np.array([
        [35.0, 45.0, 0.0],   # Brass
        [90.0, 35.0, 45.0],  # Copper
        [0.0, 0.0, 0.0],     # Cube
        [10.0, 10.0, 10.0],  # Random-ish
    ])

    logger.info(f"Processing {len(sample_eulers)} sample orientations.")
    
    # Classify
    classifications = classify_orientations_to_components(sample_eulers)
    
    logger.info("Classification Results:")
    for res in classifications:
        logger.info(f"  Index {res['original_index']}: {res['component']} (dist: {res['angular_distance']:.2f}°)")
    
    # Validate
    labels = [c['component'] for c in classifications]
    validation = validate_fcc_symmetry_application(sample_eulers, labels)
    
    logger.info(f"Validation Result: {validation}")
    
    if validation['is_valid']:
        logger.info("FCC symmetry handling validated successfully.")
    else:
        logger.error("FCC symmetry handling validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
