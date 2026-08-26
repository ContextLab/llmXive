"""
Optical Flow and HOG Density Feature Extraction Module.

Implements CPU-only extraction of optical flow (magnitude/variance) and HOG density
from video clips using OpenCV. Handles missing data gracefully by flagging failures
without returning zero vectors.
"""
import os
import sys
import logging
import cv2
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from src.config import get_processed_data_dir, get_raw_data_dir
from src.utils import setup_logging, get_logger, ensure_directories

# Constants
OPTICAL_FLOW_WIN_SIZE = 15
OPTICAL_FLOW_MAX_LEVEL = 3
HOG_BLOCK_SIZE = (16, 16)
HOG_BLOCK_STRIDE = (8, 8)
HOG_CELL_SIZE = (8, 8)
HOG_N_BINS = 9

logger = None

def init_logging():
    """Initialize logging for the module."""
    global logger
    logger = setup_logging("extract_optical")
    return logger

def extract_optical_flow_features(frame1: np.ndarray, frame2: np.ndarray) -> Tuple[float, float]:
    """
    Extract optical flow magnitude and variance between two frames.

    Args:
        frame1: First grayscale frame (uint8).
        frame2: Second grayscale frame (uint8).

    Returns:
        Tuple of (mean_magnitude, variance_magnitude).
    """
    if frame1 is None or frame2 is None:
        raise ValueError("Input frames cannot be None")
    
    if frame1.shape != frame2.shape:
        raise ValueError("Frame shapes must match")

    try:
        # Calculate optical flow using Farneback method
        flow = cv2.calcOpticalFlowFarneback(
            frame1, frame2, None,
            pyr_scale=0.5,
            levels=OPTICAL_FLOW_MAX_LEVEL,
            winsize=OPTICAL_FLOW_WIN_SIZE,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0
        )

        if flow is None:
            raise ValueError("Optical flow calculation returned None")

        # Calculate magnitude and angle
        mag, _ = cv2.phase(flow, np.zeros_like(flow), angleInDegrees=True)
        
        mean_mag = np.mean(mag)
        var_mag = np.var(mag)

        return float(mean_mag), float(var_mag)

    except cv2.error as e:
        raise RuntimeError(f"OpenCV error during optical flow: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error extracting optical flow: {str(e)}")

def extract_hog_density(frame: np.ndarray) -> float:
    """
    Extract HOG density from a single frame.

    Args:
        frame: Grayscale frame (uint8).

    Returns:
        HOG density value (normalized histogram sum).
    """
    if frame is None:
        raise ValueError("Input frame cannot be None")

    try:
        hog_descriptor = cv2.HOGDescriptor()
        hog_descriptor.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        # Resize frame to a manageable size if too large
        h, w = frame.shape[:2]
        target_size = (640, 480)
        if h > target_size[1] or w > target_size[0]:
            scale = min(target_size[1] / h, target_size[0] / w)
            new_w, new_h = int(w * scale), int(h * scale)
            frame_resized = cv2.resize(frame, (new_w, new_h))
        else:
            frame_resized = frame

        # Calculate HOG features
        # We use the descriptor to compute features on the whole image
        # The density is approximated by the sum of HOG descriptor values
        # normalized by image area
        descriptors = hog_descriptor.compute(frame_resized)
        
        if len(descriptors) == 0:
            return 0.0

        # Normalize by image size to get density
        density = np.sum(np.abs(descriptors)) / (frame_resized.shape[0] * frame_resized.shape[1])
        return float(density)

    except cv2.error as e:
        raise RuntimeError(f"OpenCV error during HOG extraction: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error extracting HOG density: {str(e)}")

