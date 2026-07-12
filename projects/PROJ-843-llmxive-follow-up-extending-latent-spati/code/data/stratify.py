import os
import sys
import json
import random
import hashlib
from pathlib import Path
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# Project imports matching API surface
from config import get_stratified_dir, get_raw_dir, get_data_dir, ensure_directories
from utils.seeds import set_global_seed
from utils.memory_monitor import MemoryMonitor, check_memory_limit

# Constants for stratification
NUM_STRATA = 4
MIN_SEQUENCE_PER_STRATUM = 50
MOTION_THRESH_HIGH = 50.0  # Optical flow magnitude threshold
TEXTURE_THRESH_HIGH = 0.5  # Entropy threshold (normalized)

def calculate_optical_flow_magnitude(frames: List[np.ndarray]) -> float:
    """
    Calculate the mean optical flow magnitude between consecutive frames.
    Returns 0.0 if fewer than 2 frames.
    """
    if len(frames) < 2:
        return 0.0
    
    total_magnitude = 0.0
    count = 0
    
    for i in range(len(frames) - 1):
        gray1 = cv2.cvtColor(frames[i], cv2.COLOR_RGB2GRAY)
        gray2 = cv2.cvtColor(frames[i + 1], cv2.COLOR_RGB2GRAY)
        
        # Calculate optical flow
        flow = cv2.calcOpticalFlowFarneback(
            gray1, gray2, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        
        # Calculate magnitude
        magnitude = cv2.magnitude(flow[:, :, 0], flow[:, :, 1])
        mean_magnitude = np.mean(magnitude)
        total_magnitude += mean_magnitude
        count += 1
    
    return total_magnitude / count if count > 0 else 0.0

def calculate_texture_entropy(frames: List[np.ndarray]) -> float:
    """
    Calculate the mean texture entropy across frames.
    Uses histogram-based entropy calculation.
    """
    if not frames:
        return 0.0
    
    total_entropy = 0.0
    count = 0
    
    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        # Calculate histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten()
        # Normalize
        hist = hist / hist.sum()
        # Calculate entropy
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        total_entropy += entropy
        count += 1
    
    # Normalize entropy to [0, 1] range (max entropy for 256 bins is 8)
    return (total_entropy / count) / 8.0 if count > 0 else 0.0

def load_sequence_frames(sequence_path: Path) -> List[np.ndarray]:
    """
    Load all frames from a sequence directory.
    Returns list of RGB frames.
    """
    frames = []
    image_files = sorted(sequence_path.glob("*.jpg")) + sorted(sequence_path.glob("*.png"))
    
    if not image_files:
        return frames
    
    for img_path in image_files:
        frame = cv2.imread(str(img_path))
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame)
    
    return frames

def classify_sequence(frames: List[np.ndarray]) -> Tuple[str, str]:
    """
    Classify a sequence based on motion magnitude and texture entropy.
    Returns (motion_class, texture_class) where each is 'Low' or 'High'.
    """
    motion_mag = calculate_optical_flow_magnitude(frames)
    texture_ent = calculate_texture_entropy(frames)
    
    motion_class = 'Fast' if motion_mag > MOTION_THRESH_HIGH else 'Static'
    texture_class = 'High' if texture_ent > TEXTURE_THRESH_HIGH else 'Low'
    
    return motion_class, texture_class

def stratify_dataset(seed: int = 42) -> Dict[str, List[Path]]:
    """
    Stratify the RealEstate10K dataset into 4 subsets:
    - Static-High, Static-Low, Fast-High, Fast-Low
    
    Returns a dictionary mapping stratum names to lists of sequence paths.
    """
    set_global_seed(seed)
    random.seed(seed)
    
    raw_dir = get_raw_dir()
    stratified_dir = get_stratified_dir()
    ensure_directories()
    
    # Check if raw data exists
    if not raw_dir.exists():
        print(f"Error: Raw data directory not found: {raw_dir}")
        sys.exit(1)
    
    # Collect all sequence directories
    sequences = []
    for seq_dir in raw_dir.iterdir():
        if seq_dir.is_dir():
            # Check if it looks like a sequence (has frames)
            if any(seq_dir.glob("*.*")):
                sequences.append(seq_dir)
    
    if not sequences:
        print("Error: No sequences found in raw data directory")
        sys.exit(1)
    
    print(f"Found {len(sequences)} sequences to stratify")
    
    # Classify each sequence
    strata: Dict[str, List[Path]] = {
        'Static-High': [],
        'Static-Low': [],
        'Fast-High': [],
        'Fast-Low': []
    }
    
    for seq_path in sequences:
        frames = load_sequence_frames(seq_path)
        if len(frames) < 2:
            continue  # Skip sequences with insufficient frames
        
        motion_class, texture_class = classify_sequence(frames)
        stratum_key = f"{motion_class}-{texture_class}"
        strata[stratum_key].append(seq_path)
        
        # Check memory periodically
        if len(strata['Static-High']) % 50 == 0:
            check_memory_limit()
    
    # Validate minimum counts
    for stratum, seqs in strata.items():
        if len(seqs) < MIN_SEQUENCE_PER_STRATUM:
            print(f"ERROR: Stratum '{stratum}' has only {len(seqs)} sequences "
                  f"(minimum required: {MIN_SEQUENCE_PER_STRATUM})")
            print("ABORTING execution as per strict n>=50 enforcement.")
            sys.exit(1)
    
    # Select fixed number per stratum (random selection with seed)
    selected_strata: Dict[str, List[Path]] = {}
    for stratum, seqs in strata.items():
        # Select exactly 50 sequences per stratum if available
        selected_count = min(MIN_SEQUENCE_PER_STRATUM, len(seqs))
        selected = random.sample(seqs, selected_count)
        selected_strata[stratum] = selected
        print(f"Selected {selected_count} sequences for stratum '{stratum}'")
    
    # Save metadata
    metadata = {
        'total_sequences': len(sequences),
        'strata_counts': {k: len(v) for k, v in strata.items()},
        'selected_counts': {k: len(v) for k, v in selected_strata.items()},
        'seed': seed,
        'motion_threshold': MOTION_THRESH_HIGH,
        'texture_threshold': TEXTURE_THRESH_HIGH
    }
    
    metadata_path = stratified_dir / "stratification_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Move sequences to stratified directories
    for stratum, seqs in selected_strata.items():
        stratum_dir = stratified_dir / stratum
        stratum_dir.mkdir(parents=True, exist_ok=True)
        
        for seq_path in seqs:
            # Create symlink or copy (using symlink for efficiency)
            dest = stratum_dir / seq_path.name
            if not dest.exists():
                os.symlink(seq_path, dest)
    
    print(f"Stratification complete. Metadata saved to {metadata_path}")
    return selected_strata

def main():
    """Main entry point for stratification."""
    print("Starting dataset stratification...")
    
    try:
        stratify_dataset(seed=42)
        print("Stratification completed successfully.")
    except Exception as e:
        print(f"Stratification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
