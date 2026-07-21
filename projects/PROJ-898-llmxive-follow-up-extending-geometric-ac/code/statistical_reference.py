"""
Statistical Reference Distribution Module (Task T010b)

Computes statistical reference distribution (mean/covariance) from physics states
and saves to data/raw/gam_reference_stats.json for latent drift detection.
"""
import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

from utils import setup_logging

logger = logging.getLogger(__name__)


def load_physics_states(file_path: str) -> List[Dict[str, Any]]:
    """Load physics states from a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Physics states file not found: {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a list of physics states, got {type(data)}")

    return data


def extract_state_vectors(physics_states: List[Dict[str, Any]]) -> np.ndarray:
    """
    Extract state vectors from physics states.

    Args:
        physics_states: List of physics state dictionaries

    Returns:
        numpy array of shape (n_samples, n_features) containing state vectors
    """
    if not physics_states:
        raise ValueError("Physics states list is empty")

    state_vectors = []
    for state in physics_states:
        if 'state_vector' not in state:
            raise ValueError(f"Missing 'state_vector' in state: {state}")

        vector = state['state_vector']
        if not isinstance(vector, list):
            raise ValueError(f"state_vector must be a list, got {type(vector)}")

        state_vectors.append(vector)

    return np.array(state_vectors)


def compute_statistics(state_vectors: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute mean and covariance of state vectors.

    Args:
        state_vectors: numpy array of shape (n_samples, n_features)

    Returns:
        Tuple of (mean_vector, covariance_matrix)
    """
    if state_vectors.ndim != 2:
        raise ValueError(f"Expected 2D array, got {state_vectors.ndim}D")

    n_samples, n_features = state_vectors.shape

    if n_samples < 2:
        raise ValueError(f"Need at least 2 samples for covariance, got {n_samples}")

    mean = np.mean(state_vectors, axis=0)
    covariance = np.cov(state_vectors, rowvar=False)

    # Handle singular covariance matrix by adding small regularization
    if np.linalg.cond(covariance) > 1e10:
        logger.warning("Covariance matrix is nearly singular. Adding regularization.")
        covariance += np.eye(n_features) * 1e-6

    return mean, covariance


def save_reference_stats(
    mean: np.ndarray,
    covariance: np.ndarray,
    output_path: str
) -> None:
    """
    Save reference statistics to a JSON file.

    Args:
        mean: Mean vector
        covariance: Covariance matrix
        output_path: Path to save the JSON file
    """
    stats = {
        "mean": mean.tolist(),
        "covariance": covariance.tolist(),
        "n_samples": mean.shape[0],
        "n_features": mean.shape[0] if mean.ndim == 1 else mean.shape[1],
        "covariance_shape": list(covariance.shape)
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)

    logger.info(f"Reference statistics saved to {output_path}")


def compute_reference_stats_from_file(
    input_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Load physics states, compute statistics, and save to output file.

    Args:
        input_path: Path to physics states JSON file
        output_path: Path to save reference statistics JSON file

    Returns:
        Dictionary containing computed statistics
    """
    logger.info(f"Loading physics states from {input_path}")
    physics_states = load_physics_states(input_path)
    logger.info(f"Loaded {len(physics_states)} physics states")

    logger.info("Extracting state vectors")
    state_vectors = extract_state_vectors(physics_states)
    logger.info(f"Extracted state vectors of shape {state_vectors.shape}")

    logger.info("Computing statistics")
    mean, covariance = compute_statistics(state_vectors)
    logger.info(f"Mean shape: {mean.shape}, Covariance shape: {covariance.shape}")

    logger.info(f"Saving reference statistics to {output_path}")
    save_reference_stats(mean, covariance, output_path)

    return {
        "mean_shape": list(mean.shape),
        "covariance_shape": list(covariance.shape),
        "n_samples": state_vectors.shape[0],
        "n_features": state_vectors.shape[1]
    }


def main():
    """Main entry point for computing reference statistics."""
    setup_logging()

    input_path = "data/generated/physics_states.json"
    output_path = "data/raw/gam_reference_stats.json"

    logger.info(f"Computing reference statistics from {input_path}")
    logger.info(f"Output will be saved to {output_path}")

    try:
        stats = compute_reference_stats_from_file(input_path, output_path)
        logger.info(f"Successfully computed reference statistics: {stats}")
        return 0
    except Exception as e:
        logger.error(f"Failed to compute reference statistics: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