def process_video_clip(clip_path: str, clip_id: str, dimension: str) -> Dict[str, Any]:
    """
    Process a single video clip to extract optical flow and HOG features.

    Args:
        clip_path: Path to the video file.
        clip_id: Unique identifier for the clip.
        dimension: The dimension label for this clip.

    Returns:
        Dictionary with clip_id, dimension, feature_vector, and missing_data_flag.
    """
    logger.info(f"Processing clip: {clip_id} at {clip_path}")
    
    cap = cv2.VideoCapture(clip_path)
    
    if not cap.isOpened():
        logger.warning(f"Failed to open video: {clip_path}")
        return {
            "clip_id": clip_id,
            "dimension": dimension,
            "feature_vector": "NaN",
            "missing_data_flag": True
        }

    try:
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # Convert to grayscale immediately
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frames.append(gray)
        
        cap.release()

        if len(frames) < 2:
            logger.warning(f"Not enough frames for optical flow in {clip_id}")
            return {
                "clip_id": clip_id,
                "dimension": dimension,
                "feature_vector": "NaN",
                "missing_data_flag": True
            }

        # Extract optical flow features (aggregate over all frame pairs)
        flow_magnitudes = []
        flow_variances = []
        
        for i in range(len(frames) - 1):
            try:
                mean_mag, var_mag = extract_optical_flow_features(frames[i], frames[i+1])
                flow_magnitudes.append(mean_mag)
                flow_variances.append(var_mag)
            except Exception as e:
                logger.warning(f"Optical flow failed for pair {i} in {clip_id}: {e}")
                continue

        if not flow_magnitudes:
            logger.warning(f"No valid optical flow data for {clip_id}")
            return {
                "clip_id": clip_id,
                "dimension": dimension,
                "feature_vector": "NaN",
                "missing_data_flag": True
            }

        # Aggregate optical flow features
        avg_flow_mag = np.mean(flow_magnitudes)
        avg_flow_var = np.mean(flow_variances)

        # Extract HOG density (average over all frames)
        hog_densities = []
        for frame in frames:
            try:
                hog_density = extract_hog_density(frame)
                hog_densities.append(hog_density)
            except Exception as e:
                logger.warning(f"HOG extraction failed for a frame in {clip_id}: {e}")
                continue

        if not hog_densities:
            logger.warning(f"No valid HOG data for {clip_id}")
            return {
                "clip_id": clip_id,
                "dimension": dimension,
                "feature_vector": "NaN",
                "missing_data_flag": True
            }

        avg_hog_density = np.mean(hog_densities)

        # Construct feature vector: [avg_flow_mag, avg_flow_var, avg_hog_density]
        feature_vector = np.array([avg_flow_mag, avg_flow_var, avg_hog_density])
        
        # Flatten to string as required
        feature_vector_str = ",".join([f"{x:.6f}" for x in feature_vector])

        return {
            "clip_id": clip_id,
            "dimension": dimension,
            "feature_vector": feature_vector_str,
            "missing_data_flag": False
        }

    except Exception as e:
        logger.error(f"Unexpected error processing {clip_id}: {e}")
        cap.release()
        return {
            "clip_id": clip_id,
            "dimension": dimension,
            "feature_vector": "NaN",
            "missing_data_flag": True
        }

def batch_process_clips(clip_paths: List[Tuple[str, str, str]], output_path: str):
    """
    Process multiple video clips and save results to CSV.

    Args:
        clip_paths: List of tuples (clip_path, clip_id, dimension).
        output_path: Path to the output CSV file.
    """
    results = []
    
    for clip_path, clip_id, dimension in clip_paths:
        result = process_video_clip(clip_path, clip_id, dimension)
        results.append(result)

    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Ensure columns are in correct order
    df = df[["clip_id", "dimension", "feature_vector", "missing_data_flag"]]
    
    # Save to CSV
    ensure_directories(output_path)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved optical flow features to {output_path}")

def load_clip_metadata(scores_path: str) -> List[Tuple[str, str, str]]:
    """
    Load clip metadata from the processed scores CSV.

    Args:
        scores_path: Path to scores.csv containing clip_id and dimension.

    Returns:
        List of tuples (clip_path, clip_id, dimension).
    """
    if not os.path.exists(scores_path):
        raise FileNotFoundError(f"Scores file not found: {scores_path}")

    df = pd.read_csv(scores_path)
    
    # Validate required columns
    required_cols = ["clip_id", "dimension"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Map clip_id to actual video path
    # Assuming video files are in data/raw/ with a standard naming convention
    raw_data_dir = get_raw_data_dir()
    
    clip_info = []
    for _, row in df.iterrows():
        clip_id = row["clip_id"]
        dimension = row["dimension"]
        
        # Construct expected video path (adjust based on actual data structure)
        # Assuming video files are named {clip_id}.mp4 or similar
        video_path = os.path.join(raw_data_dir, f"{clip_id}.mp4")
        
        # If exact match not found, try to find a file with clip_id in name
        if not os.path.exists(video_path):
            # Try to find any video file matching the clip_id pattern
            for ext in [".mp4", ".avi", ".mov", ".mkv"]:
                potential_path = os.path.join(raw_data_dir, f"{clip_id}{ext}")
                if os.path.exists(potential_path):
                    video_path = potential_path
                    break
        
        if os.path.exists(video_path):
            clip_info.append((video_path, clip_id, dimension))
        else:
            logger.warning(f"Video file not found for clip_id: {clip_id}")
            # Still include it to maintain order, will be flagged as missing
            clip_info.append((None, clip_id, dimension))

    return clip_info

def main():
    """Main entry point for optical flow extraction."""
    init_logging()
    
    try:
        # Define paths
        scores_path = os.path.join(get_processed_data_dir(), "scores.csv")
        output_path = os.path.join(get_processed_data_dir(), "features_optical.csv")
        
        logger.info(f"Loading clip metadata from {scores_path}")
        clip_info = load_clip_metadata(scores_path)
        
        logger.info(f"Processing {len(clip_info)} clips for optical flow features")
        batch_process_clips(clip_info, output_path)
        
        logger.info("Optical flow extraction completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Optical flow extraction failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
