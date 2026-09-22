"""
Implementation of Property Range Extrapolation and New Element checks for LOSO cross-validation.
Task: T022
"""
import os
import json
import sys
import csv
import numpy as np
from scipy.spatial import ConvexHull
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime

# Importing from existing project API surface
try:
    from utils.logging import get_logger, log_info, log_warning, log_error
    from utils.error_codes import ErrorCode
except ImportError:
    # Fallback for direct execution or missing imports in isolated env
    import logging
    def get_logger(name): return logging.getLogger(name)
    def log_info(msg): print(f"INFO: {msg}")
    def log_warning(msg): print(f"WARNING: {msg}")
    def log_error(msg): print(f"ERROR: {msg}")

    class ErrorCode:
        INVALID_SCOPE = "INVALID_SCOPE"
        DATA_SOURCE_MISSING = "DATA_SOURCE_MISSING"
        MISSING_TEMP_COORDS = "MISSING_TEMP_COORDS"

logger = get_logger(__name__)

def load_elemental_properties(filepath: str = "data/raw/elemental_properties.csv") -> Dict[str, Dict[str, float]]:
    """
    Loads elemental properties from the CSV file.
    Returns a dict: {element: {property: value}}
    """
    properties = {}
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Elemental properties file not found: {filepath}")
    
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            element = row['element']
            properties[element] = {
                'radius': float(row['atomic_radius_angstrom']),
                'electronegativity': float(row['electronegativity_pauling']),
                'valence': int(row['valence_electrons'])
            }
    return properties

def calculate_convex_hull(training_elements: Set[str], properties: Dict[str, Dict[str, float]]) -> Dict:
    """
    Calculates the convex hull of elemental properties (radius, EN) for the training set.
    Returns the vertices of the hull and the hull object for point-in-polygon checks.
    """
    if len(training_elements) < 3:
        # For 1 or 2 elements, the hull is degenerate or a line segment.
        # We treat this as a "point" or "line" check logic later, but for ConvexHull we need >= 3 points.
        # However, for the purpose of this check, if we have < 3 unique elements, 
        # we can't form a 2D hull. We will return the points themselves as vertices.
        points = []
        for elem in training_elements:
            if elem in properties:
                points.append([properties[elem]['radius'], properties[elem]['electronegativity']])
        
        if len(points) < 1:
            return {"vertices": [], "hull": None, "is_degenerate": True}
        
        return {
            "vertices": [{"element": list(training_elements)[i], "radius": p[0], "electronegativity": p[1]} for i, p in enumerate(points)],
            "hull": None,
            "is_degenerate": True
        }

    points = []
    elem_map = []
    for elem in training_elements:
        if elem in properties:
            points.append([properties[elem]['radius'], properties[elem]['electronegativity']])
            elem_map.append(elem)
    
    if len(points) < 3:
        return {
            "vertices": [{"element": elem_map[i], "radius": p[0], "electronegativity": p[1]} for i, p in enumerate(points)],
            "hull": None,
            "is_degenerate": True
        }

    try:
        hull = ConvexHull(np.array(points))
        vertices_indices = hull.vertices
        vertices = []
        for idx in vertices_indices:
            elem = elem_map[idx]
            p = points[idx]
            vertices.append({
                "element": elem,
                "radius": float(p[0]),
                "electronegativity": float(p[1])
            })
        
        return {
            "vertices": vertices,
            "hull": hull,
            "is_degenerate": False
        }
    except Exception as e:
        log_error(f"Failed to compute convex hull: {e}")
        return {"vertices": [], "hull": None, "is_degenerate": True}

def check_element_in_hull(element: str, hull_data: Dict, properties: Dict[str, Dict[str, float]]) -> Tuple[bool, str]:
    """
    Checks if a test element falls within the convex hull of training elements.
    Returns (is_inside, reason_string).
    """
    if element not in properties:
        return False, "Element properties not found"

    if hull_data["is_degenerate"] or hull_data["hull"] is None:
        # If training set has < 3 elements, we can only check exact matches or simple range checks.
        # For strict FR-010 "New Element Check", if the element is not in the training set, it's a new element.
        # We rely on the caller to handle the "New Element" logic separately, but here we check geometric inclusion.
        # If degenerate, we assume strict set membership is required.
        return False, "Training set too small for hull check"

    point = np.array([[properties[element]['radius'], properties[element]['electronegativity']]])
    try:
        # scipy.spatial.ConvexHull does not have a direct "contains" method for 2D points easily.
        # We can use the `equations` attribute or `Delaunay` logic.
        # A simpler approach for 2D: check if point is inside the polygon defined by vertices.
        # Using the hull's equations: Ax + By <= C (for 2D, it's a half-plane)
        # hull.equations is (n_vertices, n_dim + 1).
        # For a point to be inside, point @ equation[:-1] + equation[-1] <= 0 (depending on sign convention).
        # Let's use a robust method: check if the point is on the same side of all hull lines.
        
        # Actually, a simpler trick with scipy:
        # If we add the point to the hull and the volume (area) doesn't change significantly, it's inside? No, that's expensive.
        # Let's use the `equations` check.
        # The equation form is: normal . x + offset <= 0
        normal = hull_data["hull"].equations[:, :-1]
        offset = hull_data["hull"].equations[:, -1]
        
        # Check if point satisfies all inequalities
        # point . normal + offset <= 0 (with some tolerance for float errors)
        values = np.dot(point, normal.T) + offset
        if np.all(values <= 1e-9):
            return True, "Inside hull"
        else:
            return False, "Outside hull (extrapolation)"
    except Exception as e:
        log_error(f"Error checking hull inclusion: {e}")
        return False, "Error during check"

