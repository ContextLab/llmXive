"""
Metric Extraction Script
========================

This script processes background images, computes visual complexity metrics,
and records performance statistics.

Metrics computed per image:
  * Entropy (grayscale Shannon entropy)
  * Color variance (variance across all RGB channels)
  * Object detection count (using YOLOv8n)

Output:
  * ``data/processed/metrics.csv`` – one row per image with the computed metrics.
  * ``data/derived/performance_log.txt`` – timing and memory usage information.
"""

import os
import time
import json
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import pandas as pd

# YOLOv8 (ultralytics) may not be importable on systems without the package.
# It is declared as a dependency in ``requirements.txt``.
from ultralytics import YOLO

# Optional: psutil for memory usage reporting.
try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None  # type: ignore

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def list_image_files(root_dir: Path) -> List[Path]:
    """Return a list of image file paths under ``root_dir``."""
    extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
    return [p for p in root_dir.rglob("*") if p.suffix.lower() in extensions]

def compute_entropy(image: np.ndarray) -> float:
    """
    Compute the Shannon entropy of a grayscale image.

    Parameters
    ----------
    image : np.ndarray
        Grayscale image (uint8).

    Returns
    -------
    float
        Entropy in bits.
    """
    # Histogram with 256 bins for uint8 images.
    hist = cv2.calcHist([image], [0], None, [256], [0, 256]).flatten()
    prob = hist / hist.sum()
    # Avoid log2(0) by masking zero probabilities.
    prob = prob[prob > 0]
    entropy = -np.sum(prob * np.log2(prob))
    return float(entropy)

def compute_color_variance(image: np.ndarray) -> float:
    """
    Compute the variance across all RGB channels.

    Parameters
    ----------
    image : np.ndarray
        Color image in BGR format (as read by OpenCV).

    Returns
    -------
    float
        Variance of pixel values across the three channels.
    """
    # Convert to float for variance calculation.
    img_float = image.astype(np.float32)
    # Compute variance per channel then average.
    variances = np.var(img_float, axis=(0, 1))
    return float(variances.mean())

def count_objects_yolo(model: YOLO, image: np.ndarray) -> int:
    """
    Run YOLOv8n on an image and return the number of detected objects.

    The image is resized to 640×640 (as required by NFR‑001) before inference.

    Parameters
    ----------
    model : ultralytics.YOLO
        Loaded YOLOv8n model.
    image : np.ndarray
        BGR image as read by OpenCV.

    Returns
    -------
    int
        Number of detected bounding boxes.
    """
    # YOLO expects RGB; convert and resize.
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # YOLO's ``predict`` can accept a numpy array directly.
    results = model.predict(
        source=rgb_image,
        imgsz=640,
        conf=0.25,
        device="cpu",
        verbose=False,
    )
    # ``results`` is a list with a single ``Results`` object.
    if not results:
        return 0
    result = results[0]
    # ``result.boxes`` holds the detections.
    return int(len(result.boxes))

# ---------------------------------------------------------------------------
# Main processing function
# ---------------------------------------------------------------------------

def process_images(
    stimuli_dir: Path,
    output_csv: Path,
    performance_log: Path,
) -> None:
    """
    Process all images under ``stimuli_dir`` and write metrics + performance log.

    Parameters
    ----------
    stimuli_dir : Path
        Directory containing stimulus images.
    output_csv : Path
        Destination CSV file for the metrics.
    performance_log : Path
        Destination text file for timing / memory statistics.
    """
    # Ensure output directories exist.
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    performance_log.parent.mkdir(parents=True, exist_ok=True)

    image_paths = list_image_files(stimuli_dir)
    if not image_paths:
        raise FileNotFoundError(f"No image files found in {stimuli_dir}")

    # Load YOLOv8n model (weights are downloaded automatically on first run).
    yolo_model = YOLO("yolov8n.pt")

    records: List[Tuple[str, float, float, int]] = []

    # Performance measurement.
    start_time = time.time()
    start_mem = (
        psutil.Process(os.getpid()).memory_info().rss / (1024 ** 2)
        if psutil
        else None
    )

    for img_path in image_paths:
        # Read image.
        img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        if img is None:
            raise IOError(f"Failed to read image {img_path}")

        # Resize to 640×640 for internal processing (NFR‑001).
        resized = cv2.resize(img, (640, 640), interpolation=cv2.INTER_AREA)

        # Compute metrics.
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        entropy = compute_entropy(gray)
        color_var = compute_color_variance(resized)
        obj_count = count_objects_yolo(yolo_model, resized)

        records.append(
            (img_path.name, entropy, color_var, obj_count)
        )

    # Assemble DataFrame.
    df = pd.DataFrame(
        records,
        columns=["image_id", "entropy", "color_variance", "object_count"],
    )
    df.to_csv(output_csv, index=False)

    # Performance statistics.
    end_time = time.time()
    elapsed = end_time - start_time
    end_mem = (
        psutil.Process(os.getpid()).memory_info().rss / (1024 ** 2)
        if psutil
        else None
    )
    peak_mem = max(start_mem or 0, end_mem or 0)

    log_content = {
        "total_images": len(image_paths),
        "total_time_seconds": round(elapsed, 3),
        "average_time_per_image_seconds": round(elapsed / len(image_paths), 3),
    }
    if psutil:
        log_content["peak_memory_mb"] = round(peak_mem, 2)

    performance_log.write_text(json.dumps(log_content, indent=2))

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Entry point for ``python -m src.metrics.extract`` or direct execution.
    """
    project_root = Path(__file__).resolve().parents[3]  # up to ``code`` directory
    stimuli_dir = project_root / "data" / "stimuli"
    output_csv = project_root / "data" / "processed" / "metrics.csv"
    performance_log = project_root / "data" / "derived" / "performance_log.txt"

    process_images(stimuli_dir, output_csv, performance_log)
    print(f"Metrics written to {output_csv}")
    print(f"Performance log written to {performance_log}")

if __name__ == "__main__":
    main()
