import os
import sys
import logging
import json
import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.config import get_processed_data_dir, get_raw_data_dir
from src.utils import setup_logging, get_logger, write_json

# Constants for Optical Flow
FLOW_SCALE = 0.5
FLOW_MORPH_SIZE = (5, 5)
FLOW_GAUSSIAN_SIGMA = 1.1
FLOW_ALPHA = 1.5
FLOW_SIGMA = 1.1
FLOW_WIN_SIZE = 15
FLOW_ITER = 2
FLOW_POLY_N = 5
FLOW_POLY_SIGMA = 1.1
FLOW_FLAGS = cv2.OPTFLOW_FARNEBACK_GAUSSIAN

# Constants for HOG
HOG_BLOCK_SIZE = (2, 2)
HOG_BLOCK_STRIDE = (1, 1)
HOG_CELL_SIZE = (8, 8)
HOG_N_BINS = 9

def init_logging() -> logging.Logger:
    """Initialize logging for the module."""
    logger = setup_logging("optical_flow_extractor", level=logging.INFO)
    return logger

def extract_optical_flow_features(frames: List[np.ndarray], logger: logging.Logger) -> np.ndarray:
    """
    Extract optical flow magnitude and variance features from a list of frames.
    
    Args:
        frames: List of grayscale frames (numpy arrays).
        logger: Logger instance.
        
    Returns:
        np.ndarray: Feature vector [mean_magnitude, std_magnitude, mean_angle, std_angle, flow_variance].
    """
    if len(frames) < 2:
        logger.warning("Not enough frames for optical flow.")
        return np.zeros(5)

    # Convert to float32 for OpenCV
    prev_frame = frames[0].astype(np.float32)
    
    magnitudes = []
    angles = []

    for i in range(1, len(frames)):
        curr_frame = frames[i].astype(np.float32)
        
        try:
            # Calculate Optical Flow
            flow = cv2.calcOpticalFlowFarneback(
                prev_frame, curr_frame, None,
                pyr_scale=FLOW_SCALE,
                levels=3,
                winsize=FLOW_WIN_SIZE,
                iterations=FLOW_ITER,
                poly_n=FLOW_POLY_N,
                poly_sigma=FLOW_POLY_SIGMA,
                flags=FLOW_FLAGS
            )
            
            # Calculate Magnitude and Angle
            mag, ang = cv2.split(flow)
            mag_flat = mag.flatten()
            ang_flat = ang.flatten()
            
            # Filter out very small magnitudes (noise)
            valid_mask = mag_flat > 0.5
            if np.any(valid_mask):
                valid_mag = mag_flat[valid_mask]
                valid_ang = ang_flat[valid_mask]
                
                magnitudes.extend(valid_mag.tolist())
                angles.extend(valid_ang.tolist())
            
            prev_frame = curr_frame
            
        except Exception as e:
            logger.error(f"Error calculating optical flow between frame {i-1} and {i}: {e}")
            continue

    if not magnitudes:
        logger.warning("No valid optical flow magnitudes detected.")
        return np.zeros(5)

    mean_mag = np.mean(magnitudes)
    std_mag = np.std(magnitudes)
    mean_ang = np.mean(angles)
    std_ang = np.std(angles)
    flow_variance = np.var(magnitudes)

    return np.array([mean_mag, std_mag, mean_ang, std_ang, flow_variance], dtype=np.float64)

def extract_hog_density(frames: List[np.ndarray], logger: logging.Logger) -> np.ndarray:
    """
    Calculate HOG density features from frames.
    
    Args:
        frames: List of grayscale frames.
        logger: Logger instance.
        
    Returns:
        np.ndarray: Feature vector [mean_hog_density, std_hog_density, max_hog_density].
    """
    hog_descriptor = cv2.HOGDescriptor()
    hog_descriptor.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    # We will compute HOG descriptors manually to get the histogram density
    # Using the standard HOG parameters
    win_size = (64, 128) # Standard detection window, but we adapt to frame size
    block_size = HOG_BLOCK_SIZE
    block_stride = HOG_BLOCK_STRIDE
    cell_size = HOG_CELL_SIZE
    n_bins = HOG_N_BINS
    
    hog = cv2.HOGDescriptor(win_size, block_size, block_stride, cell_size, n_bins)
    
    densities = []
    
    for i, frame in enumerate(frames):
        if frame is None or frame.size == 0:
            continue
        
        try:
            # Resize frame to a standard size if too large to avoid memory issues
            # but keep aspect ratio roughly, or just use a fixed size for density comparison
            h, w = frame.shape[:2]
            if h > 256 or w > 256:
                scale = min(256.0/h, 256.0/w)
                new_w, new_h = int(w * scale), int(h * scale)
                frame_resized = cv2.resize(frame, (new_w, new_h))
            else:
                frame_resized = frame
            
            # Compute HOG descriptor
            # Note: HOG descriptor returns a flat array of histogram bins
            # We interpret the "density" as the sum of magnitudes in the histogram
            # or the number of non-zero cells relative to total cells.
            # Here we use the sum of the histogram values as a proxy for "edge density".
            desc = hog.compute(frame_resized)
            
            # Normalize to handle lighting variations
            if desc.size > 0:
                desc_sum = np.sum(desc)
                densities.append(float(desc_sum))
            
        except Exception as e:
            logger.warning(f"Error computing HOG for frame {i}: {e}")
            continue
    
    if not densities:
        logger.warning("No valid HOG densities computed.")
        return np.zeros(3)
    
    densities_arr = np.array(densities)
    return np.array([
        np.mean(densities_arr),
        np.std(densities_arr),
        np.max(densities_arr)
    ], dtype=np.float64)

