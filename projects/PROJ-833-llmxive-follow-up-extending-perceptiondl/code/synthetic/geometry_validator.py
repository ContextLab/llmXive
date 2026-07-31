"""
Geometry Validator for Synthetic Data.

This module verifies that the `derived_relations` stored in generated JSON
annotation files match the geometric reality of the bounding box coordinates.
It re-computes relations from saved coordinates and asserts they match the
stored values. Fail if any mismatch is found.
"""
import json
import sys
import math
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

# Import from existing API surface
from synthetic.deriver import calculate_centroid, derive_spatial_relation


def validate_geometry_in_file(json_path: Path, tolerance: float = 1e-6) -> bool:
    """
    Validate that derived_relations in a JSON file match the geometric reality
    of the bounding box coordinates.

    Args:
        json_path: Path to the JSON annotation file.
        tolerance: Floating point tolerance for centroid comparisons.

    Returns:
        True if all relations match geometric reality, False otherwise.

    Raises:
        ValueError: If a mismatch is found (fail loudly).
    """
    if not json_path.exists():
        raise FileNotFoundError(f"File not found: {json_path}")

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {json_path}: {e}")

    bounding_boxes = data.get("bounding_boxes", [])
    stored_relations = data.get("derived_relations", [])

    if not bounding_boxes:
        # No boxes means no relations to validate
        return True

    # Re-compute relations from coordinates
    # We need to map box IDs to their centroids
    box_centroids = {}
    box_dims = {}
    for box in bounding_boxes:
        box_id = box["id"]
        x, y, w, h = box["x"], box["y"], box["w"], box["h"]
        cx, cy = calculate_centroid(x, y, w, h)
        box_centroids[box_id] = (cx, cy)
        box_dims[box_id] = (x, y, w, h)

    # Re-derive all pairwise relations
    computed_relations = []
    box_ids = sorted(box_centroids.keys())
    for i, id1 in enumerate(box_ids):
        for j, id2 in enumerate(box_ids):
            if i >= j:
                continue
            cx1, cy1 = box_centroids[id1]
            cx2, cy2 = box_centroids[id2]
            
            # Derive relation from id1 to id2
            rel = derive_spatial_relation(cx1, cy1, cx2, cy2)
            computed_relations.append(f"{id1} {rel} {id2}")
            
            # Derive inverse relation from id2 to id1
            rel_inv = derive_spatial_relation(cx2, cy2, cx1, cy1)
            computed_relations.append(f"{id2} {rel_inv} {id1}")

    # Compare stored vs computed
    stored_set = set(stored_relations)
    computed_set = set(computed_relations)

    if stored_set != computed_set:
        missing = computed_set - stored_set
        extra = stored_set - computed_set
        error_msg = f"Geometry mismatch in {json_path}:\n"
        if missing:
            error_msg += f"  Missing (should exist): {missing}\n"
        if extra:
            error_msg += f"  Extra (should not exist): {extra}\n"
        raise ValueError(error_msg)

    return True


def validate_all_in_directory(directory: Path, recursive: bool = False) -> int:
    """
    Validate all JSON files in a directory.

    Args:
        directory: Path to the directory containing JSON files.
        recursive: If True, search subdirectories.

    Returns:
        Number of files validated successfully.

    Raises:
        ValueError: If any file fails validation.
    """
    pattern = "**/*.json" if recursive else "*.json"
    json_files = list(directory.glob(pattern))
    
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {directory}")

    success_count = 0
    for json_file in json_files:
        try:
            validate_geometry_in_file(json_file)
            success_count += 1
        except (ValueError, FileNotFoundError) as e:
            # Fail loudly on first error
            raise e
        
    return success_count


def main():
    """CLI entry point for geometry validation."""
    if len(sys.argv) < 2:
        print("Usage: python -m synthetic.geometry_validator <json_file_or_dir>")
        sys.exit(1)

    target = Path(sys.argv[1])

    if not target.exists():
        print(f"Error: Path not found: {target}")
        sys.exit(1)

    try:
        if target.is_file():
            validate_geometry_in_file(target)
            print(f"Geometry validation PASSED: {target}")
        else:
            count = validate_all_in_directory(target)
            print(f"Geometry validation PASSED for {count} files in {target}")
        
        sys.exit(0)
    except (ValueError, FileNotFoundError) as e:
        print(f"Geometry validation FAILED:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
