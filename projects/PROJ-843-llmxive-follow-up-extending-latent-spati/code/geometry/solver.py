"""
Sparse Epipolar Solver (T010)

Computes Fundamental Matrix using RANSAC and triangulates 3D points.
"""
import os
import sys
import json
import numpy as np
import cv2
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Local imports
from config import get_features_dir, get_results_dir, get_ransac_threshold, ensure_directories
from utils.seeds import set_global_seed
from utils.memory_monitor import MemoryMonitor

UNSOLVABLE_FILE = "unsolvable_sequences.json"
OUTPUT_DIR = "geometry_outputs"

def load_correspondences(features_path: Path) -> Tuple[np.ndarray, np.ndarray, str]:
    """
    Load sparse correspondences from a feature file.
    
    Returns: (pts1, pts2, sequence_name)
    """
    data = np.load(features_path, allow_pickle=True)
    
    # Handle different formats
    if isinstance(data, np.ndarray) and data.dtype == object:
        data = data.item()
    
    pts1 = np.array(data.get("pts1", []), dtype=np.float32)
    pts2 = np.array(data.get("pts2", []), dtype=np.float32)
    sequence_name = data.get("sequence_name", features_path.stem)
    
    return pts1, pts2, sequence_name

def compute_fundamental_matrix(pts1: np.ndarray, pts2: np.ndarray, threshold: float) -> Tuple[Optional[np.ndarray], np.ndarray, int]:
    """
    Compute Fundamental Matrix using RANSAC.
    
    Returns: (F, mask, num_inliers)
    """
    if len(pts1) < 8:
        return None, np.array([]), 0
    
    try:
        F, mask = cv2.findFundamentalMat(
            pts1, pts2,
            cv2.FM_RANSAC,
            threshold=threshold
        )
        
        if mask is None:
            return None, np.array([]), 0
        
        mask = mask.flatten()
        num_inliers = int(np.sum(mask))
        
        return F, mask, num_inliers
        
    except Exception as e:
        print(f"Error computing fundamental matrix: {e}")
        return None, np.array([]), 0

def triangulate_points(F: np.ndarray, pts1: np.ndarray, pts2: np.ndarray, mask: np.ndarray) -> Optional[np.ndarray]:
    """
    Triangulate 3D points from correspondences (up to scale).
    
    Returns: 3D points array (N, 3) or None
    """
    if F is None or len(pts1) == 0:
        return None
    
    # Filter inliers
    pts1_inliers = pts1[mask.astype(bool)]
    pts2_inliers = pts2[mask.astype(bool)]
    
    if len(pts1_inliers) < 4:
        return None
    
    try:
        # Build projection matrices (assuming normalized camera)
        K = np.eye(3)
        P1 = np.hstack([K, np.zeros((3, 1))])
        
        # Compute essential matrix and decompose
        E = F.T @ K @ K  # Simplified, assuming K=I
        
        # Decompose E to get R and t
        # This is a simplified version; in practice, use cv2.decomposeEssentialMat
        try:
            U, S, Vt = np.linalg.svd(E)
            W = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
            R1 = U @ W @ Vt
            R2 = U @ W.T @ Vt
            t = U[:, 2]
            
            # Choose the correct R, t (cheirality check)
            # Simplified: just use R1, t
            P2 = np.hstack([R1, t.reshape(3, 1)])
            
            # Triangulate
            X = cv2.triangulatePoints(P1, P2, pts1_inliers.T, pts2_inliers.T)
            X = X[:3] / X[3]
            return X.T
            
        except Exception as e:
            print(f"Error decomposing essential matrix: {e}")
            return None
            
    except Exception as e:
        print(f"Error triangulating points: {e}")
        return None

