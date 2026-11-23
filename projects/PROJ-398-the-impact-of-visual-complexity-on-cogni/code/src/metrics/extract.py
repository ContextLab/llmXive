"""
src/metrics/extract.py

This module provides utilities to extract visual complexity metrics from image files.
It computes:
  - Shannon entropy of the grayscale image.
  - Color variance across RGB channels.
  - Object count using a CPU‑only YOLOv8n model.

The functions are deliberately lightweight and avoid side‑effects so they can be
reused in pipelines and unit tests. The `process_images` function writes a CSV
compatible with the `BackgroundFrame` schema required by downstream tasks.
"""

import csv
import json
import os
import time
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

# Ultralytics YOLOv8n is a heavy dependency; we import lazily to keep module import
# cheap for tests that do not need object detection.
from ultralytics import YOLO

# Global model instance – loaded once on first use.
_YOLO_MODEL = None

def _load_yolo_model() -> YOLO:
    """
    Load the YOLOv8n model (CPU‑only) lazily.

    Returns
    -------
    YOLO
        The loaded YOLO model.
    """
    global _YOLO_MODEL
    if _YOLO_MODEL is None:
        # The pretrained weights are bundled with the ultralytics package.
        # Using the smallest nano model keeps CPU usage reasonable.
        _YOLO_MODEL = YOLO("yolov8n.pt")
    return _YOLO_MODEL

def list_image_files(stimuli_dir: Path) -> List[Path]:
    """
    Return a list of image file paths (png, jpg, jpeg) in ``stimuli_dir``.
    """
    valid_ext = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
    return [
        p
        for p in sorted(stimuli_dir.iterdir())
        if p.is_file() and p.suffix.lower() in valid_ext
    ]

def compute_entropy(image_path: Path) -> float:
    """
    Compute the Shannon entropy of a grayscale version of the image.

    Parameters
    ----------
    image_path: Path
        Path to the image file.

    Returns
    -------
    float
        Entropy value (bits).
    """
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Unable to read image {image_path}")
    # Histogram of pixel intensities (256 bins)
    hist = cv2.calcHist([img], [0], None, [256], [0, 256]).flatten()
    prob = hist / hist.sum()
    prob = prob[prob > 0]  # discard zero entries to avoid log(0)
    entropy = -np.sum(prob * np.log2(prob))
    return float(entropy)

def compute_color_variance(image_path: Path) -> float:
    """
    Compute the variance of pixel intensities across the three colour channels.

    Parameters
    ----------
    image_path: Path
        Path to the image file.

    Returns
    -------
    float
        Mean variance across R, G, B channels.
    """
    img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Unable to read image {image_path}")
    # Split into channels and compute variance per channel
    variances = [np.var(img[:, :, i]) for i in range(3)]
    return float(np.mean(variances))

def count_objects_yolo(image_path: Path) -> int:
    """
    Detect objects in ``image_path`` using YOLOv8n (CPU‑only) and return the count.

    If the detector finds no objects, the function returns ``0`` rather than
    ``None`` or raising an error. This satisfies T020.

    Parameters
    ----------
    image_path: Path
        Path to the image file.

    Returns
    -------
    int
        Number of detected objects (0 if none).
    """
    model = _load_yolo_model()
    # YOLO inference returns a list of results; each result corresponds to an
    # input image (here a single image). ``boxes`` holds the detections.
    results = model(str(image_path), imgsz=640, device="cpu")
    if not results:
        # No result object – treat as zero detections.
        return 0
    result = results[0]
    # ``result.boxes`` may be empty; ``len`` works for both Torch tensors and
    # ultralytics Boxes objects.
    try:
        count = len(result.boxes)
    except Exception:
        # Defensive fallback – if the attribute is missing or not iterable.
        count = 0
    return int(count)

def process_images(stimuli_dir: Path, output_csv: Path) -> None:
    """
    Process all images in ``stimuli_dir`` and write a CSV with computed metrics.

    The CSV columns are:
        image_id, entropy, color_variance, object_count

    Parameters
    ----------
    stimuli_dir: Path
        Directory containing stimulus images.
    output_csv: Path
        Destination CSV file path.
    """
    images = list_image_files(stimuli_dir)
    if not images:
        raise RuntimeError(f"No images found in {stimuli_dir}")

    start_time = time.time()
    rows = []
    for img_path in images:
        image_id = img_path.stem
        entropy = compute_entropy(img_path)
        color_variance = compute_color_variance(img_path)
        object_count = count_objects_yolo(img_path)
        rows.append(
            {
                "image_id": image_id,
                "entropy": entropy,
                "color_variance": color_variance,
                "object_count": object_count,
            }
        )

    # Ensure parent directory exists
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    with output_csv.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "image_id",
                "entropy",
                "color_variance",
                "object_count",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    # Write a simple performance log (used by other tasks)
    perf_log_path = output_csv.parent.parent / "derived" / "performance_log.txt"
    perf_log_path.parent.mkdir(parents=True, exist_ok=True)
    duration = time.time() - start_time
    with perf_log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(
            f"Processed {len(rows)} images in {duration:.2f} seconds. "
            f"Average time per image: {duration/len(rows):.3f}s\\n"
        )

def main() -> None:
    """
    Command‑line entry point.

    Usage
    -----
    python -m src.metrics.extract --stimuli-dir data/stimuli/raw --output-csv data/processed/metrics.csv
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract visual‑complexity metrics from image stimuli."
    )
    parser.add_argument(
        "--stimuli-dir",
        type=Path,
        required=True,
        help="Directory containing stimulus image files.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        required=True,
        help="Path to write the metrics CSV (e.g., data/processed/metrics.csv).",
    )
    args = parser.parse_args()
    process_images(args.stimuli_dir, args.output_csv)

if __name__ == "__main__":
    main()