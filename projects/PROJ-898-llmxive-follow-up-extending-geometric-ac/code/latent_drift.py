"""
Latent Drift Detection Module.

Implements Mahalanobis distance-based drift detection for latent vectors.
"""
import logging
import math
import os
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import json

logger = logging.getLogger(__name__)


class LatentDriftDetector:
    """
    Detects distributional drift in latent vectors using Mahalanobis distance.
    """
    def __init__(
        self,
        reference_stats: Dict[str, np.ndarray],
        threshold_percentile: float = 0.99
    ):
        """
        Initialize the drift detector.

        Args:
            reference_stats: Dictionary containing 'mean' and 'cov' of reference distribution.
            threshold_percentile: Percentile for Chi-squared threshold (default 99th).
        """
        self.mean = reference_stats.get("mean")
        self.cov = reference_stats.get("cov")
        self.threshold_percentile = threshold_percentile

        if self.mean is None or self.cov is None:
            raise ValueError("Reference stats must contain 'mean' and 'cov'")

        # Compute threshold
        self.threshold = self._compute_threshold()

    def _compute_threshold(self) -> float:
        """
        Compute the Mahalanobis distance threshold.

        Returns:
            Threshold value (99th percentile of Chi-squared distribution).
        """
        dim = len(self.mean)
        # Chi-squared distribution with dim degrees of freedom
        # Approximate 99th percentile
        from scipy.stats import chi2
        threshold = chi2.ppf(self.threshold_percentile, dim)
        logger.info(f"Computed drift threshold: {threshold:.4f} for dim={dim}")
        return float(threshold)

    def compute_mahalanobis(self, latent_vector: Union[np.ndarray, List[float]]) -> float:
        """
        Compute the Mahalanobis distance of a latent vector from the reference distribution.

        Args:
            latent_vector: Input latent vector.

        Returns:
            Mahalanobis distance.
        """
        latent = np.array(latent_vector)
        diff = latent - self.mean

        # Compute inverse covariance (regularized if needed)
        try:
            cov_inv = np.linalg.inv(self.cov)
        except np.linalg.LinAlgError:
            logger.warning("Covariance matrix is singular, using pseudo-inverse")
            cov_inv = np.linalg.pinv(self.cov)

        # Mahalanobis distance
        mahal_sq = diff @ cov_inv @ diff
        return float(math.sqrt(mahal_sq))

    def is_out_of_distribution(self, latent_vector: Union[np.ndarray, List[float]]) -> bool:
        """
        Check if a latent vector is out-of-distribution.

        Args:
            latent_vector: Input latent vector.

        Returns:
            True if drift is detected, False otherwise.
        """
        distance = self.compute_mahalanobis(latent_vector)
        return distance > self.threshold


def load_reference_stats(path: str) -> Dict[str, np.ndarray]:
    """
    Load reference statistics from a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Dictionary with 'mean' and 'cov' arrays.
    """
    with open(path, 'r') as f:
        data = json.load(f)

    return {
        "mean": np.array(data["latent_stats"]["mean"]),
        "cov": np.array(data["latent_stats"]["cov"])
    }


def compute_reference_stats_from_latents(
    latent_vectors: List[np.ndarray]
) -> Dict[str, np.ndarray]:
    """
    Compute reference statistics from a list of latent vectors.

    Args:
        latent_vectors: List of latent vectors.

    Returns:
        Dictionary with 'mean' and 'cov'.
    """
    matrix = np.array(latent_vectors)
    mean = np.mean(matrix, axis=0)
    cov = np.cov(matrix, rowvar=False)

    return {
        "mean": mean,
        "cov": cov
    }


def main() -> None:
    """
    Main entry point for testing drift detection.
    """
    logging.basicConfig(level=logging.INFO)

    # Create dummy reference stats
    ref_stats = {
        "mean": np.zeros(10),
        "cov": np.eye(10)
    }

    detector = LatentDriftDetector(ref_stats)

    # Test with in-distribution sample
    in_dist = np.random.randn(10)
    is_ood = detector.is_out_of_distribution(in_dist)
    logger.info(f"In-distribution sample OOD: {is_ood}")

    # Test with out-of-distribution sample
    out_dist = np.random.randn(10) * 5 + 10  # Shifted and scaled
    is_ood = detector.is_out_of_distribution(out_dist)
    logger.info(f"Out-distribution sample OOD: {is_ood}")


if __name__ == "__main__":
    main()
