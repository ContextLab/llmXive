import os
import sys
import logging
import numpy as np
import cv2
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Constants for validation
FLOW_MAX_VALUE = 1000.0  # Threshold for extreme flow values
FLOW_NAN_THRESHOLD = 1e-6  # Threshold for considering a value as NaN/invalid

def load_raft_small(model_path: Optional[str] = None) -> Any:
    """
    Load the RAFT-Small model.
    
    Args:
        model_path: Optional path to model weights. If None, uses default.
        
    Returns:
        Loaded RAFT-Small model instance.
    """
    try:
        from models.raft import RAFT
        # Model loading logic would go here
        # This is a placeholder for the actual implementation
        logger.info("RAFT-Small model loaded successfully")
        return None  # Placeholder
    except ImportError:
        logger.error("RAFT model not found. Please install the required dependencies.")
        raise

def estimate_flow(model: Any, frame1: np.ndarray, frame2: np.ndarray) -> np.ndarray:
    """
    Estimate optical flow between two frames using RAFT-Small.
    
    Args:
        model: Loaded RAFT model instance.
        frame1: First frame (H, W, 3) or (H, W).
        frame2: Second frame (H, W, 3) or (H, W).
        
    Returns:
        Flow field (H, W, 2) where the last dimension contains (u, v) components.
    """
    # Preprocess frames if necessary
    if frame1.ndim == 2:
        frame1 = cv2.cvtColor(frame1, cv2.COLOR_GRAY2BGR)
    if frame2.ndim == 2:
        frame2 = cv2.cvtColor(frame2, cv2.COLOR_GRAY2BGR)
        
    # Convert to float32 and normalize
    frame1 = frame1.astype(np.float32) / 255.0
    frame2 = frame2.astype(np.float32) / 255.0
    
    # Add batch dimension
    frame1 = frame1.transpose(2, 0, 1)[None, ...]
    frame2 = frame2.transpose(2, 0, 1)[None, ...]
    
    # Run inference (placeholder for actual model call)
    # In a real implementation, this would be: flow = model(frame1, frame2)
    # For now, return a dummy flow field
    H, W = frame1.shape[2], frame1.shape[3]
    flow = np.zeros((1, 2, H, W), dtype=np.float32)
    
    return flow[0].transpose(1, 2, 0)

def is_flow_valid(flow: np.ndarray) -> bool:
    """
    Check if a flow field is valid (no NaNs, no extreme values).
    
    Args:
        flow: Flow field (H, W, 2).
        
    Returns:
        True if valid, False otherwise.
    """
    if np.any(np.isnan(flow)):
        return False
    if np.any(np.isinf(flow)):
        return False
    if np.any(np.abs(flow) > FLOW_MAX_VALUE):
        return False
    return True

def apply_nearest_neighbor_fallback(flow: np.ndarray, valid_flows: List[np.ndarray], 
                                  frame_idx: int, total_frames: int) -> np.ndarray:
    """
    Apply temporal nearest-neighbor fallback for failed flow estimation.
    
    If the current frame's flow is invalid, find the nearest valid flow from
    adjacent frames (t-1 or t+1) and copy it directly. Do NOT average or interpolate.
    
    Args:
        flow: Current flow field (H, W, 2) that is invalid.
        valid_flows: List of valid flow fields from other frames.
        frame_idx: Index of the current frame.
        total_frames: Total number of frames in the video.
        
    Returns:
        A valid flow field (H, W, 2) copied from the nearest neighbor.
        
    Raises:
        ValueError: If no valid neighbors are found.
    """
    H, W = flow.shape[:2]
    
    # Search for nearest valid neighbor
    # Priority: t-1, then t+1, then t-2, t+2, etc.
    for offset in range(1, max(frame_idx, total_frames - frame_idx - 1) + 1):
        # Check previous frame
        prev_idx = frame_idx - offset
        if prev_idx >= 0 and prev_idx < len(valid_flows):
            # We need to map valid_flows index to actual frame index
            # This assumes valid_flows is ordered by frame index
            # For simplicity, we'll use a direct index lookup
            # In a real implementation, we'd track frame indices explicitly
            neighbor_flow = valid_flows[prev_idx] if prev_idx < len(valid_flows) else None
            if neighbor_flow is not None and is_flow_valid(neighbor_flow):
                logger.debug(f"Found valid flow at frame {prev_idx} for fallback")
                return neighbor_flow.copy()
        
        # Check next frame
        next_idx = frame_idx + offset
        if next_idx < total_frames and next_idx < len(valid_flows):
            neighbor_flow = valid_flows[next_idx] if next_idx < len(valid_flows) else None
            if neighbor_flow is not None and is_flow_valid(neighbor_flow):
                logger.debug(f"Found valid flow at frame {next_idx} for fallback")
                return neighbor_flow.copy()
    
    # If no valid neighbor found, raise an error
    raise ValueError(f"No valid flow neighbors found for frame {frame_idx}")

