import logging
import math
import os
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from utils import setup_logging

logger = logging.getLogger(__name__)


class LatentDriftDetector:
    """
    Detects latent drift using Mahalanobis distance against a reference distribution.
    
    This module implements out-of-distribution (OOD) detection for the Geometric
    Action Model (GFM) latent space. It computes the Mahalanobis distance between
    incoming latent vectors and a reference distribution (mean and covariance)
    derived from the training data or a baseline set.
    
    If the distance exceeds a configurable threshold, the input is flagged as OOD.
    """

    def __init__(
        self,
        reference_mean: Optional[np.ndarray] = None,
        reference_cov: Optional[np.ndarray] = None,
        threshold: float = 9.21,
        regularization: float = 1e-5,
        log_path: Optional[str] = None,
    ):
        """
        Initialize the drift detector.
        
        Args:
            reference_mean: Mean vector of the reference distribution (latent space).
            reference_cov: Covariance matrix of the reference distribution.
            threshold: Mahalanobis distance threshold for OOD flagging. 
                       Default 9.21 corresponds to p=0.01 for 3 degrees of freedom.
            regularization: Small value added to diagonal of covariance for stability.
            log_path: Optional path to write detailed drift logs.
        """
        self.reference_mean = reference_mean
        self.reference_cov = reference_cov
        self.threshold = threshold
        self.regularization = regularization
        self.log_path = log_path
        self._inverse_cov = None
        self._is_fitted = False

        if log_path:
            self._ensure_log_dir(log_path)

        if reference_mean is not None and reference_cov is not None:
            self._fit(reference_mean, reference_cov)

    @staticmethod
    def _ensure_log_dir(log_path: str) -> None:
        """Ensure the directory for the log file exists."""
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def _fit(self, mean: np.ndarray, cov: np.ndarray) -> None:
        """
        Fit the detector with reference statistics.
        
        Args:
            mean: Reference mean vector.
            cov: Reference covariance matrix.
        """
        if mean.shape[0] != cov.shape[0] or cov.shape[0] != cov.shape[1]:
            raise ValueError(
                f"Mean and covariance dimensions mismatch: "
                f"mean={mean.shape}, cov={cov.shape}"
            )

        self.reference_mean = mean
        self.reference_cov = cov

        # Regularize covariance matrix
        reg_cov = cov + np.eye(cov.shape[0]) * self.regularization

        try:
            self._inverse_cov = np.linalg.inv(reg_cov)
        except np.linalg.LinAlgError as e:
            logger.error(f"Failed to invert covariance matrix: {e}")
            raise ValueError("Covariance matrix is singular or ill-conditioned.") from e

        self._is_fitted = True
        logger.info(
            f"LatentDriftDetector fitted with mean shape {mean.shape}, "
            f"cov shape {cov.shape}, threshold {self.threshold}"
        )

    def compute_mahalanobis(self, latent_vector: np.ndarray) -> float:
        """
        Compute the Mahalanobis distance of a single latent vector.
        
        Args:
            latent_vector: The latent vector to evaluate (1D array).
        
        Returns:
            The Mahalanobis distance (float).
        
        Raises:
            ValueError: If the detector is not fitted or dimensions mismatch.
        """
        if not self._is_fitted:
            raise ValueError(
                "LatentDriftDetector is not fitted. Call fit() or provide "
                "reference_mean and reference_cov during initialization."
            )

        latent_vector = np.asarray(latent_vector).flatten()
        
        if latent_vector.shape[0] != self.reference_mean.shape[0]:
            raise ValueError(
                f"Input dimension {latent_vector.shape[0]} does not match "
                f"reference dimension {self.reference_mean.shape[0]}"
            )

        diff = latent_vector - self.reference_mean
        # Mahalanobis distance: sqrt((x - mu)^T * Sigma^-1 * (x - mu))
        left = np.dot(diff, self._inverse_cov)
        dist_sq = np.dot(left, diff)
        distance = math.sqrt(max(0.0, dist_sq))  # Ensure non-negative due to float errors

        return distance

    def is_out_of_distribution(self, latent_vector: np.ndarray) -> Tuple[bool, float]:
        """
        Check if a latent vector is out-of-distribution.
        
        Args:
            latent_vector: The latent vector to check.
        
        Returns:
            A tuple (is_ood, distance).
        """
        distance = self.compute_mahalanobis(latent_vector)
        is_ood = distance > self.threshold
        
        if is_ood:
            logger.warning(
                f"Out-of-distribution detected! Distance: {distance:.4f} > "
                f"Threshold: {self.threshold}"
            )
            if self.log_path:
                with open(self.log_path, "a") as f:
                    f.write(f"OOD_FLAG, distance={distance:.4f}\n")
        
        return is_ood, distance

    def update_statistics(
        self,
        new_latents: List[np.ndarray],
        batch_weight: float = 0.1
    ) -> None:
        """
        (Optional) Update running statistics with new latent vectors.
        
        This is a simplified online update for demonstration. In a full system,
        one might maintain a running covariance or recompute from a buffer.
        
        Args:
            new_latents: List of new latent vectors observed.
            batch_weight: Weight for the new batch in the update (0.0 to 1.0).
        """
        if not new_latents:
            return

        new_array = np.stack(new_latents, axis=0)
        new_mean = np.mean(new_array, axis=0)
        
        if new_array.shape[0] > 1:
            new_cov = np.cov(new_array, rowvar=False)
            if new_cov.ndim == 0:
                # Handle 1D case if necessary, though cov returns scalar for 1 item
                new_cov = np.array([[new_cov]])
        else:
            # If only one sample, we cannot compute a new covariance reliably
            # Fallback to keeping old covariance or returning
            logger.warning("Cannot update covariance with a single sample.")
            return

        if self.reference_mean is None:
            self._fit(new_mean, new_cov)
            return

        # Weighted update of mean
        alpha = batch_weight
        new_mu = (1 - alpha) * self.reference_mean + alpha * new_mean

        # Weighted update of covariance (simplified)
        # New Cov ~ (1-alpha)*OldCov + alpha*NewCov + alpha*(1-alpha)*(mu_old - mu_new)^2
        diff_mean = self.reference_mean - new_mean
        new_cov_term = (1 - alpha) * self.reference_cov + \
                       alpha * new_cov + \
                       alpha * (1 - alpha) * np.outer(diff_mean, diff_mean)
        
        self._fit(new_mu, new_cov_term)
        logger.info("Updated latent drift statistics with new batch.")


