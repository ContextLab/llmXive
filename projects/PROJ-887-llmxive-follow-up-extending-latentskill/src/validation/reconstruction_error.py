"""
Reconstruction Error Calculator for LatentSkill Validation.

This module calculates the cosine distance (reconstruction error) between
synthesized LoRA weights and the synthetic ground truth weights generated
in T022g. It implements SC-005 validation logic.

Explicitly uses synthetic weights from T022g as the ground truth for SC-005.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

# Import config for path resolution
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.config import get_project_root, get_results_path, get_data_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Threshold for flagging non-linearity (cosine distance > 0.1 is significant)
RECONSTRUCTION_ERROR_THRESHOLD = 0.1


def load_npz_safe(path: Path) -> Optional[Dict[str, np.ndarray]]:
    """
    Safely load an .npz file and return its contents as a dictionary.

    Args:
        path: Path to the .npz file.

    Returns:
        Dictionary of arrays if successful, None if file not found or corrupted.
    """
    if not path.exists():
        logger.error(f"File not found: {path}")
        return None

    try:
        data = np.load(path, allow_pickle=False)
        return dict(data)
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return None


def cosine_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate the cosine distance between two vectors.

    Cosine distance = 1 - cosine_similarity.
    Handles edge cases where vectors might be zero or NaN.

    Args:
        vec1: First vector (flattened).
        vec2: Second vector (flattened).

    Returns:
        Cosine distance (0.0 to 2.0).
    """
    # Flatten just in case
    v1 = vec1.flatten()
    v2 = vec2.flatten()

    # Handle NaN or Inf
    if np.any(np.isnan(v1)) or np.any(np.isnan(v2)):
        logger.warning("NaN detected in vectors. Returning max distance.")
        return 2.0

    # Handle zero vectors
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 == 0 or norm2 == 0:
        logger.warning("Zero vector detected. Returning max distance.")
        return 2.0

    # Calculate cosine similarity
    similarity = np.dot(v1, v2) / (norm1 * norm2)

    # Clip to [-1, 1] to handle floating point errors
    similarity = np.clip(similarity, -1.0, 1.0)

    return 1.0 - similarity


def calculate_reconstruction_errors(
    synthesized_weights: Dict[str, np.ndarray],
    ground_truth_weights: Dict[str, np.ndarray]
) -> Tuple[float, float, List[Dict[str, Any]]]:
    """
    Calculate cosine distance for each matrix pair and aggregate statistics.

    Args:
        synthesized_weights: Dictionary of synthesized A/B matrices.
        ground_truth_weights: Dictionary of ground truth A/B matrices.

    Returns:
        Tuple of (mean_error, max_error, detailed_results).
    """
    errors = []
    detailed_results = []

    # Expecting keys like 'A', 'B' or specific layer names
    common_keys = set(synthesized_weights.keys()) & set(ground_truth_weights.keys())

    if not common_keys:
        raise ValueError(
            f"No common keys found between synthesized and ground truth weights. "
            f"Synthesized: {list(synthesized_weights.keys())}, "
            f"Ground Truth: {list(ground_truth_weights.keys())}"
        )

    for key in common_keys:
        syn_vec = synthesized_weights[key]
        gt_vec = ground_truth_weights[key]

        # Ensure shapes match
        if syn_vec.shape != gt_vec.shape:
            logger.warning(
                f"Shape mismatch for {key}: synthesized {syn_vec.shape} vs ground truth {gt_vec.shape}. "
                f"Attempting to flatten and compare."
            )
            # Flatten to 1D if shapes differ but total elements match? No, strict check.
            if syn_vec.size != gt_vec.size:
                raise ValueError(
                    f"Total elements mismatch for {key}: {syn_vec.size} vs {gt_vec.size}. "
                    "Cannot calculate error."
                )

        dist = cosine_distance(syn_vec, gt_vec)
        errors.append(dist)

        detailed_results.append({
            "matrix": key,
            "shape": list(syn_vec.shape),
            "cosine_distance": float(dist)
        })

    mean_error = float(np.mean(errors))
    max_error = float(np.max(errors))

    return mean_error, max_error, detailed_results


