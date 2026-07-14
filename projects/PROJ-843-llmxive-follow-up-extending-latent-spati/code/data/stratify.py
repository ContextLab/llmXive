"""
code/data/stratify.py
Implements stratified dataset preparation for RealEstate10K.

Calculates motion magnitude (optical flow) and texture entropy for sequences,
ranks them, and splits into 4 strata (Static/Slow/Fast x High/Low texture).
Enforces n>=50 per stratum or aborts.
"""
import os
import sys
import json
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import cv2
from scipy import stats

# Import project config and utils
from config import (
    get_raw_dir, 
    get_stratified_dir, 
    get_processed_dir, 
    ensure_directories,
    get_config_summary
)
from utils.seeds import set_global_seed
from utils.memory_monitor import MemoryMonitor

# Constants
MIN_STRATUM_SIZE = 50
SEED = 42
MOTION_THRESHOLD_LOW = 0.5   # Placeholder, will be dynamic based on distribution
MOTION_THRESHOLD_HIGH = 0.8  # Placeholder, will be dynamic based on distribution
TEXTURE_THRESHOLD_HIGH = 0.5 # Placeholder, will be dynamic based on distribution

def set_seed(seed: int = SEED):
    """Set global random seeds for reproducibility."""
    set_global_seed(seed)

def calculate_optical_flow_magnitude(frames: List[np.ndarray]) -> float:
    """
    Calculate the average optical flow magnitude across a sequence of frames.
    
    Args:
        frames: List of grayscale numpy arrays (frames).
        
    Returns:
        float: Average magnitude of optical flow.
    """
    if len(frames) < 2:
        return 0.0
    
    magnitudes = []
    prev_gray = frames[0]
    
    for i in range(1, len(frames)):
        curr_gray = frames[i]
        
        # Calculate optical flow using Farneback method
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        
        # Calculate magnitude
        magnitude = cv2.magnitude(flow[:, :, 0], flow[:, :, 1])
        magnitudes.append(np.mean(magnitude))
        
        prev_gray = curr_gray
    
    return float(np.mean(magnitudes)) if magnitudes else 0.0

def calculate_texture_entropy(frames: List[np.ndarray]) -> float:
    """
    Calculate the average texture entropy (GLCM-based) across frames.
    
    Uses skimage.feature.greycomatrix and greycoprops to calculate entropy.
    
    Args:
        frames: List of grayscale numpy arrays (frames).
        
    Returns:
        float: Average texture entropy.
    """
    if not frames:
        return 0.0
    
    try:
        from skimage.feature import greycomatrix, greycoprops
    except ImportError:
        # Fallback to a simpler entropy calculation if skimage is unavailable
        # This is a simplified version using Shannon entropy on histograms
        entropies = []
        for frame in frames:
            # Flatten and compute histogram
            hist, _ = np.histogram(frame.flatten(), bins=256, range=(0, 256))
            hist = hist / hist.sum()
            # Shannon entropy
            entropy = -np.sum(hist * np.log2(hist + 1e-10))
            entropies.append(entropy)
        return float(np.mean(entropies))
    
    entropies = []
    for frame in frames:
        # Compute GLCM
        # distances: [1], angles: [0], levels: 256, symmetric: True, normed: True
        glcm = greycomatrix(frame, distances=[1], angles=[0], levels=256, symmetric=True, normed=True)
        
        # Calculate entropy
        entropy = greycoprops(glcm, 'dissimilarity')[0, 0] # Using dissimilarity as a proxy for texture complexity
        # Actually, greycoprops doesn't have 'entropy'. Let's compute it manually from GLCM
        # Entropy = -sum(p * log(p))
        glcm_flat = glcm.flatten()
        glcm_flat = glcm_flat / glcm_flat.sum()
        entropy = -np.sum(glcm_flat * np.log2(glcm_flat + 1e-10))
        entropies.append(entropy)
    
    return float(np.mean(entropies))

