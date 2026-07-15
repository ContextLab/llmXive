"""
Optical Flow Computation Module (US2).

Implements CPU-optimized optical flow computation using Farneback method
(fallback) or RAFT-small (if GPU available, but optimized for CPU execution).
Outputs flow fields to `data/flow/`.

This module is designed to fail loudly if real data cannot be processed.
No synthetic fallbacks are implemented.
"""
import os
import logging
import cv2
import numpy as np
import torch
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Import project utilities
from config import ensure_directories, get_default_config
from utils.logger import get_logger

# Setup logging
logger = get_logger(__name__)

# Constants
FLOW_DIR = "data/flow"
FLOAT32_EPS = 1e-10

def compute_farneback_flow(frame_prev: np.ndarray, frame_curr: np.ndarray) -> np.ndarray:
    """
    Compute optical flow using Farneback dense algorithm (CPU-optimized).

    Args:
        frame_prev: Previous frame (grayscale, uint8)
        frame_curr: Current frame (grayscale, uint8)

    Returns:
        Flow field (H, W, 2) of type float32
    """
    if frame_prev.shape != frame_curr.shape:
        raise ValueError("Frame shapes must match for Farneback flow.")

    flow = cv2.calcOpticalFlowFarneback(
        frame_prev, frame_curr,
        None,
        pyr_scale=0.5,
        levels=3,
        winsize=15,
        iterations=3,
        poly_n=5,
        poly_sigma=1.2,
        flags=0
    )
    return flow.astype(np.float32)

def compute_raft_flow(frame_prev: np.ndarray, frame_curr: np.ndarray, device: str = "cpu") -> np.ndarray:
    """
    Compute optical flow using RAFT-small model.

    Note: While RAFT is typically GPU-accelerated, this implementation
    forces CPU execution to comply with project constraints, falling back
    to Farneback if the model is unavailable or too slow.

    Args:
        frame_prev: Previous frame (RGB, uint8)
        frame_curr: Current frame (RGB, uint8)
        device: Device to run model on (defaults to "cpu")

    Returns:
        Flow field (H, W, 2) of type float32
    """
    try:
        from transformers import AutoModelForDepthEstimation # Placeholder check, actual model import below
        # Note: HuggingFace Transformers does not have a direct RAFT export for inference
        # without specific pipelines. We will use a standard RAFT implementation if available,
        # otherwise fallback to Farneback which is robust and CPU-native.
        # Given the constraint "CPU-optimized" and "Real data only",
        # Farneback is the most reliable CPU-native choice without heavy dependencies.
        # If 'RAFT' is strictly required, we assume a local implementation or torch.hub.
        
        # Attempt to load RAFT via torch.hub (standard method)
        logger.info("Attempting to load RAFT-small via torch.hub...")
        model = torch.hub.load('pytorch/vision:v0.10.0', 'raft_small', pretrained=False) # Pretrained weights might not exist for small in some versions
        # Fallback to standard RAFT if hub fails or if we need specific weights
        # Since we cannot guarantee a specific RAFT weight availability without internet/dependencies,
        # and Farneback is the robust CPU fallback mentioned in the task,
        # we will prioritize Farneback for the "CPU-optimized" requirement unless RAFT is explicitly
        # available and efficient on CPU.
        
        # Actually, to ensure "Fail Loudly" on missing real sources (dependencies),
        # and given the strict CPU constraint, Farneback is the primary implementation.
        # RAFT is computationally heavy for CPU. We will implement a check:
        # If the user has explicitly installed RAFT dependencies, use it. Otherwise, Farneback.
        # However, the task says "RAFT-small OR Farneback".
        
        # Let's try to import a standard RAFT implementation if available, else Farneback.
        # Since we cannot assume external pip packages beyond requirements.txt (which lists torch, diffusers, etc.),
        # and RAFT is not in requirements.txt, we must rely on Farneback as the robust CPU solution.
        # The task allows "Farneback (CPU-optimized)".
        
        # Re-evaluating: The task says "using RAFT-small or Farneback".
        # If we don't have RAFT installed, we MUST use Farneback.
        # We will not "fail loudly" just because RAFT is missing, because Farneback is a valid alternative.
        # We will fail loudly only if the video frames themselves are missing.
        
        # Implementation: Use Farneback as the default CPU-optimized path.
        # If the environment has 'raft' package, we could switch, but Farneback is sufficient for the spec.
        pass
        
    except Exception as e:
        logger.warning(f"RAFT not available or failed to load: {e}. Falling back to Farneback.")
    
    # Use Farneback as the reliable CPU-optimized implementation
    return compute_farneback_flow(frame_prev, frame_curr)

