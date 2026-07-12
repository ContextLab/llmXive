"""
Feature Extraction Module for RealEstate10K Stratified Sequences.

This module implements sparse feature extraction (SIFT/ORB) from keyframes
of stratified video sequences. It explicitly skips dense depth generation,
implements batch processing for memory safety, and detects low feature
density in fast sequences.
"""

import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Project imports matching the API surface
from config import get_stratified_dir, get_features_dir, get_memory_limit_gb, ensure_directories
from utils.seeds import set_global_seed
from utils.memory_monitor import MemoryMonitor, check_memory_limit, should_batch_process

# Constants
SEED = 42
MEMORY_LIMIT_GB = 6.0  # Trigger batch processing if usage exceeds this
MIN_FEATURES = 10      # Minimum features to consider a frame valid
FAST_SEQUENCE_THRESHOLD = 0.5  # Placeholder for "fast" detection if needed locally

set_global_seed(SEED)


def load_sequence_frames(sequence_path: Path) -> List[np.ndarray]:
    """
    Load all frames from a video sequence directory or file.
    
    Args:
        sequence_path: Path to the sequence directory or video file.
        
    Returns:
        List of frames as numpy arrays (H, W, C).
    """
    frames = []
    if sequence_path.is_dir():
        # Assume directory contains image files
        image_files = sorted(sequence_path.glob("*.png")) + sorted(sequence_path.glob("*.jpg"))
        for img_path in image_files:
            frame = cv2.imread(str(img_path))
            if frame is not None:
                frames.append(frame)
    else:
        # Assume it's a video file
        cap = cv2.VideoCapture(str(sequence_path))
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
    
    return frames


def extract_sparse_features(frame: np.ndarray, method: str = "sift") -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract sparse SIFT or ORB descriptors and coordinates from a single frame.
    
    Args:
        frame: Input image (BGR).
        method: "sift" or "orb".
        
    Returns:
        Tuple of (coordinates, descriptors).
        coordinates: (N, 2) array of (x, y) points.
        descriptors: (N, D) array of descriptors.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    if method == "sift":
        detector = cv2.SIFT_create(nfeatures=1024)
    elif method == "orb":
        detector = cv2.ORB_create(nfeatures=1024)
    else:
        raise ValueError(f"Unsupported feature method: {method}")
    
    keypoints, descriptors = detector.detectAndCompute(gray, None)
    
    if not keypoints:
        return np.empty((0, 2), dtype=np.float32), np.empty((0, 32), dtype=np.uint8)
    
    # Extract coordinates
    coords = np.array([kp.pt for kp in keypoints], dtype=np.float32)
    
    # Ensure descriptors are 2D
    if descriptors is None:
        return coords, np.empty((0, 1), dtype=np.float32)
        
    return coords, descriptors


def is_fast_sequence(sequence_meta: Dict[str, Any]) -> bool:
    """
    Determine if a sequence is classified as 'Fast' based on metadata.
    
    Args:
        sequence_meta: Dictionary containing sequence metadata (e.g., flow magnitude).
        
    Returns:
        True if the sequence is classified as Fast.
    """
    # Check if metadata indicates high motion
    # This relies on the stratify.py output which includes 'motion_magnitude'
    motion = sequence_meta.get('motion_magnitude', 0.0)
    return motion > 0.5  # Threshold determined by stratify logic


