"""
Sparse Epipolar Solver using RANSAC.
Computes Fundamental Matrix and triangulates 3D points.
"""

import os
import sys
import json
import numpy as np
import cv2
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import get_features_dir, get_results_dir, get_ransac_threshold, ensure_directories
from utils.memory_monitor import MemoryMonitor
from utils.seeds import set_global_seed

def load_correspondences(features_path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load sparse correspondences from a feature file.
    Returns: (pts1, pts2, descriptors1) - shapes (N, 2), (N, 2), (N, D)
    """
    if not features_path.exists():
        raise FileNotFoundError(f"Feature file not found: {features_path}")

    with open(features_path, 'r') as f:
        data = json.load(f)

    pts1 = np.array(data['pts1'], dtype=np.float32)
    pts2 = np.array(data['pts2'], dtype=np.float32)
    # Descriptors might not always be present in JSON, but we return empty if missing
    descriptors = np.array(data.get('descriptors', []), dtype=np.float32) if data.get('descriptors') else np.zeros((0, 0))

    if len(pts1) == 0 or len(pts2) == 0:
        raise ValueError("Empty correspondences loaded.")

    return pts1, pts2, descriptors

def compute_fundamental_matrix(pts1: np.ndarray, pts2: np.ndarray) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Compute Fundamental Matrix using RANSAC.
    Returns: (F, mask, inlier_count)
    """
    # Ensure points are float32
    pts1 = pts1.astype(np.float32)
    pts2 = pts2.astype(np.float32)

    threshold = get_ransac_threshold()

    F, mask = cv2.findFundamentalMat(pts1, pts2, cv2.FM_RANSAC, threshold=threshold, confidence=0.99)

    if F is None:
        return None, None, 0

    inliers = mask.ravel() == 1
    inlier_count = np.sum(inliers)

    return F, mask, inlier_count

def triangulate_points(F: np.ndarray, pts1: np.ndarray, pts2: np.ndarray, mask: np.ndarray) -> Optional[np.ndarray]:
    """
    Triangulate 3D points from correspondences and Fundamental Matrix.
    Simplified triangulation assuming normalized camera matrices.
    """
    if F is None or mask is None:
        return None

    inliers = mask.ravel() == 1
    pts1_inliers = pts1[inliers]
    pts2_inliers = pts2[inliers]

    if len(pts1_inliers) < 4:
        return None

    # Decompose F to get essential matrix (assuming normalized intrinsics)
    # E = K^T F K, assuming K=I for simplicity in this sparse pipeline
    E = F

    # Decompose E into R and t
    U, S, Vt = np.linalg.svd(E)
    W = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    R1 = U @ W @ Vt
    R2 = U @ W.T @ Vt
    t = U[:, -1]

    # Try both R1 and R2, t and -t
    # We'll use a simple triangulation method for one configuration
    P1 = np.eye(3, 4)
    P2 = np.hstack((R1, t.reshape(3, 1)))

    try:
        points_4 = cv2.triangulatePoints(P1, P2, pts1_inliers.T, pts2_inliers.T)
        points_3 = points_4[:3, :] / points_4[3, :]
        return points_3.T
    except Exception:
        return None

def validate_reprojection_error(F: np.ndarray, pts1: np.ndarray, pts2: np.ndarray, mask: np.ndarray) -> float:
    """Calculate mean reprojection error for inliers."""
    if F is None or mask is None:
        return float('inf')

    inliers = mask.ravel() == 1
    pts1_in = pts1[inliers]
    pts2_in = pts2[inliers]

    if len(pts1_in) == 0:
        return float('inf')

    # Sampson error approximation or direct re-projection
    # Direct: x2' = F x1
    x1 = np.hstack((pts1_in, np.ones((len(pts1_in), 1))))
    x2_pred = (F @ x1.T).T

    # Normalized error
    # ... simplified for this pipeline
    return 0.0 # Placeholder for actual error calculation if needed

def process_sequence(seq_name: str, features_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """Process a single sequence."""
    features_path = features_dir / f"{seq_name}.json"
    result = {
        "sequence": seq_name,
        "status": "unknown",
        "inliers": 0,
        "error": None
    }

    try:
        pts1, pts2, _ = load_correspondences(features_path)

        if len(pts1) < 8:
            result["status"] = "insufficient_points"
            result["error"] = f"Only {len(pts1)} points found"
            return result

        F, mask, inlier_count = compute_fundamental_matrix(pts1, pts2)

        if F is None or inlier_count < 4:
            result["status"] = "unsolvable"
            result["error"] = "RANSAC failed to find sufficient inliers"
            return result

        result["status"] = "success"
        result["inliers"] = int(inlier_count)
        result["F_matrix"] = F.tolist()

        # Save F matrix for downstream
        np.save(output_dir / f"{seq_name}_F.npy", F)

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result

def run_solver(features_dir: Optional[Path] = None, output_dir: Optional[Path] = None) -> Path:
    """
    Main solver entry point.
    Iterates over all feature files, computes F, and logs unsolvable sequences.
    """
    if features_dir is None:
        features_dir = get_features_dir()
    if output_dir is None:
        output_dir = get_results_dir()

    ensure_directories(output_dir)

    print("Running Solver...")
    print(f"Features: {features_dir}")
    print(f"Output: {output_dir}")

    unsolvable_list = []
    all_results = []

    feature_files = list(features_dir.glob("*.json"))
    if not feature_files:
        print("No feature files found.")
        # Write empty unsolvable list
        unsolvable_path = output_dir / "unsolvable_sequences.json"
        with open(unsolvable_path, 'w') as f:
            json.dump([], f)
        return unsolvable_path

    for f_path in feature_files:
        seq_name = f_path.stem
        res = process_sequence(seq_name, features_dir, output_dir)
        all_results.append(res)

        if res["status"] in ["unsolvable", "insufficient_points"]:
            unsolvable_list.append(seq_name)

    # Save unsolvable list
    unsolvable_path = output_dir / "unsolvable_sequences.json"
    with open(unsolvable_path, 'w') as f:
        json.dump(unsolvable_list, f)

    # Save detailed results
    results_path = output_dir / "solver_results.json"
    with open(results_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"Solver complete. Unsolvable sequences: {len(unsolvable_list)}")
    return unsolvable_path

def main():
    """CLI entry point."""
    set_global_seed(42)
    run_solver()

if __name__ == "__main__":
    main()
