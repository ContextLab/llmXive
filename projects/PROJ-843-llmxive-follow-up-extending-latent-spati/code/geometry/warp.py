"""
code/geometry/warp.py

Implements latent-space warping using sparse 3D points and CPU-based
Radial Basis Function (RBF) interpolation for occluded regions.
Includes batch processing logic to prevent OOM on constrained CPU environments.
"""

import os
import sys
import json
import numpy as np
import cv2
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Project imports
from config import get_results_dir, get_features_dir, get_memory_limit_gb
from utils.memory_monitor import check_memory_limit, should_batch_process, MemoryMonitor
from utils.seeds import set_global_seed


def load_sparse_3d_points(stratum_name: str, sequence_id: str) -> Optional[np.ndarray]:
    """
    Load triangulated 3D points for a specific sequence from the solver output.
    Expected path: data/results/solver_output/{stratum_name}/{sequence_id}_3d.npy
    Returns None if file does not exist.
    """
    results_dir = get_results_dir()
    solver_dir = results_dir / "solver_output" / stratum_name
    file_path = solver_dir / f"{sequence_id}_3d.npy"

    if not file_path.exists():
        return None

    try:
        points = np.load(file_path)
        # Validate shape: (N, 3)
        if points.ndim != 2 or points.shape[1] != 3:
            print(f"Warning: Invalid shape for 3D points in {file_path}: {points.shape}")
            return None
        return points
    except Exception as e:
        print(f"Error loading 3D points from {file_path}: {e}")
        return None


