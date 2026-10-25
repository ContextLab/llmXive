"""
Preprocess raw dataset files to produce dense and non‑dense subsets
and an exclusion log.

This script reads the three raw parquet files produced by T001:
- data/raw/vrsbench.parquet
- data/raw/coco_val.parquet
- data/raw/refcoco_plus.parquet

For each image it:
  1. Removes ambiguous ground‑truth boxes:
     * zero‑area boxes
     * boxes that overlap another box with IoU > 0.95
  2. Computes the number of overlapping box pairs with IoU > 0.10.
  3. Classifies the image as **dense** if the count of such pairs is > 5,
     otherwise as **non‑dense**.
  4. Writes the cleaned annotations for each class to parquet files.
  5. Writes a JSON exclusion log containing statistics about the
     number of excluded boxes and images.

The script is deliberately lightweight and uses only the standard
scientific stack (pandas, numpy, tqdm). It aborts loudly if the expected
column names are not present, ensuring that any mismatch is visible during
CI runs.

The resulting files are:
  - data/processed/dense_subset.parquet
  - data/processed/non_dense.parquet
  - data/processed/exclusion_log.json
"""

import json
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

from llmxive_toolkit import paths, get_logger

# Import download utilities to lazily fetch missing raw data.
from code.data.download import (
    download_vrsbench,
    download_coco_val,
    download_refcoco_plus,
)

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _ensure_raw_data() -> None:
    """
    Ensure that the three expected raw parquet files exist.
    If any are missing, invoke the download functions to create them.
    """
    raw_dir = paths.data("raw")
    files_and_downloads = [
        (raw_dir / "vrsbench.parquet", download_vrsbench),
        (raw_dir / "coco_val.parquet", download_coco_val),
        (raw_dir / "refcoco_plus.parquet", download_refcoco_plus),
    ]
    for path_obj, download_fn in files_and_downloads:
        if not path_obj.is_file():
            log.info(f"Raw file {path_obj.name} missing – downloading.")
            download_fn(path_obj)
        else:
            log.info(f"Raw file {path_obj.name} found.")

def _load_raw_datasets() -> pd.DataFrame:
    """Load and concatenate the three raw parquet files."""
    _ensure_raw_data()
    raw_dir = paths.data("raw")
    files = [
        raw_dir / "vrsbench.parquet",
        raw_dir / "coco_val.parquet",
        raw_dir / "refcoco_plus.parquet",
    ]
    dfs = []
    for f in files:
        if not f.is_file():
            raise FileNotFoundError(f"Raw dataset not found: {f}")
        log.info(f"Loading raw dataset {f.name}")
        dfs.append(pd.read_parquet(f))
    combined = pd.concat(dfs, ignore_index=True)
    log.info(f"Combined raw dataset shape: {combined.shape}")
    return combined

def _extract_bbox_column(df: pd.DataFrame) -> str:
    """
    Determine which column holds bounding‑box data.
    Handles three cases:
      1. Direct bbox column (e.g., 'bbox', 'boxes', etc.).
      2. An 'annotations' column where each entry is a list of dicts
         containing a 'bbox' key.
    The function adds a new column named 'boxes' containing a list of
    [x1, y1, x2, y2] boxes and returns its name.
    """
    possible_names = ["bbox", "boxes", "bounding_box", "bounding_boxes"]
    for name in possible_names:
        if name in df.columns:
            return name

    # Fallback: use 'annotations' if present.
    if "annotations" in df.columns:
        # Create a new column 'boxes' with extracted bbox lists.
        def _extract(entry):
            # entry may be a list of dicts or a single dict.
            if isinstance(entry, list):
                return [ann["bbox"] for ann in entry if "bbox" in ann]
            elif isinstance(entry, dict):
                return [entry["bbox"]] if "bbox" in entry else []
            else:
                return []

        df["boxes"] = df["annotations"].apply(_extract)
        return "boxes"

    raise KeyError(
        "Could not find a bounding‑box column. Expected one of "
        f"{possible_names + ['annotations']}, found columns: {list(df.columns)}"
    )

def _iou(box_a: np.ndarray, box_b: np.ndarray) -> float:
    """Compute Intersection‑over‑Union of two boxes."""
    # box format: [x1, y1, x2, y2]
    x_left = max(box_a[0], box_b[0])
    y_top = max(box_a[1], box_b[1])
    x_right = min(box_a[2], box_b[2])
    y_bottom = min(box_a[3], box_b[3])

    if x_right <= x_left or y_bottom <= y_top:
        return 0.0

    inter_area = (x_right - x_left) * (y_bottom - y_top)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union = area_a + area_b - inter_area
    if union == 0:
        return 0.0
    return inter_area / union