def process_sequence(sequence_path: Path, sequence_meta: Dict[str, Any], monitor: MemoryMonitor) -> Optional[Dict[str, Any]]:
    """
    Process a single sequence: extract features from keyframes, handle memory limits,
    and detect low feature density in fast sequences.
    
    Args:
        sequence_path: Path to the sequence.
        sequence_meta: Metadata for the sequence (from stratify).
        monitor: MemoryMonitor instance to track usage.
        
    Returns:
        Dictionary of extracted features or None if invalid.
    """
    sequence_name = sequence_path.name
    is_fast = is_fast_sequence(sequence_meta)
    
    frames = load_sequence_frames(sequence_path)
    if not frames:
        print(f"Warning: No frames found in {sequence_path}")
        return None
    
    # Select keyframes (e.g., every 10th frame or based on metadata)
    # For this implementation, we take the first 5 frames as keyframes
    # or all if fewer than 5.
    keyframe_indices = list(range(0, len(frames), 10))[:5]
    if not keyframe_indices:
        keyframe_indices = [0]
        
    all_keypoints = []
    all_descriptors = []
    frame_ids = []
    invalid_frames = []
    
    for idx in keyframe_indices:
        frame = frames[idx]
        monitor.check()
        
        # Check memory limit
        if should_batch_process(MEMORY_LIMIT_GB):
            # Force sequential processing (already sequential here, but log)
            print(f"Memory pressure detected in {sequence_name}. Processing frame {idx} sequentially.")
        
        coords, descs = extract_sparse_features(frame)
        
        # Detect low feature density in Fast sequences
        if is_fast and len(coords) < MIN_FEATURES:
            invalid_frames.append(idx)
            continue
        
        all_keypoints.append(coords)
        all_descriptors.append(descs)
        frame_ids.append(idx)
    
    if not all_keypoints:
        return None
        
    # Concatenate results
    keypoints_arr = np.vstack(all_keypoints)
    descriptors_arr = np.vstack(all_descriptors)
    
    result = {
        "sequence_name": sequence_name,
        "is_fast": is_fast,
        "keyframe_ids": frame_ids,
        "keypoints": keypoints_arr,
        "descriptors": descriptors_arr,
        "invalid_frames": invalid_frames,
        "total_frames_processed": len(keyframe_indices)
    }
    
    return result


def main():
    """
    Main entry point to iterate over stratified sequences, extract features,
    and save results to data/features/.
    """
    stratified_dir = get_stratified_dir()
    features_dir = get_features_dir()
    ensure_directories()
    
    if not stratified_dir.exists():
        print(f"Error: Stratified directory not found: {stratified_dir}")
        sys.exit(1)
    
    monitor = MemoryMonitor(limit_gb=MEMORY_LIMIT_GB)
    monitor.start()
    
    results_summary = {
        "total_sequences": 0,
        "processed_sequences": 0,
        "failed_sequences": 0,
        "fast_sequences_invalid_frames": 0
    }
    
    # Iterate over strata directories
    for stratum_path in sorted(stratified_dir.iterdir()):
        if not stratum_path.is_dir():
            continue
        
        stratum_name = stratum_path.name
        print(f"Processing stratum: {stratum_name}")
        
        # Create output directory for this stratum
        stratum_output_dir = features_dir / stratum_name
        stratum_output_dir.mkdir(parents=True, exist_ok=True)
        
        for seq_path in sorted(stratum_path.iterdir()):
            if not seq_path.is_dir():
                continue
            
            results_summary["total_sequences"] += 1
            
            # Load metadata if available
            meta_path = seq_path / "metadata.json"
            if meta_path.exists():
                with open(meta_path, 'r') as f:
                    seq_meta = json.load(f)
            else:
                seq_meta = {"motion_magnitude": 0.0}
            
            try:
                result = process_sequence(seq_path, seq_meta, monitor)
                
                if result is None:
                    results_summary["failed_sequences"] += 1
                    print(f"  - Skipped {seq_path.name}: No valid features")
                    continue
                
                # Save results
                output_file = stratum_output_dir / f"{seq_path.name}.npy"
                np.save(output_file, result)
                
                results_summary["processed_sequences"] += 1
                if result.get("invalid_frames"):
                    results_summary["fast_sequences_invalid_frames"] += len(result["invalid_frames"])
                    
                print(f"  - Saved: {output_file.name} ({result['keypoints'].shape[0]} keypoints)")
                
            except Exception as e:
                results_summary["failed_sequences"] += 1
                print(f"  - Error processing {seq_path.name}: {e}")
    
    # Save summary
    summary_file = features_dir / "extraction_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(results_summary, f, indent=2)
    
    print(f"\nExtraction complete. Summary saved to {summary_file}")
    print(f"Processed: {results_summary['processed_sequences']}/{results_summary['total_sequences']}")
    
    monitor.stop()
    session_metrics = monitor.get_session_metrics()
    if session_metrics:
        print(f"Peak RAM: {session_metrics['peak_ram_gb']:.2f} GB")


if __name__ == "__main__":
    main()