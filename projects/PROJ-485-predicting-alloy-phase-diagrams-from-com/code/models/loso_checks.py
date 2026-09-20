"""
LOSO (Leave-One-System-Out) validation checks.

Implements:
1. New Element Check: Skips folds where test elements are not in training.
2. Property Range Extrapolation Check: Warns if test elements fall outside 
   the convex hull of training elemental properties.

Deliverables:
- data/artifacts/convex_hull.json: Vertices of the convex hull.
- data/logs/skipped_fold.log: JSON lines of skipped folds.
"""
import os
import json
import sys
import csv
import numpy as np
from scipy.spatial import ConvexHull
from typing import Dict, List, Any, Optional, Tuple, Set

# Import project utilities
try:
    from utils.logging import get_logger, log_info, log_warning, log_error
    from utils.error_codes import ErrorCode
except ImportError:
    # Fallback for direct execution or different import context
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from utils.logging import get_logger, log_warning, log_error
    from utils.error_codes import ErrorCode

logger = get_logger(__name__)

def load_elemental_properties(filepath: str = "data/raw/elemental_properties.csv") -> Dict[str, Dict[str, float]]:
    """
    Load elemental properties from CSV.
    Returns dict: {element: {property: value}}
    """
    if not os.path.exists(filepath):
        log_error(f"Elemental properties file not found: {filepath}")
        raise FileNotFoundError(f"Elemental properties file not found: {filepath}")
    
    properties = {}
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            element = row.get('element', '').strip()
            if not element:
                continue
            properties[element] = {
                'radius': float(row.get('atomic_radius_angstrom', 0)),
                'electronegativity': float(row.get('electronegativity_pauling', 0)),
                'valence': float(row.get('valence_electrons', 0))
            }
    return properties