def _filter_ambiguous_boxes(
    boxes: List[List[float]],
) -> Tuple[List[List[float]], int]:
    """
    Remove zero‑area boxes and boxes that overlap another box with IoU > 0.95.
    Returns the cleaned list of boxes and the number of boxes excluded.
    """
    if not boxes:
        return [], 0

    boxes_arr = np.array(boxes, dtype=float)  # shape (N, 4)
    keep_mask = np.ones(len(boxes), dtype=bool)
    excluded = 0

    # Zero‑area removal
    widths = boxes_arr[:, 2] - boxes_arr[:, 0]
    heights = boxes_arr[:, 3] - boxes_arr[:, 1]
    zero_area = (widths <= 0) | (heights <= 0)
    if zero_area.any():
        keep_mask &= ~zero_area
        excluded += zero_area.sum()

    # High‑IoU (>0.95) removal
    idxs = np.where(keep_mask)[0]
    for i in range(len(idxs)):
        for j in range(i + 1, len(idxs)):
            idx_i = idxs[i]
            idx_j = idxs[j]
            iou_val = _iou(boxes_arr[idx_i], boxes_arr[idx_j])
            if iou_val > 0.95:
                # Exclude both boxes
                if keep_mask[idx_i]:
                    keep_mask[idx_i] = False
                    excluded += 1
                if keep_mask[idx_j]:
                    keep_mask[idx_j] = False
                    excluded += 1

    cleaned = boxes_arr[keep_mask].tolist()
    return cleaned, excluded

def _count_overlapping_pairs(
    boxes: List[List[float]], iou_threshold: float = 0.10
) -> int:
    """
    Count the number of unordered box pairs whose IoU exceeds `iou_threshold`.
    """
    if len(boxes) < 2:
        return 0
    boxes_arr = np.array(boxes, dtype=float)
    count = 0
    for i in range(len(boxes_arr)):
        for j in range(i + 1, len(boxes_arr)):
            if _iou(boxes_arr[i], boxes_arr[j]) > iou_threshold:
                count += 1
    return count

# ----------------------------------------------------------------------
# Main preprocessing routine
# ----------------------------------------------------------------------
def preprocess() -> None:
    """
    Execute the preprocessing pipeline:
    - Load raw parquet files (downloading them if necessary).
    - Normalise the bounding‑box column.
    - Filter ambiguous boxes.
    - Classify images as dense or non‑dense.
    - Persist results and an exclusion log.
    """
    raw_df = _load_raw_datasets()
    bbox_col = _extract_bbox_column(raw_df)

    # Ensure the bbox column contains list‑like objects
    if not pd.api.types.is_object_dtype(raw_df[bbox_col]):
        raise TypeError(
            f"The column '{bbox_col}' must contain list‑like bounding boxes."
        )

    # Prepare containers for results
    dense_rows = []
    non_dense_rows = []
    total_boxes = 0
    total_excluded_boxes = 0
    total_images = raw_df["image_id"].nunique()
    excluded_images_set = set()

    # Group by image_id
    grouped = raw_df.groupby("image_id")
    log.info(f"Processing {len(grouped)} images for density classification")

    for image_id, group in tqdm(grouped, desc="Images"):
        # Collect all boxes for this image (flatten if multiple rows)
        boxes: List[List[float]] = []
        for entry in group[bbox_col]:
            # Entry may be a list of boxes, a single box, or nested lists.
            if isinstance(entry, (list, tuple)):
                if len(entry) == 4 and all(isinstance(v, (int, float)) for v in entry):
                    # Single box
                    boxes.append(list(entry))
                else:
                    # Assume iterable of boxes (list of lists)
                    boxes.extend([list(b) for b in entry if isinstance(b, (list, tuple))])
            else:
                raise ValueError(
                    f"Unexpected bbox entry type {type(entry)} for image {image_id}"
                )

        total_boxes += len(boxes)

        # Remove ambiguous boxes
        cleaned_boxes, excluded_cnt = _filter_ambiguous_boxes(boxes)
        total_excluded_boxes += excluded_cnt

        if not cleaned_boxes:
            # No valid boxes left – treat as excluded image
            excluded_images_set.add(image_id)
            continue

        # Determine density
        overlap_pairs = _count_overlapping_pairs(cleaned_boxes, iou_threshold=0.10)
        dense = overlap_pairs > 5

        # Store cleaned annotation rows (preserve original columns except bbox)
        # We keep the first row of the group as a template and replace its bbox
        # with the cleaned list.
        template_row = group.iloc[0].copy()
        template_row[bbox_col] = cleaned_boxes
        if dense:
            dense_rows.append(template_row)
        else:
            non_dense_rows.append(template_row)

    # Build DataFrames
    dense_df = pd.DataFrame(dense_rows)
    non_dense_df = pd.DataFrame(non_dense_rows)

    # Write outputs
    out_dense = paths.data("processed", "dense_subset.parquet")
    out_non_dense = paths.data("processed", "non_dense.parquet")
    out_log = paths.data("processed", "exclusion_log.json")

    dense_df.to_parquet(out_dense, index=False)
    non_dense_df.to_parquet(out_non_dense, index=False)

    exclusion_log = {
        "total_images": int(total_images),
        "excluded_images": int(len(excluded_images_set)),
        "proportion_excluded_images": len(excluded_images_set) / total_images
        if total_images > 0
        else 0.0,
        "total_boxes": int(total_boxes),
        "excluded_boxes": int(total_excluded_boxes),
        "proportion_excluded_boxes": total_excluded_boxes / total_boxes
        if total_boxes > 0
        else 0.0,
    }

    with out_log.open("w", encoding="utf-8") as f:
        json.dump(exclusion_log, f, indent=2)

    log.info(f"Dense subset written to {out_dense}")
    log.info(f"Non‑dense subset written to {out_non_dense}")
    log.info(f"Exclusion log written to {out_log}")

if __name__ == "__main__":
    preprocess()
