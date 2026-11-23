import cv2
import json
import sys
import os
import gc
import numpy as np
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator, Tuple
from src.data.loader import load_config

def load_frames_from_video_path(video_path: str, frame_indices: List[int]) -> List[np.ndarray]:
    """
    Loads specific frames from a video file without loading the whole video into memory.
    Uses cv2.VideoCapture with explicit seeking.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    frames = []
    try:
        for idx in sorted(frame_indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                # If we can't read a frame at the requested index, stop
                break
            # Convert BGR to RGB for consistency if needed, but optical flow works on grayscale
            frames.append(frame)
    finally:
        cap.release()
        gc.collect()

    return frames

def compute_optical_flow_magnitude(prev_frame: np.ndarray, next_frame: np.ndarray) -> float:
    """
    Computes the optical flow magnitude between two frames using Farneback method.
    Returns the mean magnitude of the flow field.
    """
    if prev_frame is None or next_frame is None:
        return 0.0

    # Convert to grayscale
    if len(prev_frame.shape) == 3:
        gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)
    else:
        gray1 = prev_frame
        gray2 = next_frame

    # Calculate optical flow
    # Parameters tuned for speed vs accuracy on CPU
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

    # Compute magnitude
    magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    mean_magnitude = np.mean(magnitude)
    return float(mean_magnitude)

def streaming_flow_processor(video_path: str, frame_indices: List[int]) -> Generator[Tuple[int, float], None, None]:
    """
    Generator that yields (frame_id, optical_flow_magnitude) pairs one by one.
    This prevents OOM by processing frame pairs sequentially and releasing memory.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    try:
        # Sort indices to ensure sequential processing where possible
        sorted_indices = sorted(frame_indices)

        prev_frame = None
        prev_idx = None

        for idx in sorted_indices:
            # Seek to the frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()

            if not ret:
                # Skip if frame cannot be read
                continue

            if prev_frame is not None:
                # Compute flow between previous and current frame
                magnitude = compute_optical_flow_magnitude(prev_frame, frame)
                # Yield the magnitude for the CURRENT frame (relative to previous)
                # Or we could yield for the interval. Let's yield for the current frame index.
                yield idx, magnitude

            # Update previous
            prev_frame = frame
            prev_idx = idx

            # Explicitly delete to free memory immediately if needed
            # frame is not needed anymore for next iteration
            del frame
            gc.collect()

    finally:
        cap.release()
        gc.collect()

def generate_motion_labels_chunked(video_path: str, frame_indices: List[int], threshold: float) -> List[Dict[str, Any]]:
    """
    Generates motion labels for a list of frame indices using a streaming approach.
    Returns a list of dictionaries with frame_id, optical_flow_magnitude, and motion_label.
    """
    labels = []
    
    for frame_id, magnitude in streaming_flow_processor(video_path, frame_indices):
        label = "High" if magnitude > threshold else "Low"
        labels.append({
            "frame_id": int(frame_id),
            "optical_flow_magnitude": magnitude,
            "motion_label": label
        })
        
        # Periodic GC to ensure memory stays low during long runs
        if len(labels) % 100 == 0:
            gc.collect()

    return labels

def save_motion_labels_to_file(labels: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves motion labels to a JSON file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(labels, f, indent=2)

def run_pipeline(args: Optional[argparse.Namespace] = None) -> None:
    """
    Main entry point for the motion labels generation pipeline.
    Reads configuration, processes videos, and saves results.
    """
    if args is None:
        parser = argparse.ArgumentParser(description="Generate motion labels from video optical flow")
        parser.add_argument("--config", type=str, default="code/config/settings.yaml", help="Path to config file")
        parser.add_argument("--output", type=str, default="data/processed/motion_labels.json", help="Output JSON path")
        parser.add_argument("--video", type=str, help="Path to a specific video file (optional, otherwise uses config)")
        parser.add_argument("--frames", type=str, help="Comma-separated list of frame indices to process (optional)")
        parser.add_argument("--threshold", type=float, help="Threshold for High/Low motion classification")
        args = parser.parse_args()

    # Load config if no specific threshold provided
    config = load_config(args.config)
    threshold = args.threshold if args.threshold is not None else config.get('motion', {}).get('optical_flow_threshold', 5.0)
    
    # Determine frame indices
    if args.frames:
        frame_indices = [int(x.strip()) for x in args.frames.split(',')]
    else:
        # Default to a sample set if not specified
        frame_indices = list(range(0, 100, 10)) # Every 10th frame up to 100

    # Determine video path
    video_path = args.video
    if not video_path:
        # Try to find a sample video in data/raw if not specified
        raw_dir = Path("data/raw")
        if raw_dir.exists():
            video_files = list(raw_dir.glob("*.mp4")) + list(raw_dir.glob("*.avi")) + list(raw_dir.glob("*.mov"))
            if video_files:
                video_path = str(video_files[0])
            else:
                raise FileNotFoundError("No video files found in data/raw and no --video specified")
        else:
            raise FileNotFoundError("data/raw directory not found and no --video specified")

    print(f"Processing video: {video_path}")
    print(f"Using threshold: {threshold}")
    print(f"Processing frames: {frame_indices}")

    # Generate labels
    try:
        labels = generate_motion_labels_chunked(video_path, frame_indices, threshold)
        save_motion_labels_to_file(labels, args.output)
        print(f"Successfully saved {len(labels)} motion labels to {args.output}")
    except Exception as e:
        print(f"Error processing video: {e}")
        raise

def main() -> None:
    """
    Entry point for the script.
    """
    run_pipeline()

if __name__ == "__main__":
    main()