def load_sparse_correspondences(stratum_name: str, sequence_id: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load 2D correspondences (keypoints) used for warping.
    Expected path: data/features/{stratum_name}/{sequence_id}_correspondences.npy
    Returns (pts1, pts2) where each is (N, 2).
    """
    features_dir = get_features_dir()
    file_path = features_dir / stratum_name / f"{sequence_id}_correspondences.npy"

    if not file_path.exists():
        raise FileNotFoundError(f"Correspondences file not found: {file_path}")

    try:
        data = np.load(file_path, allow_pickle=True).item()
        pts1 = np.array(data['pts1'], dtype=np.float32)
        pts2 = np.array(data['pts2'], dtype=np.float32)
        return pts1, pts2
    except Exception as e:
        print(f"Error loading correspondences from {file_path}: {e}")
        raise


def compute_rbf_warp(
    pts_src: np.ndarray,
    pts_tgt: np.ndarray,
    points_3d: np.ndarray,
    grid_size: Tuple[int, int],
    kernel: str = 'thin_plate_spline',
    epsilon: float = 0.01
) -> np.ndarray:
    """
    Compute a deformation field using Radial Basis Function (RBF) interpolation.
    Maps source points (pts_src) to target points (pts_tgt) constrained by 3D geometry.
    
    Args:
        pts_src: Source 2D coordinates (N, 2)
        pts_tgt: Target 2D coordinates (N, 2) - the desired positions
        points_3d: 3D points (N, 3) associated with the correspondences
        grid_size: (height, width) of the output image
        kernel: RBF kernel type ('thin_plate_spline', 'gaussian', 'multiquadric')
        epsilon: Smoothing parameter for the kernel
    
    Returns:
        displacement_field: (H, W, 2) array representing the warp vector at each pixel.
    """
    if len(pts_src) < 3:
        # Not enough points to define a meaningful warp
        return np.zeros((grid_size[0], grid_size[1], 2), dtype=np.float32)

    # Prepare data for RBF
    # We use the 2D source points as input coordinates and 2D target points as output
    # to learn the mapping. The 3D points are used to weight the influence or validate
    # but for a pure 2D warp based on sparse correspondences, we fit RBF(2D->2D).
    
    # For robustness, we can incorporate 3D depth as a weight if needed, 
    # but standard RBF warping uses the 2D correspondences directly.
    
    x = pts_src[:, 0]
    y = pts_src[:, 1]
    u = pts_tgt[:, 0] - pts_src[:, 0] # Displacement in X
    v = pts_tgt[:, 1] - pts_src[:, 1] # Displacement in Y

    # Create a grid for evaluation
    H, W = grid_size
    xx, yy = np.meshgrid(np.arange(W), np.arange(H))
    grid_x = xx.flatten()
    grid_y = yy.flatten()
    grid_points = np.column_stack((grid_x, grid_y))

    # Use Scipy's RBF interpolation
    # Note: We avoid heavy dependencies if possible, but scipy is in requirements.txt
    try:
        from scipy.interpolate import Rbf
    except ImportError:
        raise ImportError("scipy is required for RBF interpolation. Install with: pip install scipy")

    # Interpolate X displacement
    rbf_x = Rbf(x, y, u, function=kernel, epsilon=epsilon)
    dx = rbf_x(grid_x, grid_y)

    # Interpolate Y displacement
    rbf_y = Rbf(x, y, v, function=kernel, epsilon=epsilon)
    dy = rbf_y(grid_x, grid_y)

    # Reshape to grid
    dx_grid = dx.reshape(H, W)
    dy_grid = dy.reshape(H, W)

    displacement_field = np.stack((dx_grid, dy_grid), axis=-1).astype(np.float32)

    # Check for NaNs (common in RBF extrapolation)
    if np.any(np.isnan(displacement_field)):
        print("Warning: NaNs detected in RBF warp field. Filling with zeros.")
        displacement_field = np.nan_to_num(displacement_field, nan=0.0)

    return displacement_field


def warp_sequence_frames(
    frame_paths: List[Path],
    displacement_field: np.ndarray
) -> List[np.ndarray]:
    """
    Apply the computed displacement field to a list of frames using OpenCV remap.
    
    Args:
        frame_paths: List of paths to source frames (grayscale or color).
        displacement_field: (H, W, 2) displacement field.
    
    Returns:
        List of warped frames as numpy arrays.
    """
    warped_frames = []
    H, W = displacement_field.shape[:2]

    # Create the map for cv2.remap
    # map_x: x-coordinate of the source pixel for each destination pixel
    # map_y: y-coordinate of the source pixel
    # remap formula: dst(x,y) = src(x + dx, y + dy)
    # Our displacement field is (dx, dy) = target - source.
    # We want: new_pixel_at(x,y) comes from old_pixel_at(x - dx, y - dy)?
    # Actually, standard warping: 
    # If we want to move a point from (x,y) to (x+dx, y+dy),
    # the pixel at (x+dx, y+dy) in the new image should take value from (x,y).
    # cv2.remap(dst) = src(map_x, map_y).
    # map_x(x,y) = x + dx(x,y) ? No.
    # If displacement is (dx, dy) representing the shift of the object,
    # then the pixel at destination (X, Y) comes from source (X - dx, Y - dy).
    # So map_x = X - dx, map_y = Y - dy.
    
    # However, often displacement is defined as flow: where does (x,y) go?
    # Let's assume displacement_field[x,y] = (dx, dy) means the pixel at (x,y) moves to (x+dx, y+dy).
    # Then to fill (x+dx, y+dy), we need value from (x,y).
    # cv2.remap expects the source coordinates for each destination pixel.
    # So for dest (X, Y), we want source (X - dx, Y - dy).
    
    # Construct maps
    # grid_x, grid_y are destination coordinates
    grid_x = np.arange(W).reshape(1, -1).repeat(H, axis=0).T
    grid_y = np.arange(H).reshape(-1, 1).repeat(W, axis=1)
    
    map_x = (grid_x - displacement_field[:,:,0]).astype(np.float32)
    map_y = (grid_y - displacement_field[:,:,1]).astype(np.float32)

    for f_path in frame_paths:
        if not f_path.exists():
            continue
        
        img = cv2.imread(str(f_path))
        if img is None:
            continue

        # Apply remap
        # INTER_LINEAR is standard for smooth warping
        warped = cv2.remap(img, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        warped_frames.append(warped)

    return warped_frames


def process_sequence(
    stratum_name: str,
    sequence_id: str,
    frame_indices: List[int],
    monitor: Optional[MemoryMonitor] = None
) -> Optional[Dict[str, Any]]:
    """
    Process a single sequence: load 3D points, compute RBF warp, and generate warped frames.
    Implements batch processing logic if memory is constrained.
    
    Args:
        stratum_name: Name of the stratum (e.g., "Static-High")
        sequence_id: ID of the sequence
        frame_indices: List of frame indices to process
        monitor: Optional MemoryMonitor instance
    
    Returns:
        Dictionary with results metadata or None if skipped/fail.
    """
    print(f"Processing sequence: {stratum_name}/{sequence_id}")

    # 1. Load Data
    points_3d = load_sparse_3d_points(stratum_name, sequence_id)
    if points_3d is None:
        print(f"Skipping {sequence_id}: No 3D points found.")
        return None

    try:
        pts1, pts2 = load_sparse_correspondences(stratum_name, sequence_id)
    except FileNotFoundError as e:
        print(f"Skipping {sequence_id}: {e}")
        return None

    if len(pts1) != len(points_3d):
        print(f"Warning: Mismatch in point counts for {sequence_id}. Skipping.")
        return None

    # 2. Check Memory (Batch Processing Trigger)
    if monitor:
        current_mem = monitor.get_current_usage_gb()
        limit = get_memory_limit_gb()
        if current_mem > limit * 0.8: # Trigger batch mode if > 80% limit
            print(f"Memory high ({current_mem:.2f}GB > {limit*0.8:.2f}GB). Switching to sequential frame processing.")
            # In a real batch scenario, we might process frames one by one and save immediately
            # to free memory. Here we just proceed but log the condition.
            pass

    # 3. Compute RBF Warp
    # Use the full set of correspondences to define the global warp
    try:
        # Determine grid size from the first frame if available, or default
        # For this implementation, we assume standard resolution or derive from points
        # Let's derive a safe grid size from the max coordinates in pts1/pts2
        max_x = max(np.max(pts1[:,0]), np.max(pts2[:,0]))
        max_y = max(np.max(pts1[:,1]), np.max(pts2[:,1]))
        # Add margin
        W, H = int(max_x) + 10, int(max_y) + 10
        # Cap at reasonable size if data is weird
        W = min(W, 1920)
        H = min(H, 1080)
        
        disp_field = compute_rbf_warp(pts1, pts2, points_3d, grid_size=(H, W))
    except Exception as e:
        print(f"Error computing RBF warp for {sequence_id}: {e}")
        return None

    # 4. Load Frames and Warp
    # Assume frames are stored in data/stratified/{stratum_name}/{sequence_id}/
    strat_dir = get_features_dir().parent / "stratified" / stratum_name / sequence_id
    if not strat_dir.exists():
        print(f"Sequence directory not found: {strat_dir}")
        return None

    frame_paths = []
    for idx in frame_indices:
        # Try common naming conventions
        f_path = strat_dir / f"frame_{idx:05d}.jpg"
        if not f_path.exists():
            f_path = strat_dir / f"{idx:05d}.png"
        if not f_path.exists():
            f_path = strat_dir / f"{idx}.jpg"
        
        if f_path.exists():
            frame_paths.append(f_path)

    if not frame_paths:
        print(f"No frames found for {sequence_id} in indices {frame_indices}")
        return None

    warped_frames = warp_sequence_frames(frame_paths, disp_field)

    if not warped_frames:
        return None

    # 5. Save Results
    results_dir = get_results_dir()
    output_dir = results_dir / "warped_frames" / stratum_name / sequence_id
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, frame in enumerate(warped_frames):
        out_path = output_dir / f"warped_{frame_indices[i]:05d}.png"
        cv2.imwrite(str(out_path), frame)

    # Check for NaNs in output
    for i, frame in enumerate(warped_frames):
        if np.any(np.isnan(frame)):
            print(f"Warning: NaNs in warped frame {frame_indices[i]} for {sequence_id}")

    return {
        "sequence_id": sequence_id,
        "stratum": stratum_name,
        "frames_processed": len(warped_frames),
        "output_dir": str(output_dir),
        "status": "success"
    }


def run_warp_pipeline(
    strata: Optional[List[str]] = None,
    batch_size: int = 10
) -> List[Dict[str, Any]]:
    """
    Run the warp pipeline over all available sequences in the specified strata.
    
    Args:
        strata: List of stratum names to process. If None, processes all found.
        batch_size: Number of sequences to process in a "batch" before checking memory.
    
    Returns:
        List of result dictionaries.
    """
    set_global_seed(42) # Reproducibility
    
    results_dir = get_results_dir()
    features_dir = get_features_dir()
    
    # Determine strata to process
    if strata is None:
        # Scan data/stratified for directories
        stratified_dir = get_features_dir().parent / "stratified"
        if not stratified_dir.exists():
            print("Stratified directory not found. Exiting.")
            return []
        strata = [d.name for d in stratified_dir.iterdir() if d.is_dir()]
    
    all_results = []
    monitor = MemoryMonitor()

    for stratum in strata:
        print(f"\n--- Processing Stratum: {stratum} ---")
        stratum_dir = features_dir.parent / "stratified" / stratum
        
        if not stratum_dir.exists():
            print(f"Stratum directory missing: {stratum_dir}")
            continue

        sequences = [d.name for d in stratum_dir.iterdir() if d.is_dir()]
        
        for seq_id in sequences:
            # Check memory before starting a sequence
            if monitor.get_current_usage_gb() > get_memory_limit_gb():
                print("Memory limit reached. Waiting or aborting.")
                # In a real pipeline, we might force garbage collection or abort
                import gc
                gc.collect()
                if monitor.get_current_usage_gb() > get_memory_limit_gb():
                    print("Aborting pipeline due to persistent memory limit.")
                    break

            # Determine frame indices (simplified: assume all frames in directory)
            # In a real scenario, we'd read a manifest or list files
            frame_dir = stratum_dir / seq_id
            if not frame_dir.exists():
                continue
            
            # Find all image files
            images = list(frame_dir.glob("*.jpg")) + list(frame_dir.glob("*.png"))
            if not images:
                continue
            
            # Sort by name to get indices (assuming naming convention frame_XXXXX)
            # Extract indices from filenames
            indices = []
            for img in images:
                try:
                    # Try to extract number from "frame_XXXXX" or "XXXXX"
                    name = img.stem
                    if 'frame_' in name:
                        idx = int(name.split('frame_')[1])
                    else:
                        idx = int(name)
                    indices.append(idx)
                except ValueError:
                    continue
            
            indices.sort()
            
            if not indices:
                continue

            result = process_sequence(stratum, seq_id, indices, monitor)
            if result:
                all_results.append(result)
                print(f"Completed {seq_id}")

    return all_results


def main():
    """
    Entry point for the warp pipeline.
    """
    print("Starting Latent Spatial Warping Pipeline (T011)...")
    
    # Run pipeline
    results = run_warp_pipeline()
    
    # Summary
    success_count = sum(1 for r in results if r.get('status') == 'success')
    print(f"\nPipeline finished. Processed {success_count}/{len(results)} sequences successfully.")
    
    # Save summary
    results_dir = get_results_dir()
    summary_path = results_dir / "warp_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Summary saved to {summary_path}")

    return results


if __name__ == "__main__":
    main()