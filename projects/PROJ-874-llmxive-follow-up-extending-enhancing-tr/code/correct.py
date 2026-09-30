import os
import sys
import argparse
import logging
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Generator

import cv2
import numpy as np

# Import from local utils and config as per API surface
from config import (
    get_processed_dir, get_results_dir, get_config,
    get_dataset_paths, LlmXiveError, ValidationError
)
from utils.video import extract_frames_to_list, write_video
from utils.flow import compute_flow_with_fallback, is_flow_valid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_results_dir() / 'flow_computation.log')
    ]
)
logger = logging.getLogger(__name__)

def get_naive_baseline_paths() -> List[Path]:
    """
    Retrieves the list of naive baseline video paths.
    These are expected to be in data/processed/naive_baselines/
    """
    base_dir = get_processed_dir() / "naive_baselines"
    if not base_dir.exists():
        raise LlmXiveError(f"Naive baseline directory not found: {base_dir}")
    
    # Find all video files (mp4, avi, mov)
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv'}
    paths = [p for p in base_dir.iterdir() if p.suffix.lower() in video_extensions]
    
    if not paths:
        raise LlmXiveError(f"No naive baseline videos found in {base_dir}")
    
    return sorted(paths)

def verify_naive_baselines_exist() -> List[Path]:
    """
    Verifies that naive baseline videos exist.
    If any are missing (or directory is empty), aborts with a clear error.
    Returns the list of valid paths if successful.
    """
    try:
        paths = get_naive_baseline_paths()
        logger.info(f"Found {len(paths)} naive baseline videos.")
        return paths
    except LlmXiveError as e:
        logger.error(f"ABORT: {e}")
        # Explicitly exit as per FR-001 requirement
        sys.exit(1)

def get_flow_field_paths(video_id: str) -> Path:
    """
    Returns the expected path for the flow field file for a given video_id.
    Flow fields are stored as .npy files in data/processed/flow_fields/
    """
    flow_dir = get_processed_dir() / "flow_fields"
    return flow_dir / f"{video_id}_flow.npy"

def verify_flow_fields_exist(video_id: str) -> Path:
    """
    Verifies that the flow field file exists for a specific video.
    Returns the path if found, otherwise raises an error.
    """
    path = get_flow_field_paths(video_id)
    if not path.exists():
        raise LlmXiveError(f"Flow field missing for video {video_id}: {path}")
    return path