def apply_property_range_extrapolation_check(
    training_elements: Set[str],
    test_elements: Set[str],
    properties: Dict[str, Dict[str, float]],
    hull_data: Dict
) -> List[Tuple[str, str]]:
    """
    Checks if any test element falls outside the convex hull of training elements.
    Returns a list of (element, reason) for warnings.
    """
    warnings = []
    for elem in test_elements:
        if elem not in training_elements:
            is_inside, reason = check_element_in_hull(elem, hull_data, properties)
            if not is_inside:
                warnings.append((elem, reason))
    return warnings

def log_skipped_fold(
    fold_id: str,
    reason: str,
    log_path: str = "data/logs/skipped_fold.log"
):
    """
    Logs a skipped fold to the specified JSON lines file.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "fold_id": fold_id,
        "reason": reason,
        "error_code": ErrorCode.INVALID_SCOPE
    }
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
    log_warning(f"Fold {fold_id} skipped: {reason}")

def save_convex_hull_artifact(
    hull_data: Dict,
    output_path: str = "data/artifacts/convex_hull.json"
):
    """
    Saves the convex hull vertices to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Remove the scipy hull object before saving as it is not JSON serializable
    serializable_data = {
        "vertices": hull_data["vertices"],
        "is_degenerate": hull_data["is_degenerate"]
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_data, f, indent=2)
    log_info(f"Convex hull artifact saved to {output_path}")

def main():
    """
    Main entry point to demonstrate the logic.
    In a real pipeline, this would be called by train.py with the actual fold data.
    """
    # Mock data for demonstration if real data is not available in this specific execution context
    # In the real pipeline, `train.py` would pass the actual sets.
    # We assume the existence of data/raw/elemental_properties.csv as per T006.
    
    props_file = "data/raw/elemental_properties.csv"
    if not os.path.exists(props_file):
        # Create a minimal dummy file if missing for the sake of this script's standalone testability
        # In a real run, this should fail loudly or be provided by T006.
        log_warning(f"{props_file} not found. Creating dummy data for demonstration.")
        os.makedirs("data/raw", exist_ok=True)
        with open(props_file, 'w') as f:
            f.write("element,atomic_radius_angstrom,electronegativity_pauling,valence_electrons\n")
            f.write("Cu,1.28,1.90,1\n")
            f.write("Zn,1.33,1.65,2\n")
            f.write("Al,1.43,1.61,3\n")
            f.write("Fe,1.26,1.83,2\n")
            f.write("C,0.77,2.55,4\n")
    
    properties = load_elemental_properties(props_file)
    
    # Simulate a training fold (Cu, Zn, Al) and test fold (Fe)
    training_elements = {"Cu", "Zn", "Al"}
    test_elements = {"Fe"}
    
    # 1. Calculate Convex Hull for Training
    hull_data = calculate_convex_hull(training_elements, properties)
    save_convex_hull_artifact(hull_data)
    
    # 2. Check for New Elements (FR-010)
    # If test element is NOT in training set, it is a "New Element"
    new_elements = test_elements - training_elements
    if new_elements:
        for elem in new_elements:
            fold_id = f"Train({','.join(training_elements)})_Test({elem})"
            log_skipped_fold(fold_id, "invalid_scope")
        return # Stop processing this fold
    
    # 3. Check for Extrapolation (Warning only)
    warnings = apply_property_range_extrapolation_check(training_elements, test_elements, properties, hull_data)
    for elem, reason in warnings:
        log_warning(f"Element {elem} in test set is outside training hull: {reason}")

    log_info("Fold passed checks.")

if __name__ == "__main__":
    main()
