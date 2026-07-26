"""
Deriver module for ground-truth spatial relation extraction.

Implements FR-004: Deriving spatial prepositions (e.g., "left of", "above")
from bounding box centroids.

This module calculates the relative position of two bounding boxes based on
their centroids and returns a standardized spatial preposition string.
"""

import math
from typing import List, Dict, Tuple, Optional, Any

# Thresholds for spatial relation determination (in pixels relative to image size)
# These are normalized thresholds (0.0 to 1.0) relative to image dimensions
HORIZONTAL_THRESHOLD = 0.05  # 5% of image width
VERTICAL_THRESHOLD = 0.05    # 5% of image height

def calculate_centroid(box: Dict[str, Any]) -> Tuple[float, float]:
    """
    Calculate the centroid (center point) of a bounding box.

    Args:
        box: A dictionary containing bounding box coordinates.
            Expected keys: 'x', 'y', 'width', 'height'
            where (x, y) is the top-left corner.

    Returns:
        A tuple (center_x, center_y) representing the centroid coordinates.
    """
    x = box['x']
    y = box['y']
    width = box['width']
    height = box['height']

    center_x = x + width / 2.0
    center_y = y + height / 2.0

    return (center_x, center_y)


def derive_spatial_relation(
    box_a: Dict[str, Any],
    box_b: Dict[str, Any],
    image_width: Optional[float] = None,
    image_height: Optional[float] = None
) -> str:
    """
    Derive the spatial preposition describing the relationship of box_a to box_b.

    The relation is determined by comparing the centroids of the two boxes.
    The result describes where box_a is relative to box_b (e.g., "left of", "above").

    Args:
        box_a: The first bounding box (subject).
        box_b: The second bounding box (reference).
        image_width: Optional width of the image for normalized threshold calculation.
        image_height: Optional height of the image for normalized threshold calculation.

    Returns:
        A string representing the spatial preposition (e.g., "left of", "above",
        "top-left of", "bottom-right of"). If the relationship is ambiguous or
        the boxes are too close, returns "near".
    """
    center_a = calculate_centroid(box_a)
    center_b = calculate_centroid(box_b)

    dx = center_a[0] - center_b[0]  # Horizontal difference (a relative to b)
    dy = center_a[1] - center_b[1]  # Vertical difference (a relative to b)

    # Determine thresholds based on image dimensions if provided
    h_threshold = HORIZONTAL_THRESHOLD
    v_threshold = VERTICAL_THRESHOLD

    if image_width is not None and image_height is not None:
        h_threshold = HORIZONTAL_THRESHOLD * image_width
        v_threshold = VERTICAL_THRESHOLD * image_height

    # Determine primary directions
    is_left = dx < -h_threshold
    is_right = dx > h_threshold
    is_above = dy < -v_threshold  # In image coordinates, smaller y is "above"
    is_below = dy > v_threshold

    # Count how many strong directional constraints we have
    horizontal_count = sum([is_left, is_right])
    vertical_count = sum([is_above, is_below])

    if horizontal_count == 0 and vertical_count == 0:
        return "near"
    elif horizontal_count == 1 and vertical_count == 0:
        return "left of" if is_left else "right of"
    elif horizontal_count == 0 and vertical_count == 1:
        return "above" if is_above else "below"
    elif horizontal_count == 1 and vertical_count == 1:
        # Combined diagonal relations
        if is_left and is_above:
            return "top-left of"
        elif is_right and is_above:
            return "top-right of"
        elif is_left and is_below:
            return "bottom-left of"
        else:  # is_right and is_below
            return "bottom-right of"
    else:
        # Fallback for ambiguous cases (should be rare with proper thresholds)
        return "near"


def derive_all_relations(
    boxes: List[Dict[str, Any]],
    image_width: Optional[float] = None,
    image_height: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Derive spatial relations for all pairs of bounding boxes.

    Generates a list of relation objects, each containing the indices of the
    two boxes and the derived spatial preposition.

    Args:
        boxes: A list of bounding box dictionaries.
        image_width: Optional width of the image.
        image_height: Optional height of the image.

    Returns:
        A list of dictionaries, each with keys:
            - 'box_a_index': Index of the first box
            - 'box_b_index': Index of the second box
            - 'relation': The derived spatial preposition string
    """
    relations = []
    n = len(boxes)

    for i in range(n):
        for j in range(i + 1, n):
            relation_str = derive_spatial_relation(
                boxes[i],
                boxes[j],
                image_width,
                image_height
            )
            relations.append({
                'box_a_index': i,
                'box_b_index': j,
                'relation': relation_str
            })

    return relations


def main():
    """
    Main function for testing the deriver module.
    This is primarily for manual verification and documentation.
    """
    # Example usage
    test_boxes = [
        {'x': 10, 'y': 10, 'width': 50, 'height': 50},
        {'x': 100, 'y': 10, 'width': 50, 'height': 50},
        {'x': 10, 'y': 100, 'width': 50, 'height': 50},
        {'x': 100, 'y': 100, 'width': 50, 'height': 50}
    ]

    image_w, image_h = 200, 200

    print("Derived spatial relations:")
    relations = derive_all_relations(test_boxes, image_w, image_h)
    for rel in relations:
        print(f"  Box {rel['box_a_index']} is {rel['relation']} Box {rel['box_b_index']}")


if __name__ == '__main__':
    main()