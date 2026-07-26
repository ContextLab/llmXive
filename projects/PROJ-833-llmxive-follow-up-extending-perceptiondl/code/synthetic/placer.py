"""
Core algorithm for placing non-overlapping bounding boxes on images.
Includes retry logic to reduce region count or skip images if placement fails.
"""
import random
import math
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

# Box format: (x_min, y_min, x_max, y_max)
Box = Tuple[int, int, int, int]


def _get_box_center(box: Box) -> Tuple[float, float]:
    """Calculate the center point of a bounding box."""
    x_min, y_min, x_max, y_max = box
    return ((x_min + x_max) / 2.0, (y_min + y_max) / 2.0)


def _boxes_overlap(box1: Box, box2: Box, padding: int = 0) -> bool:
    """
    Check if two bounding boxes overlap.
    Args:
        box1: First box (x_min, y_min, x_max, y_max)
        box2: Second box (x_min, y_min, x_max, y_max)
        padding: Minimum gap required between boxes
    Returns:
        True if boxes overlap or are too close, False otherwise
    """
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2

    # Check for separation with padding
    if x1_max + padding < x2_min or x2_max + padding < x1_min:
        return False
    if y1_max + padding < y2_min or y2_max + padding < y1_min:
        return False

    return True


def _check_no_overlaps(boxes: List[Box], padding: int = 0) -> bool:
    """
    Verify that no boxes in the list overlap.
    Args:
        boxes: List of bounding boxes
        padding: Minimum gap required between boxes
    Returns:
        True if no overlaps, False otherwise
    """
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if _boxes_overlap(boxes[i], boxes[j], padding):
                return False
    return True


def _generate_random_box(
    image_width: int,
    image_height: int,
    min_size: int = 20,
    max_size: int = 100,
    margin: int = 5
) -> Optional[Box]:
    """
    Generate a random bounding box within image bounds.
    Args:
        image_width: Width of the image
        image_height: Height of the image
        min_size: Minimum dimension (width/height) of the box
        max_size: Maximum dimension of the box
        margin: Minimum margin from image edges
    Returns:
        A random box (x_min, y_min, x_max, y_max) or None if generation fails
    """
    # Ensure min_size doesn't exceed available space
    max_possible = min(image_width, image_height) - 2 * margin
    if min_size > max_possible:
        return None

    size_max = min(max_size, max_possible)
    size_min = min(min_size, size_max)

    width = random.randint(size_min, size_max)
    height = random.randint(size_min, size_max)

    # Ensure box fits within image with margin
    x_max = image_width - margin
    y_max = image_height - margin
    x_min = margin
    y_min = margin

    if width > x_max - x_min or height > y_max - y_min:
        return None

    x_min = random.randint(margin, x_max - width)
    y_min = random.randint(margin, y_max - height)
    x_max = x_min + width
    y_max = y_min + height

    return (x_min, y_min, x_max, y_max)


def place_boxes(
    image_width: int,
    image_height: int,
    target_count: int,
    min_size: int = 20,
    max_size: int = 100,
    max_attempts_per_box: int = 50,
    max_total_attempts: int = 5000,
    padding: int = 5
) -> Tuple[List[Box], bool]:
    """
    Place non-overlapping bounding boxes on an image.
    
    Implements retry logic: if placement fails to reach target count,
    it returns the boxes successfully placed (which may be fewer than target).
    
    Args:
        image_width: Width of the image
        image_height: Height of the image
        target_count: Desired number of boxes to place
        min_size: Minimum dimension for boxes
        max_size: Maximum dimension for boxes
        max_attempts_per_box: Max attempts to place a single box
        max_total_attempts: Max total attempts before giving up
        padding: Minimum gap between boxes
        
    Returns:
        Tuple of (list of placed boxes, success_flag)
        success_flag is True if target_count was reached, False otherwise
    """
    if target_count <= 0:
        return [], True

    placed_boxes: List[Box] = []
    total_attempts = 0

    for _ in range(target_count):
        if total_attempts >= max_total_attempts:
            # Exceeded total attempts, stop trying
            return placed_boxes, False

        box_placed = False
        attempts = 0

        while attempts < max_attempts_per_box:
            if total_attempts >= max_total_attempts:
                break

            candidate = _generate_random_box(
                image_width, image_height, min_size, max_size, padding
            )

            if candidate is None:
                # Image too small for requested box sizes
                return placed_boxes, False

            # Check overlap with all placed boxes
            overlaps = False
            for existing_box in placed_boxes:
                if _boxes_overlap(candidate, existing_box, padding):
                    overlaps = True
                    break

            if not overlaps:
                placed_boxes.append(candidate)
                box_placed = True
                break

            attempts += 1
            total_attempts += 1

        if not box_placed:
            # Could not place this box after max attempts
            # Return what we have so far
            return placed_boxes, False

    return placed_boxes, True