def load_reference_stats(filepath: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load reference mean and covariance from a JSON or NPZ file.
    
    Expected format for JSON: {"mean": [...], "cov": [[...]]}
    Expected format for NPZ: keys 'mean' and 'cov'
    
    Args:
        filepath: Path to the statistics file.
    
    Returns:
        Tuple of (mean, cov) numpy arrays.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid or keys are missing.
    """
    import json

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Reference stats file not found: {filepath}")

    if filepath.endswith(".npz"):
        data = np.load(filepath)
        if "mean" not in data or "cov" not in data:
            raise ValueError("NPZ file must contain 'mean' and 'cov' keys.")
        return data["mean"], data["cov"]
    
    elif filepath.endswith(".json"):
        with open(filepath, "r") as f:
            data = json.load(f)
        
        if "mean" not in data or "cov" not in data:
            raise ValueError("JSON file must contain 'mean' and 'cov' keys.")
        
        return np.array(data["mean"]), np.array(data["cov"])
    
    else:
        raise ValueError(f"Unsupported file format: {filepath}. Use .json or .npz")


def compute_reference_stats_from_latents(
    latents: List[np.ndarray],
    output_path: Optional[str] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute mean and covariance from a list of latent vectors.
    
    Args:
        latents: List of 1D numpy arrays representing latent vectors.
        output_path: Optional path to save the statistics as .npz.
    
    Returns:
        Tuple of (mean, cov).
    """
    if not latents:
        raise ValueError("Cannot compute statistics from an empty list of latents.")
    
    arr = np.stack(latents, axis=0)
    mean = np.mean(arr, axis=0)
    
    if arr.shape[0] > 1:
        cov = np.cov(arr, rowvar=False)
        if cov.ndim == 0:
            cov = np.array([[cov]])
    else:
        # Fallback for single sample: identity matrix scaled by variance estimate
        logger.warning("Only one latent vector provided. Using identity covariance.")
        cov = np.eye(len(mean))
    
    if output_path:
        np.savez(output_path, mean=mean, cov=cov)
        logger.info(f"Saved reference statistics to {output_path}")
    
    return mean, cov


def main():
    """
    Main entry point for testing the Latent Drift Detector.
    
    This function:
    1. Generates synthetic reference latents (simulating training data).
    2. Computes and saves reference statistics.
    3. Loads the detector and tests it on in-distribution and out-of-distribution samples.
    4. Reports the results.
    """
    setup_logging(level=logging.INFO)
    
    # 1. Generate synthetic reference data (simulating training distribution)
    # Assume latent space dimension is 10
    dim = 10
    n_ref = 1000
    np.random.seed(42)
    
    ref_mean = np.random.randn(dim) * 0.5
    ref_cov = np.eye(dim) + np.random.randn(dim, dim) * 0.1
    ref_cov = ref_cov @ ref_cov.T # Make positive definite
    
    ref_data = np.random.multivariate_normal(ref_mean, ref_cov, n_ref)
    
    # 2. Compute and save stats
    stats_path = "data/generated/latent_reference_stats.npz"
    os.makedirs("data/generated", exist_ok=True)
    
    calc_mean, calc_cov = compute_reference_stats_from_latents(list(ref_data), output_path=stats_path)
    
    # 3. Initialize Detector
    detector = LatentDriftDetector(
        reference_mean=calc_mean,
        reference_cov=calc_cov,
        threshold=9.21,
        log_path="data/generated/drift_logs.txt"
    )
    
    # 4. Test on In-Distribution (ID) samples
    id_sample = np.random.multivariate_normal(calc_mean, calc_cov, 1)[0]
    is_ood_id, dist_id = detector.is_out_of_distribution(id_sample)
    print(f"ID Sample Distance: {dist_id:.4f}, Is OOD: {is_ood_id}")
    
    # 5. Test on Out-Of-Distribution (OOD) samples (shifted mean)
    ood_sample = np.random.multivariate_normal(calc_mean + 5.0, calc_cov, 1)[0]
    is_ood_ood, dist_ood = detector.is_out_of_distribution(ood_sample)
    print(f"OOD Sample Distance: {dist_ood:.4f}, Is OOD: {is_ood_ood}")
    
    # 6. Verification
    assert not is_ood_id, "ID sample should not be flagged as OOD"
    assert is_ood_ood, "OOD sample should be flagged as OOD"
    
    print("Latent Drift Detection test PASSED.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())