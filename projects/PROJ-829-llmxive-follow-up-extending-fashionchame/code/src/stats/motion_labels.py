"""
Motion Labels Module (FR-010 Revision Fix).

Calculates optical flow magnitude using cv2.calcOpticalFlowFarneback
on a strictly sampled frame sequence (every 5th frame) and implements
a chunked processing loop to prevent OOM during flow calculation.
"""
import cv2
import json
import sys
import os
import gc
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Generator
from PIL import Image

from src.data.loader import load_config


# Constants for optical flow and downsampling
OPTICAL_FLOW_SUBSAMPLING_RATIO = 5  # Process every 5th frame
OPTICAL_FLOW_THRESHOLD = 5.0  # Default threshold for High/Low motion label


def load_frames_from_video_path(video_path: Path) -> Generator[np.ndarray, None, None]:
    """
    Generator to yield frames from a video file one by one to minimize memory usage.
    Uses OpenCV VideoCapture.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {video_path}")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Convert BGR (OpenCV default) to RGB for consistency with PIL/other modules if needed,
        # but cv2.calcOpticalFlowFarneback works on grayscale or BGR.
        # We convert to grayscale immediately for flow calculation.
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        yield gray

    cap.release()


def compute_optical_flow_magnitude(prev_frame: np.ndarray, next_frame: np.ndarray) -> np.ndarray:
    """
    Computes the optical flow magnitude between two frames using Farneback method.
    Optimized for CPU.

    Args:
        prev_frame: Grayscale frame at t
        next_frame: Grayscale frame at t+1

    Returns:
        np.ndarray: Magnitude map of the optical flow.
    """
    if prev_frame is None or next_frame is None:
        raise ValueError("Input frames cannot be None")

    # Parameters for Farneback optical flow
    # pyr_scale: 0.5, levels: 3, winsize: 15, iterations: 3, poly_n: 5, poly_sigma: 1.2
    flow = cv2.calcOpticalFlowFarneback(
        prev_frame,
        next_frame,
        None,
        pyr_scale=0.5,
        levels=3,
        winsize=15,
        iterations=3,
        poly_n=5,
        poly_sigma=1.2,
        flags=cv2.OPTFLOW_FARNEBACK_GAUSSIAN
    )

    # Calculate magnitude
    magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
    return magnitude


def generate_motion_labels_chunked(
    video_path: Path,
    chunk_size: int = 10,
    subsampling_ratio: int = OPTICAL_FLOW_SUBSAMPLING_RATIO
) -> Generator[Dict[str, Any], None, None]:
    """
    Generates motion labels for a video by processing frames in chunks.
    This prevents OOM by not loading all frames or all flow maps at once.
    It strictly samples every Nth frame as defined by subsampling_ratio.

    Args:
        video_path: Path to the video file.
        chunk_size: Number of frame pairs to process before yielding results and clearing memory.
        subsampling_ratio: Process every Nth frame (e.g., 5 means frame 0, 5, 10...).

    Yields:
        Dict containing frame_id, optical_flow_magnitude (mean), and motion_label.
    """
    # Load frames into a generator to avoid loading all at once
    frame_generator = load_frames_from_video_path(video_path)
    
    # We need to buffer frames to apply subsampling
    # We will collect frames until we have enough to form a pair with the required stride
    frames_buffer: List[np.ndarray] = []
    frame_indices: List[int] = []
    
    current_global_frame_idx = 0
    
    for frame in frame_generator:
        frames_buffer.append(frame)
        frame_indices.append(current_global_frame_idx)
        
        # If we have enough frames to process a chunk of pairs
        # We need at least (chunk_size + 1) frames to make chunk_size pairs if we were consecutive,
        # but with subsampling, we need to be careful.
        # Strategy: Accumulate frames until we can form a full chunk of pairs with stride.
        
        # To simplify: We process pairs (i, i + subsampling_ratio).
        # We need to ensure we have frames available for the next pair.
        
        # Let's process as soon as we have a complete chunk of pairs.
        # A pair is (frame[k], frame[k + subsampling_ratio])
        # We can only process frame[k] if frame[k + subsampling_ratio] exists in buffer.
        
        # Check if we have enough frames to form a chunk of pairs
        # We want to process pairs starting from the oldest available index that hasn't been processed yet.
        # But to keep memory low, we should discard old frames once processed.
        
        # Let's implement a sliding window approach for chunks.
        # We will wait until we have `chunk_size * subsampling_ratio + 1` frames to safely process a chunk?
        # No, simpler: We accumulate frames. When we have enough to form `chunk_size` pairs with the stride,
        # we process them and then clear the processed frames from the buffer.
        
        # Minimum frames needed to process one pair with stride S is S+1.
        # To process `chunk_size` pairs starting from index 0: we need indices 0, S, 2S, ... (chunk_size-1)S, chunk_size*S.
        # So we need `chunk_size * subsampling_ratio + 1` frames in buffer to process the first chunk starting at 0.
        
        min_frames_for_chunk = (chunk_size * subsampling_ratio) + 1
        
        if len(frames_buffer) >= min_frames_for_chunk:
            # We can process a chunk
            # Process pairs: (0, S), (S, 2S), ... ((chunk_size-1)S, chunk_size*S)
            # Wait, the requirement is "every 5th frame". Usually this means frame 0, 5, 10...
            # So pairs are (0, 5), (5, 10), (10, 15)...
            # This requires indices: 0, 5, 10, 15...
            # To process `chunk_size` such pairs, we need indices up to `chunk_size * subsampling_ratio`.
            
            processed_count = 0
            start_idx = 0
            
            while processed_count < chunk_size and (start_idx + subsampling_ratio) < len(frames_buffer):
                idx_prev = start_idx
                idx_next = start_idx + subsampling_ratio
                
                prev_frame = frames_buffer[idx_prev]
                next_frame = frames_buffer[idx_next]
                
                # Calculate flow magnitude
                try:
                    mag_map = compute_optical_flow_magnitude(prev_frame, next_frame)
                    mean_magnitude = float(np.mean(mag_map))
                    
                    # Determine label
                    label = "High" if mean_magnitude > OPTICAL_FLOW_THRESHOLD else "Low"
                    
                    # Use the timestamp or index of the first frame of the pair as the identifier
                    # The global index in the buffer corresponds to the frame number in the video
                    # (assuming we read sequentially)
                    frame_id = frame_indices[idx_prev]
                    
                    yield {
                        "frame_id": int(frame_id),
                        "optical_flow_magnitude": mean_magnitude,
                        "motion_label": label,
                        "video_path": str(video_path)
                    }
                    
                    processed_count += 1
                    start_idx += subsampling_ratio
                except Exception as e:
                    # Log error but continue to next chunk if possible
                    print(f"Error computing flow for pair ({idx_prev}, {idx_next}): {e}", file=sys.stderr)
                    processed_count += 1 # Skip this pair
                    start_idx += subsampling_ratio

            # Cleanup: Remove processed frames from buffer to save memory.
            # We keep frames from the last processed index to the end of the buffer for the next chunk.
            # The last processed pair ended at `start_idx` (which is now the next start).
            # Actually, we processed up to `start_idx` (exclusive of the next start).
            # We need to keep frames from `start_idx` onwards.
            # But `start_idx` might have advanced by `chunk_size * subsampling_ratio`.
            # We should truncate the buffer.
            
            # How many frames did we consume?
            # We processed pairs starting at 0, S, 2S... up to (chunk_size-1)S.
            # The last frame used was (chunk_size-1)S + S = chunk_size * S.
            # So we can remove indices 0 to (chunk_size * S - 1).
            # We keep indices from `chunk_size * S` onwards.
            
            frames_to_keep = len(frames_buffer) - (chunk_size * subsampling_ratio)
            if frames_to_keep > 0:
                # Keep only the tail
                frames_buffer = frames_buffer[-frames_to_keep:]
                frame_indices = frame_indices[-frames_to_keep:]
            else:
                frames_buffer = []
                frame_indices = []
            
            # Force garbage collection
            gc.collect()

    # Process remaining frames in the buffer if any
    # We can't form a full chunk, but we can process whatever pairs we can form with the stride
    start_idx = 0
    while (start_idx + subsampling_ratio) < len(frames_buffer):
        idx_prev = start_idx
        idx_next = start_idx + subsampling_ratio
        
        prev_frame = frames_buffer[idx_prev]
        next_frame = frames_buffer[idx_next]
        
        try:
            mag_map = compute_optical_flow_magnitude(prev_frame, next_frame)
            mean_magnitude = float(np.mean(mag_map))
            label = "High" if mean_magnitude > OPTICAL_FLOW_THRESHOLD else "Low"
            frame_id = frame_indices[idx_prev]
            
            yield {
                "frame_id": int(frame_id),
                "optical_flow_magnitude": mean_magnitude,
                "motion_label": label,
                "video_path": str(video_path)
            }
        except Exception as e:
            print(f"Error computing flow for pair ({idx_prev}, {idx_next}): {e}", file=sys.stderr)
        
        start_idx += subsampling_ratio
    
    # Final cleanup
    del frames_buffer
    del frame_indices
    gc.collect()


def save_motion_labels_to_file(
    results_generator: Generator[Dict[str, Any], None, None],
    output_path: Path
) -> int:
    """
    Consumes the generator and saves results to a JSON file.
    Returns the count of records written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    count = 0
    with open(output_path, 'w') as f:
        # Write as JSON Lines or a list? The spec says `data/processed/motion_labels.json`.
        # Usually a list is easier to consume later.
        f.write("[\n")
        first = True
        for record in results_generator:
            if not first:
                f.write(",\n")
            first = False
            json.dump(record, f)
            count += 1
        f.write("\n]")
    
    return count


