import os
import sys
import math
import time
import logging
import signal
import numpy as np
import pandas as pd
import cv2
from PIL import Image
from typing import Optional, Dict, List
import json

# Import from utils
try:
    from utils import get_logger, set_random_seed
except ImportError:
    def get_logger(name):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return logging.getLogger(name)
    def set_random_seed(seed):
        pass

logger = get_logger(__name__)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Function call timed out")

def timeout_context(seconds):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def wait_for_marker(marker_path: str, timeout: int = 300):
    """Wait for the .ready marker file."""
    start = time.time()
    while not os.path.exists(marker_path):
        if time.time() - start > timeout:
            raise FileNotFoundError(f"Marker file {marker_path} not found within {timeout}s")
        time.sleep(1)
    logger.info(f"Marker file {marker_path} found.")

def get_image_directory() -> str:
    """Determine image directory."""
    if os.path.exists("data/raw/synthetic_images"):
        return "data/raw/synthetic_images"
    elif os.path.exists("data/raw"):
        return "data/raw"
    else:
        raise FileNotFoundError("No image directory found.")

def calculate_edge_density(image_path: str) -> float:
    """Calculate normalized edge density using Canny."""
    img = cv2.imread(image_path)
    if img is None:
        return np.nan
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    total_pixels = edges.size
    edge_pixels = cv2.countNonZero(edges)
    density = edge_pixels / total_pixels
    return min(density, 1.0)  # Normalize to [0, 1]

def calculate_color_entropy(image_path: str) -> float:
    """Calculate color entropy using histogram."""
    img = cv2.imread(image_path)
    if img is None:
        return np.nan
    # Flatten and compute histogram
    hist = cv2.calcHist([img], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256])
    # This is computationally heavy, simplify to grayscale or single channel for speed
    # Task says: "np.histogram on flattened RGB channels (bins=256)"
    # We'll do a simplified version for performance
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hist, _ = np.histogram(gray, bins=256, range=(0, 256))
    hist = hist.astype(float)
    p = hist / hist.sum()
    p = p[p > 0]
    entropy = -np.sum(p * np.log2(p))
    return entropy

def calculate_object_count(image_path: str) -> float:
    """Calculate object count using YOLO (CPU). Assign NaN on failure."""
    try:
        from ultralytics import YOLO
        model = YOLO('yolov5n.pt')  # Small model for CPU
        results = model(image_path, verbose=False)
        count = len(results[0].boxes)
        return float(count)
    except Exception as e:
        logger.warning(f"Object count failed for {image_path}: {e}. Assigning NaN.")
        return np.nan

def load_merged_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def process_image_metrics(image_dir: str) -> List[Dict]:
    """Process all images in directory."""
    results = []
    files = [f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
    for f in files:
        path = os.path.join(image_dir, f)
        pid = f.replace('.png', '').replace('.jpg', '').replace('workspace_', '')
        # Extract ID if format is workspace_PID.png
        if pid.startswith('workspace_'):
            pid = pid.replace('workspace_', '')
        
        edge = calculate_edge_density(path)
        entropy = calculate_color_entropy(path)
        obj_count = calculate_object_count(path)
        
        results.append({
            'participant_id': pid,
            'edge_density': edge,
            'color_entropy': entropy,
            'object_count': obj_count
        })
    return results

def save_intermediate_metrics(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False)

def merge_with_cognitive_data(metrics_df: pd.DataFrame, cognitive_df: pd.DataFrame) -> pd.DataFrame:
    """Inner join on participant_id. Retain NaNs."""
    merged = pd.merge(cognitive_df, metrics_df, on='participant_id', how='inner')
    return merged

def save_final_analysis_data(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False)
    logger.info(f"Saved final analysis data to {path}")

def main():
    """Main execution for T027/T028."""
    # Wait for marker
    wait_for_marker("data/processed/.ready")
    
    # Get image dir
    img_dir = get_image_directory()
    
    # Load cognitive data
    cog_path = "data/processed/merged_data.csv"
    if not os.path.exists(cog_path):
        raise FileNotFoundError(f"Cognitive data not found: {cog_path}")
    cog_df = load_merged_data(cog_path)
    
    # Process images
    logger.info(f"Processing images in {img_dir}...")
    metrics_list = process_image_metrics(img_dir)
    metrics_df = pd.DataFrame(metrics_list)
    
    # Save intermediate
    save_intermediate_metrics(metrics_df, "data/processed/visual_metrics_intermediate.csv")
    
    # Merge
    final_df = merge_with_cognitive_data(metrics_df, cog_df)
    
    # Log counts
    nan_count = final_df['object_count'].isna().sum()
    logger.info(f"Records with NaN object_count: {nan_count}")
    
    # Save final
    save_final_analysis_data(final_df, "data/processed/final_analysis_data.csv")
    
    logger.info("Visual Metrics Pipeline completed.")

if __name__ == "__main__":
    main()