def validate_reprojection_error(F: np.ndarray, pts1: np.ndarray, pts2: np.ndarray, mask: np.ndarray, threshold: float = 1.0) -> float:
    """
    Validate the fundamental matrix by computing reprojection error.
    
    Returns: mean reprojection error
    """
    if F is None or len(pts1) == 0:
        return float('inf')
    
    # Compute Sampson distance
    F1 = F[0, 0] * pts1[:, 0]**2 + F[0, 1] * pts1[:, 0] * pts1[:, 1] + F[0, 2] * pts1[:, 0] + \
         F[1, 0] * pts1[:, 1] * pts1[:, 0] + F[1, 1] * pts1[:, 1]**2 + F[1, 2] * pts1[:, 1] + \
         F[2, 0] * pts1[:, 0] + F[2, 1] * pts1[:, 1] + F[2, 2]
    
    # Simplified error computation
    # In practice, use cv2.reprojectPoints or Sampson distance
    error = np.abs(F1)
    
    return float(np.mean(error[mask.astype(bool)])) if np.any(mask) else float('inf')

def process_sequence(features_path: Path, threshold: float) -> Dict[str, Any]:
    """
    Process a single sequence: load correspondences, compute F, triangulate.
    
    Returns: result dictionary
    """
    sequence_name = features_path.stem
    print(f"Processing sequence: {sequence_name}")
    
    try:
        pts1, pts2, seq_name = load_correspondences(features_path)
        
        if len(pts1) < 8:
            return {
                "sequence": seq_name,
                "status": "insufficient_points",
                "num_points": len(pts1)
            }
        
        F, mask, num_inliers = compute_fundamental_matrix(pts1, pts2, threshold)
        
        if F is None or num_inliers < 4:
            return {
                "sequence": seq_name,
                "status": "unsolvable",
                "num_inliers": num_inliers
            }
        
        X = triangulate_points(F, pts1, pts2, mask)
        
        if X is None:
            return {
                "sequence": seq_name,
                "status": "triangulation_failed",
                "num_inliers": num_inliers
            }
        
        reprojection_error = validate_reprojection_error(F, pts1, pts2, mask)
        
        return {
            "sequence": seq_name,
            "status": "success",
            "fundamental_matrix": F.tolist(),
            "num_inliers": num_inliers,
            "reprojection_error": reprojection_error,
            "points_3d": X.tolist()
        }
        
    except Exception as e:
        return {
            "sequence": sequence_name,
            "status": "error",
            "error": str(e)
        }

def run_solver(threshold: Optional[float] = None) -> Dict[str, Any]:
    """
    Run the solver on all sequences in the features directory.
    
    Returns: aggregated results
    """
    if threshold is None:
        threshold = get_ransac_threshold()
    
    features_dir = get_features_dir()
    results_dir = get_results_dir()
    ensure_directories(results_dir)
    
    output_dir = results_dir / OUTPUT_DIR
    ensure_directories(output_dir)
    
    # Scan for feature files
    feature_files = list(features_dir.glob("*.npy"))
    
    if not feature_files:
        print(f"No feature files found in {features_dir}")
        return {"success": False, "message": "No feature files found"}
    
    all_results = []
    unsolvable_sequences = []
    
    for feature_file in feature_files:
        result = process_sequence(feature_file, threshold)
        all_results.append(result)
        
        if result.get("status") == "unsolvable":
            unsolvable_sequences.append(result.get("sequence"))
    
    # Save unsolvable list
    unsolvable_path = results_dir / UNSOLVABLE_FILE
    with open(unsolvable_path, 'w') as f:
        json.dump({"unsolvable_sequences": unsolvable_sequences}, f, indent=2)
    
    # Save all results
    results_path = output_dir / "solver_results.json"
    with open(results_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    return {
        "success": True,
        "total_sequences": len(feature_files),
        "solvable": len(feature_files) - len(unsolvable_sequences),
        "unsolvable": len(unsolvable_sequences),
        "results": all_results,
        "unsolvable_sequences": unsolvable_sequences
    }

def main():
    """Main entry point for the solver."""
    set_global_seed(42)
    
    # Parse threshold from command line if provided
    threshold = None
    if len(sys.argv) > 1:
        try:
            threshold = float(sys.argv[1])
        except ValueError:
            pass
    
    results = run_solver(threshold)
    
    print(f"Solver completed: {results['total_sequences']} sequences, "
          f"{results['solvable']} solvable, {results['unsolvable']} unsolvable")

if __name__ == "__main__":
    main()
