import os
import sys
import math
import time
import logging
import numpy as np
import pandas as pd
import cv2
from typing import List, Dict, Any, Optional
from ultralytics import YOLO
import signal

# Import shared utilities
from utils import get_logger, set_random_seed, get_global_seed

# Configure logging
logger = get_logger(__name__)

# Timeout handling for object detection
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Object detection timed out")

def timeout_context(seconds):
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def calculate_edge_density(image_path: str) -> float:
    """
    Calculate normalized edge density using Canny edge detection.
    Returns a value between 0 and 1.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Failed to load image: {image_path}")
            return np.nan

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        
        edge_count = cv2.countNonZero(edges)
        total_pixels = edges.shape[0] * edges.shape[1]
        
        density = edge_count / total_pixels
        return float(density)
    except Exception as e:
        logger.error(f"Edge density calculation failed for {image_path}: {e}")
        return np.nan

def calculate_color_entropy(image_path: str) -> float:
    """
    Calculate color entropy based on histogram distribution.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Failed to load image: {image_path}")
            return np.nan

        # Convert to HSV for better color entropy calculation
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Calculate histograms for each channel
        h_hist = cv2.calcHist([hsv], [0], None, [256], [0, 256])
        s_hist = cv2.calcHist([hsv], [1], None, [256], [0, 256])
        v_hist = cv2.calcHist([hsv], [2], None, [256], [0, 256])
        
        # Normalize histograms
        h_hist = h_hist.flatten() / h_hist.sum()
        s_hist = s_hist.flatten() / s_hist.sum()
        v_hist = v_hist.flatten() / v_hist.sum()
        
        # Calculate entropy for each channel
        def entropy(hist):
            # Filter out zero probabilities to avoid log(0)
            hist = hist[hist > 0]
            return -np.sum(hist * np.log2(hist))
        
        h_ent = entropy(h_hist)
        s_ent = entropy(s_hist)
        v_ent = entropy(v_hist)
        
        # Average entropy across channels
        avg_entropy = (h_ent + s_ent + v_ent) / 3.0
        return float(avg_entropy)
    except Exception as e:
        logger.error(f"Color entropy calculation failed for {image_path}: {e}")
        return np.nan

def calculate_object_count(image_path: str, timeout_sec: int = 10) -> float:
    """
    Calculate object count using YOLOv5n model.
    Returns NaN if model fails, times out, or returns no objects.
    """
    try:
        # Load model (CPU mode)
        model = YOLO('yolov5n.pt')
        
        # Set timeout
        with timeout_context(timeout_sec):
            results = model(image_path, verbose=False)
        
        # Check if detections exist
        if results[0].boxes is None or len(results[0].boxes) == 0:
            logger.warning(f"No objects detected in {image_path}. Returning NaN.")
            return np.nan
        
        count = len(results[0].boxes)
        return float(count)
    except TimeoutError:
        logger.warning(f"Object detection timed out for {image_path}. Returning NaN.")
        return np.nan
    except Exception as e:
        logger.error(f"Object count calculation failed for {image_path}: {e}")
        return np.nan

def process_image_metrics(image_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Process a list of images and extract visual metrics.
    """
    metrics_list = []
    for path in image_paths:
        logger.info(f"Processing image: {path}")
        
        edge_density = calculate_edge_density(path)
        color_entropy = calculate_color_entropy(path)
        object_count = calculate_object_count(path)
        
        # Extract participant_id from filename (assumes format: participant_id_*.png)
        basename = os.path.basename(path)
        participant_id = basename.split('_')[0] if '_' in basename else "unknown"
        
        metrics_list.append({
            'participant_id': participant_id,
            'image_path': path,
            'edge_density': edge_density,
            'color_entropy': color_entropy,
            'object_count': object_count
        })
    
    return metrics_list

def main():
    """
    Main execution block for Task T027 and T028.
    1. Wait for marker file.
    2. Process images.
    3. Save intermediate metrics.
    4. Merge with cognitive data (T028).
    """
    logger.info("Starting Visual Metrics Pipeline (Tasks T027 & T028)")
    
    # Set global seed for reproducibility
    set_random_seed(get_global_seed())
    
    # T027: Wait for marker
    marker_path = "data/raw/.generation_complete"
    if not os.path.exists(marker_path):
        logger.error(f"Marker file not found: {marker_path}. T015c must complete first.")
        sys.exit(1)
    logger.info("Marker file found. Proceeding.")
    
    # Determine image directory
    raw_dir = "data/raw/synthetic_images"
    if not os.path.exists(raw_dir):
        # Fallback to data/raw if synthetic_images doesn't exist
        raw_dir = "data/raw"
    
    if not os.path.exists(raw_dir):
        logger.error(f"Image directory not found: {raw_dir}")
        sys.exit(1)
    
    # Get list of images
    image_files = [
        os.path.join(raw_dir, f) 
        for f in os.listdir(raw_dir) 
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]
    
    if not image_files:
        logger.warning("No images found to process.")
        # Create empty intermediate file to allow downstream to handle gracefully?
        # But spec says fail loudly if no data.
        # Let's create empty file with headers to avoid cascade failure in merge, 
        # but log error.
        pd.DataFrame(columns=['participant_id', 'image_path', 'edge_density', 'color_entropy', 'object_count']).to_csv(
            "data/processed/visual_metrics_intermediate.csv", index=False
        )
        logger.error("No images found. Created empty intermediate file.")
        return

    logger.info(f"Found {len(image_files)} images to process.")
    
    # Process images
    metrics_data = process_image_metrics(image_files)
    
    # Save intermediate metrics (T027)
    df_intermediate = pd.DataFrame(metrics_data)
    intermediate_path = "data/processed/visual_metrics_intermediate.csv"
    df_intermediate.to_csv(intermediate_path, index=False)
    logger.info(f"Saved intermediate metrics to {intermediate_path}")
    
    # T028: Merge with cognitive data
    cognitive_data_path = "data/processed/merged_data.csv"
    if not os.path.exists(cognitive_data_path):
        logger.error(f"Cognitive data not found: {cognitive_data_path}. T020 must complete first.")
        sys.exit(1)
    
    df_cognitive = pd.read_csv(cognitive_data_path)
    logger.info(f"Loaded cognitive data with {len(df_cognitive)} rows.")
    
    # Inner join on participant_id
    # CRITICAL: Do NOT drop NaN object_count here.
    df_merged = pd.merge(
        df_cognitive, 
        df_intermediate, 
        on='participant_id', 
        how='inner'
    )
    
    # Log unmatched records
    unmatched_count = len(df_cognitive) - len(df_merged)
    nan_object_count = df_merged['object_count'].isna().sum()
    
    logger.info(f"Merge complete. Unmatched records: {unmatched_count}.")
    logger.info(f"Records with NaN object_count: {nan_object_count}.")
    
    if nan_object_count > 0:
        logger.warning(f"WARNING: {nan_object_count} records have NaN object_count. These will be excluded from object-count analyses in T031.")
    
    # Save final analysis data
    output_path = "data/processed/final_analysis_data.csv"
    df_merged.to_csv(output_path, index=False)
    logger.info(f"Saved final merged dataset to {output_path}")
    
    logger.info("Visual Metrics Pipeline completed successfully.")

if __name__ == "__main__":
    main()