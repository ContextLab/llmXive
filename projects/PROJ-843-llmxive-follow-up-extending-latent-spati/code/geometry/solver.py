import os
import sys
import json
import numpy as np
import cv2
from pathlib import Path
from config import (
    get_features_dir,
    get_results_dir,
    ensure_directories,
)
from utils.memory_monitor import should_batch_process

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def load_correspondences(sequence_path: Path):
    """
    Load sparse correspondences for a given sequence.

    Expected file: <sequence_path>/correspondences.npz
    containing two arrays:
        - pts1 : (N, 2) float32 – keypoints in frame 1
        - pts2 : (N, 2) float32 – matching keypoints in frame 2
    """
    corr_file = sequence_path / "correspondences.npz"
    if not corr_file.is_file():
        raise FileNotFoundError(f"Correspondence file not found: {corr_file}")
    data = np.load(corr_file)
    pts1 = data["pts1"]
    pts2 = data["pts2"]
    return pts1, pts2


def compute_fundamental_matrix(pts1: np.ndarray, pts2: np.ndarray):
    """
    Compute the fundamental matrix using RANSAC.
    Returns:
        - F (3x3) or None if estimation fails
        - mask of inliers (Nx1) as returned by cv2.findFundamentalMat
        - number of inliers (int)
    """
    pts1_f = pts1.astype(np.float32)
    pts2_f = pts2.astype(np.float32)

    # RANSAC parameters: 1.0 pixel threshold, confidence 0.99
    F, mask = cv2.findFundamentalMat(
        pts1_f, pts2_f, cv2.FM_RANSAC, 1.0, 0.99
    )
    if F is None or F.shape != (3, 3):
        return None, None, 0

    inlier_count = int(mask.sum()) if mask is not None else 0
    return F, mask, inlier_count


def triangulate_points(
    F: np.ndarray,
    pts1: np.ndarray,
    pts2: np.ndarray,
    mask: np.ndarray,
):
    """
    Triangulate 3‑D points from inlier correspondences.
    Uses cv2.recoverPose to obtain a relative pose (R, t) and then
    cv2.triangulatePoints with canonical projection matrices.
    Returns:
        - pts3d : (N, 3) array of 3‑D points (up to scale)
    """
    # Keep only inliers
    inlier_idx = mask.ravel() == 1
    pts1_in = pts1[inlier_idx].astype(np.float32)
    pts2_in = pts2[inlier_idx].astype(np.float32)

    # Recover relative camera pose
    _, R, t, _ = cv2.recoverPose(F, pts1_in, pts2_in)

    # Projection matrices
    proj1 = np.hstack((np.eye(3), np.zeros((3, 1))))  # [I|0]
    proj2 = np.hstack((R, t))  # [R|t]

    # Triangulate (OpenCV expects points as 2xN)
    pts1_h = pts1_in.T
    pts2_h = pts2_in.T
    pts4d_hom = cv2.triangulatePoints(proj1, proj2, pts1_h, pts2_h)

    # Convert from homogeneous coordinates
    pts3d = pts4d_hom[:3] / pts4d_hom[3]
    return pts3d.T  # shape (N, 3)


def validate_reprojection_error(
    pts3d: np.ndarray,
    R: np.ndarray,
    t: np.ndarray,
    pts1: np.ndarray,
    pts2: np.ndarray,
) -> float:
    """
    Compute the mean reprojection error (in pixel units) for both views.
    Returns the average error across the two cameras.
    """
    # Build projection matrices
    proj1 = np.hstack((np.eye(3), np.zeros((3, 1))))  # [I|0]
    proj2 = np.hstack((R, t))  # [R|t]

    # Convert 3‑D points to homogeneous
    pts3d_h = np.hstack((pts3d, np.ones((pts3d.shape[0], 1)))).T  # 4 x N

    # Project into both cameras
    reproj1_h = proj1 @ pts3d_h
    reproj2_h = proj2 @ pts3d_h

    reproj1 = reproj1_h[:2] / reproj1_h[2]
    reproj2 = reproj2_h[:2] / reproj2_h[2]

    err1 = np.linalg.norm(reproj1.T - pts1, axis=1)
    err2 = np.linalg.norm(reproj2.T - pts2, axis=1)

    mean_err = float(np.mean(np.hstack((err1, err2))))
    return mean_err


