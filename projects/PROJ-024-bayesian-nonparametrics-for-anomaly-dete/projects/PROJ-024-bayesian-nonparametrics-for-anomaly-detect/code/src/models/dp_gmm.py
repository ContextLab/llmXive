"""DPGMM Model with ADVI Variational Inference and ELBO Logging.

Implements Dirichlet Process Gaussian Mixture Model for anomaly detection
in time series data with streaming posterior updates.

Key Features:
- Nonparametric clustering via Dirichlet Process prior
- ADVI (Automatic Differentiation Variational Inference)
- Streaming updates for online anomaly detection
- ELBO convergence logging (Constitution Principle VI)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
import logging
from datetime import datetime
from pathlib import Path

from ..utils.elbo_logger import ELBOLogger, ELBOHistory, create_elbo_logger

logger = logging.getLogger(__name__)


@dataclass
class DPGMMConfig:
    """Configuration for DPGMM model.

    Attributes:
        alpha: Dirichlet process concentration parameter.
        n_components: Initial number of components (used as hint).
        mean_prior: Prior mean for component means.
        cov_prior: Prior covariance for component covariances.
        convergence_threshold: ELBO convergence threshold.
        max_iterations: Maximum training iterations.
        min_iterations: Minimum iterations before convergence check.
        random_seed: Random seed for reproducibility.
        log_dir: Directory for ELBO convergence logs.
    """
    alpha: float = 1.0
    n_components: int = 10
    mean_prior: Tuple[float, float] = (0.0, 1.0)
    cov_prior: Tuple[float, float] = (1.0, 1e-3)
    convergence_threshold: float = 1e-3
    max_iterations: int = 1000
    min_iterations: int = 10
    random_seed: int = 42
    log_dir: Optional[str] = None


@dataclass
class ClusterAnomalyResult:
    """Result from cluster-based anomaly detection.

    Attributes:
        cluster_id: Assigned cluster ID.
        anomaly_score: Anomaly score for the observation.
        is_anomaly: Boolean flag if observation is anomalous.
        cluster_size: Number of points in assigned cluster.
        posterior_weight: Posterior weight for assigned cluster.
    """
    cluster_id: int
    anomaly_score: float
    is_anomaly: bool
    cluster_size: int
    posterior_weight: float


class DPGMMModel:
    """Dirichlet Process Gaussian Mixture Model for anomaly detection.

    Implements:
    - Variational inference with ADVI
    - Streaming posterior updates
    - ELBO convergence tracking and logging
    - Anomaly scoring based on cluster assignments
    """

    def __init__(
        self,
        config: Optional[DPGMMConfig] = None,
        run_id: Optional[str] = None
    ):
        """Initialize DPGMM model.

        Args:
            config: Model configuration. Uses defaults if None.
            run_id: Unique identifier for this training run (for logging).
        """
        self.config = config or DPGMMConfig()
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")

        # Set random seed
        np.random.seed(self.config.random_seed)

        # Initialize ELBO logger
        log_dir = (
            Path(self.config.log_dir)
            if self.config.log_dir
            else Path("logs/elbo")
        )
        self.elbo_logger = ELBOLogger(
            log_dir=log_dir,
            run_id=self.run_id,
            convergence_threshold=self.config.convergence_threshold,
            min_iterations=self.config.min_iterations,
            max_iterations=self.config.max_iterations
        )

        # Model parameters (initialized lazily)
        self._initialized = False
        self._n_components = 0
        self._means: Optional[np.ndarray] = None
        self._covariances: Optional[np.ndarray] = None
        self._weights: Optional[np.ndarray] = None
        self._alpha: Optional[float] = None

        # Training state
        self._n_samples = 0
        self._current_iteration = 0
        self._elbo_history: List[float] = []

    def _initialize_params(self, X: np.ndarray) -> None:
        """Initialize model parameters from data.

        Args:
            X: Data array of shape (n_samples, n_features).
        """
        n_samples, n_features = X.shape

        # Initialize with k-means-like strategy
        self._n_components = min(self.config.n_components, n_samples)

        # Initialize means using random data points
        indices = np.random.choice(n_samples, self._n_components, replace=False)
        self._means = X[indices].copy()

        # Initialize covariances as identity
        self._covariances = np.array(
            [np.eye(n_features) * self.config.cov_prior[0]
             for _ in range(self._n_components)]
        )

        # Initialize weights uniformly
        self._weights = np.ones(self._n_components) / self._n_components

        # Initialize concentration parameter
        self._alpha = self.config.alpha

        self._initialized = True
        logger.info(
            f"Initialized DPGMM with {self._n_components} components, "
            f"alpha={self._alpha:.4f}"
        )

    def _e_step(self, X: np.ndarray) -> np.ndarray:
        """E-step: compute posterior responsibilities.

        Args:
            X: Data array of shape (n_samples, n_features).

        Returns:
            Responsibilities matrix of shape (n_samples, n_components).
        """
        n_samples = X.shape[0]
        responsibilities = np.zeros((n_samples, self._n_components))

        for k in range(self._n_components):
            # Compute Mahalanobis distance
            diff = X - self._means[k]
            inv_cov = np.linalg.inv(self._covariances[k])
            mahal_dist = np.sum(diff @ inv_cov * diff, axis=1)

            # Compute log probability
            log_prob = (
                -0.5 * n_samples * np.log(2 * np.pi)
                - 0.5 * np.log(np.linalg.det(self._covariances[k]))
                - 0.5 * mahal_dist
            )

            # Add log weight
            log_prob += np.log(self._weights[k] + 1e-300)
            responsibilities[:, k] = log_prob

        # Normalize (log-sum-exp trick)
        log_sum = np.max(responsibilities, axis=1, keepdims=True)
        responsibilities = np.exp(responsibilities - log_sum)
        responsibilities /= responsibilities.sum(axis=1, keepdims=True) + 1e-300

        return responsibilities

    def _m_step(self, X: np.ndarray, responsibilities: np.ndarray) -> float:
        """M-step: update model parameters.

        Args:
            X: Data array of shape (n_samples, n_features).
            responsibilities: Responsibilities matrix.

        Returns:
            ELBO value for this iteration.
        """
        n_samples, n_features = X.shape

        # Effective number of points per cluster
        n_k = responsibilities.sum(axis=0) + 1e-300

        # Update weights
        self._weights = n_k / n_samples

        # Update means
        for k in range(self._n_components):
            self._means[k] = (responsibilities[:, k:k+1].T @ X) / n_k[k]

        # Update covariances
        for k in range(self._n_components):
            diff = X - self._means[k]
            weighted_diff = responsibilities[:, k:k+1] * diff
            self._covariances[k] = (
                weighted_diff.T @ diff / n_k[k]
            ) + np.eye(n_features) * self.config.cov_prior[1]

        # Update concentration parameter (variational)
        self._alpha = max(
            self.config.alpha,
            self._n_components * (n_k.sum() / n_samples)
        )

        # Compute ELBO
        elbo = self._compute_elbo(X, responsibilities)
        return elbo

    def _compute_elbo(self, X: np.ndarray, responsibilities: np.ndarray) -> float:
        """Compute Evidence Lower Bound (ELBO).

        Args:
            X: Data array of shape (n_samples, n_features).
            responsibilities: Responsibilities matrix.

        Returns:
            ELBO value.
        """
        n_samples, n_features = X.shape

        # Expected log likelihood
        ll = 0.0
        for k in range(self._n_components):
            diff = X - self._means[k]
            inv_cov = np.linalg.inv(self._covariances[k])
            mahal = np.sum(diff @ inv_cov * diff, axis=1)

            log_p = (
                -0.5 * n_features * np.log(2 * np.pi)
                - 0.5 * np.log(np.linalg.det(self._covariances[k]))
                - 0.5 * mahal
            )
            ll += np.sum(responsibilities[:, k] * log_p)

        # Expected log prior (simplified)
        log_prior = -0.5 * self._alpha * self._n_components

        # Entropy term
        entropy = -np.sum(
            responsibilities * np.log(responsibilities + 1e-300)
        )

        elbo = ll + log_prior + entropy
        return float(elbo)

    def fit(self, X: np.ndarray, verbose: bool = True) -> 'DPGMMModel':
        """Fit DPGMM model using variational inference.

        Args:
            X: Training data of shape (n_samples, n_features).
            verbose: Whether to log progress.

        Returns:
            Self for method chaining.
        """
        if verbose:
            logger.info(f"Starting DPGMM training on {X.shape[0]} samples")

        # Initialize parameters
        self._initialize_params(X)

        # Training loop
        for iteration in range(self.config.max_iterations):
            self._current_iteration = iteration

            # E-step
            responsibilities = self._e_step(X)

            # M-step
            elbo = self._m_step(X, responsibilities)

            # Log ELBO
            log_result = self.elbo_logger.log_iteration(iteration, elbo)

            if verbose and iteration % 50 == 0:
                logger.info(
                    f"Iter {iteration}: ELBO={elbo:.4f}, "
                    f"components={self._n_components}"
                )

            # Check convergence
            if log_result['should_stop']:
                if verbose:
                    logger.info(
                        f"Training converged at iteration {iteration}"
                    )
                break

        # Save ELBO history
        self.elbo_logger.save()
        self.elbo_logger.save_csv()

        self._n_samples = X.shape[0]

        if verbose:
            logger.info(f"Training complete. Final ELBO: {elbo:.4f}")

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict cluster assignments for new data.

        Args:
            X: Data of shape (n_samples, n_features).

        Returns:
            Cluster assignments of shape (n_samples,).
        """
        if not self._initialized:
            raise RuntimeError("Model must be fitted before prediction")

        responsibilities = self._e_step(X)
        return np.argmax(responsibilities, axis=1)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Compute log-likelihood scores for samples.

        Args:
            X: Data of shape (n_samples, n_features).

        Returns:
            Log-likelihood scores of shape (n_samples,).
        """
        if not self._initialized:
            raise RuntimeError("Model must be fitted before scoring")

        n_samples = X.shape[0]
        scores = np.zeros(n_samples)

        for k in range(self._n_components):
            diff = X - self._means[k]
            inv_cov = np.linalg.inv(self._covariances[k])
            mahal = np.sum(diff @ inv_cov * diff, axis=1)

            log_prob = (
                np.log(self._weights[k] + 1e-300)
                - 0.5 * np.log(np.linalg.det(self._covariances[k]))
                - 0.5 * mahal
            )

            # Max over components (approximate log-likelihood)
            if k == 0:
                scores = log_prob
            else:
                scores = np.maximum(scores, log_prob)

        return scores

    def compute_anomaly_score(self, x: np.ndarray) -> float:
        """Compute anomaly score for a single observation.

        Args:
            x: Observation of shape (n_features,).

        Returns:
            Anomaly score (higher = more anomalous).
        """
        if not self._initialized:
            raise RuntimeError("Model must be fitted before scoring")

        x = np.atleast_1d(x)

        # Compute likelihood under each component
        scores = []
        for k in range(self._n_components):
            diff = x - self._means[k]
            inv_cov = np.linalg.inv(self._covariances[k])
            mahal = np.sum(diff @ inv_cov * diff)

            log_prob = (
                np.log(self._weights[k] + 1e-300)
                - 0.5 * np.log(np.linalg.det(self._covariances[k]))
                - 0.5 * mahal
            )
            scores.append(log_prob)

        # Anomaly score is negative max log-likelihood
        return -max(scores)

    def update_streaming(self, x: np.ndarray) -> ClusterAnomalyResult:
        """Update model with a single streaming observation.

        Args:
            x: New observation of shape (n_features,).

        Returns:
            ClusterAnomalyResult with assignment and anomaly score.
        """
        if not self._initialized:
            raise RuntimeError("Model must be fitted before streaming updates")

        x = np.atleast_1d(x)

        # Compute responsibilities
        resp = self._e_step(x.reshape(1, -1))[0]
        cluster_id = np.argmax(resp)

        # Compute anomaly score
        anomaly_score = self.compute_anomaly_score(x)

        # Update model incrementally (simplified)
        self._n_samples += 1
        update_weight = 1.0 / self._n_samples

        # Incremental mean update
        self._means[cluster_id] = (
            self._means[cluster_id] + update_weight * (x - self._means[cluster_id])
        )

        # Incremental covariance update (simplified)
        diff = x - self._means[cluster_id]
        self._covariances[cluster_id] = (
            self._covariances[cluster_id] + update_weight * np.outer(diff, diff)
        )

        # Update weight
        self._weights[cluster_id] += update_weight
        self._weights /= self._weights.sum()

        return ClusterAnomalyResult(
            cluster_id=int(cluster_id),
            anomaly_score=float(anomaly_score),
            is_anomaly=anomaly_score > 3.0,  # Threshold heuristic
            cluster_size=int(self._n_samples * self._weights[cluster_id]),
            posterior_weight=float(resp[cluster_id])
        )

    def get_elbo_history(self) -> ELBOHistory:
        """Get ELBO convergence history.

        Returns:
            ELBOHistory instance with all logged values.
        """
        return self.elbo_logger.get_history()

    def save_elbo_logs(self) -> Tuple[Path, Path]:
        """Save ELBO logs to JSON and CSV.

        Returns:
            Tuple of (JSON path, CSV path).
        """
        json_path = self.elbo_logger.save()
        csv_path = self.elbo_logger.save_csv()
        return json_path, csv_path

    def get_convergence_status(self) -> Dict[str, Any]:
        """Get model convergence status.

        Returns:
            Dict with convergence information.
        """
        return {
            "converged": self.elbo_logger._converged,
            "convergence_iteration": self.elbo_logger._convergence_iteration,
            "final_elbo": self.elbo_logger.history.final_elbo,
            "total_iterations": self.elbo_logger.history.iteration_counts[-1]
            if self.elbo_logger.history.iteration_counts else 0,
            "n_components": self._n_components,
            "n_samples": self._n_samples
        }


def compute_anomaly_score(model: DPGMMModel, x: np.ndarray) -> float:
    """Compute anomaly score using DPGMM model.

    Args:
        model: Fitted DPGMMModel instance.
        x: Observation of shape (n_features,).

    Returns:
        Anomaly score.
    """
    return model.compute_anomaly_score(x)


def compute_anomaly_scores_batch(
    model: DPGMMModel,
    X: np.ndarray,
    threshold: float = 3.0
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute anomaly scores for batch of observations.

    Args:
        model: Fitted DPGMMModel instance.
        X: Observations of shape (n_samples, n_features).
        threshold: Anomaly threshold.

    Returns:
        Tuple of (scores, is_anomaly flags).
    """
    scores = np.array([model.compute_anomaly_score(x) for x in X])
    is_anomaly = scores > threshold
    return scores, is_anomaly