def load_sequence_frames(sequence_path: Path, max_frames: int = 30) -> List[np.ndarray]:
    """
    Load frames from a video sequence directory or file.
    
    Args:
        sequence_path: Path to the sequence directory or video file.
        max_frames: Maximum number of frames to load.
        
    Returns:
        List of grayscale numpy arrays.
    """
    frames = []
    
    # Check if it's a directory with images
    if sequence_path.is_dir():
        image_files = sorted([f for f in sequence_path.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']])
        for img_path in image_files[:max_frames]:
            frame = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
            if frame is not None:
                frames.append(frame)
    else:
        # Assume it's a video file
        cap = cv2.VideoCapture(str(sequence_path))
        count = 0
        while cap.isOpened() and count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frames.append(frame_gray)
            count += 1
        cap.release()
    
    return frames

def classify_sequence(motion: float, texture: float, 
                     motion_thresholds: Tuple[float, float], 
                     texture_threshold: float) -> Tuple[str, str]:
    """
    Classify a sequence based on motion and texture metrics.
    
    Args:
        motion: Calculated motion magnitude.
        texture: Calculated texture entropy.
        motion_thresholds: (low, high) thresholds for motion.
        texture_threshold: Threshold for texture.
        
    Returns:
        Tuple of (motion_class, texture_class) where class is 'Static', 'Slow', 'Fast' or 'Low', 'High'.
    """
    # Motion classification
    if motion < motion_thresholds[0]:
        motion_class = 'Static'
    elif motion < motion_thresholds[1]:
        motion_class = 'Slow'
    else:
        motion_class = 'Fast'
        
    # Texture classification
    if texture < texture_threshold:
        texture_class = 'Low'
    else:
        texture_class = 'High'
        
    return motion_class, texture_class

def stratify_dataset(sequences_dir: Path, output_dir: Path, 
                    strata_size: int = MIN_STRATUM_SIZE) -> Dict[str, Any]:
    """
    Stratify the dataset into 4 subsets based on motion and texture.
    
    Args:
        sequences_dir: Directory containing sequence folders/files.
        output_dir: Directory to save stratified subsets.
        strata_size: Target number of sequences per stratum.
        
    Returns:
        Dictionary with stratification metadata.
    """
    # Ensure output directory exists
    ensure_directories(output_dir)
    
    # Collect all sequences
    sequences = []
    if sequences_dir.is_dir():
        for item in sequences_dir.iterdir():
            if item.is_dir() or (item.is_file() and item.suffix.lower() in ['.mp4', '.avi', '.mov']):
                sequences.append(item)
    
    if not sequences:
        raise ValueError(f"No sequences found in {sequences_dir}")
    
    # Calculate metrics for all sequences
    print(f"Calculating metrics for {len(sequences)} sequences...")
    sequence_metrics = []
    
    for seq_path in sequences:
        try:
            frames = load_sequence_frames(seq_path)
            if len(frames) < 2:
                continue
                
            motion = calculate_optical_flow_magnitude(frames)
            texture = calculate_texture_entropy(frames)
            
            sequence_metrics.append({
                'path': str(seq_path),
                'motion': motion,
                'texture': texture,
                'name': seq_path.name
            })
        except Exception as e:
            print(f"Warning: Failed to process {seq_path}: {e}")
            continue
    
    if not sequence_metrics:
        raise ValueError("No valid sequences found after metric calculation")
    
    # Determine thresholds based on distribution (percentiles)
    motions = [m['motion'] for m in sequence_metrics]
    textures = [m['texture'] for m in sequence_metrics]
    
    # Use percentiles to define thresholds for balanced stratification
    motion_low = np.percentile(motions, 33)
    motion_high = np.percentile(motions, 66)
    texture_thresh = np.percentile(textures, 50)
    
    print(f"Motion thresholds: Low < {motion_low:.4f}, High > {motion_high:.4f}")
    print(f"Texture threshold: Low < {texture_thresh:.4f}, High >= {texture_thresh:.4f}")
    
    # Classify and group sequences
    strata = {
        'Static-High': [],
        'Static-Low': [],
        'Fast-High': [],
        'Fast-Low': []
    }
    
    for metric in sequence_metrics:
        motion_class, texture_class = classify_sequence(
            metric['motion'], metric['texture'],
            (motion_low, motion_high), texture_thresh
        )
        
        # Map to required strata: Static/Slow/Fast x High/Low
        # The task requires 4 specific strata: Static-High, Static-Low, Fast-High, Fast-Low
        # We need to map 'Slow' to either Static or Fast based on proximity, or include it in a broader category
        # For this implementation, we'll map 'Slow' to 'Static' if it's closer to static, or 'Fast' if closer to fast
        # However, the task specifically asks for Static and Fast. Let's re-classify 'Slow' into 'Static' or 'Fast'
        # based on the threshold. Actually, the task description says "Static/Slow/Fast x High/Low texture"
        # but then lists 4 specific strata: Static-High, Static-Low, Fast-High, Fast-Low.
        # This implies we should map 'Slow' to either Static or Fast. Let's map 'Slow' to 'Static' for simplicity,
        # or better, let's re-read the task: "Stratify into subsets (Static-High, Static-Low, Fast-High, Fast-Low)"
        # This suggests we need to group 'Slow' with 'Static' or 'Fast'. Let's map 'Slow' to 'Static' if motion < (low+high)/2, else 'Fast'.
        if motion_class == 'Slow':
            mid_motion = (motion_low + motion_high) / 2
            motion_class = 'Static' if metric['motion'] < mid_motion else 'Fast'
        
        stratum_name = f"{motion_class}-{texture_class}"
        if stratum_name in strata:
            strata[stratum_name].append(metric)
    
    # Check if any stratum has fewer than 50 sequences
    for stratum_name, items in strata.items():
        if len(items) < strata_size:
            print(f"ERROR: Stratum '{stratum_name}' has only {len(items)} sequences (min required: {strata_size})")
            print("ABORTING execution as per strict n>=50 enforcement.")
            sys.exit(1)
    
    # Sort each stratum by motion magnitude (descending) to ensure statistical power
    for stratum_name in strata:
        strata[stratum_name].sort(key=lambda x: x['motion'], reverse=True)
    
    # Select N=50 sequences per stratum using random selection with seed
    set_seed()
    selected_strata = {}
    for stratum_name, items in strata.items():
        if len(items) > strata_size:
            selected = random.sample(items, strata_size)
        else:
            selected = items
        selected_strata[stratum_name] = selected
    
    # Create output directories and copy/move sequences
    metadata = {
        'thresholds': {
            'motion_low': motion_low,
            'motion_high': motion_high,
            'texture': texture_thresh
        },
        'counts': {name: len(items) for name, items in selected_strata.items()},
        'total_sequences': sum(len(items) for items in selected_strata.values())
    }
    
    for stratum_name, items in selected_strata.items():
        stratum_dir = output_dir / stratum_name
        ensure_directories(stratum_dir)
        
        # Save metadata for this stratum
        stratum_metadata = {
            'stratum': stratum_name,
            'sequences': [
                {
                    'name': item['name'],
                    'path': item['path'],
                    'motion': item['motion'],
                    'texture': item['texture']
                }
                for item in items
            ]
        }
        
        with open(stratum_dir / 'metadata.json', 'w') as f:
            json.dump(stratum_metadata, f, indent=2)
        
        # Create symlinks or copy files (using symlinks for efficiency)
        for item in items:
            src_path = Path(item['path'])
            dst_path = stratum_dir / src_path.name
            if not dst_path.exists():
                try:
                    dst_path.symlink_to(src_path.resolve())
                except OSError:
                    # If symlink fails, try copying
                    import shutil
                    if src_path.is_dir():
                        shutil.copytree(src_path, dst_path)
                    else:
                        shutil.copy2(src_path, dst_path)
    
    # Save overall metadata
    with open(output_dir / 'stratification_report.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Stratification complete. Output saved to {output_dir}")
    print(f"Metadata: {json.dumps(metadata, indent=2)}")
    
    return metadata

def main():
    """Main entry point for stratification."""
    print("Starting dataset stratification...")
    
    # Initialize memory monitor
    monitor = MemoryMonitor()
    monitor.start()
    
    try:
        # Get directories
        raw_dir = get_raw_dir()
        stratified_dir = get_stratified_dir()
        
        # Ensure directories exist
        ensure_directories(raw_dir, stratified_dir)
        
        # Check if sequences exist in raw_dir
        sequences_dir = raw_dir / "RealEstate10K" / "train"
        if not sequences_dir.exists():
            # Try alternative path
            sequences_dir = raw_dir / "sequences"
            if not sequences_dir.exists():
                # Look for any subdirectory that might contain sequences
                for item in raw_dir.iterdir():
                    if item.is_dir() and item.name != "stratified" and item.name != "features":
                        sequences_dir = item
                        break
        
        if not sequences_dir.exists():
            raise FileNotFoundError(f"Could not find sequences directory in {raw_dir}")
        
        print(f"Found sequences in: {sequences_dir}")
        
        # Perform stratification
        metadata = stratify_dataset(sequences_dir, stratified_dir, strata_size=MIN_STRATUM_SIZE)
        
        # Log results
        monitor.stop()
        print(f"Peak RAM: {monitor.get_peak_ram_mb():.2f} MB")
        print(f"Wall time: {monitor.get_wall_time():.2f} seconds")
        
        # Save memory log
        log_path = Path("data/results/memory_log.json")
        ensure_directories(log_path.parent)
        with open(log_path, 'w') as f:
            json.dump({
                'task': 'stratify',
                'peak_ram_mb': monitor.get_peak_ram_mb(),
                'wall_time_seconds': monitor.get_wall_time(),
                'timestamp': monitor.get_timestamp()
            }, f)
        
        print("Stratification completed successfully.")
        
    except Exception as e:
        print(f"Error during stratification: {e}")
        monitor.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()