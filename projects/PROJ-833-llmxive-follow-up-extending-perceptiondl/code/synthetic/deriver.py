"""
code/synthetic/deriver.py

Implements ground-truth relation derivation logic.
Derives spatial prepositions (e.g., "left of", "above") from bounding box centroids.
"""

import math
from typing import List, Dict, Tuple, Optional, Any

def calculate_centroid(box: Dict[str, Any]) -> Tuple[float, float]:
    """Calculate the centroid (center) of a bounding box."""
    cx = box['x'] + box['w'] / 2.0
    cy = box['y'] + box['h'] / 2.0
    return cx, cy

def derive_spatial_relation(box1: Dict[str, Any], box2: Dict[str, Any]) -> Optional[str]:
    """
    Derive the primary spatial relation between two boxes based on centroids.
    Returns a string like "left of", "right of", "above", "below", or None.
    """
    c1 = calculate_centroid(box1)
    c2 = calculate_centroid(box2)

    dx = c2[0] - c1[0]
    dy = c2[1] - c1[1]

    # Thresholds for determining direction
    # If the difference is small, it might be ambiguous
    threshold = 20.0 

    relations = []

    if abs(dx) > threshold and abs(dy) > threshold:
        # Diagonal
        if dx > 0:
            relations.append("right")
        else:
            relations.append("left")
        
        if dy > 0:
            relations.append("below")
        else:
            relations.append("above")
        
        # Return combined relation, e.g., "right and below"
        return " and ".join(relations)

    elif abs(dx) > threshold:
        if dx > 0:
            return "right of"
        else:
            return "left of"

    elif abs(dy) > threshold:
        if dy > 0:
            return "below"
        else:
            return "above"

    return None

def derive_all_relations(boxes: List[Dict[str, Any]]) -> List[str]:
    """
    Derive all pairwise spatial relations for a set of boxes.
    Returns a list of strings describing relations.
    """
    relations = []
    n = len(boxes)
    for i in range(n):
        for j in range(i + 1, n):
            rel = derive_spatial_relation(boxes[i], boxes[j])
            if rel:
                relations.append(f"box_{boxes[i]['id']} is {rel} box_{boxes[j]['id']}")
    return relations

def main():
    """Test deriver."""
    boxes = [
        {'x': 10, 'y': 10, 'w': 20, 'h': 20, 'id': 0},
        {'x': 100, 'y': 10, 'w': 20, 'h': 20, 'id': 1},
        {'x': 10, 'y': 100, 'w': 20, 'h': 20, 'id': 2}
    ]
    relations = derive_all_relations(boxes)
    for r in relations:
        print(r)

if __name__ == "__main__":
    main()
