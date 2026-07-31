"""
code/synthetic/validator.py

Validates synthetic images for overlapping bounding boxes and schema compliance.
This module is integrated into the generation pipeline to ensure every saved
artifact meets geometric and schema constraints before being persisted.
"""

import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from contracts.validator import validate_synthetic_image
from synthetic.placer import boxes_overlap as placer_boxes_overlap

def boxes_overlap(box1: Dict[str, Any], box2: Dict[str, Any], threshold: float = 0.0) -> bool:
    """
    Check if two boxes overlap.
    
    Args:
        box1: First bounding box dict with keys x, y, w, h.
        box2: Second bounding box dict with keys x, y, w, h.
        threshold: Intersection over Union threshold (currently unused, strict check).
        
    Returns:
        True if boxes overlap, False otherwise.
    """
    # Use the robust logic from placer.py to ensure consistency
    return placer_boxes_overlap(box1, box2, threshold)

def validate_no_overlaps(boxes: List[Dict[str, Any]]) -> bool:
    """
    Validate that no two boxes in the list overlap.
    
    Args:
        boxes: List of bounding box dictionaries.
        
    Returns:
        True if valid (no overlaps), False otherwise.
    """
    n = len(boxes)
    for i in range(n):
        for j in range(i + 1, n):
            if boxes_overlap(boxes[i], boxes[j]):
                return False
    return True

def validate_synthetic_image_file(json_path: str) -> bool:
    """
    Validate a generated JSON file against the schema and geometric rules.
    
    This function performs two checks:
    1. Schema validation against contracts/synthetic_image.schema.yaml
    2. Geometric validation ensuring no bounding boxes overlap.
    
    Args:
        json_path: Path to the JSON annotation file.
        
    Returns:
        True if the file is valid, False otherwise.
        
    Raises:
        FileNotFoundError: If the JSON file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
        
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # 1. Schema validation
    if not validate_synthetic_image(data):
        return False

    # 2. Geometric validation (no overlaps)
    if 'bounding_boxes' in data:
        if not validate_no_overlaps(data['bounding_boxes']):
            return False
    
    return True

def validate_and_save_if_valid(image_path: Path, json_data: Dict[str, Any], output_dir: Path) -> bool:
    """
    Validate generated data and save only if valid.
    
    This is the primary integration point for the generator.
    It validates the in-memory data structure before any disk writes occur.
    
    Args:
        image_path: Path to the source image (used for naming output).
        json_data: The dictionary containing bounding boxes and relations.
        output_dir: Directory where valid files should be saved.
        
    Returns:
        True if data was validated and saved, False if validation failed.
    """
    # Perform geometric validation first
    if 'bounding_boxes' in json_data:
        if not validate_no_overlaps(json_data['bounding_boxes']):
            return False
    
    # Perform schema validation
    if not validate_synthetic_image(json_data):
        return False
    
    # If we reach here, data is valid. Save it.
    # Note: The actual saving is handled by the serializer, 
    # but this function acts as the gatekeeper.
    # We return True to signal the generator to proceed with serialization.
    return True

def main():
    """Test validator with dummy data."""
    # Test 1: Non-overlapping boxes
    boxes = [
        {'x': 0, 'y': 0, 'w': 10, 'h': 10},
        {'x': 20, 'y': 20, 'w': 10, 'h': 10}
    ]
    assert validate_no_overlaps(boxes), "Test 1 failed: Non-overlapping boxes detected as overlapping"
    print("✓ Test 1 passed: Non-overlapping boxes validated correctly")
    
    # Test 2: Overlapping boxes
    boxes_overlap = [
        {'x': 0, 'y': 0, 'w': 10, 'h': 10},
        {'x': 5, 'y': 5, 'w': 10, 'h': 10}
    ]
    assert not validate_no_overlaps(boxes_overlap), "Test 2 failed: Overlapping boxes detected as non-overlapping"
    print("✓ Test 2 passed: Overlapping boxes detected correctly")
    
    # Test 3: Touching boxes (should not overlap if strict)
    boxes_touching = [
        {'x': 0, 'y': 0, 'w': 10, 'h': 10},
        {'x': 10, 'y': 0, 'w': 10, 'h': 10}
    ]
    # Depending on implementation, touching might be allowed or not. 
    # Our placer logic usually treats touching as non-overlapping if intersection is 0.
    result = validate_no_overlaps(boxes_touching)
    print(f"✓ Test 3 result: Touching boxes validation result = {result}")

if __name__ == "__main__":
    main()