"""
code/synthetic/geometry_validator.py

Validates that derived spatial relations in synthetic JSON annotations match the
geometric reality of the bounding box coordinates.

This module implements the core logic for T048b: re-computing relations from
saved coordinates and asserting they match the stored `derived_relations`.
"""

import json
import sys
import math
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

from synthetic.deriver import calculate_centroid, derive_spatial_relation

def validate_geometry_in_file(json_path: str, tolerance: float = 0.01) -> Tuple[bool, List[str]]:
    """
    Validate that derived relations in a JSON file match geometric reality.

    This function:
    1. Loads the JSON file containing bounding boxes and derived_relations.
    2. Re-computes the spatial relations from the bounding box coordinates.
    3. Compares the recomputed relations with the stored ones.
    4. Returns True if all match, False otherwise, along with a list of mismatches.

    Args:
        json_path: Path to the JSON annotation file.
        tolerance: Small tolerance for floating point comparisons (not used for string comparison but kept for API consistency).

    Returns:
        Tuple of (is_valid, list_of_error_messages).
        is_valid is True if all relations match, False otherwise.
        list_of_error_messages contains descriptions of any mismatches found.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        ValueError: If the JSON structure is invalid.
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, 'r') as f:
        data = json.load(f)

    if 'bounding_boxes' not in data:
        raise ValueError(f"Missing 'bounding_boxes' in {json_path}")
    if 'derived_relations' not in data:
        raise ValueError(f"Missing 'derived_relations' in {json_path}")

    boxes = data['bounding_boxes']
    stored_relations = data['derived_relations']

    errors = []

    # Re-compute relations for every pair of boxes
    recomputed_relations = []
    n = len(boxes)
    for i in range(n):
        for j in range(i + 1, n):
            box1 = boxes[i]
            box2 = boxes[j]

            # Calculate centroids
            c1 = calculate_centroid(box1)
            c2 = calculate_centroid(box2)

            # Derive the relation (e.g., "left of", "above")
            relation = derive_spatial_relation(c1, c2)
            recomputed_relations.append(relation)

    # Compare stored vs recomputed
    # Note: The order of relations in the stored list might not be deterministic
    # if the generator didn't enforce a specific ordering. However, the set of
    # relations must match exactly.
    stored_set = set(stored_relations)
    recomputed_set = set(recomputed_relations)

    if stored_set != recomputed_set:
        missing_in_stored = recomputed_set - stored_set
        extra_in_stored = stored_set - recomputed_set

        if missing_in_stored:
            errors.append(f"Missing relations in stored data: {missing_in_stored}")
        if extra_in_stored:
            errors.append(f"Extra relations in stored data (not geometrically valid): {extra_in_stored}")

    return len(errors) == 0, errors

def validate_all_in_directory(directory: str) -> Tuple[int, int, List[str]]:
    """
    Validate all JSON files in a directory.

    Args:
        directory: Path to the directory containing JSON files.

    Returns:
        Tuple of (total_files, valid_files, list_of_all_errors).
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    json_files = list(dir_path.glob("*.json"))
    total = len(json_files)
    valid = 0
    all_errors = []

    for file_path in json_files:
        try:
            is_valid, errors = validate_geometry_in_file(str(file_path))
            if is_valid:
                valid += 1
            else:
                all_errors.extend([f"{file_path.name}: {e}" for e in errors])
        except Exception as e:
            all_errors.append(f"{file_path.name}: Exception during validation - {str(e)}")

    return total, valid, all_errors

def main():
    """
    Execute validation on the synthetic dataset directory.
    This is the script entry point for T048b execution.
    """
    # Default path based on project structure
    synthetic_dir = "data/synthetic"

    # Check for command line argument override
    if len(sys.argv) > 1:
        synthetic_dir = sys.argv[1]

    print(f"Validating synthetic dataset in: {synthetic_dir}")

    try:
        total, valid, errors = validate_all_in_directory(synthetic_dir)

        if total == 0:
            print("⚠ No JSON files found in the directory.")
            sys.exit(1)

        print(f"Total files: {total}, Valid: {valid}, Invalid: {total - valid}")

        if errors:
            print("\n❌ Validation Errors Found:")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        else:
            print("\n✅ All geometric relations validated successfully.")
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
