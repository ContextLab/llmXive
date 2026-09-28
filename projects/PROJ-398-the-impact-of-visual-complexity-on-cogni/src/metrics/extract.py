"""
src/metrics/extract.py

This module implements the core visual‑complexity metric extraction pipeline
used throughout the project. It provides utilities to:

* enumerate image files in a directory,
* compute image entropy,
* compute colour variance,
* count detectable objects using a YOLOv8n model (CPU‑only),
* process a directory of images and write the results to a CSV file.

The implementation is deliberately lightweight and free of side‑effects
beyond writing the output CSV, making it suitable for unit‑testing.  The
``count_objects_yolo`` function is robust: if the model fails to load or if
the inference returns no detections, it returns ``0`` – satisfying task
**T020** (handle no‑object images).
"""

import csv
import os
import pathlib
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

# The ultralytics package is listed in ``requirements.txt``.
# Import lazily so that the module can be imported even on systems
# without the optional heavy dependencies (e.g. during static analysis).
try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover
    YOLO = None  # type: ignore

__all__ = [
    "list_image_files",
    "compute_entropy",
    "compute_color_variance",
    "count_objects_yolo",
    "process_images",
    "main",
]

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def list_image_files(directory: Path) -> List[Path]:
    """
    Return a list of image file paths (PNG/JPG/JPEG) found recursively
    under ``directory``. The order is deterministic (sorted alphabetically).
    """
    supported = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
    files: List[Path] = []
    for root, _dirs, _files in os.walk(directory):
        for name in _files:
            p = Path(root) / name
            if p.suffix.lower() in supported:
                files.append(p)
    files.sort()
    return files

# ----------------------------------------------------------------------
# Metric calculations
# ----------------------------------------------------------------------
def compute_entropy(image: np.ndarray) -> float:
    """
    Compute the Shannon entropy of a grayscale version of ``image``.
    The image is expected to be in BGR order (as returned by OpenCV).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist.ravel()
    prob = hist / hist.sum()
    # Avoid log(0) by masking zero probabilities
    prob = prob[prob > 0]
    entropy = -float(np.sum(prob * np.log2(prob)))
    return entropy

def compute_color_variance(image: np.ndarray) -> float:
    """
    Compute the average variance across the three colour channels.
    """
    # Split channels (B, G, R)
    variances = [float(np.var(image[:, :, i])) for i in range(3)]
    return float(np.mean(variances))

# ----------------------------------------------------------------------
# Object detection (YOLOv8n, CPU‑only)
# ----------------------------------------------------------------------
_yolo_model = None  # cached model instance

def _load_yolo_model() -> "YOLO":
    """
    Load the YOLOv8n model (CPU‑only) and cache it for reuse.
    Raises an informative error if the model cannot be loaded.
    """
    global _yolo_model
    if _yolo_model is not None:
        return _yolo_model

    if YOLO is None:  # pragma: no cover
        raise RuntimeError(
            "ultralytics package is not available. Install it via "
            "`pip install ultralytics`."
        )
    # ``yolov8n.pt`` is the smallest public YOLOv8 model; it will be
    # downloaded automatically on first use.
    _yolo_model = YOLO("yolov8n.pt")
    return _yolo_model

def count_objects_yolo(image_path: Path) -> int:
    """
    Run YOLOv8n on ``image_path`` and return the number of detected objects.

    If the model fails to load, the image cannot be read, or the inference
    yields no detections, the function returns ``0`` – fulfilling the
    requirement of **T020** (no‑object images must produce ``object_count = 0``).
    """
    try:
        # Load image – OpenCV reads as BGR; YOLO expects a file path.
        if not image_path.is_file():
            return 0
        model = _load_yolo_model()
        # ``model`` returns a list of results; each result corresponds to an image.
        results = model(str(image_path))
        if not results:
            return 0
        # YOLOv8 result objects have a ``boxes`` attribute.
        # ``len(result.boxes)`` gives the number of detections.
        result = results[0]
        # ``result.boxes`` may be ``None`` if nothing was detected.
        if getattr(result, "boxes", None) is None:
            return 0
        return int(len(result.boxes))
    except Exception:
        # Any unexpected error (e.g., model download failure) is treated as
        # “no objects detected” so that downstream pipelines continue.
        return 0

# ----------------------------------------------------------------------
# Pipeline orchestration
# ----------------------------------------------------------------------
def process_images(
    input_dir: Path,
    output_csv: Path,
    max_images: int | None = None,
) -> None:
    """
    Iterate over image files in ``input_dir`` and compute the three
    visual‑complexity metrics for each image.

    The results are written to ``output_csv`` with the following columns:

    ``image_id, entropy, color_variance, object_count``

    Parameters
    ----------
    input_dir:
        Directory containing the source images.
    output_csv:
        Destination CSV file. Parent directories are created if missing.
    max_images:
        Optional cap on the number of images processed (useful for quick
        sanity checks). If ``None``, all images are processed.
    """
    input_dir = Path(input_dir)
    output_csv = Path(output_csv)

    # Ensure output directory exists
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    image_paths = list_image_files(input_dir)
    if max_images is not None:
        image_paths = image_paths[:max_images]

    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image_id", "entropy", "color_variance", "object_count"])

        for img_path in image_paths:
            # Read image with OpenCV (fails gracefully)
            img = cv2.imread(str(img_path))
            if img is None:
                # Skip unreadable images but still write a placeholder row
                writer.writerow([img_path.name, "", "", ""])
                continue

            entropy = compute_entropy(img)
            colour_var = compute_color_variance(img)
            obj_cnt = count_objects_yolo(img_path)

            writer.writerow(
                [img_path.name, f"{entropy:.6f}", f"{colour_var:.6f}", obj_cnt]
            )

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _parse_cli_args() -> Tuple[Path, Path, int | None]:
    """
    Minimal CLI parser for manual execution.
    Returns ``(input_dir, output_csv, max_images)``.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract visual‑complexity metrics from a directory of images."
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Path to directory containing stimulus images.",
    )
    parser.add_argument(
        "output_csv",
        type=Path,
        help="Path where the resulting CSV should be written.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="Optional limit on number of images to process.",
    )
    args = parser.parse_args()
    return args.input_dir, args.output_csv, args.max_images

def main() -> None:
    """
    Command‑line entry point.  Example usage::

        python -m src.metrics.extract data/stimuli/raw data/processed/metrics.csv
    """
    input_dir, output_csv, max_images = _parse_cli_args()
    process_images(input_dir, output_csv, max_images)

if __name__ == "__main__":  # pragma: no cover
    main()