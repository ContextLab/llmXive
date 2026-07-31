import json
import sys
import math
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

# Import from existing API surface
from synthetic.deriver import calculate_centroid, derive_spatial_relation
from config import get_data_path


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_relations_in_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Re-compute geometric relations from bounding box coordinates and compare
    against stored derived_relations.
    
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    try:
        data = load_json_file(file_path)
        
        bounding_boxes = data.get('bounding_boxes', [])
        stored_relations = data.get('derived_relations', [])
        
        if not bounding_boxes:
            errors.append(f"{file_path}: No bounding boxes found.")
            return False, errors
        
        if not stored_relations:
            errors.append(f"{file_path}: No derived_relations found.")
            return False, errors
        
        # Re-compute relations from coordinates
        # We need to pair up boxes and derive relations between them
        # The stored relations should be a list of strings like "box_0 left of box_1"
        
        # Reconstruct expected relations
        expected_relations = []
        
        # Sort boxes by ID to ensure consistent ordering
        sorted_boxes = sorted(bounding_boxes, key=lambda b: b['id'])
        
        for i in range(len(sorted_boxes)):
            for j in range(i + 1, len(sorted_boxes)):
                box_a = sorted_boxes[i]
                box_b = sorted_boxes[j]
                
                centroid_a = calculate_centroid(box_a)
                centroid_b = calculate_centroid(box_b)
                
                relation = derive_spatial_relation(centroid_a, centroid_b)
                
                # Format relation string consistently with storage format
                expected_relations.append(f"box_{box_a['id']} {relation} box_{box_b['id']}")
        
        # Compare sets of relations
        expected_set = set(expected_relations)
        stored_set = set(stored_relations)
        
        if expected_set != stored_set:
            missing = expected_set - stored_set
            extra = stored_set - expected_set
            
            if missing:
                errors.append(f"{file_path}: Missing relations: {missing}")
            if extra:
                errors.append(f"{file_path}: Extra relations: {extra}")
            
            return False, errors
        
        return True, []
        
    except json.JSONDecodeError as e:
        errors.append(f"{file_path}: Invalid JSON - {str(e)}")
        return False, errors
    except Exception as e:
        errors.append(f"{file_path}: Unexpected error - {str(e)}")
        return False, errors


def validate_all_files(data_dir: Path) -> Tuple[bool, List[str]]:
    """
    Validate all JSON files in the data directory.
    
    Returns:
        Tuple of (all_valid, list_of_all_errors)
    """
    all_errors = []
    all_valid = True
    
    json_files = list(data_dir.glob('*.json'))
    
    if not json_files:
        all_errors.append(f"No JSON files found in {data_dir}")
        return False, all_errors
    
    print(f"Validating {len(json_files)} JSON files in {data_dir}")
    
    for file_path in sorted(json_files):
        is_valid, errors = validate_relations_in_file(file_path)
        
        if is_valid:
            print(f"✓ {file_path.name}: Valid")
        else:
            print(f"✗ {file_path.name}: Invalid")
            all_errors.extend(errors)
            all_valid = False
    
    return all_valid, all_errors


def main():
    """Main entry point for validation script."""
    data_path = get_data_path()
    synthetic_dir = data_path / 'synthetic'
    
    if not synthetic_dir.exists():
        print(f"Error: Synthetic data directory not found: {synthetic_dir}")
        sys.exit(1)
    
    print(f"Validating synthetic dataset in: {synthetic_dir}")
    print("-" * 60)
    
    all_valid, errors = validate_all_files(synthetic_dir)
    
    print("-" * 60)
    
    if all_valid:
        print("SUCCESS: All geometric relations validated successfully.")
        print(f"Checked {len(list(synthetic_dir.glob('*.json')))} files.")
        sys.exit(0)
    else:
        print("FAILURE: Geometric relation validation failed.")
        print(f"Found {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()
