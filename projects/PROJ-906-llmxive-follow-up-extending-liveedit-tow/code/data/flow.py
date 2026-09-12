"""
Optical flow computation and magnitude extraction for video analysis.

This module provides utilities for:
1. Computing full optical flow fields (RAFT/Farneback)
2. Extracting lightweight flow magnitudes for stratification
3. Handling invalid flow vectors (NaN/Inf)
"""

import os
import logging
import cv2
import numpy as np
import torch
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from config import ensure_directories
from utils.logger import get_logger

logger = get_logger(__name__)


def compute_flow_magnitude(flow: np.ndarray) -> float:
    """
    Compute the mean magnitude of a flow field, handling NaN/Inf values.

    Args:
        flow: Optical flow field of shape (H, W, 2) with dtype float32.

    Returns:
        Mean magnitude of valid flow vectors. Returns 0.0 if all values are invalid.
    """
    if flow.size == 0:
        return 0.0

    # Compute magnitude: sqrt(u^2 + v^2)
    magnitude = np.sqrt(np.sum(flow**2, axis=2, dtype=np.float64))

    # Mask out invalid values (NaN and Inf)
    valid_mask = np.isfinite(magnitude)

    if not np.any(valid_mask):
        logger.warning("All flow values are invalid (NaN/Inf). Returning 0.0.")
        return 0.0

    # Compute mean of valid magnitudes
    mean_mag = np.mean(magnitude[valid_mask])
    return float(mean_mag)


def compute_flow_magnitude_for_video(
    video_path: str,
    flow_method: str = "farneback",
    frame_indices: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Compute mean flow magnitude for a single video.

    Args:
        video_path: Path to the input video file.
        flow_method: Method to use for flow computation ('farneback' or 'raft').
        frame_indices: Optional list of frame indices to process. If None, process all.

    Returns:
        Dictionary with keys:
            - 'video_path': str
            - 'mean_magnitude': float
            - 'num_frames': int
            - 'invalid_frames': int
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_indices is None:
        frame_indices = list(range(total_frames))

    magnitudes = []
    invalid_count = 0
    processed_count = 0

    prev_gray = None
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx not in frame_indices:
            frame_idx += 1
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_gray is not None:
            if flow_method == "farneback":
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray, gray, None,
                    pyr_scale=0.5, levels=3, winsize=15,
                    iterations=3, poly_n=5, poly_sigma=1.2, flags=0
                )
            elif flow_method == "raft":
                # RAFT would be implemented here with PyTorch
                # For now, fall back to Farneback for CPU compatibility
                logger.warning("RAFT not available, using Farneback as fallback")
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray, gray, None,
                    pyr_scale=0.5, levels=3, winsize=15,
                    iterations=3, poly_n=5, poly_sigma=1.2, flags=0
                )
            else:
                raise ValueError(f"Unknown flow method: {flow_method}")

            mag = compute_flow_magnitude(flow)
            if mag == 0.0 and not np.all(np.isfinite(flow)):
                invalid_count += 1
            else:
                magnitudes.append(mag)

            processed_count += 1

        prev_gray = gray
        frame_idx += 1

    cap.release()

    mean_mag = np.mean(magnitudes) if magnitudes else 0.0

    return {
        "video_path": video_path,
        "mean_magnitude": float(mean_mag),
        "num_frames": processed_count,
        "invalid_frames": invalid_count
    }


def extract_flow_magnitudes_for_dataset(
    clip_paths: List[str],
    output_path: str,
    flow_method: str = "farneback"
) -> Dict[str, Any]:
    """
    Extract flow magnitudes for a dataset of clips and save to JSON.

    Args:
        clip_paths: List of paths to video clips.
        output_path: Path to the output JSON file.
        flow_method: Method to use for flow computation.

    Returns:
        Dictionary mapping clip paths to their flow magnitude statistics.
    """
    ensure_directories([output_path])

    results = {}
    logger.info(f"Processing {len(clip_paths)} clips for flow magnitude extraction...")

    for clip_path in clip_paths:
        if not os.path.exists(clip_path):
            logger.warning(f"Clip not found: {clip_path}. Skipping.")
            results[clip_path] = {
                "mean_magnitude": 0.0,
                "num_frames": 0,
                "invalid_frames": 0,
                "error": "File not found"
            }
            continue

        try:
            stats = compute_flow_magnitude_for_video(clip_path, flow_method)
            results[clip_path] = stats
            logger.info(f"Processed {clip_path}: mean_mag={stats['mean_magnitude']:.4f}")
        except Exception as e:
            logger.error(f"Error processing {clip_path}: {e}")
            results[clip_path] = {
                "mean_magnitude": 0.0,
                "num_frames": 0,
                "invalid_frames": 0,
                "error": str(e)
            }

    # Write results to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Flow magnitudes saved to {output_path}")
    return results


def compute_full_flow_field(
    video_path: str,
    output_dir: str,
    method: str = "farneback"
) -> str:
    """
    Compute full optical flow field for a video and save to disk.

    Args:
        video_path: Path to input video.
        output_dir: Directory to save flow fields.
        method: Flow computation method.

    Returns:
        Path to the saved flow magnitude summary file.
    """
    ensure_directories([output_dir])

    video_name = Path(video_path).stem
    flow_dir = os.path.join(output_dir, f"{video_name}_flow")
    ensure_directories([flow_dir])

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    prev_gray = None
    frame_idx = 0

    magnitudes = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_gray is not None:
            if method == "farneback":
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray, gray, None,
                    pyr_scale=0.5, levels=3, winsize=15,
                    iterations=3, poly_n=5, poly_sigma=1.2, flags=0
                )
            else:
                raise ValueError(f"Unsupported method: {method}")

            mag = compute_flow_magnitude(flow)
            magnitudes.append(mag)

            # Save flow field as .npy
            flow_path = os.path.join(flow_dir, f"flow_{frame_idx:04d}.npy")
            np.save(flow_path, flow)

        prev_gray = gray
        frame_idx += 1

    cap.release()

    # Save summary
    summary_path = os.path.join(output_dir, f"{video_name}_magnitudes.json")
    with open(summary_path, 'w') as f:
        json.dump({
            "video_path": video_path,
            "mean_magnitude": float(np.mean(magnitudes)) if magnitudes else 0.0,
            "num_frames": len(magnitudes),
            "magnitudes": magnitudes
        }, f, indent=2)

    logger.info(f"Flow fields saved to {flow_dir}")
    return summary_path


def main():
    """CLI entry point for flow magnitude extraction."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract flow magnitudes from video dataset")
    parser.add_argument("--input_dir", type=str, required=True, help="Directory containing video clips")
    parser.add_argument("--output_path", type=str, required=True, help="Output JSON path")
    parser.add_argument("--method", type=str, default="farneback", choices=["farneback", "raft"],
                        help="Flow computation method")
    parser.add_argument("--clip_pattern", type=str, default="*.mp4", help="Glob pattern for clips")

    args = parser.parse_args()

    # Find all clips
    import glob
    clip_paths = glob.glob(os.path.join(args.input_dir, args.clip_pattern))

    if not clip_paths:
        logger.error(f"No clips found in {args.input_dir} matching {args.clip_pattern}")
        return 1

    logger.info(f"Found {len(clip_paths)} clips")

    results = extract_flow_magnitudes_for_dataset(
        clip_paths=clip_paths,
        output_path=args.output_path,
        flow_method=args.method
    )

    logger.info(f"Completed. Results written to {args.output_path}")
    return 0


if __name__ == "__main__":
    exit(main())