# ----------------------------------------------------------------------
# Core processing per sequence
# ----------------------------------------------------------------------


def process_sequence(sequence_path: Path, results_dir: Path, unsolvable_list: list):
    """
    Process a single sequence:
        1. Load correspondences
        2. Estimate fundamental matrix with RANSAC
        3. If estimation fails or not enough inliers → mark unsolvable
        4. Triangulate 3‑D points
        5. Validate reprojection error (threshold = 5.0 px)
        6. Save 3‑D points as <seq_name>_3d.npy in the results directory
    """
    seq_name = sequence_path.name
    try:
        pts1, pts2 = load_correspondences(sequence_path)

        # ------------------------------------------------------------------
        # Fundamental matrix estimation
        # ------------------------------------------------------------------
        F, mask, inlier_cnt = compute_fundamental_matrix(pts1, pts2)
        if F is None or inlier_cnt < 8:
            unsolvable_list.append(seq_name)
            return

        # ------------------------------------------------------------------
        # Pose recovery (needed for reprojection validation)
        # ------------------------------------------------------------------
        inlier_idx = mask.ravel() == 1
        pts1_in = pts1[inlier_idx].astype(np.float32)
        pts2_in = pts2[inlier_idx].astype(np.float32)

        _, R, t, _ = cv2.recoverPose(F, pts1_in, pts2_in)

        # ------------------------------------------------------------------
        # Triangulation
        # ------------------------------------------------------------------
        pts3d = triangulate_points(F, pts1, pts2, mask)

        # ------------------------------------------------------------------
        # Re‑projection validation
        # ------------------------------------------------------------------
        reproj_err = validate_reprojection_error(
            pts3d, R, t, pts1_in, pts2_in
        )
        if reproj_err > 5.0:  # pixel threshold – can be tuned
            unsolvable_list.append(seq_name)
            return

        # ------------------------------------------------------------------
        # Save results
        # ------------------------------------------------------------------
        out_file = results_dir / f"{seq_name}_3d.npy"
        np.save(out_file, pts3d)

    except Exception as exc:
        # Any unexpected error also marks the sequence as unsolvable
        unsolvable_list.append(seq_name)
        print(f"[solver] Failed processing {seq_name}: {exc}", file=sys.stderr)


# ----------------------------------------------------------------------
# Solver orchestration
# ----------------------------------------------------------------------


def run_solver():
    """
    Iterate over all sequences in the features directory and solve each.
    Unsolvable sequences are recorded in
    <results_dir>/unsolvable_sequences.json.
    The function respects the batch‑processing guard from
    utils.memory_monitor.should_batch_process().
    """
    features_dir = Path(get_features_dir())
    results_dir = Path(get_results_dir())
    ensure_directories([results_dir])

    unsolvable_sequences = []

    # Determine processing mode (currently sequential is the safe default)
    batch_mode = should_batch_process()
    if batch_mode:
        print("[solver] Memory limit exceeded – running in batch (sequential) mode.")
    else:
        print("[solver] Sufficient memory – processing sequences sequentially (no parallelism).")

    for seq_path in sorted(features_dir.iterdir()):
        if not seq_path.is_dir():
            continue
        process_sequence(seq_path, results_dir, unsolvable_sequences)

    # Persist unsolvable list
    unsolvable_path = results_dir / "unsolvable_sequences.json"
    with unsolvable_path.open("w") as f:
        json.dump(unsolvable_sequences, f, indent=2)

    print(
        f"[solver] Completed processing. "
        f"Total sequences: {len(list(features_dir.iterdir()))}, "
        f"Unsolvable: {len(unsolvable_sequences)}."
    )


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------


def main():
    """
    CLI entry point. Executes the solver pipeline.
    """
    run_solver()


if __name__ == "__main__":
    main()