def main():
    """Demo/test of DPGMM model with ELBO logging."""
    import sys

    # Generate synthetic data
    np.random.seed(42)
    n_samples = 1000
    n_features = 2

    # Create clusters
    X1 = np.random.randn(n_samples // 3, n_features)
    X2 = np.random.randn(n_samples // 3, n_features) + 3
    X3 = np.random.randn(n_samples // 3, n_features) - 3
    X = np.vstack([X1, X2, X3])

    # Add anomalies
    anomalies = np.random.randn(50, n_features) * 2 + 10
    X = np.vstack([X, anomalies])

    # Create and fit model
    config = DPGMMConfig(
        max_iterations=200,
        convergence_threshold=1e-3,
        log_dir="logs/elbo"
    )
    model = DPGMMModel(config=config, run_id="test_dp_gmm_elbo")

    print("Fitting DPGMM model...")
    model.fit(X, verbose=True)

    # Get convergence status
    status = model.get_convergence_status()
    print(f"\nConvergence status: {status}")

    # Save logs
    json_path, csv_path = model.save_elbo_logs()
    print(f"\nELBO logs saved to: {json_path}, {csv_path}")

    # Test anomaly scoring
    test_point = np.array([10.0, 10.0])
    score = model.compute_anomaly_score(test_point)
    print(f"\nAnomaly score for test point: {score:.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
