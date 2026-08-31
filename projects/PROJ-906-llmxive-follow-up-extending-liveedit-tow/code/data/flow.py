import os
import logging
import cv2
import numpy as np
import torch
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json

from config import ensure_directories
from utils.logger import get_logger

logger = get_logger(__name__)

def compute_flow_magnitude(flow_field: np.ndarray) -> float:
    """
    Compute the mean magnitude of an optical flow field.
    
    Args:
        flow_field: Optical flow field of shape (H, W, 2) where the last
                    dimension contains (u, v) vectors.
                    
    Returns:
        Mean magnitude of the flow field (float).
        
    Raises:
        ValueError: If the flow field contains NaN or Inf values.
    """
    if flow_field.shape[-1] != 2:
        raise ValueError(f"Flow field must have shape (H, W, 2), got {flow_field.shape}")

    # Check for NaN or Inf
    if np.any(np.isnan(flow_field)) or np.any(np.isinf(flow_field)):
        raise ValueError("Flow field contains NaN or Inf values. Fallback to identity warp required.")

    # Compute magnitude: sqrt(u^2 + v^2)
    magnitude = np.sqrt(np.sum(flow_field ** 2, axis=-1))
    
    # Compute mean magnitude, ignoring any remaining invalid values if they slipped through
    # (though the check above should catch them)
    valid_mask = np.isfinite(magnitude)
    if not np.any(valid_mask):
        raise ValueError("All flow values are invalid.")
        
    return float(np.mean(magnitude[valid_mask]))

def extract_flow_magnitudes_for_dataset(
    clip_paths: List[str],
    output_path: str,
    method: str = "farneback"
) -> Dict[str, float]:
    """
    Compute flow magnitude for a list of video clips and save to JSON.
    
    Args:
        clip_paths: List of paths to video files.
        output_path: Path to save the magnitudes JSON file.
        method: Flow computation method ('farneback' or 'raft').
                
    Returns:
        Dict mapping clip_id to flow magnitude.
    """
    ensure_directories(output_path)
    magnitudes = {}

    for clip_path in clip_paths:
        clip_id = Path(clip_path).stem
        logger.info(f"Computing flow magnitude for {clip_id}...")
        
        try:
            mag = compute_flow_magnitude_for_video(clip_path, method)
            magnitudes[clip_id] = mag
        except ValueError as e:
            logger.warning(f"Failed to compute flow for {clip_id}: {e}. Skipping.")
            magnitudes[clip_id] = 0.0 # Fallback to 0 for stratification purposes if failed

    # Save to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(magnitudes, f, indent=2)
    
    logger.info(f"Flow magnitudes saved to {output_path}")
    return magnitudes

def compute_flow_magnitude_for_video(
    video_path: str,
    method: str = "farneback"
) -> float:
    """
    Compute mean flow magnitude for a single video file.
    
    Args:
        video_path: Path to the video file.
        method: Flow computation method.
                
    Returns:
        Mean flow magnitude for the video.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    ret, prev_frame = cap.read()
    if not ret:
        raise ValueError(f"Could not read first frame from: {video_path}")
    
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    magnitudes = []

    while True:
        ret, curr_frame = cap.read()
        if not ret:
            break
        
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)

        # Compute optical flow
        if method == "farneback":
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, curr_gray, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )
        else:
            # Placeholder for other methods (RAFT would require torch)
            raise NotImplementedError(f"Method {method} not implemented in this CPU-only version.")

        if flow is not None:
            # Compute magnitude for this frame
            # Handle potential NaN/Inf in flow
            if np.any(np.isnan(flow)) or np.any(np.isinf(flow)):
                logger.warning(f"NaN/Inf detected in flow for {video_path}. Skipping frame.")
            else:
                mag = compute_flow_magnitude(flow)
                magnitudes.append(mag)

        prev_gray = curr_gray

    cap.release()

    if not magnitudes:
        return 0.0
    
    return float(np.mean(magnitudes))

def compute_full_flow_field(
    video_path: str,
    output_dir: str,
    method: str = "farneback"
) -> str:
    """
    Compute full optical flow fields for a video and save as .npy files.
    
    Args:
        video_path: Path to video.
        output_dir: Directory to save flow fields.
        method: Flow computation method.
                
    Returns:
        Path to the directory containing flow fields.
    """
    ensure_directories(output_dir)
    clip_id = Path(video_path).stem
    flow_dir = os.path.join(output_dir, f"{clip_id}_flows")
    ensure_directories(flow_dir)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    ret, prev_frame = cap.read()
    if not ret:
        raise ValueError(f"Could not read first frame from: {video_path}")
    
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    frame_idx = 0

    while True:
        ret, curr_frame = cap.read()
        if not ret:
            break
        
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)

        if method == "farneback":
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, curr_gray, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )
        else:
            raise NotImplementedError(f"Method {method} not implemented.")

        if flow is not None:
            flow_path = os.path.join(flow_dir, f"flow_{frame_idx:04d}.npy")
            np.save(flow_path, flow)
        
        prev_gray = curr_gray
        frame_idx += 1

    cap.release()
    logger.info(f"Flow fields saved to {flow_dir}")
    return flow_dir

def main():
    """
    Entry point for flow computation.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Flow module loaded.")

if __name__ == "__main__":
    main()
