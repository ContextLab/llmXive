import os
import sys
import math
import time
import logging
import signal
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import cv2
from PIL import Image
from ultralytics import YOLO

# Import from utils
from utils import get_logger, log_structured_error, get_global_seed, set_random_seed

# Setup logging
logger = get_logger(__name__)

# Constants
MARKER_FILE = "data/processed/.ready"
RAW_IMAGE_DIR = "data/raw/workspace_images"
SANITIZED_IMAGE_DIR = "data/processed/sanitized_images"
COGNITIVE_DATA_PATH = "data/raw/cognitive_data.csv"
MERGED_DATA_PATH = "data/processed/merged_data.csv"
INTERMEDIATE_METRICS_PATH = "data/processed/visual_metrics_intermediate.csv"
FINAL_ANALYSIS_ALL_PATH = "data/processed/final_analysis_data_all.csv"
FINAL_ANALYSIS_OBJECT_ONLY_PATH = "data/processed/final_analysis_data_object_only.csv"
# Legacy path for backward compatibility with 03_analysis.py
FINAL_ANALYSIS_LEGACY_PATH = "data/processed/final_analysis_data.csv"

TIMEOUT_SECONDS = 300

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def timeout_context(seconds=TIMEOUT_SECONDS):
    def decorator(func):
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)
                return result
            except TimeoutError:
                signal.alarm(0)
                raise
        return wrapper
    return decorator

def wait_for_marker(marker_path: str = MARKER_FILE, timeout: int = 300):
    """Wait for the marker file to appear."""
    start_time = time.time()
    while not os.path.exists(marker_path):
        if time.time() - start_time > timeout:
            raise FileNotFoundError(f"Marker file {marker_path} not found after {timeout} seconds")
        time.sleep(5)
    logger.info(f"Marker file {marker_path} found.")

def get_image_directory() -> str:
    """Get the directory containing sanitized images."""
    if os.path.exists(SANITIZED_IMAGE_DIR):
        return SANITIZED_IMAGE_DIR
    elif os.path.exists(RAW_IMAGE_DIR):
        return RAW_IMAGE_DIR
    else:
        raise FileNotFoundError(f"Neither {SANITIZED_IMAGE_DIR} nor {RAW_IMAGE_DIR} exists")