def load_clip_metadata(clip_id: str, dimension: str, raw_data_dir: Path) -> Optional[List[np.ndarray]]:
    """
    Load frames for a specific clip.
    Assumes raw data is stored as video files or image sequences.
    For this implementation, we assume a structure like:
    raw_data_dir / dimension / {clip_id}.mp4 (or similar)
    If not found, return None.
    """
    # Try common video extensions
    extensions = ['.mp4', '.avi', '.mov', '.mkv']
    video_path = None
    
    for ext in extensions:
        path = raw_data_dir / dimension / f"{clip_id}{ext}"
        if path.exists():
            video_path = path
            break
    
    if video_path is None:
        # Fallback: check if it's an image sequence folder
        seq_dir = raw_data_dir / dimension / clip_id
        if seq_dir.exists() and seq_dir.is_dir():
            # Load all images
            images = []
            for img_path in sorted(seq_dir.glob("*.jpg")) + sorted(seq_dir.glob("*.png")):
                img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    images.append(img)
            if images:
                return images
        return None

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frames.append(gray)
    
    cap.release()
    
    # Limit frames to avoid excessive memory/time for very long clips
    # Sample every Nth frame if too many
    if len(frames) > 30:
        step = len(frames) // 30
        frames = frames[::step]
        
    return frames

def process_video_clip(clip_id: str, dimension: str, raw_data_dir: Path, logger: logging.Logger) -> Dict[str, Any]:
    """
    Process a single video clip to extract optical flow and HOG features.
    
    Args:
        clip_id: Unique identifier for the clip.
        dimension: The dimension/category of the clip.
        raw_data_dir: Path to the raw data directory.
        logger: Logger instance.
        
    Returns:
        Dict containing clip_id, dimension, feature_vector, and missing_data_flag.
    """
    result = {
        "clip_id": clip_id,
        "dimension": dimension,
        "feature_vector": [],
        "missing_data_flag": False
    }
    
    frames = load_clip_metadata(clip_id, dimension, raw_data_dir)
    
    if frames is None or len(frames) == 0:
        logger.warning(f"Could not load frames for clip {clip_id} in dimension {dimension}.")
        result["missing_data_flag"] = True
        return result
    
    try:
        flow_features = extract_optical_flow_features(frames, logger)
        hog_features = extract_hog_density(frames, logger)
        
        # Concatenate features
        full_vector = np.concatenate([flow_features, hog_features])
        
        result["feature_vector"] = [float(x) for x in full_vector]
        
    except Exception as e:
        logger.error(f"Error processing clip {clip_id}: {e}")
        result["missing_data_flag"] = True
        
    return result

def batch_process_clips(clip_list: List[Dict[str, str]], raw_data_dir: Path, logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Process a batch of clips.
    
    Args:
        clip_list: List of dicts with 'clip_id' and 'dimension'.
        raw_data_dir: Path to raw data.
        logger: Logger instance.
        
    Returns:
        List of result dictionaries.
    """
    results = []
    for clip_info in clip_list:
        clip_id = clip_info.get('clip_id')
        dimension = clip_info.get('dimension')
        if not clip_id or not dimension:
            logger.warning(f"Skipping invalid clip info: {clip_info}")
            continue
        
        res = process_video_clip(clip_id, dimension, raw_data_dir, logger)
        results.append(res)
        
        # Log progress
        if len(results) % 10 == 0:
            logger.info(f"Processed {len(results)} clips...")
            
    return results

def main():
    """Main entry point for optical flow extraction."""
    logger = init_logging()
    logger.info("Starting optical flow feature extraction...")
    
    processed_dir = get_processed_data_dir()
    raw_data_dir = get_raw_data_dir()
    
    # Load metadata from scores.csv if available, or scan raw data
    # The task description implies we have a list of clips to process.
    # We assume scores.csv (from T042) contains the necessary clip_id and dimension mapping.
    scores_path = processed_dir / "scores.csv"
    
    if not scores_path.exists():
        logger.error(f"Scores file not found at {scores_path}. Please run T042 first.")
        sys.exit(1)
    
    try:
        df = pd.read_csv(scores_path)
        required_cols = ['clip_id', 'dimension']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Scores file missing required columns: {required_cols}")
            sys.exit(1)
        
        # Extract unique clips/dimensions to process
        # We process each row in the scores file to ensure we cover all data points
        clip_data = df[required_cols].drop_duplicates().to_dict('records')
        
        logger.info(f"Found {len(clip_data)} unique clip/dimension pairs to process.")
        
        results = batch_process_clips(clip_data, raw_data_dir, logger)
        
        output_path = processed_dir / "features_optical.json"
        write_json(results, output_path)
        logger.info(f"Optical flow features saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Fatal error in optical flow extraction: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
