import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from contracts.validator import validate_synthetic_image

def boxes_overlap(
    box1: Tuple[int, int, int, int],
    box2: Tuple[int, int, int, int],
    tolerance: int = 0
) -> bool:
    """
    Check if two bounding boxes overlap.
    
    Args:
        box1: (x1, y1, x2, y2)
        box2: (x1, y1, x2, y2)
        tolerance: Minimum gap required between boxes (0 means touching is overlap).
        
    Returns:
        True if boxes overlap, False otherwise.
    """
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

    # Check for non-overlap conditions
    # If one box is to the left of the other (with tolerance)
    if x2_1 + tolerance <= x1_2 or x2_2 + tolerance <= x1_1:
        return False
    # If one box is above the other
    if y2_1 + tolerance <= y1_2 or y2_2 + tolerance <= y1_1:
        return False

    return True

def validate_no_overlaps(boxes: List[Tuple[int, int, int, int]]) -> bool:
    """
    Validate that no boxes in a list overlap with each other.
    
    Args:
        boxes: List of bounding boxes (x1, y1, x2, y2).
        
    Returns:
        True if no overlaps found, False otherwise.
    """
    n = len(boxes)
    for i in range(n):
        for j in range(i + 1, n):
            if boxes_overlap(boxes[i], boxes[j]):
                return False
    return True

def validate_synthetic_image_file(json_path: Path) -> bool:
    """
    Validate a generated JSON annotation file against the schema.
    
    Args:
        json_path: Path to the JSON file.
        
    Returns:
        True if valid, False otherwise.
    """
    if not json_path.exists():
        return False

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Use the contract validator defined in T042
        is_valid = validate_synthetic_image(data)
        return is_valid
    except (json.JSONDecodeError, Exception) as e:
        return False

def main():
    """CLI entry point for validator."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m synthetic.validator <json_file_path>")
        sys.exit(1)
    
    target = Path(sys.argv[1])
    
    if not target.exists():
        print(f"Error: File not found: {target}")
        sys.exit(1)
        
    is_valid = validate_synthetic_image_file(target)
    
    if is_valid:
        print(f"Validation PASSED: {target}")
        sys.exit(0)
    else:
        print(f"Validation FAILED: {target}")
        sys.exit(1)

if __name__ == "__main__":
    main()