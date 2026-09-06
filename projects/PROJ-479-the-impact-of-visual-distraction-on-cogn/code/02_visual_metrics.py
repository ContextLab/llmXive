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
    """Determine image directory based on existence of raw or synthetic_images folders."""
    if os.path.exists("data/raw/synthetic_images"):
        return "data/raw/synthetic_images"
    elif os.path.exists("data/raw/workspace_images"):
        return "data/raw/workspace_images"
    elif os.path.exists("data/raw"):
        # Fallback if only data/raw exists but subdirs missing
        return "data/raw"
    else:
        raise FileNotFoundError("No image directory found. Expected data/raw/workspace_images or data/raw/synthetic_images.")

def calculate_edge_density(image_path: str) -> float:
    """
    Calculate normalized edge density using Canny edge detection.
    Output: Normalized value in [0, 1].
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.warning(f"Could not read image for edge density: {image_path}")
            return np.nan
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Canny edge detection
        edges = cv2.Canny(gray, 100, 200)
        
        total_pixels = edges.size
        if total_pixels == 0:
            return 0.0
            
        edge_pixels = cv2.countNonZero(edges)
        density = edge_pixels / total_pixels
        
        # Ensure normalization [0, 1]
        return float(min(density, 1.0))
    except Exception as e:
        logger.error(f"Edge density calculation failed for {image_path}: {e}")
        return np.nan

def calculate_color_entropy(image_path: str) -> float:
    """
    Calculate color entropy using histogram on flattened RGB channels.
    Uses np.histogram on grayscale for performance, as per spec simplification.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.warning(f"Could not read image for color entropy: {image_path}")
            return np.nan
        
        # Convert to grayscale for entropy calculation (performance)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Compute histogram
        hist, _ = np.histogram(gray, bins=256, range=(0, 256))
        
        # Normalize to probabilities
        hist = hist.astype(float)
        total = hist.sum()
        if total == 0:
            return 0.0
            
        p = hist / total
        
        # Filter out zeros to avoid log(0)
        p = p[p > 0]
        
        # Calculate entropy: -sum(p * log2(p))
        entropy = -np.sum(p * np.log2(p))
        
        return float(entropy)
    except Exception as e:
        logger.error(f"Color entropy calculation failed for {image_path}: {e}")
        return np.nan

def calculate_object_count(image_path: str) -> float:
    """
    Calculate object count using YOLO (CPU).
    Assigns NaN on failure, timeout, or if no objects are detected.
    """
    try:
        from ultralytics import YOLO
        # Use YOLOv8n.pt as specified in task T026c
        model = YOLO('yolov8n.pt')
        
        # Run inference with timeout context
        with timeout_context(60):  # 60s timeout for CPU inference
            results = model(image_path, verbose=False, conf=0.25)
            
        if len(results) > 0 and len(results[0].boxes) > 0:
            count = len(results[0].boxes)
            return float(count)
        else:
            # No objects detected -> NaN as per spec
            logger.info(f"No objects detected in {image_path}, assigning NaN.")
            return np.nan
    except TimeoutError:
        logger.warning(f"Object count timed out for {image_path}, assigning NaN.")
        return np.nan
    except Exception as e:
        logger.warning(f"Object count failed for {image_path}: {e}. Assigning NaN.")
        return np.nan

def load_merged_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def process_image_metrics(image_dir: str) -> List[Dict]:
    """Process all images in directory."""
    results = []
    if not os.path.exists(image_dir):
        logger.error(f"Image directory does not exist: {image_dir}")
        return results
        
    files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    logger.info(f"Found {len(files)} images in {image_dir}")
    
    for f in files:
        path = os.path.join(image_dir, f)
        
        # Extract participant ID from filename
        # Expected formats: img_<hash>.jpg, workspace_<pid>.jpg, or just <pid>.jpg
        pid = f
        if pid.endswith('.png'):
            pid = pid[:-4]
        elif pid.endswith('.jpg'):
            pid = pid[:-4]
        elif pid.endswith('.jpeg'):
            pid = pid[:-5]
        
        # Handle workspace_ prefix
        if pid.startswith('workspace_'):
            pid = pid.replace('workspace_', '')
        
        # Handle img_<hash> prefix (extract hash or use full hash as ID)
        if pid.startswith('img_'):
            pid = pid.replace('img_', '')
        
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
    logger.info(f"Saved intermediate metrics to {path}")

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
    logger.info(f"Using image directory: {img_dir}")
    
    # Load cognitive data
    cog_path = "data/processed/merged_data.csv"
    if not os.path.exists(cog_path):
        raise FileNotFoundError(f"Cognitive data not found: {cog_path}")
    cog_df = load_merged_data(cog_path)
    logger.info(f"Loaded cognitive data with {len(cog_df)} rows")
    
    # Process images
    logger.info(f"Processing images in {img_dir}...")
    metrics_list = process_image_metrics(img_dir)
    if not metrics_list:
        logger.warning("No metrics generated from images.")
        return
        
    metrics_df = pd.DataFrame(metrics_list)
    logger.info(f"Processed {len(metrics_df)} images")
    
    # Save intermediate
    save_intermediate_metrics(metrics_df, "data/processed/visual_metrics_intermediate.csv")
    
    # Merge
    final_df = merge_with_cognitive_data(metrics_df, cog_df)
    logger.info(f"Merged data has {len(final_df)} rows")
    
    # Log counts
    nan_count = final_df['object_count'].isna().sum()
    logger.info(f"Records with NaN object_count: {nan_count}")
    
    # Save final
    save_final_analysis_data(final_df, "data/processed/final_analysis_data.csv")
    
    logger.info("Visual Metrics Pipeline completed.")

if __name__ == "__main__":
    main()