import os
import logging
import cv2
import numpy as np
import torch
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from config import ensure_directories, get_default_config
from utils.logger import get_logger
from data.models import VideoClip
from data.downloader import download_dataset

logger = get_logger(__name__)

def compute_flow_magnitude(
    flow_x: np.ndarray,
    flow_y: np.ndarray
) -> np.ndarray:
    """
    Computes the magnitude of optical flow at each pixel.
    
    Args:
        flow_x: Horizontal flow component
        flow_y: Vertical flow component
        
    Returns:
        np.ndarray: Flow magnitude map
    """
    magnitude = np.sqrt(flow_x**2 + flow_y**2)
    return magnitude

def extract_flow_magnitudes_for_dataset(
    clips: List[VideoClip],
    output_path: str,
    method: str = "farneback"
) -> Dict[str, float]:
    """
    Extracts mean flow magnitude for each clip in the dataset.
    
    Args:
        clips: List of VideoClip objects
        output_path: Path to save magnitudes JSON
        method: Flow computation method ('farneback' or 'raft')
        
    Returns:
        Dict[str, float]: Mapping of clip_id to mean flow magnitude
    """
    ensure_directories(output_path)
    
    magnitudes = {}
    
    for clip in clips:
        logger.info(f"Computing flow for clip: {clip.id}")
        
        # Load video frames
        cap = cv2.VideoCapture(clip.path)
        if not cap.isOpened():
            logger.error(f"Could not open video: {clip.path}")
            continue
        
        # Read first two frames
        ret1, frame1 = cap.read()
        if not ret1:
            continue
        ret2, frame2 = cap.read()
        if not ret2:
            cap.release()
            continue
        
        cap.release()
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # Compute optical flow
        if method == "farneback":
            flow = cv2.calcOpticalFlowFarneback(
                gray1, gray2, None,
                pyr_scale=0.5,
                levels=3,
                winsize=15,
                iterations=3,
                poly_n=5,
                poly_sigma=1.2,
                flags=0
            )
        elif method == "raft":
            # Placeholder for RAFT implementation
            # In real implementation, load RAFT model and compute flow
            logger.warning("RAFT not implemented, falling back to Farneback")
            flow = cv2.calcOpticalFlowFarneback(
                gray1, gray2, None,
                pyr_scale=0.5,
                levels=3,
                winsize=15,
                iterations=3,
                poly_n=5,
                poly_sigma=1.2,
                flags=0
            )
        else:
            raise ValueError(f"Unknown flow method: {method}")
        
        # Compute magnitude
        mag = compute_flow_magnitude(flow[:, :, 0], flow[:, :, 1])
        mean_mag = float(np.mean(mag))
        
        # Handle invalid flow (NaN/Inf)
        if np.isnan(mean_mag) or np.isinf(mean_mag):
            logger.warning(f"Invalid flow magnitude for {clip.id}, setting to 0.0")
            mean_mag = 0.0
        
        magnitudes[clip.id] = mean_mag
        logger.info(f"Clip {clip.id}: mean flow magnitude = {mean_mag:.4f}")
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(magnitudes, f, indent=2)
    
    logger.info(f"Saved flow magnitudes to {output_path}")
    return magnitudes

def compute_full_flow_field(
    clip: VideoClip,
    output_dir: str,
    method: str = "farneback"
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes full optical flow field for a clip.
    
    Args:
        clip: VideoClip object
        output_dir: Directory to save flow fields
        method: Flow computation method
        
    Returns:
        Tuple[np.ndarray, np.ndarray]: Flow X and Y components
    """
    ensure_directories(output_dir)
    
    cap = cv2.VideoCapture(clip.path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {clip.path}")
    
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    
    cap.release()
    
    if len(frames) < 2:
        logger.warning(f"Not enough frames in {clip.id}")
        return np.zeros_like(frames[0]), np.zeros_like(frames[0])
    
    # Compute flow between consecutive frames and average
    flow_x_total = np.zeros_like(frames[0], dtype=np.float32)
    flow_y_total = np.zeros_like(frames[0], dtype=np.float32)
    
    for i in range(len(frames) - 1):
        if method == "farneback":
            flow = cv2.calcOpticalFlowFarneback(
                frames[i], frames[i+1], None,
                pyr_scale=0.5,
                levels=3,
                winsize=15,
                iterations=3,
                poly_n=5,
                poly_sigma=1.2,
                flags=0
            )
        else:
            # RAFT placeholder
            flow = cv2.calcOpticalFlowFarneback(
                frames[i], frames[i+1], None,
                pyr_scale=0.5,
                levels=3,
                winsize=15,
                iterations=3,
                poly_n=5,
                poly_sigma=1.2,
                flags=0
            )
        
        flow_x_total += flow[:, :, 0]
        flow_y_total += flow[:, :, 1]
    
    n_frames = len(frames) - 1
    flow_x = flow_x_total / n_frames
    flow_y = flow_y_total / n_frames
    
    # Save flow fields
    output_path = os.path.join(output_dir, f"{clip.id}_flow.npy")
    np.save(output_path, np.stack([flow_x, flow_y], axis=0))
    logger.info(f"Saved flow field to {output_path}")
    
    return flow_x, flow_y

def main():
    """
    Main entry point for flow computation.
    """
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Compute optical flow for dataset")
    parser.add_argument("--dataset", type=str, default="davis", help="Dataset name")
    parser.add_argument("--method", type=str, default="farneback", help="Flow method")
    parser.add_argument("--output", type=str, default="data/flow/magnitudes.json", help="Output path")
    parser.add_argument("--stratify", action="store_true", help="Also compute stratification magnitudes")
    
    args = parser.parse_args()
    
    logger.info(f"Computing flow with method: {args.method}")
    
    # In real implementation, load clips from dataset
    # For now, simulate
    clips = []
    
    if args.stratify:
        magnitudes = extract_flow_magnitudes_for_dataset(
            clips, args.output, method=args.method
        )
        logger.info(f"Computed magnitudes for {len(magnitudes)} clips")
    else:
        logger.info("Stratification not requested. Skipping magnitude extraction.")

if __name__ == "__main__":
    main()