"""
Unit tests for the preprocessing script (code/data/preprocess.py).

The test suite checks two things:
  1. The proportion of excluded images (as recorded in the exclusion log)
     does not exceed 5 % of the total number of images.
  2. At least one dense‑scene image contains more than five overlapping
     box pairs with IoU > 0.10 (spot‑check).
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from llmxive_toolkit import paths

# Import the preprocessing function – this will also generate the outputs.
from code.data.preprocess import preprocess

@pytest.fixture(scope="module")
def run_preprocess():
    """Execute the preprocessing step once for the whole test module."""
    preprocess()
    # No return value; the function writes files to disk.

def test_exclusion_proportion(run_preprocess):
    """Assert that ≤ 5 % of images were excluded."""
    log_path = paths.data("processed", "exclusion_log.json")
    assert log_path.is_file(), f"Exclusion log missing: {log_path}"
    with log_path.open("r", encoding="utf-8") as f:
        log = json.load(f)
    proportion = log.get("proportion_excluded_images")
    assert proportion is not None, "Log missing 'proportion_excluded_images'"
    assert proportion <= 0.05, f"Excluded proportion too high: {proportion:.2%}"

def test_dense_scene_overlap(run_preprocess):
    """Spot‑check that at least one dense image has > 5 overlapping pairs."""
    dense_path = paths.data("processed", "dense_subset.parquet")
    assert dense_path.is_file(), f"Dense subset missing: {dense_path}"
    df = pd.read_parquet(dense_path)

    # Determine which column holds the boxes (mirroring the preprocessing logic)
    bbox_col = None
    for cand in ["bbox", "boxes", "bounding_box", "bounding_boxes"]:
        if cand in df.columns:
            bbox_col = cand
            break
    assert bbox_col is not None, "No bbox column found in dense subset"

    # Helper IoU (duplicate of implementation for test reliability)
    def iou(a, b):
        x_left = max(a[0], b[0])
        y_top = max(a[1], b[1])
        x_right = min(a[2], b[2])
        y_bottom = min(a[3], b[3])
        if x_right <= x_left or y_bottom <= y_top:
            return 0.0
        inter = (x_right - x_left) * (y_bottom - y_top)
        area_a = (a[2] - a[0]) * (a[3] - a[1])
        area_b = (b[2] - b[0]) * (b[3] - b[1])
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    # Verify condition for at least one image
    found = False
    for _, row in df.iterrows():
        boxes = row[bbox_col]
        if not isinstance(boxes, list) or len(boxes) < 2:
            continue
        overlap_cnt = 0
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if iou(boxes[i], boxes[j]) > 0.10:
                    overlap_cnt += 1
        if overlap_cnt > 5:
            found = True
            break

    assert found, "No dense image with > 5 overlapping box pairs found"