"""
Aggregate warped frames into a single artifact.
Filters out unsolvable sequences and compiles results.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from config import get_results_dir, ensure_directories

def scan_warped_frames(warped_dir: Path) -> List[Path]:
    """Scan for warped frame files."""
    return list(warped_dir.glob("*.png")) + list(warped_dir.glob("*.npy"))

def load_warped_frame(frame_path: Path) -> np.ndarray:
    """Load a single warped frame."""
    if frame_path.suffix == '.png':
        img = cv2.imread(str(frame_path))
        if img is None:
            raise ValueError(f"Could not read image: {frame_path}")
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    elif frame_path.suffix == '.npy':
        return np.load(frame_path)
    else:
        raise ValueError(f"Unsupported format: {frame_path}")

def load_unsolvable_list(unsolvable_path: Path) -> List[str]:
    """Load list of unsolvable sequences."""
    if not unsolvable_path.exists():
        return []
    with open(unsolvable_path, 'r') as f:
        return json.load(f)

def validate_aggregated_data(frames: List[np.ndarray]) -> bool:
    """Validate aggregated data."""
    if not frames:
        return False
    # Check for NaNs
    for i, f in enumerate(frames):
        if np.any(np.isnan(f)):
            print(f"NaN detected in frame {i}")
            return False
    return True

def aggregate_warped_frames(
    warped_frames_dir: Path,
    unsolvable_list: List[str],
    output_path: Path
) -> Path:
    """
    Aggregate warped frames into a single numpy array.
    """
    ensure_directories(output_path.parent)

    # Scan frames
    frame_files = scan_warped_frames(warped_frames_dir)
    if not frame_files:
        raise FileNotFoundError(f"No warped frames found in {warped_frames_dir}")

    # Filter based on unsolvable list?
    # The unsolvable list contains sequence names. We need to map frame names to sequences.
    # Assuming frame names are {seq_name}_warped.png
    valid_frames = []
    valid_sequences = []

    for f_path in frame_files:
        seq_name = f_path.stem.replace("_warped", "")
        if seq_name not in unsolvable_list:
            try:
                frame = load_warped_frame(f_path)
                valid_frames.append(frame)
                valid_sequences.append(seq_name)
            except Exception as e:
                print(f"Skipping {f_path}: {e}")

    if not valid_frames:
        raise ValueError("No valid frames to aggregate after filtering.")

    # Stack frames
    # Ensure all frames are same shape
    shapes = [f.shape for f in valid_frames]
    if len(set(shapes)) > 1:
        # Resize or pad? For now, take the first shape and resize others
        target_shape = shapes[0]
        resized_frames = []
        for f in valid_frames:
            if f.shape != target_shape:
                f = cv2.resize(f, (target_shape[1], target_shape[0]))
            resized_frames.append(f)
        valid_frames = resized_frames

    stacked = np.stack(valid_frames, axis=0)

    # Save
    np.save(output_path, stacked)
    print(f"Aggregated {len(valid_frames)} frames to {output_path}")

    # Save metadata
    metadata = {
        "total_frames": len(valid_frames),
        "sequences": valid_sequences,
        "excluded_sequences": unsolvable_list,
        "shape": list(stacked.shape)
    }
    meta_path = output_path.with_suffix('.json')
    with open(meta_path, 'w') as f:
        json.dump(metadata, f)

    return output_path

def main():
    """CLI entry point."""
    results_dir = get_results_dir()
    unsolvable_path = results_dir / "unsolvable_sequences.json"
    warped_dir = results_dir / "warped_frames"
    output_path = results_dir / "sparse_warped_frames.npy"

    unsolvable_list = load_unsolvable_list(unsolvable_path)
    aggregate_warped_frames(warped_dir, unsolvable_list, output_path)

if __name__ == "__main__":
    main()