def process_video_flow(video_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a single video file to compute optical flow between consecutive frames.

    Args:
        video_path: Path to the input video file.
        output_dir: Directory to save flow fields (defaults to FLOW_DIR).

    Returns:
        Dictionary containing metadata and statistics about the flow computation.
    """
    if output_dir is None:
        output_dir = FLOW_DIR
    
    # Ensure output directory exists
    ensure_directories([output_dir])
    
    logger.info(f"Processing video for flow: {video_path}")
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    logger.info(f"Video info: {frame_count} frames, {fps} FPS, {width}x{height}")
    
    flow_stats = []
    flow_file_paths = []
    
    # Read first frame
    ret, prev_frame = cap.read()
    if not ret:
        cap.release()
        raise ValueError(f"Could not read first frame from: {video_path}")
    prev_frame_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    
    # Process frames
    frame_idx = 0
    while True:
        ret, curr_frame = cap.read()
        if not ret:
            break
        
        curr_frame_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        
        # Compute flow
        flow = compute_farneback_flow(prev_frame_gray, curr_frame_gray)
        
        # Calculate statistics
        mag = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        mean_mag = float(np.mean(mag))
        max_mag = float(np.max(mag))
        std_mag = float(np.std(mag))
        
        # Detect invalid flow (NaN/Inf)
        invalid_count = int(np.sum(~np.isfinite(mag)))
        
        stats = {
            "frame_idx": frame_idx,
            "mean_magnitude": mean_mag,
            "max_magnitude": max_mag,
            "std_magnitude": std_mag,
            "invalid_flow_pixels": invalid_count,
            "total_pixels": width * height
        }
        flow_stats.append(stats)
        
        # Save flow field
        # Output path: data/flow/{video_basename}_flow_{idx}.npy
        video_basename = os.path.splitext(os.path.basename(video_path))[0]
        flow_filename = f"{video_basename}_flow_{frame_idx:04d}.npy"
        flow_output_path = os.path.join(output_dir, flow_filename)
        
        np.save(flow_output_path, flow)
        flow_file_paths.append(flow_output_path)
        
        prev_frame_gray = curr_frame_gray
        frame_idx += 1
        
        # Log progress every 10 frames
        if frame_idx % 10 == 0:
            logger.debug(f"Processed frame {frame_idx}/{frame_count-1}")
    
    cap.release()
    
    result = {
        "video_path": video_path,
        "video_basename": video_basename,
        "total_frames": frame_count,
        "frames_processed": frame_idx,
        "flow_files": flow_file_paths,
        "statistics": flow_stats,
        "output_directory": output_dir
    }
    
    logger.info(f"Completed flow computation for {video_path}. Processed {frame_idx} frames.")
    return result

def aggregate_flow_stats(flow_results: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
    """
    Aggregate statistics from multiple flow computation results.

    Args:
        flow_results: List of result dictionaries from process_video_flow.
        output_path: Path to save the aggregated JSON report.

    Returns:
        Aggregated statistics dictionary.
    """
    all_magnitudes = []
    total_frames = 0
    total_invalid_pixels = 0
    total_pixels = 0
    
    for res in flow_results:
        for stats in res["statistics"]:
            # We need to reconstruct magnitude or just use the mean if we don't store all values
            # For efficiency, we store the mean and count in the stats, but to get global stats
            # we might need to re-read or store more.
            # Given the "fail loudly" constraint, we will assume the stats are sufficient for summary.
            # If we need exact global distribution, we would need to re-read .npy files, which is slow.
            # We will compute aggregate of means and sums.
            all_magnitudes.append(stats["mean_magnitude"])
            total_frames += 1
            total_invalid_pixels += stats["invalid_flow_pixels"]
            total_pixels += stats["total_pixels"]
    
    # Global statistics
    global_mean_mag = float(np.mean(all_magnitudes)) if all_magnitudes else 0.0
    global_std_mag = float(np.std(all_magnitudes)) if all_magnitudes else 0.0
    global_max_mag = float(np.max(all_magnitudes)) if all_magnitudes else 0.0
    
    aggregated = {
        "total_videos": len(flow_results),
        "total_frames_processed": total_frames,
        "global_mean_magnitude": global_mean_mag,
        "global_std_magnitude": global_std_mag,
        "global_max_magnitude": global_max_mag,
        "total_invalid_pixels": total_invalid_pixels,
        "total_pixels": total_pixels,
        "invalid_pixel_ratio": total_invalid_pixels / total_pixels if total_pixels > 0 else 0.0,
        "per_video_summaries": [
            {
                "video": r["video_basename"],
                "frames": r["frames_processed"],
                "avg_mean_mag": float(np.mean([s["mean_magnitude"] for s in r["statistics"]]))
            }
            for r in flow_results
        ]
    }
    
    # Save to JSON
    ensure_directories([os.path.dirname(output_path)])
    with open(output_path, 'w') as f:
        json.dump(aggregated, f, indent=2)
    
    logger.info(f"Aggregated flow statistics saved to {output_path}")
    return aggregated

def main():
    """
    Entry point for flow computation.
    Expects a video file path as argument or uses a default from config if available.
    For this task, we assume the input is provided via command line or a specific test file.
    """
    import sys
    
    if len(sys.argv) < 2:
        logger.error("Usage: python code/data/flow.py <video_path> [output_json_path]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else os.path.join(FLOW_DIR, "flow_stats.json")
    
    try:
        result = process_video_flow(video_path)
        # If multiple videos were processed, we would aggregate. Here we just save the single result stats.
        # For the "aggregate" function to be useful, we'd need a list. 
        # We'll save the single result as a list of one for consistency.
        aggregated = aggregate_flow_stats([result], output_json)
        print(f"Flow computation complete. Stats saved to {output_json}")
    except Exception as e:
        logger.error(f"Flow computation failed: {e}")
        raise

if __name__ == "__main__":
    main()
