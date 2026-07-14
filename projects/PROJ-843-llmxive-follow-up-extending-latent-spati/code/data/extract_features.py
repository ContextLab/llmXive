"""
Sparse feature extraction utilities.

Public API:
  * ``load_sequence_frames`` – load image file paths for a sequence.
  * ``extract_sparse_features`` – compute SIFT/ORB keypoints & descriptors.
  * ``is_fast_sequence`` – heuristic to decide whether a sequence is “fast”.
  * ``process_sequence`` – end‑to‑end processing for a single sequence.
  * ``main`` – entry‑point used by the orchestrator.
"""

import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from scipy import stats

# Project imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_stratified_dir, get_features_dir, ensure_directories
from utils.seeds import set_global_seed
from utils.memory_monitor import MemoryMonitor

# Constants
SIFT_MAX_FEATURES = 500
ORB_MAX_FEATURES = 500
TEXTURE_ENTROPY_THRESHOLD = 0.5  # Threshold for low texture detection
FAST_MOTION_THRESHOLD = 15.0     # Motion magnitude threshold for "Fast" classification
BATCH_SIZE = 20                  # Frames to process in memory before saving batch

def calculate_texture_entropy(frame_gray: np.ndarray, block_size: int = 8) -> float:
    """
    Calculate texture entropy using Local Binary Patterns (LBP) as a proxy for GLCM.
    OpenCV does not have a direct GLCM function, so we use LBP histogram entropy.
    """
    if frame_gray.size == 0:
        return 0.0
    
    # Calculate LBP
    lbp = np.zeros_like(frame_gray, dtype=np.uint8)
    h, w = frame_gray.shape
    
    # Simple LBP implementation (center pixel comparison)
    for i in range(1, h-1):
        for j in range(1, w-1):
            center = frame_gray[i, j]
            code = 0
            code |= (frame_gray[i-1, j-1] >= center) << 7
            code |= (frame_gray[i-1, j] >= center) << 6
            code |= (frame_gray[i-1, j+1] >= center) << 5
            code |= (frame_gray[i, j+1] >= center) << 4
            code |= (frame_gray[i+1, j+1] >= center) << 3
            code |= (frame_gray[i+1, j] >= center) << 2
            code |= (frame_gray[i+1, j-1] >= center) << 1
            code |= (frame_gray[i, j-1] >= center) << 0
            lbp[i, j] = code
    
    # Flatten and calculate histogram entropy
    lbp_flat = lbp.flatten()
    hist, _ = np.histogram(lbp_flat, bins=256, range=(0, 256))
    hist = hist[hist > 0]
    prob = hist / hist.sum()
    entropy = -np.sum(prob * np.log2(prob))
    
    return float(entropy)

def load_sequence_frames(sequence_path: Path) -> List[np.ndarray]:
    """Load all frames from a sequence directory."""
    frames = []
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    
    image_files = sorted([
        f for f in sequence_path.iterdir() 
        if f.suffix.lower() in valid_extensions
    ])
    
    for img_path in image_files:
        frame = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if frame is not None:
            frames.append(frame)
        else:
            print(f"Warning: Could not read {img_path}")
    
    return frames

def extract_sparse_features(frame: np.ndarray) -> Tuple[List[cv2.KeyPoint], np.ndarray]:
    """
    Extract SIFT and ORB features from a single frame.
    Returns keypoints and descriptors.
    """
    if frame.size == 0:
        return [], np.array([])
    
    # SIFT
    sift = cv2.SIFT_create(nfeatures=SIFT_MAX_FEATURES)
    kp_sift, des_sift = sift.detectAndCompute(frame, None)
    
    # ORB (fallback if SIFT fails or for variety)
    orb = cv2.ORB_create(nfeatures=ORB_MAX_FEATURES)
    kp_orb, des_orb = orb.detectAndCompute(frame, None)
    
    # Combine features (prioritize SIFT, fallback to ORB)
    if len(kp_sift) > 0:
        return kp_sift, des_sift if des_sift is not None else np.array([])
    elif len(kp_orb) > 0:
        return kp_orb, des_orb if des_orb is not None else np.array([])
    else:
        return [], np.array([])

def is_fast_sequence(sequence_name: str, frames: List[np.ndarray]) -> bool:
    """
    Determine if a sequence is 'Fast' based on optical flow magnitude.
    This is a simplified check; in a full pipeline, we'd use the stratify metadata.
    """
    if len(frames) < 2:
        return False
    
    # Calculate optical flow between first two frames
    prev_gray = frames[0].astype(np.float32)
    curr_gray = frames[1].astype(np.float32)
    
    flow = cv2.calcOpticalFlowFarneback(
        prev_gray, curr_gray, None,
        pyr_scale=0.5, levels=3, winsize=15,
        iterations=3, poly_n=5, poly_sigma=1.2, flags=0
    )
    
    if flow.size == 0:
        return False
    
    magnitude = cv2.cartToPolar(flow[..., 0], flow[..., 1])[0]
    mean_magnitude = np.mean(magnitude)
    
    return mean_magnitude > FAST_MOTION_THRESHOLD

