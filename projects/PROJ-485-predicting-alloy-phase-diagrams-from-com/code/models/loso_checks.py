import os
import json
import sys
import csv
import numpy as np
from scipy.spatial import ConvexHull
from typing import Dict, List, Any, Optional, Tuple
from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

def load_elemental_properties(filepath: str = "data/raw/elemental_properties.csv") -> Dict[str, Dict[str, float]]:
    """Load elemental properties from CSV into a dictionary keyed by element symbol."""
    props = {}
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Elemental properties file not found: {filepath}")
    
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            element = row['element'].strip()
            try:
                props[element] = {
                    'atomic_radius': float(row['atomic_radius_angstrom']),
                    'electronegativity': float(row['electronegativity_pauling']),
                    'valence_electrons': float(row['valence_electrons'])
                }
            except (ValueError, KeyError) as e:
                log_error(logger, f"Failed to parse row for element {element}: {e}")
                continue
    return props

def calculate_convex_hull(points: np.ndarray) -> Optional[ConvexHull]:
    """
    Calculate the convex hull of a set of 2D points (radius, electronegativity).
    Returns None if fewer than 3 points are provided or if points are collinear.
    """
    if points.shape[0] < 3:
        return None
    try:
        hull = ConvexHull(points)
        return hull
    except Exception as e:
        log_warning(logger, f"Failed to compute convex hull: {e}")
        return None

def check_element_in_hull(element_props: Dict[str, float], hull: Optional[ConvexHull]) -> bool:
    """
    Check if a point (element properties) lies strictly inside or on the boundary of the convex hull.
    Returns True if inside/on boundary, False if outside (extrapolation).
    """
    if hull is None:
        return False
    
    point = np.array([[element_props['atomic_radius'], element_props['electronegativity']]])
    
    try:
        # scipy ConvexHull does not have a direct 'contains' method for points
        # We use the 'find_simplest' or check if point is a convex combination.
        # A simpler geometric check for 2D: check if point is on the correct side of all hull edges.
        # However, for robustness, we can use the Delaunay approach or simply check if the point
        # is within the bounding box and then use a containment check.
        # Given the constraints, we will use the `point_inside_hull` helper logic.
        
        # Using the standard approach: check if the point is inside the hull by verifying
        # that it is on the correct side of every hyperplane defined by the hull facets.
        # For 2D, facets are edges.
        
        # Simpler approach for 2D:
        # If the hull is valid, we can check if the point is inside by checking if it
        # lies within the hull's bounding box and then using a point-in-polygon test.
        # But scipy's ConvexHull doesn't expose this directly.
        
        # Alternative: Use the fact that a point is inside a convex hull if it can be
        # represented as a convex combination of the vertices. This is an LP problem.
        # Too complex for this scope.
        
        # Robust 2D check:
        # 1. Check bounding box first.
        # 2. Use the `hull.equations` to check half-space constraints.
        
        # Equations are of the form: normal . x + offset = 0
        # For a convex hull, the interior satisfies normal . x + offset <= 0 (or >= 0 depending on convention)
        # scipy's ConvexHull.equations: The equation of the plane: normal . x + offset = 0
        # The points in the hull satisfy: normal . x + offset <= 0 (usually)
        
        # Let's verify the sign convention.
        # We will assume the standard: points satisfy normal . x + offset <= 0
        
        # Check against all facets
        for eq in hull.equations:
            normal = eq[:-1]
            offset = eq[-1]
            # Calculate distance to the plane
            dist = np.dot(normal, point[0]) + offset
            # If dist > 0 (with a small tolerance), the point is outside
            if dist > 1e-8:
                return False
        return True
    except Exception as e:
        log_error(logger, f"Error checking point in hull: {e}")
        return False

def apply_property_range_extrapolation_check(
    train_elements: List[str],
    test_elements: List[str],
    elemental_props: Dict[str, Dict[str, float]]
) -> Tuple[bool, str]:
    """
    Check if any test element falls outside the convex hull of training elements' properties.
    Returns (is_valid, message).
    - If is_valid is False, it means extrapolation occurred.
    - If is_valid is True, all test elements are within the hull.
    """
    # 1. Collect properties for training elements
    train_points = []
    for elem in train_elements:
        if elem in elemental_props:
            props = elemental_props[elem]
            train_points.append([props['atomic_radius'], props['electronegativity']])
    
    if len(train_points) < 3:
        # Cannot form a 2D hull with fewer than 3 points.
        # If there are test elements, we cannot guarantee they are inside.
        # Treat as extrapolation risk unless test set is empty or subset of train.
        if set(test_elements).issubset(set(train_elements)):
            return True, "Test elements are subset of training elements (no new elements)."
        else:
            return False, "Training set too small to form convex hull. Extrapolation risk."

    train_array = np.array(train_points)
    hull = calculate_convex_hull(train_array)
    
    if hull is None:
        return False, "Failed to compute convex hull for training set."

    # 2. Check each test element
    for elem in test_elements:
        if elem not in elemental_props:
            continue # Should have been caught by "New Element" check earlier
        
        props = elemental_props[elem]
        if not check_element_in_hull(props, hull):
            return False, f"Element {elem} falls outside the convex hull of training elements (Extrapolation)."
    
    return True, "All test elements within training convex hull."

def log_skipped_fold(
    system_id: str,
    reason: str,
    log_file: str = "data/logs/skipped_fold.log"
):
    """Log a skipped fold to the specified JSON log file."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    entry = {
        "fold_id": system_id,
        "reason": reason,
        "timestamp": str(datetime.now())
    }
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + "\n")
    log_warning(logger, f"Fold {system_id} skipped: {reason}")

def save_convex_hull_artifact(
    hull_data: Dict[str, Any],
    output_path: str = "data/artifacts/convex_hull.json"
):
    """Save convex hull metadata to a JSON file for traceability."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(hull_data, f, indent=2)
    log_info(logger, f"Convex hull artifact saved to {output_path}")

def main():
    """
    Main entry point for running the extrapolation checks.
    This function is intended to be called by code/models/train.py.
    """
    logger.info("Starting convex hull and extrapolation checks...")
    
    # Load properties
    try:
        props = load_elemental_properties()
        logger.info(f"Loaded properties for {len(props)} elements.")
    except Exception as e:
        log_error(logger, f"Failed to load elemental properties: {e}")
        sys.exit(1)

    # Example usage (typically integrated into the LOSO loop in train.py)
    # This function provides the core logic to be used by train.py
    logger.info("Extrapolation check module ready.")

if __name__ == "__main__":
    main()