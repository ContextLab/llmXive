"""
Symmetry handling module for FCC crystallography using orix.

This module provides utilities to ensure correct component identification
for FCC crystals by applying proper symmetry operations and orientation
handling.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
from orix.quaternion import Orientation, Rotation
from orix.crystal_map import CrystalMap
from orix.space_group import SpaceGroup
from orix.vector import Vector3d
from orix.quaternion.symmetry import Oh

# Import local utilities
from utils.logging import get_logger

logger = get_logger(__name__)


def get_fcc_symmetry() -> Oh:
    """
    Return the full cubic symmetry (Oh) for FCC crystals.

    Returns:
        Oh: The octahedral symmetry group for FCC crystals.
    """
    return Oh


def align_orientations_to_fcc(orientations: np.ndarray) -> Orientation:
    """
    Convert raw Euler angles (in degrees, Bunge convention) to orix Orientations
    and align them to the fundamental zone of FCC symmetry.

    Args:
        orientations: Array of shape (N, 3) containing Euler angles (phi1, Phi, phi2)
                    in degrees.

    Returns:
        Orientation: orix Orientation object with symmetry applied and
                    orientations mapped to the fundamental zone.
    """
    logger.debug(f"Aligning {orientations.shape[0]} orientations to FCC symmetry")

    # Convert degrees to radians for orix
    euler_rad = np.radians(orientations)

    # Create Rotation object from Euler angles (Bunge convention)
    rotation = Rotation.from_euler(euler_rad, convention="bunge")

    # Create Orientation with FCC symmetry (Oh)
    symmetry = get_fcc_symmetry()
    orientation = Orientation(rotation, symmetry=symmetry)

    # Map to fundamental zone
    orientation = orientation.map2fundamental()

    logger.debug("Orientation alignment complete")
    return orientation


def find_closest_component(
    orientation: Orientation,
    component_angles: Dict[str, Tuple[float, float, float, float]]
) -> Tuple[str, float]:
    """
    Find the closest texture component for a given orientation using orix distance.

    Args:
        orientation: A single orix Orientation object.
        component_angles: Dictionary mapping component names to their Euler angle
                        ranges (phi1_min, phi1_max, Phi_min, Phi_max) in degrees.

    Returns:
        Tuple of (closest_component_name, minimum_distance).
    """
    min_distance = np.inf
    closest_component = "Unknown"

    for component_name, (phi1_min, phi1_max, phi_min, phi_max) in component_angles.items():
        # Calculate center of the search range
        phi1_center = np.radians((phi1_min + phi1_max) / 2)
        phi_center = np.radians((phi_min + phi_max) / 2)
        phi2_center = np.radians((phi1_min + phi1_max) / 2)  # Assuming same range for phi2

        # Create reference rotation for this component
        ref_rotation = Rotation.from_euler(
            [[phi1_center, phi_center, phi2_center]],
            convention="bunge"
        )
        ref_orientation = Orientation(ref_rotation, symmetry=get_fcc_symmetry())
        ref_orientation = ref_orientation.map2fundamental()

        # Calculate distance using orix's built-in distance metric
        distance = orientation.distance(ref_orientation).item()

        if distance < min_distance:
            min_distance = distance
            closest_component = component_name

    return closest_component, min_distance


def classify_orientations_to_components(
    orientations: np.ndarray,
    component_angles: Dict[str, Tuple[float, float, float, float]],
    distance_threshold: float = 0.2
) -> Dict[str, List[int]]:
    """
    Classify a set of orientations into texture components based on orix distance.

    Args:
        orientations: Array of shape (N, 3) containing Euler angles in degrees.
        component_angles: Dictionary mapping component names to Euler angle ranges.
        distance_threshold: Maximum distance to consider a match (in radians).

    Returns:
        Dictionary mapping component names to lists of indices of matching orientations.
    """
    logger.info(f"Classifying {orientations.shape[0]} orientations to components")

    # Align all orientations to FCC symmetry
    aligned_orientations = align_orientations_to_fcc(orientations)

    classification = {name: [] for name in component_angles.keys()}
    classification["Unassigned"] = []

    for i, orientation in enumerate(aligned_orientations):
        component_name, distance = find_closest_component(orientation, component_angles)

        if distance <= distance_threshold:
            classification[component_name].append(i)
        else:
            classification["Unassigned"].append(i)

    logger.info(f"Classification complete: {len(classification['Unassigned'])} unassigned")
    return classification


def calculate_symmetry_equivalent_count(orientation: Orientation) -> int:
    """
    Calculate the number of symmetry equivalents for a given orientation.

    Args:
        orientation: A single orix Orientation object.

    Returns:
        int: Number of symmetry equivalents.
    """
    return orientation.symmetry.order


def validate_fcc_symmetry_application(orientations: np.ndarray) -> Dict[str, Any]:
    """
    Validate that symmetry application is working correctly.

    Args:
        orientations: Array of shape (N, 3) containing Euler angles in degrees.

    Returns:
        Dictionary with validation metrics.
    """
    logger.info("Validating FCC symmetry application")

    aligned = align_orientations_to_fcc(orientations)

    # Check that all orientations are in the fundamental zone
    in_fundamental_zone = aligned._is_in_fundamental_zone()
    percent_in_fz = np.mean(in_fundamental_zone) * 100

    # Check symmetry order consistency
    symmetry_orders = [o.symmetry.order for o in aligned]
    unique_orders = set(symmetry_orders)

    validation_result = {
        "total_orientations": len(orientations),
        "percent_in_fundamental_zone": percent_in_fundamental_zone,
        "unique_symmetry_orders": list(unique_orders),
        "all_fcc_symmetry": all(order == 48 for order in unique_orders)  # Oh has 48 elements
    }

    logger.info(
        f"Validation complete: {percent_in_fundamental_zone:.2f}% in fundamental zone, "
        f"all FCC symmetry: {validation_result['all_fcc_symmetry']}"
    )

    return validation_result


def main():
    """
    Main entry point for symmetry validation and testing.
    """
    logger.info("Starting symmetry handling module validation")

    # Example usage with synthetic data for demonstration
    # In production, this would be called from preprocess.py or descriptors.py
    sample_euler_angles = np.array([
        [0, 0, 0],      # Cube component
        [35, 45, 35],   # Copper component
        [39, 45, 0],    # S component
        [0, 45, 0],     # Goss component
        [45, 45, 0],    # Brass component
    ])

    # Validate symmetry application
    validation = validate_fcc_symmetry_application(sample_euler_angles)
    logger.info(f"Validation results: {validation}")

    # Define standard FCC texture components (from T018)
    fcc_components = {
        "Brass": (35, 45, 35, 45),
        "Copper": (35, 45, 35, 45),
        "S": (35, 45, 35, 45),
        "Goss": (35, 45, 35, 45),
        "Cube": (0, 10, 0, 10),
    }

    # Classify sample orientations
    classification = classify_orientations_to_components(
        sample_euler_angles,
        fcc_components,
        distance_threshold=0.3
    )

    logger.info("Classification results:")
    for component, indices in classification.items():
        if indices:
            logger.info(f"  {component}: {len(indices)} orientations")

    logger.info("Symmetry handling module validation complete")


if __name__ == "__main__":
    main()