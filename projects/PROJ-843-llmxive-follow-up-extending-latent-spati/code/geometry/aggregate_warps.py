"""
Aggregate warped frames from the geometry pipeline (T012).

Consumes outputs from the warp pipeline and compiles them into a single artifact.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# Local imports
from config import get_results_dir, get_features_dir, ensure_directories
from utils.seeds import set_global_seed

OUTPUT_FILE = "sparse_warped_frames.npy"
UNSOLVABLE_FILE = "unsolvable_sequences.json"

def scan_warped_frames(warped_dir: Path) -> List[Path]:
    """Scan a directory for warped frame files."""
    if not warped_dir.exists():
        return []
    
    files = []
    for ext in ["*.npy", "*.npz"]:
        files.extend(warped_dir.glob(ext))
    
    return sorted(files)

def load_warped_frame(file_path: Path) -> np.ndarray:
    """Load a warped frame from file."""
    if file_path.suffix == ".npy":
        return np.load(file_path)
    elif file_path.suffix == ".npz":
        data = np.load(file_path)
        # Assume the first key is the frame data
        return data[list(data.keys())[0]]
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

def load_unsolvable_list(results_dir: Path) -> List[str]:
    """Load the list of unsolvable sequences."""
    unsolvable_path = results_dir / UNSOLVABLE_FILE
    
    if not unsolvable_path.exists():
        return []
    
    with open(unsolvable_path, 'r') as f:
        data = json.load(f)
    
    return data.get("unsolvable_sequences", [])

def validate_aggregated_data(frames: np.ndarray) -> Tuple[bool, str]:
    """Validate the aggregated warped frames."""
    if frames is None:
        return False, "No frames loaded"
    
    if len(frames) == 0:
        return False, "Empty frame array"
    
    if not isinstance(frames, np.ndarray):
        return False, f"Expected np.ndarray, got {type(frames)}"
    
    if frames.ndim < 3:
        return False, f"Expected at least 3D array, got {frames.ndim}D"
    
    # Check for NaNs
    if np.any(np.isnan(frames)):
        return False, "Array contains NaN values"
    
    return True, "Valid"

def aggregate_warped_frames(warped_dir: Path, unsolvable_list: List[str]) -> np.ndarray:
    """
    Aggregate all valid warped frames into a single array.
    
    Filters out frames from unsolvable sequences.
    """
    frame_files = scan_warped_frames(warped_dir)
    
    if not frame_files:
        print(f"No warped frame files found in {warped_dir}")
        return np.array([])
    
    all_frames = []
    metadata = []
    
    for file_path in frame_files:
        # Extract sequence name from file path
        sequence_name = file_path.parent.name
        
        # Skip if sequence is unsolvable
        if sequence_name in unsolvable_list:
            print(f"Skipping unsolvable sequence: {sequence_name}")
            continue
        
        try:
            frame = load_warped_frame(file_path)
            all_frames.append(frame)
            metadata.append({
                "file": str(file_path),
                "sequence": sequence_name,
                "shape": frame.shape
            })
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue
    
    if not all_frames:
        return np.array([])
    
    # Stack frames
    try:
        # Ensure all frames have the same shape
        first_shape = all_frames[0].shape
        valid_frames = []
        
        for frame in all_frames:
            if frame.shape == first_shape:
                valid_frames.append(frame)
            else:
                # Resize or pad if necessary (simplified: skip mismatched)
                print(f"Skipping frame with mismatched shape: {frame.shape} vs {first_shape}")
        
        if not valid_frames:
            return np.array([])
        
        return np.stack(valid_frames, axis=0)
        
    except Exception as e:
        print(f"Error stacking frames: {e}")
        return np.array([])

def main():
    """Main entry point for aggregating warped frames."""
    set_global_seed(42)
    
    results_dir = get_results_dir()
    features_dir = get_features_dir()
    ensure_directories(results_dir)
    
    # Determine warped frames directory
    # This depends on the output of the warp pipeline
    warped_dir = features_dir / "warped"  # Adjust based on actual output location
    
    if not warped_dir.exists():
        # Try alternative location
        warped_dir = results_dir / "warped"
    
    if not warped_dir.exists():
        print(f"Warped frames directory not found: {warped_dir}")
        # Create empty output
        output_path = results_dir / OUTPUT_FILE
        np.save(output_path, np.array([]))
        print(f"Saved empty warped frames to {output_path}")
        return
    
    # Load unsolvable list
    unsolvable_list = load_unsolvable_list(results_dir)
    print(f"Found {len(unsolvable_list)} unsolvable sequences")
    
    # Aggregate frames
    aggregated = aggregate_warped_frames(warped_dir, unsolvable_list)
    
    # Validate
    is_valid, message = validate_aggregated_data(aggregated)
    print(f"Validation: {message}")
    
    # Save
    output_path = results_dir / OUTPUT_FILE
    np.save(output_path, aggregated)
    print(f"Saved {len(aggregated)} frames to {output_path}")

if __name__ == "__main__":
    main()