def run_pipeline(
    input_manifest_path: Path,
    output_path: Path,
    config_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main entry point to run the motion labeling pipeline.
    Reads video paths from a manifest, computes optical flow, and saves labels.
    """
    if config_path:
        config = load_config(config_path)
        # Override defaults if present in config
        if 'motion' in config and 'optical_flow_subsampling_ratio' in config['motion']:
            global OPTICAL_FLOW_SUBSAMPLING_RATIO
            OPTICAL_FLOW_SUBSAMPLING_RATIO = int(config['motion']['optical_flow_subsampling_ratio'])
        if 'motion' in config and 'optical_flow_threshold' in config['motion']:
            global OPTICAL_FLOW_THRESHOLD
            OPTICAL_FLOW_THRESHOLD = float(config['motion']['optical_flow_threshold'])

    if not input_manifest_path.exists():
        raise FileNotFoundError(f"Input manifest not found: {input_manifest_path}")

    with open(input_manifest_path, 'r') as f:
        manifest = json.load(f)

    # Expect manifest to be a list of items with 'video_path' or similar
    if not isinstance(manifest, list):
        raise ValueError("Input manifest must be a list of records.")

    all_results: List[Dict[str, Any]] = []
    
    # We process video by video to keep memory low per video
    for item in manifest:
        video_path = Path(item.get('video_path'))
        if not video_path.exists():
            print(f"Warning: Video not found, skipping: {video_path}", file=sys.stderr)
            continue

        print(f"Processing video: {video_path}")
        # Create generator for this video
        video_results = generate_motion_labels_chunked(
            video_path,
            chunk_size=10, # Process 10 pairs at a time
            subsampling_ratio=OPTICAL_FLOW_SUBSAMPLING_RATIO
        )
        
        # Collect results for this video into the main list (or write directly? 
        # The function save_motion_labels_to_file expects a generator, but we are aggregating across videos.
        # Let's just append to a list and write at the end, assuming the total result size fits in memory.
        # If the result JSON is huge, we might need to stream write. 
        # Given the downsampling, the number of records should be manageable (N/5).
        for res in video_results:
            all_results.append(res)
        
        # Explicitly clear memory after each video
        gc.collect()

    # Write final output
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    return {
        "total_records": len(all_results),
        "output_path": str(output_path)
    }


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate motion labels from video using optical flow.")
    parser.add_argument("--manifest", type=str, required=True, help="Path to input manifest JSON.")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file.")
    parser.add_argument("--config", type=str, default=None, help="Path to config file (optional).")
    
    args = parser.parse_args()
    
    result = run_pipeline(
        input_manifest_path=Path(args.manifest),
        output_path=Path(args.output),
        config_path=Path(args.config) if args.config else None
    )
    
    print(f"Motion labeling complete. Records: {result['total_records']}, Output: {result['output_path']}")


if __name__ == "__main__":
    main()