def process_sequence(sequence_path: Path, sequence_name: str, monitor: MemoryMonitor) -> Optional[Dict[str, Any]]:
    """
    Process a single sequence: extract features and save to data/features.
    Returns metadata about the processing.
    """
    frames = load_sequence_frames(sequence_path)
    if not frames:
        return None
    
    # Determine if fast sequence
    fast_motion = is_fast_sequence(sequence_name, frames)
    
    features_data = {
        'sequence_name': sequence_name,
        'is_fast_motion': fast_motion,
        'total_frames': len(frames),
        'feature_results': []
    }
    
    # Batch processing to manage memory
    for i in range(0, len(frames), BATCH_SIZE):
        batch_end = min(i + BATCH_SIZE, len(frames))
        batch_frames = frames[i:batch_end]
        
        for idx, frame in enumerate(batch_frames):
            global_idx = i + idx
            entropy = calculate_texture_entropy(frame)
            
            # Check for low texture
            if entropy < TEXTURE_ENTROPY_THRESHOLD:
                # Mark as invalid due to low texture
                features_data['feature_results'].append({
                    'frame_idx': global_idx,
                    'valid': False,
                    'reason': 'low_texture',
                    'texture_entropy': entropy,
                    'keypoints': [],
                    'descriptors': []
                })
                continue
            
            # Extract features
            kps, des = extract_sparse_features(frame)
            
            # Convert keypoints to serializable format
            kps_serializable = [
                {'pt': [kp.pt[0], kp.pt[1]], 'size': kp.size, 'angle': kp.angle}
                for kp in kps
            ]
            
            # Convert descriptors to list if not empty
            des_serializable = []
            if des is not None and len(des) > 0:
                des_serializable = des.tolist()
            
            # Check feature density for fast sequences
            is_invalid = False
            reason = None
            if fast_motion and len(kps) < 10:
                is_invalid = True
                reason = 'low_feature_density_fast_motion'
            
            features_data['feature_results'].append({
                'frame_idx': global_idx,
                'valid': not is_invalid,
                'reason': reason,
                'texture_entropy': entropy,
                'keypoints': kps_serializable,
                'descriptors': des_serializable
            })
        
        # Monitor memory periodically
        monitor.start()
        monitor.info(f"Processed frames {i}-{batch_end} for {sequence_name}")
    
    return features_data

def main():
    """Main entry point for feature extraction."""
    set_global_seed(42)
    monitor = MemoryMonitor()
    monitor.start()
    
    stratified_dir = get_stratified_dir()
    features_dir = get_features_dir()
    ensure_directories(features_dir)
    
    if not stratified_dir.exists():
        print(f"Error: Stratified directory {stratified_dir} does not exist.")
        print("Please run stratify.py first.")
        sys.exit(1)
    
    print(f"Processing sequences from {stratified_dir}...")
    
    all_results = []
    strata_dirs = [d for d in stratified_dir.iterdir() if d.is_dir()]
    
    for stratum_dir in strata_dirs:
        stratum_name = stratum_dir.name
        print(f"Processing stratum: {stratum_name}")
        
        sequence_dirs = [d for d in stratum_dir.iterdir() if d.is_dir()]
        
        for seq_dir in sequence_dirs:
            seq_name = seq_dir.name
            print(f"  Processing sequence: {seq_name}")
            
            try:
                result = process_sequence(seq_dir, seq_name, monitor)
                if result:
                    all_results.append(result)
                    
                    # Save individual sequence result
                    output_path = features_dir / f"{seq_name}.json"
                    with open(output_path, 'w') as f:
                        json.dump(result, f, indent=2)
                    print(f"    Saved: {output_path}")
            except Exception as e:
                print(f"    Error processing {seq_name}: {e}")
                continue
    
    # Save aggregated results
    aggregated_path = features_dir / "all_features.json"
    with open(aggregated_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nCompleted. Aggregated results saved to {aggregated_path}")
    print(f"Total sequences processed: {len(all_results)}")
    
    monitor.end()
    monitor.log_summary()

    coords = np.array([kp.pt for kp in keypoints], dtype=np.float32)
    return coords, descriptors

# ----------------------------------------------------------------------
def is_fast_sequence(seq_dir: Path) -> bool:
    """
    Very lightweight heuristic: if the number of frames is greater than
    a threshold, we label the sequence as “fast”.  This mirrors the
    specification that fast sequences may have low feature density.
    """
    try:
        frames = load_sequence_frames(seq_dir)
    except FileNotFoundError:
        return False
    return len(frames) > 30  # arbitrary threshold for demo purposes

# ----------------------------------------------------------------------
def process_sequence(seq_dir: Path, out_dir: Path) -> None:
    """
    Extract sparse features for every frame in ``seq_dir`` and store them
    as ``<frame_name>.npz`` under ``out_dir``.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = load_sequence_frames(seq_dir)

    for frame_path in frames:
        coords, descs = extract_sparse_features(frame_path)
        # Store both arrays; downstream code expects ``coords`` and
        # ``descriptors`` keys.
        out_file = out_dir / f"{frame_path.stem}.npz"
        np.savez_compressed(out_file, coords=coords, descriptors=descs)

# ----------------------------------------------------------------------
def main() -> None:
    """
    Orchestrator entry‑point – walks through the stratified dataset and
    extracts features for each sequence.
    """
    stratified_dir: Path = get_stratified_dir()
    features_dir: Path = get_features_dir()

    ensure_directories([features_dir])

    # The stratified directory contains four sub‑folders (the strata).
    for stratum in stratified_dir.iterdir():
        if not stratum.is_dir():
            continue
        for seq in stratum.iterdir():
            if not seq.is_dir():
                continue
            out_seq_dir = features_dir / stratum.name / seq.name
            try:
                process_sequence(seq, out_seq_dir)
            except Exception as exc:
                print(
                    f"[extract_features] Skipping sequence {seq} due to error: {exc}",
                    file=sys.stderr,
                )