def save_results(
    mean_error: float,
    max_error: float,
    detailed_results: List[Dict[str, Any]],
    threshold: float,
    output_path: Path
) -> None:
    """
    Save the reconstruction error results to a JSON file.

    Args:
        mean_error: Mean cosine distance.
        max_error: Maximum cosine distance.
        detailed_results: List of per-matrix error details.
        threshold: The threshold used for flagging.
        output_path: Path to save the JSON report.
    """
    flagged = max_error > threshold

    report = {
        "task": "T022d: Reconstruction Error Calculation",
        "ground_truth_source": "data/processed/known_composites_true_weights.npz (from T022g)",
        "synthesized_source": "artifacts/synthesized_adapters/ (from T022b)",
        "threshold": threshold,
        "results": {
            "mean_cosine_distance": mean_error,
            "max_cosine_distance": max_error,
            "flagged_for_non_linearity": flagged,
            "per_matrix_details": detailed_results
        },
        "status": "WARNING" if flagged else "OK"
    }

    if flagged:
        logger.warning(
            f"Maximum deviation ({max_error:.4f}) exceeds threshold ({threshold}). "
            "This indicates potential non-linearity in the skill interpolation space."
        )
    else:
        logger.info(
            f"Reconstruction error within acceptable limits. "
            f"Mean: {mean_error:.4f}, Max: {max_error:.4f}."
        )

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Results saved to {output_path}")


def main() -> int:
    """
    Main entry point for T022d.

    1. Load synthesized weights (from T022b output).
    2. Load ground truth weights (from T022g output).
    3. Calculate errors.
    4. Save results to data/results/reconstruction_error.json.

    Returns:
        0 on success, 1 on failure.
    """
    project_root = get_project_root()

    # Define paths
    # T022b saves to artifacts/synthesized_adapters/ (usually one file per task)
    # For this validation, we assume we are comparing the latest synthesized adapter
    # against the known composite ground truth.
    # In a real pipeline, we would iterate over pairs. Here we assume a 1:1 mapping
    # or a specific pair defined by the test runner.
    # We will load the 'known_composites_true_weights.npz' and compare it against
    # the corresponding synthesized adapter if available, or the most recent one.

    # Let's assume the synthesized adapter for the known composites is saved
    # in artifacts/synthesized_adapters/known_composites_synthesized.npz
    # (This naming convention is assumed based on T022b logic).
    # If T022b saved individual files, we might need to aggregate or pick one.
    # For robustness, we look for the file explicitly mentioned in T022g context.

    synthesized_path = project_root / "artifacts" / "synthesized_adapters" / "known_composites_synthesized.npz"
    ground_truth_path = project_root / "data" / "processed" / "known_composites_true_weights.npz"
    output_path = get_results_path() / "reconstruction_error.json"

    # Check for ground truth
    if not ground_truth_path.exists():
        logger.error(
            f"Ground truth file not found: {ground_truth_path}. "
            "Please ensure T022g has been executed successfully."
        )
        return 1

    # Check for synthesized weights
    if not synthesized_path.exists():
        # Fallback: Look for any npz in the synthesized folder if the specific name is missing
        synthesized_dir = project_root / "artifacts" / "synthesized_adapters"
        if synthesized_dir.exists():
            files = list(synthesized_dir.glob("*.npz"))
            if files:
                synthesized_path = files[0]
                logger.warning(
                    f"Specific synthesized file not found. Using first available: {synthesized_path.name}"
                )
            else:
                logger.error(f"No synthesized weights found in {synthesized_dir}.")
                return 1
        else:
            logger.error(f"Synthesized adapters directory not found: {synthesized_dir}.")
            return 1

    logger.info(f"Loading synthesized weights from: {synthesized_path}")
    syn_data = load_npz_safe(synthesized_path)
    if syn_data is None:
        return 1

    logger.info(f"Loading ground truth weights from: {ground_truth_path}")
    gt_data = load_npz_safe(ground_truth_path)
    if gt_data is None:
        return 1

    try:
        mean_err, max_err, details = calculate_reconstruction_errors(syn_data, gt_data)
        save_results(mean_err, max_err, details, RECONSTRUCTION_ERROR_THRESHOLD, output_path)
        return 0
    except ValueError as e:
        logger.error(f"Calculation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
