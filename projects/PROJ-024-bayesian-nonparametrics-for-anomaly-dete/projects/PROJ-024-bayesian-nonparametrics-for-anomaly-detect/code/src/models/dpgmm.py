"""
Dirichlet Process Gaussian Mixture Model for Anomaly Detection in Time Series.

This module implements a Bayesian nonparametric model that can:
1. Learn the number of clusters automatically from data
2. Support streaming posterior updates for sequential observations
3. Compute anomaly scores based on posterior predictive probability

The model uses variational inference (ADVI) for efficient posterior estimation.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
import logging
from datetime import datetime
from pathlib import Path
import json

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class DPGMMConfig:
    """Configuration for DPGMM model."""
    # Variational inference parameters
    max_components: int = 50
    min_components: int = 1
    concentration_prior: float = 1.0  # Alpha_0 for Dirichlet process
    learning_rate: float = 0.01  # For streaming updates
    convergence_threshold: float = 1e-4
    max_iterations: int = 1000

    # Gaussian prior parameters
    mean_prior: float = 0.0
    variance_prior: float = 1.0
    precision_prior: float = 1.0

    # Anomaly detection parameters
    anomaly_threshold: float = 0.05  # Percentile threshold for anomaly scoring
    min_anomaly_score: float = 0.0
    max_anomaly_score: float = 1.0

    # Streaming parameters
    streaming_batch_size: int = 100
    streaming_update_frequency: int = 10

    # Random seed for reproducibility
    random_seed: int = 42

@dataclass
class ELBOHistory:
    """Tracks ELBO convergence during training."""
    elbo_values: List[float] = field(default_factory=list)
    iteration: int = 0
    converged: bool = False
    final_elbo: Optional[float] = None

    def add(self, elbo: float) -> None:
        """Add ELBO value to history."""
        self.elbo_values.append(elbo)
        self.iteration += 1
        if len(self.elbo_values) >= 2:
            diff = abs(self.elbo_values[-1] - self.elbo_values[-2])
            if diff < 1e-4:
                self.converged = True
                self.final_elbo = self.elbo_values[-1]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'elbo_values': self.elbo_values,
            'iteration': self.iteration,
            'converged': self.converged,
            'final_elbo': self.final_elbo
        }

@dataclass
class ClusterAnomalyResult:
    """Result of anomaly scoring for a cluster."""
    cluster_id: int
    mean: np.ndarray
    covariance: np.ndarray
    weight: float
    anomaly_threshold: float
    anomaly_count: int = 0

class DPGMMModel:
    """
    Dirichlet Process Gaussian Mixture Model with streaming posterior updates.

    This implementation supports:
    - Automatic cluster number determination via Dirichlet process
    - Streaming posterior updates for sequential observations
    - Anomaly scoring based on posterior predictive probability
    - Variational inference for efficient computation
    """

    def __init__(self, config: Optional[DPGMMConfig] = None):
        """Initialize DPGMM model with configuration."""
        self.config = config or DPGMMConfig()
        np.random.seed(self.config.random_seed)

        # Model state
        self._initialized = False
        self._n_components = 0
        self._max_components = self.config.max_components

        # Variational parameters (will be initialized on first observation)
        self._variational_params: Dict[str, np.ndarray] = {}

        # Streaming state
        self._streaming_buffer: List[np.ndarray] = []
        self._n_observations: int = 0
        self._last_update_iteration: int = 0

        # ELBO tracking
        self._elbo_history = ELBOHistory()

        # Convergence monitoring
        self._concentration_alpha = self.config.concentration_prior
        self._active_clusters: List[int] = []

        logger.info(f"DPGMMModel initialized with config: {self.config}")

    @property
    def is_initialized(self) -> bool:
        """Check if model has been initialized with data."""
        return self._initialized

    @property
    def n_components(self) -> int:
        """Get current number of active components."""
        return self._n_components

    @property
    def elbo_history(self) -> ELBOHistory:
        """Get ELBO convergence history."""
        return self._elbo_history

    def _initialize_variational_params(self, dim: int, n_clusters: int) -> None:
        """Initialize variational parameters for given dimension and clusters."""
        # Mean parameters (K x D)
        self._variational_params['m'] = np.random.randn(n_clusters, dim) * 0.1

        # Precision parameters (K x D) - diagonal covariance approximation
        self._variational_params['w'] = np.ones((n_clusters, dim)) * 0.1

        # Concentration parameters (K,)
        self._variational_params['gamma'] = np.ones(n_clusters)

        # Mixing weights (K,)
        self._variational_params['pi'] = np.ones(n_clusters) / n_clusters

        # Sufficient statistics
        self._variational_params['N'] = np.zeros(n_clusters)

        self._n_components = n_clusters
        self._active_clusters = list(range(n_clusters))

    def _compute_elbo(self, X: np.ndarray) -> float:
        """
        Compute Evidence Lower Bound (ELBO) for current variational parameters.

        ELBO = E_q[log p(X|Z,θ)] - E_q[KL(q(θ)||p(θ))]

        Returns:
            float: ELBO value
        """
        if not self._initialized or len(self._active_clusters) == 0:
            return 0.0

        # Compute responsibilities
        responsibilities = self._compute_responsibilities(X)

        # Expected log-likelihood
        log_likelihood = self._compute_expected_log_likelihood(X, responsibilities)

        # Expected KL divergence (simplified for diagonal covariance)
        kl_div = self._compute_expected_kl_divergence()

        elbo = log_likelihood - kl_div
        return elbo

    def _compute_responsibilities(self, X: np.ndarray) -> np.ndarray:
        """
        Compute responsibilities (posterior probability of cluster assignment).

        Args:
            X: Observation data (N x D)

        Returns:
            responsibilities: (N x K) matrix of responsibilities
        """
        if not self._initialized or len(self._active_clusters) == 0:
            return np.zeros((X.shape[0], 0))

        K = len(self._active_clusters)
        N = X.shape[0]
        responsibilities = np.zeros((N, K))

        for k_idx, k in enumerate(self._active_clusters):
            # Compute Mahalanobis distance
            diff = X - self._variational_params['m'][k]
            precision = self._variational_params['w'][k]
            mahal_dist = np.sum((diff ** 2) * precision, axis=1)

            # Log probability
            log_p = -0.5 * mahal_dist + np.log(self._variational_params['pi'][k] + 1e-10)
            responsibilities[:, k_idx] = log_p

        # Normalize (log-sum-exp trick)
        max_log = np.max(responsibilities, axis=1, keepdims=True)
        responsibilities = np.exp(responsibilities - max_log)
        responsibilities = responsibilities / (np.sum(responsibilities, axis=1, keepdims=True) + 1e-10)

        return responsibilities

    def _compute_expected_log_likelihood(self, X: np.ndarray, responsibilities: np.ndarray) -> float:
        """Compute expected log-likelihood under current variational parameters."""
        if not self._initialized or len(self._active_clusters) == 0:
            return 0.0

        log_ll = 0.0
        N = X.shape[0]

        for k_idx, k in enumerate(self._active_clusters):
            diff = X - self._variational_params['m'][k]
            precision = self._variational_params['w'][k]
            mahal_dist = np.sum((diff ** 2) * precision, axis=1)

            log_p = -0.5 * mahal_dist + np.log(self._variational_params['pi'][k] + 1e-10)
            log_ll += np.sum(responsibilities[:, k_idx] * log_p)

        return log_ll

    def _compute_expected_kl_divergence(self) -> float:
        """Compute expected KL divergence between variational posterior and prior."""
        if not self._initialized or len(self._active_clusters) == 0:
            return 0.0

        kl = 0.0

        # KL for concentration parameters
        for k in self._active_clusters:
            gamma = self._variational_params['gamma'][k]
            kl += gamma * np.log(gamma / self._concentration_alpha)

        return kl

    def _update_variational_params(self, X: np.ndarray, responsibilities: np.ndarray) -> None:
        """
        Update variational parameters using variational Bayes updates.

        This is the core variational inference update step.
        """
        if not self._initialized or len(self._active_clusters) == 0:
            return

        N = X.shape[0]
        lr = self.config.learning_rate

        for k_idx, k in enumerate(self._active_clusters):
            # Effective count for this cluster
            N_k = np.sum(responsibilities[:, k_idx]) + 1e-10

            # Update mixing weights
            self._variational_params['pi'][k] = (
                (1 - lr) * self._variational_params['pi'][k] +
                lr * (N_k / N)
            )

            # Update mean (weighted average)
            weighted_X = responsibilities[:, k_idx:k_idx+1] * X
            new_mean = np.sum(weighted_X, axis=0) / N_k
            self._variational_params['m'][k] = (
                (1 - lr) * self._variational_params['m'][k] +
                lr * new_mean
            )

            # Update precision (inverse variance)
            diff = X - self._variational_params['m'][k]
            weighted_var = np.sum(responsibilities[:, k_idx:k_idx+1] * (diff ** 2), axis=0) / N_k
            new_precision = 1.0 / (weighted_var + 1e-10)
            self._variational_params['w'][k] = (
                (1 - lr) * self._variational_params['w'][k] +
                lr * new_precision
            )

            # Update concentration parameter
            self._variational_params['gamma'][k] = (
                (1 - lr) * self._variational_params['gamma'][k] +
                lr * N_k
            )

    def _check_new_cluster(self, X: np.ndarray, responsibilities: np.ndarray) -> bool:
        """
        Check if a new cluster should be created based on Dirichlet process prior.

        Returns True if a new cluster should be created.
        """
        if not self._initialized:
            return False

        # Check if any observation has low responsibility for all existing clusters
        min_responsibility = np.min(np.max(responsibilities, axis=1))

        # If minimum responsibility is below threshold, consider new cluster
        if min_responsibility < 0.1 and self._n_components < self._max_components:
            # Check concentration parameter
            expected_new_cluster = self._concentration_alpha / (
                self._concentration_alpha + self._n_observations
            )

            if expected_new_cluster > 0.01:
                return True

        return False

    def _create_new_cluster(self, X: np.ndarray) -> None:
        """Create a new cluster for observations that don't fit existing clusters."""
        if self._n_components >= self._max_components:
            logger.warning("Maximum number of clusters reached, cannot create new cluster")
            return

        # Find observations with low responsibility
        # Initialize new cluster with random observation
        new_cluster_idx = self._n_components
        self._active_clusters.append(new_cluster_idx)

        # Initialize with random observation from X
        random_idx = np.random.randint(0, X.shape[0])
        new_mean = X[random_idx].copy()

        # Expand parameter arrays
        for param_name in ['m', 'w', 'gamma', 'pi']:
            old_shape = self._variational_params[param_name].shape
            if len(old_shape) == 1:
                new_shape = (old_shape[0] + 1,)
            else:
                new_shape = (old_shape[0] + 1, old_shape[1])

            new_param = np.zeros(new_shape)
            new_param[:old_shape[0]] = self._variational_params[param_name]
            if param_name == 'm':
                new_param[-1] = new_mean
            elif param_name == 'w':
                new_param[-1] = np.ones(X.shape[1]) * 0.1
            elif param_name == 'gamma':
                new_param[-1] = self._concentration_alpha
            elif param_name == 'pi':
                new_param[-1] = 1.0 / (self._n_components + 1)

            self._variational_params[param_name] = new_param

        self._n_components += 1
        logger.info(f"Created new cluster {new_cluster_idx}, total clusters: {self._n_components}")

    def _prune_inactive_clusters(self, responsibilities: np.ndarray) -> None:
        """Remove clusters with very low effective count."""
        if not self._initialized:
            return

        min_count = 10  # Minimum observations to keep a cluster
        clusters_to_remove = []

        for k_idx, k in enumerate(self._active_clusters):
            if self._variational_params['N'][k] < min_count:
                clusters_to_remove.append(k)

        if clusters_to_remove:
            # Remove inactive clusters
            for k in clusters_to_remove:
                self._active_clusters.remove(k)
                self._n_components -= 1

            # Compact arrays
            self._variational_params['m'] = self._variational_params['m'][self._active_clusters]
            self._variational_params['w'] = self._variational_params['w'][self._active_clusters]
            self._variational_params['gamma'] = self._variational_params['gamma'][self._active_clusters]
            self._variational_params['pi'] = self._variational_params['pi'][self._active_clusters]
            self._variational_params['N'] = self._variational_params['N'][self._active_clusters]

            logger.info(f"Pruned {len(clusters_to_remove)} inactive clusters, remaining: {self._n_components}")

    def initialize(self, X: np.ndarray) -> None:
        """
        Initialize model with initial data batch.

        Args:
            X: Initial observation data (N x D)
        """
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        dim = X.shape[1]
        n_clusters = min(self.config.min_components, self._max_components)

        self._initialize_variational_params(dim, n_clusters)
        self._initialized = True

        # Run initial variational inference
        self._variational_inference(X)

        logger.info(f"Model initialized with {X.shape[0]} observations, {dim} dimensions, {self._n_components} clusters")

    def _variational_inference(self, X: np.ndarray) -> ELBOHistory:
        """
        Run variational inference to optimize variational parameters.

        Args:
            X: Observation data (N x D)

        Returns:
            ELBOHistory: Convergence history
        """
        if not self._initialized:
            logger.error("Model not initialized")
            return self._elbo_history

        for iteration in range(self.config.max_iterations):
            # E-step: compute responsibilities
            responsibilities = self._compute_responsibilities(X)

            # M-step: update variational parameters
            self._update_variational_params(X, responsibilities)

            # Compute ELBO
            elbo = self._compute_elbo(X)
            self._elbo_history.add(elbo)

            # Check convergence
            if self._elbo_history.converged:
                logger.info(f"ELBO converged at iteration {iteration}")
                break

            # Check for new cluster
            if self._check_new_cluster(X, responsibilities):
                self._create_new_cluster(X)

        # Prune inactive clusters
        self._prune_inactive_clusters(responsibilities)

        return self._elbo_history

    def streaming_update(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Update posterior incrementally with new observations (streaming mode).

        This method enables online learning where the model updates its
        posterior distribution as new observations arrive, without
        retraining from scratch.

        Args:
            X: New observation data (N x D) or single observation (D,)

        Returns:
            Dict containing:
                - 'updated': bool indicating if update was performed
                - 'n_observations': total observations seen
                - 'n_components': current number of clusters
                - 'elbo': current ELBO value
                - 'new_cluster_created': bool if new cluster was created
        """
        # Handle single observation
        if X.ndim == 1:
            X = X.reshape(1, -1)

        if not self._initialized:
            # First streaming update initializes the model
            self.initialize(X)
            return {
                'updated': True,
                'n_observations': X.shape[0],
                'n_components': self._n_components,
                'elbo': self._compute_elbo(X),
                'new_cluster_created': False
            }

        # Add to streaming buffer
        self._streaming_buffer.append(X)
        self._n_observations += X.shape[0]

        # Perform update at configured frequency
        update_due = (self._n_observations - self._last_update_iteration) >= self.config.streaming_update_frequency

        if update_due or len(self._streaming_buffer) >= self.config.streaming_batch_size:
            # Combine buffered observations
            X_batch = np.vstack(self._streaming_buffer) if self._streaming_buffer else X

            # Compute responsibilities for batch
            responsibilities = self._compute_responsibilities(X_batch)

            # Streaming variational update (using stochastic gradient)
            self._update_variational_params(X_batch, responsibilities)

            # Check for new cluster
            new_cluster_created = self._check_new_cluster(X_batch, responsibilities)
            if new_cluster_created:
                self._create_new_cluster(X_batch)

            # Prune inactive clusters periodically
            if self._n_observations % 1000 == 0:
                self._prune_inactive_clusters(responsibilities)

            # Update last iteration
            self._last_update_iteration = self._n_observations

            # Clear buffer
            self._streaming_buffer = []

            # Log update
            elbo = self._compute_elbo(X_batch)
            logger.debug(
                f"Streaming update: n_obs={self._n_observations}, "
                f"n_clusters={self._n_components}, elbo={elbo:.4f}"
            )

            return {
                'updated': True,
                'n_observations': self._n_observations,
                'n_components': self._n_components,
                'elbo': elbo,
                'new_cluster_created': new_cluster_created
            }

        return {
            'updated': False,
            'n_observations': self._n_observations,
            'n_components': self._n_components,
            'elbo': self._compute_elbo(X),
            'new_cluster_created': False
        }

    def compute_anomaly_score(self, x: np.ndarray) -> float:
        """
        Compute anomaly score for a single observation.

        The anomaly score is based on the posterior predictive probability:
        lower probability = higher anomaly score.

        Args:
            x: Single observation (D,)

        Returns:
            float: Anomaly score in [0, 1]
        """
        if not self._initialized or self._n_components == 0:
            return 0.5  # Default score if model not ready

        if x.ndim == 1:
            x = x.reshape(1, -1)

        # Compute responsibilities
        responsibilities = self._compute_responsibilities(x)

        if responsibilities.shape[1] == 0:
            return 1.0  # Maximum anomaly if no clusters

        # Compute max responsibility (how well does this point fit best cluster)
        max_resp = np.max(responsibilities[0])

        # Convert to anomaly score (inverse relationship)
        anomaly_score = 1.0 - max_resp

        # Clamp to [min, max] range
        anomaly_score = np.clip(
            anomaly_score,
            self.config.min_anomaly_score,
            self.config.max_anomaly_score
        )

        return float(anomaly_score)

    def compute_anomaly_scores_batch(self, X: np.ndarray) -> np.ndarray:
        """
        Compute anomaly scores for multiple observations.

        Args:
            X: Observation data (N x D)

        Returns:
            np.ndarray: Anomaly scores (N,)
        """
        if not self._initialized or self._n_components == 0:
            return np.full(X.shape[0], 0.5)

        if X.ndim == 1:
            X = X.reshape(1, -1)

        scores = np.zeros(X.shape[0])
        for i in range(X.shape[0]):
            scores[i] = self.compute_anomaly_score(X[i])

        return scores

    def get_cluster_info(self) -> List[ClusterAnomalyResult]:
        """
        Get information about all active clusters.

        Returns:
            List of ClusterAnomalyResult for each active cluster
        """
        results = []
        for k_idx, k in enumerate(self._active_clusters):
          result = ClusterAnomalyResult(
              cluster_id=k,
              mean=self._variational_params['m'][k_idx].copy(),
              covariance=np.diag(1.0 / (self._variational_params['w'][k_idx] + 1e-10)),
              weight=self._variational_params['pi'][k_idx],
              anomaly_threshold=self.config.anomaly_threshold,
              anomaly_count=int(self._variational_params['N'][k_idx])
          )
          results.append(result)

        return results

    def save(self, path: Union[str, Path]) -> None:
        """
        Save model state to disk.

        Args:
            path: Path to save model
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        model_state = {
            'config': {k: v for k, v in self.config.__dict__.items()},
            'variational_params': {
                k: v.tolist() if isinstance(v, np.ndarray) else v
                for k, v in self._variational_params.items()
            },
            'n_components': self._n_components,
            'n_observations': self._n_observations,
            'concentration_alpha': self._concentration_alpha,
            'active_clusters': self._active_clusters,
            'elbo_history': self._elbo_history.to_dict(),
            'initialized': self._initialized
        }

        with open(path, 'w') as f:
            json.dump(model_state, f, indent=2)

        logger.info(f"Model saved to {path}")

    @classmethod
    def load(cls, path: Union[str, Path]) -> 'DPGMMModel':
        """
        Load model state from disk.

        Args:
            path: Path to load model from

        Returns:
            DPGMMModel instance
        """
        path = Path(path)

        with open(path, 'r') as f:
            model_state = json.load(f)

        # Reconstruct config
        config_dict = model_state['config']
        config = DPGMMConfig(**config_dict)

        # Create model
        model = cls(config)

        # Restore state
        model._variational_params = {
            k: np.array(v) for k, v in model_state['variational_params'].items()
        }
        model._n_components = model_state['n_components']
        model._n_observations = model_state['n_observations']
        model._concentration_alpha = model_state['concentration_alpha']
        model._active_clusters = model_state['active_clusters']
        model._initialized = model_state['initialized']

        # Restore ELBO history
        elbo_data = model_state['elbo_history']
        model._elbo_history.elbo_values = elbo_data['elbo_values']
        model._elbo_history.iteration = elbo_data['iteration']
        model._elbo_history.converged = elbo_data['converged']
        model._elbo_history.final_elbo = elbo_data['final_elbo']

        logger.info(f"Model loaded from {path}")
        return model

def compute_anomaly_score(model: DPGMMModel, x: np.ndarray) -> float:
    """
    Convenience function to compute anomaly score.

    Args:
        model: Trained DPGMMModel
        x: Observation to score

    Returns:
        float: Anomaly score
    """
    return model.compute_anomaly_score(x)

def compute_anomaly_scores_batch(model: DPGMMModel, X: np.ndarray) -> np.ndarray:
    """
    Convenience function to compute anomaly scores for batch.

    Args:
        model: Trained DPGMMModel
        X: Observations to score

    Returns:
        np.ndarray: Anomaly scores
    """
    return model.compute_anomaly_scores_batch(X)

def main():
    """Main entry point for testing DPGMM streaming updates."""
    logging.basicConfig(level=logging.INFO)

    # Create model
    config = DPGMMConfig()
    model = DPGMMModel(config)

    # Generate synthetic data
    np.random.seed(42)
    n_samples = 1000
    dim = 1

    # Create two clusters
    X_cluster1 = np.random.randn(n_samples // 2, dim) * 0.5 + 2
    X_cluster2 = np.random.randn(n_samples // 2, dim) * 0.5 - 2
    X = np.vstack([X_cluster1, X_cluster2])

    # Initialize model
    model.initialize(X[:100])

    # Streaming updates
    for i in range(0, len(X[100:]), 50):
        X_batch = X[100+i:100+i+50]
        result = model.streaming_update(X_batch)
        print(f"Update {i//50}: n_obs={result['n_observations']}, "
              f"n_clusters={result['n_components']}, elbo={result['elbo']:.4f}")

    # Test anomaly scoring
    anomaly_point = np.array([10.0])
    score = model.compute_anomaly_score(anomaly_point)
    print(f"Anomaly score for outlier: {score:.4f}")

    # Save model
    model.save('dpgmm_model.json')
    print("Model saved successfully")

if __name__ == '__main__':
    main()