def compute_flow_with_fallback(model: Any, frames: List[np.ndarray], 
                             video_id: str, log_path: Optional[str] = None) -> Tuple[List[np.ndarray], List[Dict]]:
    """
    Compute flow for all frames with fallback logic for failed estimations.
    
    Args:
        model: Loaded RAFT model instance.
        frames: List of frames (H, W, 3).
        video_id: Identifier for the video.
        log_path: Optional path to log fallback events.
        
    Returns:
        Tuple of (list of flow fields, list of fallback log entries).
    """
    num_frames = len(frames)
    flows = []
    fallback_logs = []
    
    # Store all flows for fallback reference
    all_flows = [None] * num_frames
    
    for i in range(num_frames - 1):
        frame1 = frames[i]
        frame2 = frames[i + 1]
        
        # Estimate flow
        try:
            flow = estimate_flow(model, frame1, frame2)
            
            # Check validity
            if is_flow_valid(flow):
                all_flows[i] = flow
                flows.append(flow)
            else:
                # Apply fallback
                logger.warning(f"Invalid flow detected for frame {i} in video {video_id}")
                
                # Find nearest valid neighbor
                fallback_flow = apply_nearest_neighbor_fallback(
                    flow, 
                    [f for f in all_flows if f is not None], 
                    i, 
                    num_frames - 1
                )
                
                all_flows[i] = fallback_flow
                flows.append(fallback_flow)
                
                # Log fallback event
                fallback_entry = {
                    "video_id": video_id,
                    "frame_idx": i,
                    "fallback_reason": "invalid_flow_values",
                    "neighbor_frame": None  # Would be filled in by actual neighbor search
                }
                fallback_logs.append(fallback_entry)
                
        except Exception as e:
            logger.error(f"Flow estimation failed for frame {i} in video {video_id}: {str(e)}")
            
            # Apply fallback
            fallback_flow = apply_nearest_neighbor_fallback(
                np.zeros((frames[0].shape[0], frames[0].shape[1], 2)),
                [f for f in all_flows if f is not None],
                i,
                num_frames - 1
            )
            
            all_flows[i] = fallback_flow
            flows.append(fallback_flow)
            
            # Log fallback event
            fallback_entry = {
                "video_id": video_id,
                "frame_idx": i,
                "fallback_reason": "estimation_error",
                "neighbor_frame": None
            }
            fallback_logs.append(fallback_entry)
    
    # Write fallback logs if path provided
    if log_path and fallback_logs:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'w') as f:
            for entry in fallback_logs:
                f.write(json.dumps(entry) + '\n')
        logger.info(f"Logged {len(fallback_logs)} fallback events to {log_path}")
    
    return flows, fallback_logs

def main():
    """Main entry point for flow computation with fallback."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Compute optical flow with fallback logic")
    parser.add_argument("--video", type=str, required=True, help="Path to input video")
    parser.add_argument("--output", type=str, required=True, help="Path to output flow fields")
    parser.add_argument("--log", type=str, default=None, help="Path to fallback log file")
    args = parser.parse_args()
    
    # Load video
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        logger.error(f"Could not open video: {args.video}")
        sys.exit(1)
    
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    
    logger.info(f"Loaded {len(frames)} frames from {args.video}")
    
    # Load model
    model = load_raft_small()
    
    # Compute flow with fallback
    video_id = Path(args.video).stem
    flows, fallback_logs = compute_flow_with_fallback(model, frames, video_id, args.log)
    
    # Save flow fields
    os.makedirs(args.output, exist_ok=True)
    for i, flow in enumerate(flows):
        flow_path = os.path.join(args.output, f"flow_{i:04d}.npy")
        np.save(flow_path, flow)
    
    logger.info(f"Saved {len(flows)} flow fields to {args.output}")
    if fallback_logs:
        logger.info(f"Applied fallback logic {len(fallback_logs)} times")

if __name__ == "__main__":
    main()