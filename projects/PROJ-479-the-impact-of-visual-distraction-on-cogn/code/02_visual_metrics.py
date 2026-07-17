"""
Visual Complexity Metric Extraction Module.
Computes edge density, color entropy, and object count.
"""
import os
import sys
import math
import time
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from contextlib import contextmanager

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

from utils import get_logger, log_structured_error

logger = get_logger(__name__)

@contextmanager
def timeout_context(timeout: float = 30.0):
    """
    Context manager for timeout handling.
    """
    start_time = time.time()
    try:
        yield
        elapsed = time.time() - start_time
        if elapsed > timeout:
            logger.warning(f"Operation took {elapsed:.2f}s, exceeding timeout {timeout}s")
    except Exception as e:
        logger.error(f"Timeout or error in context: {e}")
        raise

def calculate_edge_density(image_path: str) -> float:
    """
    Calculate normalized edge density using OpenCV Canny.
    Returns value in [0, 1].
    """
    if cv2 is None:
        raise ImportError("OpenCV not installed")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    
    total_pixels = edges.size
    edge_pixels = cv2.countNonZero(edges)
    
    density = edge_pixels / total_pixels
    return float(density)

def calculate_color_entropy(image_path: str) -> float:
    """
    Calculate color entropy using histogram-based analysis.
    """
    if cv2 is None:
        raise ImportError("OpenCV not installed")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    # Convert to HSV for better color distribution
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    channels = [hsv[:, :, i] for i in range(3)]
    
    entropies = []
    for channel in channels:
        hist = cv2.calcHist([channel], [0], None, [256], [0, 256])
        hist = hist.flatten()
        hist = hist / hist.sum()
        hist = hist[hist > 0]
        entropy = -np.sum(hist * np.log2(hist))
        entropies.append(entropy)
    
    return float(np.mean(entropies))

def calculate_object_count(image_path: str) -> float:
    """
    Calculate object count using YOLOv5n/tiny.
    Returns NaN on failure or timeout.
    """
    if YOLO is None:
        logger.warning("Ultralytics not installed, returning NaN for object count")
        return float('nan')

    try:
        with timeout_context(timeout=30.0):
            model = YOLO("yolov5n.pt")
            results = model(image_path)
            count = len(results[0].boxes)
            return float(count)
    except Exception as e:
        log_structured_error("image_processing_failures", {
            "file": image_path, 
            "error": str(e)
        })
        return float('nan')

def process_image_metrics(
    image_path: str, 
    participant_id: str
) -> Dict[str, Any]:
    """
    Process a single image and return metrics.
    """
    metrics = {
        "participant_id": participant_id,
        "file_path": image_path,
        "edge_density": 0.0,
        "color_entropy": 0.0,
        "object_count": float('nan')
    }

    try:
        metrics["edge_density"] = calculate_edge_density(image_path)
    except Exception as e:
        logger.error(f"Edge density failed for {image_path}: {e}")

    try:
        metrics["color_entropy"] = calculate_color_entropy(image_path)
    except Exception as e:
        logger.error(f"Color entropy failed for {image_path}: {e}")

    try:
        metrics["object_count"] = calculate_object_count(image_path)
    except Exception as e:
        logger.error(f"Object count failed for {image_path}: {e}")

    return metrics

def main() -> None:
    """
    Main execution for visual metrics extraction.
    """
    raw_dir = "data/raw"
    processed_dir = "data/processed"
    os.makedirs(processed_dir, exist_ok=True)

    images = [
        os.path.join(raw_dir, f) 
        for f in os.listdir(raw_dir) 
        if f.endswith(('.png', '.jpg', '.jpeg'))
    ]

    results = []
    for img_path in images:
        pid = os.path.splitext(os.path.basename(img_path))[0]
        metrics = process_image_metrics(img_path, pid)
        results.append(metrics)

    df = pd.DataFrame(results)
    df.to_csv(os.path.join(processed_dir, "visual_metrics_intermediate.csv"), index=False)
    
    # Merge with main data
    main_data_path = os.path.join(processed_dir, "merged_data.csv")
    if os.path.exists(main_data_path):
        main_df = pd.read_csv(main_data_path)
        merged = pd.merge(main_df, df, on="participant_id", how="inner")
        merged.to_csv(os.path.join(processed_dir, "final_analysis_data.csv"), index=False)
        logger.info(f"Merged data saved. Unmatched: {len(main_df) - len(merged)}")

if __name__ == "__main__":
    main()