def place_boxes_with_retry(
    image_width: int,
    image_height: int,
    target_count: int,
    min_size: int = 20,
    max_size: int = 100,
    max_attempts_per_box: int = 50,
    max_total_attempts: int = 5000,
    padding: int = 5,
    min_acceptable_count: int = 1
) -> Dict[str, Any]:
    """
    Attempt to place boxes with retry logic to reduce region count if needed.
    
    If the initial placement fails to reach target_count, this function
    will retry with a reduced count until either:
    1. A successful placement is found (>= min_acceptable_count boxes)
    2. The count drops below min_acceptable_count (then skip image)
    
    Args:
        image_width: Width of the image
        image_height: Height of the image
        target_count: Desired number of boxes
        min_size: Minimum dimension for boxes
        max_size: Maximum dimension for boxes
        max_attempts_per_box: Max attempts per box placement
        max_total_attempts: Max total attempts per placement attempt
        padding: Minimum gap between boxes
        min_acceptable_count: Minimum boxes required to consider placement successful
        
    Returns:
        Dictionary with:
            - 'boxes': List of placed boxes (empty if skipped)
            - 'count': Number of boxes placed
            - 'skipped': Boolean indicating if image was skipped
            - 'final_target': The count that was successfully placed (or 0 if skipped)
            - 'reason': Explanation of outcome
    """
    current_target = target_count
    max_retries = target_count - min_acceptable_count + 1

    for retry in range(max_retries + 1):
        boxes, success = place_boxes(
            image_width=image_width,
            image_height=image_height,
            target_count=current_target,
            min_size=min_size,
            max_size=max_size,
            max_attempts_per_box=max_attempts_per_box,
            max_total_attempts=max_total_attempts,
            padding=padding
        )

        if len(boxes) >= min_acceptable_count:
            return {
                'boxes': boxes,
                'count': len(boxes),
                'skipped': False,
                'final_target': len(boxes),
                'reason': f"Successfully placed {len(boxes)} boxes (target was {target_count})"
            }

        # If we reached the minimum acceptable count but it's less than target,
        # and we can't reduce further, we skip
        if current_target <= min_acceptable_count:
            return {
                'boxes': [],
                'count': 0,
                'skipped': True,
                'final_target': 0,
                'reason': f"Could not place even {min_acceptable_count} boxes; skipping image"
            }

        # Reduce target count and retry
        current_target -= 1

    # Should not reach here, but handle gracefully
    return {
        'boxes': [],
        'count': 0,
        'skipped': True,
        'final_target': 0,
        'reason': "Placement failed after all retries"
    }


def main():
    """
    Standalone test function for the placer module.
    Demonstrates placement logic with various configurations.
    """
    # Test with a sample image size
    width, height = 512, 512
    target = 30

    print(f"Attempting to place {target} boxes on {width}x{height} image...")
    
    result = place_boxes_with_retry(
        image_width=width,
        image_height=height,
        target_count=target,
        min_size=20,
        max_size=80,
        padding=5
    )

    print(f"Result: {result['reason']}")
    print(f"Boxes placed: {result['count']}")
    print(f"Skipped: {result['skipped']}")

    # Validate no overlaps
    if result['boxes']:
        has_overlap = not _check_no_overlaps(result['boxes'], padding=5)
        print(f"Overlap check: {'FAIL' if has_overlap else 'PASS'}")

    return result


if __name__ == "__main__":
    main()