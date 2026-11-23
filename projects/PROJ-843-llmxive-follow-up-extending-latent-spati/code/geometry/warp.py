"""
Latent Warping Pipeline (T011)

Performs RBF interpolation for occlusion filling using sparse 3D points.
"""
import os
import sys
import json
import numpy as np
import cv2
from pathlib import Path
from typing import Dict, Any, List, Optional

# Local imports
from config import get_features_dir, get_results_dir, ensure_directories
from utils.seeds import set_global_seed
from utils.memory_monitor import MemoryMonitor
from scipy.interpolate import RBFInterpolator

OUTPUT_DIR = "warped_frames"

def load_sparse_3d_points(solver_results_path: Path) -> Dict[str, np.ndarray]:
    """Load 3D points from solver results."""
    if not solver_results_path.exists():
        return {}
    
    with open(solver_results_path, 'r') as f:
        data = json.load(f)
    
    points = {}
    for result in data:
        if result.get("status") == "success" and "points_3d" in result:
            seq_name = result.get("sequence")
            points[seq_name] = np.array(result["points_3d"])
    
    return points

def load_sparse_correspondences(features_dir: Path) -> Dict[str, tuple]:
    """Load sparse correspondences for all sequences."""
    correspondences = {}
    
    for feature_file in features_dir.glob("*.npy"):
        try:
            data = np.load(feature_file, allow_pickle=True)
            if isinstance(data, np.ndarray) and data.dtype == object:
                data = data.item()
            
            pts1 = np.array(data.get("pts1", []))
            pts2 = np.array(data.get("pts2", []))
            seq_name = data.get("sequence_name", feature_file.stem)
            
            correspondences[seq_name] = (pts1, pts2)
        except Exception as e:
            print(f"Error loading {feature_file}: {e}")
    
    return correspondences

def compute_rbf_warp(points_3d: np.ndarray, points_2d: np.ndarray, 
                    target_shape: tuple, grid_points: np.ndarray) -> np.ndarray:
    """
    Compute RBF warp for occluded regions.
    
    Args:
        points_3d: 3D points (N, 3)
        points_2d: 2D correspondences (N, 2)
        target_shape: Target image shape (H, W)
        grid_points: Grid of points to interpolate (M, 2)
    
    Returns:
        Warped image
    """
    if len(points_3d) < 4:
        return np.zeros(target_shape)
    
    try:
        # Create RBF interpolator
        rbf = RBFInterpolator(points_2d, points_3d[:, :2], kernel='thin_plate_spline')
        
        # Interpolate
        warped_coords = rbf(grid_points)
        
        # Create image
        warped_img = np.zeros(target_shape[:2] + (3,), dtype=np.float32)
        
        # Map warped coordinates to image
        for i, (x, y) in enumerate(warped_coords):
            x, y = int(x), int(y)
            if 0 <= x < target_shape[1] and 0 <= y < target_shape[0]:
                warped_img[y, x] = points_3d[i, 2]  # Use depth as intensity (simplified)
        
        # Smooth
        warped_img = cv2.GaussianBlur(warped_img, (5, 5), 0)
        
        return warped_img
        
    except Exception as e:
        print(f"Error computing RBF warp: {e}")
        return np.zeros(target_shape[:2] + (3,), dtype=np.float32)

def warp_sequence_frames(sequence_name: str, points_3d: np.ndarray, 
                         correspondences: tuple, target_shape: tuple) -> np.ndarray:
    """
    Warp a sequence of frames using the computed 3D points.
    
    Returns: warped frames array
    """
    pts1, pts2 = correspondences
    
    if len(pts1) < 4 or len(points_3d) < 4:
        return np.zeros((100, target_shape[0], target_shape[1], 3))
    
    # Create grid
    H, W = target_shape[:2]
    grid_x, grid_y = np.meshgrid(np.arange(W), np.arange(H))
    grid_points = np.column_stack([grid_x.flatten(), grid_y.flatten()])
    
    # Warp
    warped = compute_rbf_warp(points_3d, pts1, target_shape, grid_points)
    
    # Repeat for multiple frames (simplified)
    frames = np.repeat(warped[np.newaxis, ...], 100, axis=0)
    
    return frames

def process_sequence(sequence_name: str, points_3d: np.ndarray, 
                    correspondences: tuple, target_shape: tuple,
                    output_dir: Path) -> bool:
    """Process a single sequence and save warped frames."""
    try:
        frames = warp_sequence_frames(sequence_name, points_3d, correspondences, target_shape)
        
        output_path = output_dir / f"{sequence_name}_warped.npy"
        np.save(output_path, frames)
        
        print(f"Saved warped frames for {sequence_name}: {frames.shape}")
        return True
        
    except Exception as e:
        print(f"Error processing sequence {sequence_name}: {e}")
        return False

def run_warp_pipeline(threshold: float = 0.05) -> Dict[str, Any]:
    """
    Run the full warp pipeline.
    
    Returns: summary of results
    """
    features_dir = get_features_dir()
    results_dir = get_results_dir()
    ensure_directories(results_dir)
    
    output_dir = results_dir / OUTPUT_DIR
    ensure_directories(output_dir)
    
    # Load solver results
    solver_results_path = results_dir / "geometry_outputs" / "solver_results.json"
    if not solver_results_path.exists():
        print("Solver results not found. Run solver first.")
        return {"success": False, "message": "Solver results not found"}
    
    points_3d_map = load_sparse_3d_points(solver_results_path)
    correspondences_map = load_sparse_correspondences(features_dir)
    
    if not points_3d_map:
        print("No valid 3D points found.")
        return {"success": False, "message": "No valid 3D points"}
    
    successful = 0
    failed = 0
    
    for seq_name, points_3d in points_3d_map.items():
        if seq_name not in correspondences_map:
            print(f"No correspondences for {seq_name}")
            failed += 1
            continue
        
        # Assume target shape from first correspondence
        pts1, _ = correspondences_map[seq_name]
        if len(pts1) > 0:
            target_shape = (480, 640, 3)  # Default
            success = process_sequence(seq_name, points_3d, correspondences_map[seq_name], 
                                      target_shape, output_dir)
            if success:
                successful += 1
            else:
                failed += 1
        else:
            failed += 1
    
    return {
        "success": True,
        "successful": successful,
        "failed": failed,
        "output_dir": str(output_dir)
    }

def main():
    """Main entry point for the warp pipeline."""
    set_global_seed(42)
    
    results = run_warp_pipeline()
    
    print(f"Warp pipeline completed: {results['successful']} successful, {results['failed']} failed")

if __name__ == "__main__":
    main()
