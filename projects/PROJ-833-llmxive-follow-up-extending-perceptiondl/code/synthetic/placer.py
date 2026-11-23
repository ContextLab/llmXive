"""
code/synthetic/placer.py

Implements the core algorithm for placing non-overlapping bounding boxes.
Includes retry logic to reduce region count or skip images if placement fails.
"""

import random
import math
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

def calculate_iou(box1: Dict[str, Any], box2: Dict[str, Any]) -> float:
    """Calculate Intersection over Union."""
    x1_min, y1_min, x1_max, y1_max = box1['x'], box1['y'], box1['x'] + box1['w'], box1['y'] + box1['h']
    x2_min, y2_min, x2_max, y2_max = box2['x'], box2['y'], box2['x'] + box2['w'], box2['y'] + box2['h']

    xi1 = max(x1_min, x2_min)
    yi1 = max(y1_min, y2_min)
    xi2 = min(x1_max, x2_max)
    yi2 = min(y1_max, y2_max)

    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    area1 = (x1_max - x1_min) * (y1_max - y1_min)
    area2 = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = area1 + area2 - inter_area

    if union_area == 0:
        return 0.0
    return inter_area / union_area

def is_within_bounds(box: Dict[str, Any], image_size: Tuple[int, int]) -> bool:
    """Check if a box is within image bounds."""
    w, h = image_size
    return (box['x'] >= 0 and box['y'] >= 0 and
            box['x'] + box['w'] <= w and box['y'] + box['h'] <= h)

def boxes_overlap(box1: Dict[str, Any], box2: Dict[str, Any], threshold: float = 0.05) -> bool:
    """Check if two boxes overlap significantly."""
    return calculate_iou(box1, box2) > threshold

def place_single_box(
    image_size: Tuple[int, int],
    existing_boxes: List[Dict[str, Any]],
    rng: random.Random,
    min_size: int = 50,
    max_size: int = 150
) -> Optional[Dict[str, Any]]:
    """Attempt to place a single non-overlapping box."""
    w, h = image_size
    attempts = 0
    max_attempts = 500

    while attempts < max_attempts:
        size = rng.randint(min_size, max_size)
        x = rng.randint(0, w - size)
        y = rng.randint(0, h - size)

        candidate = {'x': x, 'y': y, 'w': size, 'h': size, 'id': len(existing_boxes)}

        if not is_within_bounds(candidate, image_size):
            continue

        overlap = False
        for existing in existing_boxes:
            if boxes_overlap(candidate, existing):
                overlap = True
                break

        if not overlap:
            return candidate

        attempts += 1

    return None

def place_boxes(
    image_size: Tuple[int, int],
    num_boxes: int,
    rng: random.Random
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Attempt to place a specific number of boxes.
    Returns (list of boxes, success_flag).
    """
    boxes = []
    target = num_boxes
    attempts = 0
    max_total_attempts = num_boxes * 1000

    while len(boxes) < target and attempts < max_total_attempts:
        box = place_single_box(image_size, boxes, rng)
        if box:
            boxes.append(box)
        attempts += 1

    if len(boxes) < target:
        # We failed to place all requested boxes
        return boxes, False

    return boxes, True

def place_boxes_with_retry(
    image_size: Tuple[int, int],
    num_boxes: int,
    rng: random.Random,
    max_attempts: int = 10
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Place boxes with retry logic.
    If placement fails for the full count, it retries with reduced counts.
    Returns (list of boxes, success_flag).
    If success is False, it means we couldn't even place a reasonable amount.
    """
    current_target = num_boxes
    attempt = 0

    while attempt < max_attempts:
        boxes, success = place_boxes(image_size, current_target, rng)
        if success:
            return boxes, True
        
        # If we failed, try with fewer boxes
        # Reduce by 10% or 5 boxes, whichever is larger, but not below 10
        reduction = max(5, int(current_target * 0.1))
        current_target = max(10, current_target - reduction)
        attempt += 1

    # Final attempt with the last reduced count
    boxes, success = place_boxes(image_size, current_target, rng)
    return boxes, success

def main():
    """Test placer."""
    import logging
    logging.basicConfig(level=logging.INFO)
    rng = random.Random(42)
    boxes, success = place_boxes_with_retry((1024, 1024), 50, rng)
    print(f"Placed {len(boxes)} boxes. Success: {success}")

if __name__ == "__main__":
    main()
