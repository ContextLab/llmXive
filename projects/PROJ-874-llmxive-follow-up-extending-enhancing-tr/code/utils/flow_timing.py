"""
RAFT-Small Inference Timing Utility

Measures and logs the inference time per frame for RAFT-Small on CPU.
This script is designed to run against CI limits (SC-005) to verify
feasibility without optimization.

Usage:
    python code/utils/flow_timing.py --video <path> --output <path>
"""

import os
import sys
import time
import json
import logging
import argparse
import numpy as np
import cv2
from pathlib import Path

# Import existing utilities from the project
try:
    from utils.flow import load_raft_small, estimate_flow, is_flow_valid
    from config import get_flow_model, get_flow_precision, setup_logging
except ImportError:
    # Fallback for standalone execution if needed, though project structure
    # implies running from root.
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from code.utils.flow import load_raft_small, estimate_flow, is_flow_valid
    from code.config import get_flow_model, get_flow_precision, setup_logging


def extract_frames_for_timing(video_path: str, max_frames: int = 10) -> list:
    """
    Extracts a limited number of frames from a video file for timing purposes.
    Returns a list of numpy arrays (BGR).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video: {video_path}")

    frames = []
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, frame_count // max_frames)
    
    logging.info(f"Extracting up to {max_frames} frames from {frame_count} total frames.")

    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if count % step == 0 or len(frames) == 0:
            # Ensure we get the first frame and then every step
            # Adjust logic to ensure we don't skip too many if video is short
            if len(frames) < max_frames:
                frames.append(frame)
                if len(frames) >= max_frames:
                    break
        
        count += 1

    cap.release()
    return frames


def run_timing_benchmark(video_path: str, output_path: str, warmup_frames: int = 2):
    """
    Runs the RAFT-Small model on the video frames and logs timing metrics.
    
    Args:
        video_path: Path to the input video file.
        output_path: Path to save the JSON results.
        warmup_frames: Number of frames to run for warmup (not timed).
    """
    logger = logging.getLogger(__name__)
    
    # Load frames
    try:
        frames = extract_frames_for_timing(video_path, max_frames=20)
        if len(frames) < 2:
            logger.error("Not enough frames to compute flow (need at least 2).")
            return
    except Exception as e:
        logger.error(f"Failed to extract frames: {e}")
        return

    # Load Model
    logger.info("Loading RAFT-Small model...")
    try:
        model = load_raft_small()
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return

    # Warmup
    logger.info(f"Running warmup on {warmup_frames} frames...")
    for i in range(min(warmup_frames, len(frames) - 1)):
        _ = estimate_flow(model, frames[i], frames[i+1])
    
    # Timing Loop
    timings = []
    logger.info("Starting timing benchmark...")
    
    for i in range(warmup_frames, len(frames) - 1):
        frame_prev = frames[i]
        frame_next = frames[i+1]
        
        start_time = time.perf_counter()
        flow = estimate_flow(model, frame_prev, frame_next)
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        timings.append(duration)
        
        if not is_flow_valid(flow):
            logger.warning(f"Frame pair {i}-{i+1} produced invalid flow.")

    if not timings:
        logger.error("No valid timings recorded.")
        return

    # Calculate Statistics
    mean_time = np.mean(timings)
    std_time = np.std(timings)
    min_time = np.min(timings)
    max_time = np.max(timings)
    total_time = sum(timings)
    fps = len(timings) / total_time if total_time > 0 else 0

    results = {
        "video_path": video_path,
        "num_pairs_tested": len(timings),
        "timing_seconds": {
            "mean": mean_time,
            "std": std_time,
            "min": min_time,
            "max": max_time,
            "total": total_time
        },
        "performance": {
            "fps": fps,
            "seconds_per_frame": mean_time
        },
        "model_info": {
            "model_name": get_flow_model(),
            "precision": get_flow_precision()
        }
    }

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Benchmark complete. Results saved to {output_path}")
    logger.info(f"Mean Inference Time: {mean_time:.4f} seconds/frame")
    logger.info(f"Estimated FPS: {fps:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Measure RAFT-Small inference time per frame.")
    parser.add_argument("--video", type=str, required=True, help="Path to input video file.")
    parser.add_argument("--output", type=str, default="data/results/raft_timing.json", 
                        help="Path to save JSON results.")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level.")
    
    args = parser.parse_args()

    # Setup logging
    setup_logging(level=getattr(logging, args.log_level.upper()))
    logger = logging.getLogger(__name__)

    if not os.path.exists(args.video):
        logger.error(f"Video file not found: {args.video}")
        sys.exit(1)

    run_timing_benchmark(args.video, args.output)


if __name__ == "__main__":
    main()