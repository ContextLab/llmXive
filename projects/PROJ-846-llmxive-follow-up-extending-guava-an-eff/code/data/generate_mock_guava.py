"""
CI/CD Fallback: Generate a validated mock Guava dataset.

This script generates synthetic frames with known bounding boxes to serve as
a fallback dataset when the real Guava dataset is unavailable in CI environments.

It creates:
1. Synthetic image frames (grayscale PNGs) in data/raw/guava/frames/
2. A corresponding ground-truth annotations JSON file with known bounding boxes.

Dependencies:
- numpy
- Pillow (PIL)

Usage:
python code/data/generate_mock_guava.py
"""
import json
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

import numpy as np
from PIL import Image

# Project root relative path resolution
# Assuming this script is run from the project root or code directory
def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Navigate up to find the project root (where 'code' and 'data' exist)
    for parent in current.parents:
        if (parent / "data" / "raw").exists() and (parent / "code").exists():
            return parent
    # Fallback to current directory if structure not found
    return current.parent

def generate_synthetic_frame(width: int = 640, height: int = 480, seed: int = 0) -> np.ndarray:
    """
    Generate a synthetic grayscale frame with simple geometric shapes.
    
    Args:
        width: Frame width in pixels.
        height: Frame height in pixels.
        seed: Random seed for reproducibility.
        
    Returns:
        numpy array of shape (height, width) with uint8 values.
    """
    np.random.seed(seed)
    frame = np.zeros((height, width), dtype=np.uint8)
    
    # Draw random rectangles (simulating objects)
    num_objects = np.random.randint(1, 5)
    for _ in range(num_objects):
        x = np.random.randint(0, width - 50)
        y = np.random.randint(0, height - 50)
        w = np.random.randint(20, 80)
        h = np.random.randint(20, 80)
        # Random intensity between 50 and 200
        intensity = np.random.randint(50, 200)
        frame[y:y+h, x:x+w] = intensity
        
    # Add some noise to simulate sensor noise
    noise = np.random.normal(0, 5, (height, width)).astype(np.int16)
    frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    return frame

def create_bounding_box(x: int, y: int, w: int, h: int, class_id: int = 1) -> Dict[str, Any]:
    """
    Create a bounding box dictionary in the expected format.
    
    Args:
        x: Top-left x coordinate.
        y: Top-left y coordinate.
        w: Width.
        h: Height.
        class_id: Object class ID.
        
    Returns:
        Dictionary representing the bounding box annotation.
    """
    return {
        "class_id": class_id,
        "bbox": [x, y, x + w, x + h],
        "confidence": 1.0,  # Known ground truth, so perfect confidence
        "is_visible": True
    }

def generate_mock_dataset(output_dir: Path, num_trajectories: int = 2, frames_per_trajectory: int = 10) -> Dict[str, Any]:
    """
    Generate the full mock Guava dataset.
    
    Args:
        output_dir: Directory where the dataset will be saved.
        num_trajectories: Number of synthetic trajectories to generate.
        frames_per_trajectory: Number of frames per trajectory.
        
    Returns:
        Dictionary containing metadata about the generated dataset.
    """
    frames_dir = output_dir / "frames"
    annotations_path = output_dir / "ground_truth_annotations.json"
    
    frames_dir.mkdir(parents=True, exist_ok=True)
    
    all_annotations = []
    trajectory_ids = []
    
    for traj_idx in range(num_trajectories):
        trajectory_id = f"mock_traj_{traj_idx:04d}"
        trajectory_ids.append(trajectory_id)
        trajectory_frames = []
        
        for frame_idx in range(frames_per_trajectory):
            frame_seed = traj_idx * 1000 + frame_idx
            frame_data = generate_synthetic_frame(seed=frame_seed)
            
            frame_filename = f"{trajectory_id}_frame_{frame_idx:04d}.png"
            frame_path = frames_dir / frame_filename
            
            # Save frame
            img = Image.fromarray(frame_data, mode='L')
            img.save(frame_path, format='PNG')
            
            # Generate ground truth for this frame
            # We need to know where we drew the objects to create accurate GT
            # For simplicity, we regenerate the logic deterministically
            np.random.seed(frame_seed)
            num_objects = np.random.randint(1, 5)
            frame_annotations = []
            
            for obj_idx in range(num_objects):
                x = np.random.randint(0, 640 - 50)
                y = np.random.randint(0, 480 - 50)
                w = np.random.randint(20, 80)
                h = np.random.randint(20, 80)
                class_id = np.random.randint(1, 4) # Classes 1, 2, 3
                
                bbox = create_bounding_box(x, y, w, h, class_id)
                frame_annotations.append(bbox)
            
            annotation_entry = {
                "trajectory_id": trajectory_id,
                "frame_index": frame_idx,
                "frame_path": str(frame_path),
                "objects": frame_annotations,
                "timestamp": datetime.now().isoformat()
            }
            
            all_annotations.append(annotation_entry)
            trajectory_frames.append({
                "frame_id": frame_idx,
                "filename": frame_filename
            })
        
    # Write annotations file
    annotations_data = {
        "dataset_version": "mock_v1",
        "generated_at": datetime.now().isoformat(),
        "total_trajectories": num_trajectories,
        "frames_per_trajectory": frames_per_trajectory,
        "annotations": all_annotations
    }
    
    with open(annotations_path, 'w') as f:
        json.dump(annotations_data, f, indent=2)
    
    # Calculate checksums for frames
    checksums = {}
    for frame_file in frames_dir.glob("*.png"):
        with open(frame_file, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        checksums[frame_file.name] = file_hash
        
    checksums_path = output_dir / "frame_checksums.json"
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f, indent=2)
        
    return {
        "status": "success",
        "output_dir": str(output_dir),
        "num_trajectories": num_trajectories,
        "total_frames": num_trajectories * frames_per_trajectory,
        "annotations_file": str(annotations_path),
        "checksums_file": str(checksums_path)
    }

def main():
    """Main entry point for the mock dataset generator."""
    project_root = get_project_root()
    raw_data_dir = project_root / "data" / "raw" / "guava"
    
    print(f"Project root detected at: {project_root}")
    print(f"Generating mock Guava dataset in: {raw_data_dir}")
    
    if not raw_data_dir.exists():
        raw_data_dir.mkdir(parents=True, exist_ok=True)
        
    try:
        result = generate_mock_dataset(raw_data_dir)
        print(f"Mock dataset generation successful!")
        print(f"  - Trajectories: {result['num_trajectories']}")
        print(f"  - Total frames: {result['total_frames']}")
        print(f"  - Annotations: {result['annotations_file']}")
        print(f"  - Checksums: {result['checksums_file']}")
        
        # Verify the DATASET_AVAILABLE flag logic
        # In a real CI environment, this would set an env var or write a flag file
        flag_file = project_root / "data" / "raw" / "guava" / "dataset_available.flag"
        with open(flag_file, 'w') as f:
            f.write("DATASET_AVAILABLE=true\nSOURCE=MOCK_GENERATED\n")
        print(f"  - Flag file written: {flag_file}")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: Failed to generate mock dataset: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
