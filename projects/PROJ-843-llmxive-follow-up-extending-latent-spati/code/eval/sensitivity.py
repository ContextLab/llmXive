import os
import sys
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple

from config import get_results_dir, get_raw_dir
from eval.metrics import calculate_world_score, calculate_sparse_consistency_score
from geometry.solver import load_correspondences, compute_fundamental_matrix, triangulate_points, validate_reprojection_error
from utils.memory_monitor import MemoryMonitor, check_memory_limit

# RANSAC threshold range for sensitivity analysis
RANSAC_THRESHOLDS = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0]

def load_sequence_correspondences(sequence_id: str, features_dir: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load sparse correspondences (pts1, pts2) for a specific sequence.
    Assumes features are stored as {sequence_id}_correspondences.npy
    """
    file_path = features_dir / f"{sequence_id}_correspondences.npy"
    if not file_path.exists():
        raise FileNotFoundError(f"Correspondences file not found: {file_path}")
    
    data = np.load(file_path, allow_pickle=True).item()
    pts1 = np.array(data['pts1'], dtype=np.float32)
    pts2 = np.array(data['pts2'], dtype=np.float32)
    return pts1, pts2

def run_sensitivity_sweep(
    thresholds: List[float],
    sequences: List[str],
    features_dir: Path,
    results_dir: Path
) -> List[Dict[str, Any]]:
    """
    Sweep RANSAC thresholds and compute WorldScore and Sparse-Consistency Score.
    """
    monitor = MemoryMonitor()
    results = []

    # Load dense baseline frames once (needed for WorldScore calculation)
    baseline_path = results_dir / "dense_baseline_frames.npy"
    if not baseline_path.exists():
        # Fallback to raw dir if results dir doesn't have it
        baseline_path = get_raw_dir() / "dense_baseline_frames.npy"
    
    if baseline_path.exists():
        dense_baseline = np.load(baseline_path, allow_pickle=True)
    else:
        dense_baseline = None
        print("Warning: Dense baseline not found. WorldScore will be computed as 0.0 or skipped.")

    for threshold in thresholds:
        print(f"Sweeping RANSAC threshold: {threshold}")
        
        sequence_scores = []
        
        for seq_id in sequences:
            try:
                # Check memory before processing
                if not check_memory_limit():
                    print("Memory limit reached. Stopping sweep.")
                    break

                # Load correspondences
                pts1, pts2 = load_sequence_correspondences(seq_id, features_dir)
                
                if len(pts1) < 8:
                    # Not enough points for F matrix
                    continue

                # Compute Fundamental Matrix with specific threshold
                F, mask = cv2.findFundamentalMat(
                    pts1, pts2, 
                    cv2.FM_RANSAC, 
                    threshold=threshold, 
                    confidence=0.99, 
                    maxIters=2000
                )

                if F is None or not np.isfinite(F).all():
                    # F matrix computation failed
                    continue

                # Triangulate points (up to scale)
                # This is a simplified triangulation for sensitivity analysis
                # In a full pipeline, camera matrices would be estimated
                try:
                    # Use epipolar geometry to estimate 3D points approximately
                    # For sensitivity analysis, we focus on the consistency of matches
                    # rather than absolute 3D reconstruction
                    K = np.eye(3)  # Simplified intrinsic matrix
                    R1, R2, C1, C2 = np.eye(3), np.eye(3), np.array([0,0,0]), np.array([1,0,0])
                    
                    P1 = np.hstack((R1, C1.reshape(3,1)))
                    P2 = np.hstack((R2, C2.reshape(3,1)))
                    
                    # Triangulate using linear method
                    X = cv2.triangulatePoints(P1, P2, pts1.T, pts2.T)
                    X = X[:3, :] / X[3, :]
                    X = X.T  # Shape: (N, 3)
                    
                    # Validate reprojection error
                    reprojection_error = validate_reprojection_error(pts1, pts2, P1, P2, X)
                    
                    if reprojection_error > 10.0:  # High error threshold
                        continue
                        
                except Exception as e:
                    # Triangulation failed, skip this sequence for this threshold
                    continue

                # Calculate metrics
                # For WorldScore, we need warped frames vs dense baseline
                # For this sensitivity sweep, we simulate the metric calculation
                # based on the quality of the fundamental matrix estimation
                
                # WorldScore proxy: based on reprojection error and inlier count
                inlier_count = np.sum(mask) if mask is not None else 0
                total_points = len(pts1)
                inlier_ratio = inlier_count / total_points if total_points > 0 else 0
                
                # WorldScore calculation (simplified for sensitivity analysis)
                # In full implementation, this would use the actual warped frames
                world_score = calculate_world_score(
                    warped_frames=None,  # Not computed in sweep
                    baseline_frames=dense_baseline,
                    reprojection_error=reprojection_error,
                    inlier_ratio=inlier_ratio
                )
                
                # Sparse-Consistency Score: based on geometric consistency
                sparse_consistency = calculate_sparse_consistency_score(
                    pts1, pts2, F, mask
                )
                
                sequence_scores.append({
                    "sequence_id": seq_id,
                    "threshold": threshold,
                    "world_score": world_score,
                    "sparse_consistency_score": sparse_consistency,
                    "inlier_count": int(inlier_count),
                    "reprojection_error": float(reprojection_error)
                })
                
            except Exception as e:
                print(f"Error processing sequence {seq_id} at threshold {threshold}: {e}")
                continue

        if sequence_scores:
            # Aggregate scores for this threshold
            avg_world_score = np.mean([s["world_score"] for s in sequence_scores])
            avg_sparse_consistency = np.mean([s["sparse_consistency_score"] for s in sequence_scores])
            
            results.append({
                "threshold": threshold,
                "avg_world_score": float(avg_world_score),
                "avg_sparse_consistency_score": float(avg_sparse_consistency),
                "num_sequences": len(sequence_scores),
                "individual_scores": sequence_scores
            })
        else:
            results.append({
                "threshold": threshold,
                "avg_world_score": 0.0,
                "avg_sparse_consistency_score": 0.0,
                "num_sequences": 0,
                "individual_scores": []
            })

    return results

def save_sensitivity_results(results: List[Dict[str, Any]], output_path: Path):
    """Save sensitivity analysis results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Sensitivity results saved to: {output_path}")

def main():
    """Main entry point for sensitivity analysis."""
    print("Starting RANSAC Threshold Sensitivity Analysis...")
    
    # Get directories
    results_dir = get_results_dir()
    features_dir = Path("data/features")
    
    if not features_dir.exists():
        print("Error: data/features directory not found. Please run feature extraction first.")
        sys.exit(1)
    
    # Get list of sequences from features directory
    sequences = []
    for f in features_dir.glob("*_correspondences.npy"):
        seq_id = f.stem.replace("_correspondences", "")
        sequences.append(seq_id)
    
    if not sequences:
        print("Error: No sequences found in data/features. Please run feature extraction first.")
        sys.exit(1)
    
    print(f"Found {len(sequences)} sequences for sensitivity analysis")
    
    # Run sensitivity sweep
    sensitivity_results = run_sensitivity_sweep(
        thresholds=RANSAC_THRESHOLDS,
        sequences=sequences,
        features_dir=features_dir,
        results_dir=results_dir
    )
    
    # Save results
    output_path = results_dir / "sensitivity_analysis.json"
    save_sensitivity_results(sensitivity_results, output_path)
    
    # Print summary
    print("\nSensitivity Analysis Summary:")
    print("-" * 60)
    print(f"{'Threshold':<12} {'WorldScore':<15} {'Sparse-Consistency':<18} {'Sequences':<10}")
    print("-" * 60)
    for res in sensitivity_results:
        print(f"{res['threshold']:<12.1f} {res['avg_world_score']:<15.4f} {res['avg_sparse_consistency_score']:<18.4f} {res['num_sequences']:<10}")
    print("-" * 60)
    
    print("Sensitivity analysis complete.")

if __name__ == "__main__":
    main()