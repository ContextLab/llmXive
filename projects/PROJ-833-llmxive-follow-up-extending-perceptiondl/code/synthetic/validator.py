"""
Synthetic Image Validator Module.

This module provides validation logic for synthetic images generated for the
PerceptionDLM overflow experiment. It specifically checks for overlapping
bounding boxes to ensure data integrity before saving to disk.
"""

import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# Import schema validation utilities from the existing contracts module
from contracts.validator import validate_synthetic_image


def boxes_overlap(box1: Tuple[float, float, float, float],
                  box2: Tuple[float, float, float, float],
                  tolerance: float = 0.0) -> bool:
    """
    Check if two bounding boxes overlap.

    Args:
        box1: A tuple (x1, y1, x2, y2) representing the first box.
              (x1, y1) is top-left, (x2, y2) is bottom-right.
        box2: A tuple (x1, y1, x2, y2) representing the second box.
        tolerance: Minimum overlap area required to be considered overlapping.
                   Default 0.0 means any intersection counts.

    Returns:
        True if the boxes overlap, False otherwise.
    """
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2

    # Calculate intersection coordinates
    inter_x_min = max(x1_min, x2_min)
    inter_y_min = max(y1_min, y2_min)
    inter_x_max = min(x1_max, x2_max)
    inter_y_max = min(y1_max, y2_max)

    # Calculate intersection area
    inter_width = max(0.0, inter_x_max - inter_x_min)
    inter_height = max(0.0, inter_y_max - inter_y_min)
    inter_area = inter_width * inter_height

    return inter_area > tolerance


def validate_no_overlaps(bounding_boxes: List[Dict[str, Any]],
                         tolerance: float = 0.0) -> Tuple[bool, Optional[List[int]]]:
    """
    Validate that no two bounding boxes in the list overlap.

    Args:
        bounding_boxes: List of dictionaries containing 'bbox' keys with
                        (x1, y1, x2, y2) tuples or lists.
        tolerance: Minimum overlap area to trigger a failure.

    Returns:
        A tuple (is_valid, conflicting_indices).
        - is_valid: True if no overlaps found, False otherwise.
        - conflicting_indices: A list of index pairs [(i, j), ...] that overlap,
                               or None if valid.
    """
    if not bounding_boxes:
        return True, None

    indices = list(range(len(bounding_boxes)))
    conflicting_pairs = []

    for i in range(len(indices)):
        for j in range(i + 1, len(indices)):
            idx1 = indices[i]
            idx2 = indices[j]
            box1 = bounding_boxes[i].get('bbox')
            box2 = bounding_boxes[j].get('bbox')

            if box1 is None or box2 is None:
                # If bbox is missing, we cannot validate geometry.
                # Treat as valid for this check but schema validation should catch it.
                continue

            # Convert list to tuple if necessary for consistent comparison
            if isinstance(box1, list):
                box1 = tuple(box1)
            if isinstance(box2, list):
                box2 = tuple(box2)

            if boxes_overlap(box1, box2, tolerance):
                conflicting_pairs.append((idx1, idx2))

    if conflicting_pairs:
        return False, conflicting_pairs
    return True, None


def validate_synthetic_image_file(file_path: str,
                                  tolerance: float = 0.0) -> Dict[str, Any]:
    """
    Validate a synthetic image JSON annotation file.

    This function performs two checks:
    1. Schema validation against contracts/synthetic_image.schema.yaml
    2. Geometric validation to ensure no bounding boxes overlap.

    Args:
        file_path: Path to the JSON annotation file.
        tolerance: Minimum overlap area to consider as a conflict.

    Returns:
        A dictionary with validation results:
        {
            "valid": bool,
            "schema_valid": bool,
            "geometry_valid": bool,
            "errors": list of error messages,
            "conflicts": list of conflicting index pairs (if any)
        }
    """
    result = {
        "valid": False,
        "schema_valid": False,
        "geometry_valid": False,
        "errors": [],
        "conflicts": None
    }

    path = Path(file_path)
    if not path.exists():
        result["errors"].append(f"File not found: {file_path}")
        return result

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        result["errors"].append(f"Invalid JSON: {str(e)}")
        return result

    # 1. Schema Validation
    schema_valid, schema_errors = validate_synthetic_image(data)
    result["schema_valid"] = schema_valid
    if not schema_valid:
        result["errors"].extend(schema_errors)

    # 2. Geometry Validation (Only if schema passed to avoid redundant checks on bad data)
    # However, we want to report geometry issues regardless if possible, but strictly
    # speaking, we need the 'objects' list which the schema guarantees.
    if schema_valid and "objects" in data:
        geo_valid, conflicts = validate_no_overlaps(data["objects"], tolerance)
        result["geometry_valid"] = geo_valid
        if not geo_valid:
            result["conflicts"] = conflicts
            result["errors"].append(f"Found {len(conflicts)} overlapping box pairs.")
    elif "objects" not in data and schema_valid:
         # Edge case: Schema valid but objects missing (unlikely if schema requires it)
         result["geometry_valid"] = True # Nothing to overlap

    # Final Validity
    result["valid"] = result["schema_valid"] and result["geometry_valid"]

    return result


def main():
    """
    CLI entry point to validate a synthetic image file.
    Usage: python -m code.synthetic.validator path/to/file.json
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m code.synthetic.validator <path_to_json>")
        sys.exit(1)

    file_path = sys.argv[1]
    result = validate_synthetic_image_file(file_path)

    print(f"Validating: {file_path}")
    print(f"  Schema Valid: {result['schema_valid']}")
    print(f"  Geometry Valid: {result['geometry_valid']}")
    print(f"  Overall Valid: {result['valid']}")

    if result['errors']:
        print("  Errors:")
        for err in result['errors']:
            print(f"    - {err}")

    if result['conflicts']:
        print(f"  Conflicts: {result['conflicts']}")

    sys.exit(0 if result['valid'] else 1)


if __name__ == "__main__":
    main()