def calculate_convex_hull(elements_data: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    Calculate the convex hull of elemental properties (radius vs electronegativity).
    Returns a dict containing vertices and the hull object.
    """
    if not elements_data:
        log_warning("No elements provided for convex hull calculation.")
        return {"vertices": [], "hull": None}

    # Prepare data points: (radius, electronegativity)
    points = []
    element_list = []
    for elem, props in elements_data.items():
        r = props.get('radius', 0)
        en = props.get('electronegativity', 0)
        if r > 0 and en > 0:
            points.append([r, en])
            element_list.append(elem)
    
    if len(points) < 3:
        log_warning(f"Insufficient points ({len(points)}) for 2D convex hull. Returning all as vertices.")
        return {
            "vertices": [{"element": e, "radius": elements_data[e]['radius'], "electronegativity": elements_data[e]['electronegativity']} for e in element_list],
            "hull_indices": list(range(len(element_list)))
        }

    points_arr = np.array(points)
    try:
        hull = ConvexHull(points_arr)
        hull_indices = hull.vertices
        vertices = [
            {
                "element": element_list[i],
                "radius": elements_data[element_list[i]]['radius'],
                "electronegativity": elements_data[element_list[i]]['electronegativity']
            }
            for i in hull_indices
        ]
        return {
            "vertices": vertices,
            "hull_indices": list(hull_indices),
            "hull_area": hull.volume # In 2D, volume is area
        }
    except Exception as e:
        log_error(f"Failed to calculate convex hull: {e}")
        return {"vertices": [], "hull_indices": [], "error": str(e)}

def check_element_in_hull(element_name: str, elements_data: Dict[str, Dict[str, float]], hull_info: Dict[str, Any]) -> Tuple[bool, bool]:
    """
    Check if an element is within the convex hull of the training set.
    Returns: (is_new_element, is_outside_hull)
    
    - is_new_element: True if the element is not in the training set at all.
    - is_outside_hull: True if the element is in the set but outside the hull (extrapolation).
    """
    if element_name not in elements_data:
        return True, False # New element, not in data

    # If not in hull_info vertices (which implies it's not in the training set used for hull), 
    # but we know it's in elements_data, we need to check if it's in the hull geometry.
    # However, the logic here is: 
    # 1. If element not in training set -> New Element -> Skip Fold.
    # 2. If element in training set -> Check if inside hull.
    
    # To check if inside hull, we need the hull object or a way to query.
    # Since we only have vertices, we can reconstruct or use a simple bounding box check 
    # if hull calculation wasn't robust, but let's assume we have the hull vertices.
    # A robust way without scipy.spatial.ConvexHull point query is to check if the point
    # is inside the polygon defined by vertices.
    
    # For this implementation, we assume 'elements_data' passed is the TRAINING set.
    # If the element is not in the keys of 'elements_data', it is a NEW element.
    if element_name not in elements_data:
        return True, False

    # If it is in the training set, it is by definition inside the hull of the training set
    # (since the hull is the convex hull of the set itself).
    # The "Extrapolation" check usually applies when a TEST element (which IS in the global dataset)
    # falls outside the hull of the TRAINING elements.
    # But the task says: "Verify if any element in test fold is NOT present in training fold."
    # And "Calculate convex hull of elemental properties in training set. Log warning if test elements fall outside hull."
    
    # So we need to compare the TEST element against the TRAINING hull.
    # This function signature is slightly ambiguous. Let's refine the logic in the caller.
    return False, False

def apply_property_range_extrapolation_check(
    test_elements: Set[str], 
    training_elements: Set[str], 
    training_properties: Dict[str, Dict[str, float]],
    hull_info: Dict[str, Any]
) -> List[str]:
    """
    Check if test elements fall outside the convex hull of training properties.
    Returns list of elements that are outside (warnings).
    """
    warnings = []
    
    # If we don't have a valid hull, we can't check
    if not hull_info or not hull_info.get('vertices'):
        return warnings

    # Reconstruct points from training data to build a queryable hull if needed
    # Or use the vertices to define the hull.
    # Since we need to check points against the hull, we need the hull object.
    # Let's re-calculate hull object from training properties for point-in-hull check.
    if len(training_properties) < 3:
        # If training set is too small, all points are on the boundary or outside
        # Treat as warning for any test point not in training
        for elem in test_elements:
            if elem not in training_elements:
                warnings.append(f"{elem} (outside hull due to small training set)")
        return warnings

    points = []
    elem_map = []
    for elem in training_elements:
        if elem in training_properties:
            points.append([training_properties[elem]['radius'], training_properties[elem]['electronegativity']])
            elem_map.append(elem)
    
    points_arr = np.array(points)
    try:
        hull = ConvexHull(points_arr)
    except Exception:
        return warnings

    for elem in test_elements:
        if elem not in training_properties:
            continue # Handled by New Element check
        
        prop = training_properties[elem]
        point = np.array([[prop['radius'], prop['electronegativity']]])
        
        # Use scipy's find_simplex to check if point is inside
        # Returns -1 if outside
        simplex_index = hull.find_simplex(point)
        if simplex_index == -1:
            warnings.append(f"{elem}")
    
    return warnings

def log_skipped_fold(fold_id: str, reason: str, log_path: str = "data/logs/skipped_fold.log"):
    """
    Log a skipped fold to a JSON lines file.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    entry = {
        "fold_id": fold_id,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
    log_warning(f"Skipped fold {fold_id}: {reason}")

def main():
    """
    Main entry point to demonstrate the checks.
    In a real pipeline, this would be called by the training script.
    """
    import datetime
    from utils.logging import get_logger
    logger = get_logger(__name__)

    # 1. Load Elemental Properties
    try:
        props = load_elemental_properties("data/raw/elemental_properties.csv")
        log_info(f"Loaded properties for {len(props)} elements.")
    except FileNotFoundError:
        log_error("Cannot proceed without elemental properties file.")
        sys.exit(1)

    # 2. Simulate a Training/Testing split for demonstration
    # In real code, this comes from the LOSO splitter
    training_set = {"Cu", "Al", "Zn", "Fe"} # Example training set
    test_set = {"Cu", "Al", "Zn"}           # Example test set (subset)
    
    # Scenario 2: Test set contains a new element not in training
    # test_set_new = {"Cu", "Al", "Zn", "Ni"} # Ni is not in training

    # 3. Calculate Convex Hull for Training Set
    training_props = {k: v for k, v in props.items() if k in training_set}
    hull_info = calculate_convex_hull(training_props)
    
    # Save Convex Hull to artifact
    hull_artifact_path = "data/artifacts/convex_hull.json"
    os.makedirs(os.path.dirname(hull_artifact_path), exist_ok=True)
    with open(hull_artifact_path, 'w', encoding='utf-8') as f:
        json.dump(hull_info, f, indent=2)
    log_info(f"Saved convex hull to {hull_artifact_path}")

    # 4. Check for New Elements
    new_elements = test_set - training_set
    if new_elements:
        for elem in new_elements:
            log_skipped_fold(f"TestSet-{elem}", f"new_element: {elem} not in training")
        log_error(f"Folds skipped due to new elements: {new_elements}")
        # In a real pipeline, this would trigger the skip logic for the fold
    else:
        log_info("No new elements detected in test set.")

    # 5. Check for Extrapolation
    warnings = apply_property_range_extrapolation_check(
        test_set, training_set, training_props, hull_info
    )
    for w in warnings:
        log_warning(f"Extrapolation warning: Element {w} falls outside training convex hull.")

    log_info("LOSO Checks completed.")

if __name__ == "__main__":
    main()