def warp_frame(frame: np.ndarray, flow: np.ndarray, prev_frame: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Warps a frame using the optical flow field.
    Uses cv2.remap with bilinear interpolation.
    
    Args:
        frame: Current frame (H, W, C)
        flow: Flow field (H, W, 2) where flow[y, x] = (u, v)
        prev_frame: Previous frame (optional, used for backward warping if needed, 
                    but here we assume forward warping from prev to curr context 
                    or simply applying flow to shift pixels).
                    
    Note: 
        Standard optical flow (u, v) at (x, y) tells where the pixel at (x, y) 
        moves to in the next frame. 
        To warp the *previous* frame to the *current* frame, we use the flow.
        Here, we assume `frame` is the target and we are warping a source based on flow.
        However, for simple flow visualization or correction, we often warp the current
        frame based on flow to align.
        
        Implementation:
        We construct a map where map_x[y, x] = x + u, map_y[y, x] = y + v.
        This maps the destination pixel (x,y) back to the source pixel (x+u, y+v).
        Wait, standard cv2.remap: dst(x,y) = src(map_x(x,y), map_y(x,y)).
        If flow is (u,v) = (dst_x - src_x, dst_y - src_y), then src_x = x - u.
        But usually flow represents displacement. 
        Let's assume flow[y,x] is the displacement vector to the NEXT frame.
        To warp the CURRENT frame to align with the NEXT frame (or vice versa),
        we need to be careful.
        
        For this task: "compute optical flow fields between consecutive frames... 
        to generate Condition C outputs".
        We will compute flow from frame t to t+1.
        Then we warp frame t using flow to approximate t+1 (or warp t+1 back).
        
        Let's implement a generic warp:
        Given frame `src` and flow `flow` (displacement from src to dst),
        we want to create `dst_approx`.
        dst_approx(x,y) = src(x - u, y - v).
        
        So map_x = X - flow[..., 0]
        map_y = Y - flow[..., 1]
    """
    h, w = frame.shape[:2]
    y, x = np.ogrid[:h, :w]
    
    # flow is (H, W, 2), u is x-displacement, v is y-displacement
    u = flow[..., 0]
    v = flow[..., 1]
    
    # Create remap maps
    # We want to pull from (x - u, y - v)
    map_x = (x - u).astype(np.float32)
    map_y = (y - v).astype(np.float32)
    
    warped = cv2.remap(frame, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
    return warped

def smooth_frames(frames: List[np.ndarray], flow_fields: List[np.ndarray], alpha: float = 0.5) -> List[np.ndarray]:
    """
    Applies temporal smoothing to frames based on flow fields.
    Simple weighted average of current frame and warped previous frame.
    """
    smoothed = []
    if len(frames) < 2:
        return frames
    
    # Assume flow_fields[i] is flow from frames[i] to frames[i+1]
    # We smooth frame[i+1] using frame[i] warped by flow[i]
    
    # Keep first frame as is (no previous to smooth with)
    smoothed.append(frames[0])
    
    for i in range(1, len(frames)):
        current = frames[i]
        prev = frames[i-1]
        flow = flow_fields[i-1] # Flow from i-1 to i
        
        # Warp previous frame to current
        warped_prev = warp_frame(prev, flow)
        
        # Blend
        blended = (1 - alpha) * current + alpha * warped_prev
        smoothed.append(blended.astype(np.uint8))
        
    return smoothed

def process_video_flow(video_path: Path) -> Dict[str, str]:
    """
    Computes optical flow for a single video and saves the flow field.
    
    Args:
        video_path: Path to the naive baseline video.
        
    Returns:
        Dict with 'video_id', 'status', 'output_path'.
    """
    video_id = video_path.stem
    logger.info(f"Processing video: {video_id}")
    
    try:
        # Extract frames
        frames = extract_frames_to_list(str(video_path))
        if len(frames) < 2:
            logger.warning(f"Video {video_id} has fewer than 2 frames, skipping flow computation.")
            return {'video_id': video_id, 'status': 'skipped', 'reason': 'insufficient_frames'}
        
        logger.info(f"Extracted {len(frames)} frames from {video_id}")
        
        flow_fields = []
        # Compute flow between consecutive frames
        for i in range(len(frames) - 1):
            frame1 = frames[i]
            frame2 = frames[i+1]
            
            # Compute flow from frame1 to frame2
            flow = compute_flow_with_fallback(frame1, frame2)
            
            if not is_flow_valid(flow):
                logger.warning(f"Invalid flow detected at frame {i} in {video_id}, using fallback.")
                # Fallback logic is handled inside compute_flow_with_fallback
                # If it still returns invalid, we might need to handle it, 
                # but the function should ensure validity via fallback.
            
            flow_fields.append(flow)
        
        # Save flow fields
        output_dir = get_processed_dir() / "flow_fields"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f"{video_id}_flow.npy"
        # Stack flow fields: (N_frames-1, H, W, 2)
        flow_stack = np.stack(flow_fields, axis=0)
        np.save(str(output_path), flow_stack)
        
        logger.info(f"Saved flow field for {video_id} to {output_path}")
        
        return {
            'video_id': video_id,
            'status': 'success',
            'output_path': str(output_path)
        }
        
    except Exception as e:
        logger.error(f"Failed to process video {video_id}: {e}", exc_info=True)
        return {
            'video_id': video_id,
            'status': 'failed',
            'reason': str(e)
        }

def main():
    """
    Main entry point for the flow computation script.
    1. Verifies naive baseline videos exist (T013 output).
    2. Iterates through each video.
    3. Computes optical flow and saves to data/processed/flow_fields/.
    """
    parser = argparse.ArgumentParser(description="Compute optical flow fields for naive baseline videos.")
    parser.add_argument('--input-dir', type=str, default=None, help="Override input directory for naive baselines.")
    parser.add_argument('--output-dir', type=str, default=None, help="Override output directory for flow fields.")
    args = parser.parse_args()
    
    # Step 1: Verify naive baselines exist (FR-001)
    logger.info("Starting pre-flight check for naive baseline videos...")
    naive_paths = verify_naive_baselines_exist()
    logger.info(f"Pre-flight check passed. Found {len(naive_paths)} videos.")
    
    # Step 2: Process each video
    results = []
    total_start = time.time()
    
    for video_path in naive_paths:
        result = process_video_flow(video_path)
        results.append(result)
    
    total_time = time.time() - total_start
    
    # Step 3: Log summary
    success_count = sum(1 for r in results if r['status'] == 'success')
    fail_count = sum(1 for r in results if r['status'] == 'failed')
    skip_count = sum(1 for r in results if r['status'] == 'skipped')
    
    logger.info(f"Flow computation complete in {total_time:.2f}s.")
    logger.info(f"Success: {success_count}, Failed: {fail_count}, Skipped: {skip_count}")
    
    # Save summary log
    summary_path = get_results_dir() / "flow_computation_summary.json"
    with open(summary_path, 'w') as f:
        json.dump({
            'total_time_seconds': total_time,
            'total_videos': len(naive_paths),
            'success': success_count,
            'failed': fail_count,
            'skipped': skip_count,
            'details': results
        }, f, indent=2)
    
    logger.info(f"Summary saved to {summary_path}")
    
    if fail_count > 0:
        logger.warning(f"{fail_count} videos failed flow computation.")
        sys.exit(1)

if __name__ == "__main__":
    main()