def calculate_edge_density(image_path: str) -> float:
    """
    Calculate edge density using Canny edge detection.
    Returns a normalized value between 0 and 1.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.warning(f"Could not read image: {image_path}")
            return np.nan

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        
        total_pixels = edges.size
        edge_pixels = cv2.countNonZero(edges)
        
        if total_pixels == 0:
            return 0.0
        
        density = edge_pixels / total_pixels
        return density
    except Exception as e:
        log_structured_error("image_processing_failures", str(e), {"image": image_path})
        return np.nan

def calculate_color_entropy(image_path: str) -> float:
    """
    Calculate color entropy using histogram of flattened RGB channels.
    """
    try:
        img = np.array(Image.open(image_path).convert('RGB'))
        if img.size == 0:
            return np.nan

        # Flatten and compute histogram for each channel
        entropies = []
        for channel in range(3):
            channel_data = img[:, :, channel].flatten()
            hist, _ = np.histogram(channel_data, bins=256, range=(0, 256))
            hist = hist / hist.sum()
            hist = hist[hist > 0]
            entropy = -np.sum(hist * np.log2(hist))
            entropies.append(entropy)
        
        return np.mean(entropies)
    except Exception as e:
        log_structured_error("image_processing_failures", str(e), {"image": image_path})
        return np.nan

@timeout_context(TIMEOUT_SECONDS)
def calculate_object_count(image_path: str) -> float:
    """
    Calculate object count using YOLOv8n model.
    Returns NaN if model fails or times out.
    """
    try:
        # Load model
        model = YOLO("yolov8n.pt")
        
        # Run inference
        results = model(image_path, conf=0.25, verbose=False)
        
        # Count detections
        count = len(results[0].boxes)
        return float(count)
    except Exception as e:
        log_structured_error("image_processing_failures", str(e), {"image": image_path})
        return np.nan

def load_merged_data() -> pd.DataFrame:
    """Load the merged cognitive and image data."""
    if not os.path.exists(MERGED_DATA_PATH):
        raise FileNotFoundError(f"Merged data not found: {MERGED_DATA_PATH}")
    return pd.read_csv(MERGED_DATA_PATH)

def process_image_metrics() -> pd.DataFrame:
    """Process all images and compute visual metrics."""
    image_dir = get_image_directory()
    logger.info(f"Processing images from: {image_dir}")
    
    results = []
    for filename in os.listdir(image_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(image_dir, filename)
            logger.info(f"Processing: {filename}")
            
            edge_density = calculate_edge_density(image_path)
            color_entropy = calculate_color_entropy(image_path)
            object_count = calculate_object_count(image_path)
            
            results.append({
                'image_filename': filename,
                'edge_density': edge_density,
                'color_entropy': color_entropy,
                'object_count': object_count
            })
    
    return pd.DataFrame(results)

def save_intermediate_metrics(df: pd.DataFrame):
    """Save intermediate metrics to CSV."""
    df.to_csv(INTERMEDIATE_METRICS_PATH, index=False)
    logger.info(f"Saved intermediate metrics to {INTERMEDIATE_METRICS_PATH}")

def merge_with_cognitive_data(visual_metrics_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Merge visual metrics with cognitive data.
    Returns two dataframes:
    1. All records (preserving NaNs for object_count)
    2. Only records where object_count is NOT NaN
    """
    cognitive_df = load_merged_data()
    
    # Ensure participant_id is string for consistent joining
    cognitive_df['participant_id'] = cognitive_df['participant_id'].astype(str)
    visual_metrics_df['image_filename'] = visual_metrics_df['image_filename'].astype(str)
    
    # Create a mapping from image_filename to participant_id if available
    # Assuming the merged_data.csv has participant_id and image_filename columns
    if 'image_filename' in cognitive_df.columns:
        cognitive_df['image_filename'] = cognitive_df['image_filename'].astype(str)
        merged_df = pd.merge(cognitive_df, visual_metrics_df, on='image_filename', how='inner')
    elif 'participant_id' in visual_metrics_df.columns:
        # If participant_id is in visual metrics
        merged_df = pd.merge(cognitive_df, visual_metrics_df, on='participant_id', how='inner')
    else:
        # Fallback: assume 1:1 mapping by order if no common key
        # This is a fallback for proxy linkage scenarios
        min_len = min(len(cognitive_df), len(visual_metrics_df))
        merged_df = pd.concat([
            cognitive_df.iloc[:min_len].reset_index(drop=True),
            visual_metrics_df.iloc[:min_len].reset_index(drop=True)
        ], axis=1)
    
    # Log unmatched records
    unmatched_count = len(cognitive_df) - len(merged_df)
    logger.warning(f"Unmatched records: {unmatched_count}")
    
    # Count NaN object_count
    nan_count = merged_df['object_count'].isna().sum()
    logger.warning(f"Records with NaN object_count: {nan_count}")
    
    # Create two output dataframes
    df_all = merged_df.copy()
    df_object_only = merged_df.dropna(subset=['object_count']).copy()
    
    logger.info(f"Total records (all): {len(df_all)}")
    logger.info(f"Records with valid object_count: {len(df_object_only)}")
    
    return df_all, df_object_only

def save_final_analysis_data(df_all: pd.DataFrame, df_object_only: pd.DataFrame):
    """Save the final analysis dataframes."""
    df_all.to_csv(FINAL_ANALYSIS_ALL_PATH, index=False)
    df_object_only.to_csv(FINAL_ANALYSIS_OBJECT_ONLY_PATH, index=False)
    
    # Also save to legacy path for backward compatibility with 03_analysis.py
    # Use the 'all' dataframe to preserve NaNs for edge/entropy analyses
    df_all.to_csv(FINAL_ANALYSIS_LEGACY_PATH, index=False)
    
    logger.info(f"Saved final analysis data to {FINAL_ANALYSIS_ALL_PATH}")
    logger.info(f"Saved object-only data to {FINAL_ANALYSIS_OBJECT_ONLY_PATH}")
    logger.info(f"Saved legacy analysis data to {FINAL_ANALYSIS_LEGACY_PATH}")

def main():
    """Main execution function."""
    # Wait for marker file
    wait_for_marker()
    
    # Process images
    visual_metrics_df = process_image_metrics()
    
    # Save intermediate metrics
    save_intermediate_metrics(visual_metrics_df)
    
    # Merge with cognitive data
    df_all, df_object_only = merge_with_cognitive_data(visual_metrics_df)
    
    # Save final analysis data
    save_final_analysis_data(df_all, df_object_only)
    
    logger.info("Visual metrics processing complete.")

if __name__ == "__main__":
    main()