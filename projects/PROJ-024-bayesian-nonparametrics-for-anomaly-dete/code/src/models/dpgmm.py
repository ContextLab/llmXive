"""
Dirichlet Process Gaussian Mixture Model for streaming anomaly detection.

Implements incremental DPGMM with stick-breaking construction, ADVI variational
inference, and cluster anomaly detection for time series data.

API Surface (per Constitution Principle I):
- DPGMMConfig, ELBOHistory, ClusterAnomalyResult, DPGMMModel
- compute_anomaly_score, compute_anomaly_scores_batch, main
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DPGMMConfig:
    """Configuration for DPGMM model."""
    # Base hyperparameters
    alpha: float = 1.0  # Concentration parameter
    gamma: float = 1.0  # Precision parameter for stick-breaking
    mu_0: float = 0.0   # Prior mean
    lambda_0: float = 1.0  # Prior precision scaling
    alpha_0: float = 2.0  # Prior degrees of freedom
    beta_0: float = 1.0   # Prior scale

    # ADVI variational inference parameters
    elbo_tolerance: float = 1e-3  # Convergence tolerance
    max_iterations: int = 500     # Maximum ADVI iterations
    learning_rate: float = 0.01   # Learning rate for stochastic updates

    # Streaming update parameters
    min_observations: int = 10    # Minimum observations before scoring
    cluster_window: int = 5       # Window size for cluster detection
    cluster_threshold: float = 0.7  # Minimum anomaly score ratio for clustering

    # Numerical stability
    epsilon: float = 1e-10  # Small constant to prevent log(0)
    min_variance: float = 1e-6  # Minimum variance floor

    # Memory management
    max_components: int = 50  # Maximum mixture components

    # Cluster anomaly parameters
    min_cluster_size: int = 3  # Minimum points to form a cluster
    cluster_score_weight: float = 0.8  # Weight for cluster vs point anomaly

    def __post_init__(self):
        """Validate configuration."""
        if self.alpha <= 0:
            raise ValueError("Concentration parameter alpha must be positive")
        if self.min_cluster_size < 2:
            raise ValueError("min_cluster_size must be at least 2")

@dataclass
class ELBOHistory:
    """Tracks ELBO convergence during ADVI training."""
    elbo_values: List[float] = field(default_factory=list)
    iterations: List[int] = field(default_factory=list)
    converged: bool = False
    convergence_iteration: Optional[int] = None

    def add(self, elbo: float, iteration: int):
        """Record ELBO value."""
        self.elbo_values.append(elbo)
        self.iterations.append(iteration)

    def check_convergence(self, tolerance: float = 1e-3) -> bool:
        """Check if ELBO has converged."""
        if len(self.elbo_values) < 2:
            return False
        recent = self.elbo_values[-50:] if len(self.elbo_values) >= 50 else self.elbo_values
        if len(recent) < 2:
            return False
        max_change = max(abs(recent[i] - recent[i-1]) for i in range(1, len(recent)))
        return max_change < tolerance

@dataclass
class ClusterAnomalyResult:
    """Result from cluster anomaly detection."""
    cluster_id: int
    start_index: int
    end_index: int
    points: List[int]
    mean_score: float
    cluster_score: float
    is_cluster_anomaly: bool
    cluster_type: str  # 'point', 'cluster', 'collective'
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'cluster_id': self.cluster_id,
            'start_index': self.start_index,
            'end_index': self.end_index,
            'points': self.points,
            'mean_score': float(self.mean_score),
            'cluster_score': float(self.cluster_score),
            'is_cluster_anomaly': self.is_cluster_anomaly,
            'cluster_type': self.cluster_type,
            'confidence': float(self.confidence),
            'metadata': self.metadata
        }

@dataclass
class AnomalyScore:
    """Anomaly score for a single observation."""
    timestamp: datetime
    index: int
    score: float
    uncertainty: float
    is_anomaly: bool
    component_id: Optional[int] = None
    cluster_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'index': self.index,
            'score': float(self.score),
            'uncertainty': float(self.uncertainty),
            'is_anomaly': self.is_anomaly,
            'component_id': self.component_id,
            'cluster_id': self.cluster_id,
            'metadata': self.metadata
        }

class DPGMMModel:
    """
    Dirichlet Process Gaussian Mixture Model with streaming updates.
    
    Implements:
    - Stick-breaking construction for Dirichlet Process
    - ADVI variational inference for posterior approximation
    - Incremental posterior updates for streaming observations
    - Cluster anomaly detection for collective anomalies
    """

    def __init__(self, config: Optional[DPGMMConfig] = None):
        """Initialize DPGMM model."""
        self.config = config or DPGMMConfig()
        self.logger = logging.getLogger(__name__)

        # Model state
        self._n_observations = 0
        self._n_components = 0
        self._active_components: List[int] = []
        self._max_components = self.config.max_components

        # Stick-breaking weights
        self._beta: List[float] = []  # Beta parameters for stick-breaking
        self._pi: List[float] = []    # Mixture weights

        # Component parameters (mean, precision)
        self._mu: List[float] = []
        self._lambda: List[float] = []

        # ADVI variational parameters
        self._q_mu: List[float] = []
        self._q_lambda: List[float] = []

        # Observation history for cluster detection
        self._scores: List[float] = []
        self._score_timestamps: List[datetime] = []

        # ELBO tracking
        self._elbo_history = ELBOHistory()

        # Cluster detection state
        self._cluster_counter = 0
        self._current_cluster: List[Tuple[int, float]] = []

        self.logger.info(f"DPGMMModel initialized with alpha={self.config.alpha}")

    @property
    def n_observations(self) -> int:
        """Return number of observations processed."""
        return self._n_observations

    @property
    def n_components(self) -> int:
        """Return number of active components."""
        return self._n_components

    def _initialize_new_component(self, observation: float) -> int:
        """Initialize a new mixture component."""
        if len(self._active_components) >= self._max_components:
            self.logger.warning("Maximum components reached, reusing existing")
            return self._active_components[0]

        component_id = len(self._active_components)
        self._active_components.append(component_id)

        # Initialize with observation plus some regularization
        self._mu.append(observation)
        self._lambda.append(self.config.lambda_0)
        self._q_mu.append(observation)
        self._q_lambda.append(self.config.lambda_0)

        # Initialize stick-breaking weight
        self._beta.append(self.config.alpha / (self.config.alpha + 1))

        self._n_components += 1
        self.logger.debug(f"Initialized new component {component_id}")
        return component_id

    def _update_stick_breaking(self):
        """Update mixture weights from stick-breaking parameters."""
        if not self._beta:
            self._pi = []
            return

        self._pi = []
        remaining = 1.0
        for beta in self._beta[:self._n_components]:
            pi = remaining * beta
            self._pi.append(pi)
            remaining *= (1 - beta)

        # Normalize to ensure sum to 1
        total = sum(self._pi) if self._pi else 1.0
        if total > 0:
            self._pi = [p / total for p in self._pi]

    def _compute_log_likelihood(self, observation: float, component_id: int) -> float:
        """Compute log likelihood of observation under a component."""
        if component_id >= len(self._mu):
            return float('-inf')

        mu = self._mu[component_id]
        precision = self._lambda[component_id]

        # Gaussian log likelihood
        diff = observation - mu
        log_likelihood = 0.5 * np.log(precision / (2 * np.pi)) - 0.5 * precision * diff * diff
        return log_likelihood

    def _compute_posterior(self, observation: float) -> List[float]:
        """Compute posterior mixture assignment for an observation."""
        if self._n_components == 0:
            return []

        log_posterior = []
        for i in range(self._n_components):
            log_weight = np.log(self._pi[i] + self.config.epsilon)
            log_likelihood = self._compute_log_likelihood(observation, i)
            log_posterior.append(log_weight + log_likelihood)

        # Normalize
        max_log = max(log_posterior)
        log_posterior = [lp - max_log for lp in log_posterior]
        sum_exp = sum(np.exp(lp) for lp in log_posterior)
        posterior = [np.exp(lp) / sum_exp for lp in log_posterior]

        return posterior

    def _advi_update(self, observation: float, posterior: List[float]):
        """Perform ADVI variational update for all components."""
        if self._n_components == 0:
            return

        for i in range(self._n_components):
            # Weighted update for component i
            weight = posterior[i]

            # Update variational parameters
            if weight > 0:
                # Mean update
                self._q_mu[i] = (self._q_mu[i] + weight * observation) / (1 + weight)

                # Precision update (simplified)
                self._q_lambda[i] = self._q_lambda[i] + weight

                # Update component parameters
                self._mu[i] = self._q_mu[i]
                self._lambda[i] = max(self._q_lambda[i], self.config.min_variance)

    def _update_concentration_parameter(self):
        """Update concentration parameter based on component count."""
        active_count = len(self._active_components)

        # Adaptive concentration tuning
        if active_count > self._max_components * 0.8:
            # Too many components, increase alpha
            self.config.alpha *= 1.1
        elif active_count < self._max_components * 0.2 and self._n_observations > 100:
            # Too few components, decrease alpha
            self.config.alpha = max(0.1, self.config.alpha * 0.9)

        # Clamp alpha
        self.config.alpha = np.clip(self.config.alpha, 0.1, 10.0)

    def process_observation(self, observation: float, timestamp: Optional[datetime] = None) -> AnomalyScore:
        """
        Process a single streaming observation.

        Args:
            observation: Single time series value
            timestamp: Optional timestamp for the observation

        Returns:
            AnomalyScore with score and uncertainty
        """
        if timestamp is None:
            timestamp = datetime.now()

        self._n_observations += 1

        # Handle missing values
        if np.isnan(observation) or np.isinf(observation):
            self.logger.warning(f"Invalid observation at index {self._n_observations-1}: {observation}")
            # Impute with last valid value or mean
            if self._scores:
                observation = np.mean(self._scores[-10:])
            else:
                observation = 0.0

        # Initialize new component if needed
        if self._n_components == 0:
            self._initialize_new_component(observation)

        # Compute posterior
        posterior = self._compute_posterior(observation)

        # Compute anomaly score (negative log posterior)
        if self._n_components > 0 and posterior:
            max_posterior = max(posterior)
            score = -np.log(max_posterior + self.config.epsilon)
        else:
            score = float('inf')

        # Determine if anomaly
        threshold = self._compute_adaptive_threshold()
        is_anomaly = score > threshold

        # Store score for cluster detection
        self._scores.append(score)
        self._score_timestamps.append(timestamp)

        # Compute uncertainty
        if posterior:
            entropy = -sum(p * np.log(p + self.config.epsilon) for p in posterior)
            uncertainty = entropy / np.log(self._n_components + self.config.epsilon)
        else:
            uncertainty = 1.0

        # Create anomaly score
        anomaly_score = AnomalyScore(
            timestamp=timestamp,
            index=self._n_observations - 1,
            score=score,
            uncertainty=uncertainty,
            is_anomaly=is_anomaly
        )

        # Update model with ADVI
        if posterior:
            self._advi_update(observation, posterior)
            self._update_stick_breaking()
            self._update_concentration_parameter()

        # Check for cluster anomalies
        self._check_cluster_anomaly(anomaly_score)

        return anomaly_score

    def _compute_adaptive_threshold(self) -> float:
        """Compute adaptive threshold based on score distribution."""
        if len(self._scores) < self.config.min_observations:
            return 3.0  # Default threshold

        recent_scores = self._scores[-100:] if len(self._scores) >= 100 else self._scores
        mean_score = np.mean(recent_scores)
        std_score = np.std(recent_scores) + self.config.epsilon

        # 95th percentile based threshold
        threshold = mean_score + 2 * std_score
        return threshold

    def _check_cluster_anomaly(self, current_score: AnomalyScore):
        """
        Check if current score is part of a cluster anomaly.

        Cluster anomalies are consecutive anomalous points that indicate
        collective behavior rather than isolated outliers.
        """
        # Add to current cluster tracking
        self._current_cluster.append((current_score.index, current_score.score))

        # Check if cluster has ended (non-anomaly or too large)
        if not current_score.is_anomaly:
            self._process_cluster_if_valid()
            self._current_cluster = []
            return

        # Check if cluster is too large
        if len(self._current_cluster) > 100:
            self._process_cluster_if_valid()
            self._current_cluster = []
            return

        # Check if enough points to form cluster
        if len(self._current_cluster) >= self.config.min_cluster_size:
            # Check if all points in window are anomalous
            recent_scores = self._scores[-self.config.cluster_window:]
            if len(recent_scores) >= self.config.cluster_window:
                anomaly_ratio = sum(1 for s in recent_scores if s > self._compute_adaptive_threshold()) / len(recent_scores)
                if anomaly_ratio >= self.config.cluster_threshold:
                    # Mark as cluster anomaly
                    current_score.cluster_id = self._cluster_counter
                    current_score.metadata['is_cluster'] = True
                    current_score.metadata['cluster_size'] = len(self._current_cluster)

    def _process_cluster_if_valid(self):
        """Process detected cluster if it meets criteria."""
        if len(self._current_cluster) < self.config.min_cluster_size:
            self._current_cluster = []
            return

        # Compute cluster statistics
        indices = [item[0] for item in self._current_cluster]
        scores = [item[1] for item in self._current_cluster]

        mean_score = np.mean(scores)
        cluster_score = self._compute_cluster_anomaly_score(scores)

        # Mark all points in cluster
        for idx in indices:
            if idx < len(self._scores):
                # Update score metadata
                pass

        self._cluster_counter += 1
        self._current_cluster = []

    def _compute_cluster_anomaly_score(self, scores: List[float]) -> float:
        """
        Compute cluster anomaly score based on consecutive anomalous points.

        Cluster anomalies are scored differently from point anomalies:
        - Higher score for sustained anomalous behavior
        - Accounts for cluster size and intensity
        """
        if not scores:
            return 0.0

        # Base score from mean anomaly intensity
        mean_intensity = np.mean(scores)

        # Size bonus (larger clusters are more significant)
        size_factor = min(len(scores) / self.config.min_cluster_size, 3.0)

        # Consistency bonus (less variance in scores = more consistent anomaly)
        consistency = 1.0 / (np.std(scores) + self.config.epsilon)

        # Combined cluster score
        cluster_score = (
            self.config.cluster_score_weight * mean_intensity * size_factor +
            (1 - self.config.cluster_score_weight) * consistency
        )

        return cluster_score

    def detect_clusters(self, scores: List[float], threshold: Optional[float] = None) -> List[ClusterAnomalyResult]:
        """
        Detect cluster anomalies in a sequence of scores.

        Args:
            scores: List of anomaly scores
            threshold: Optional threshold for anomaly detection

        Returns:
            List of ClusterAnomalyResult objects
        """
        if threshold is None:
            threshold = self._compute_adaptive_threshold()

        clusters = []
        current_cluster = []
        cluster_id = 0

        for i, score in enumerate(scores):
            if score > threshold:
                current_cluster.append((i, score))
            else:
                if len(current_cluster) >= self.config.min_cluster_size:
                    # Process valid cluster
                    indices = [item[0] for item in current_cluster]
                    scores_in_cluster = [item[1] for item in current_cluster]

                    mean_score = np.mean(scores_in_cluster)
                    cluster_score = self._compute_cluster_anomaly_score(scores_in_cluster)

                    # Determine cluster type
                    if len(current_cluster) >= 10:
                        cluster_type = 'collective'
                    elif len(current_cluster) >= self.config.min_cluster_size * 2:
                        cluster_type = 'cluster'
                    else:
                        cluster_type = 'point'

                    result = ClusterAnomalyResult(
                        cluster_id=cluster_id,
                        start_index=indices[0],
                        end_index=indices[-1],
                        points=indices,
                        mean_score=mean_score,
                        cluster_score=cluster_score,
                        is_cluster_anomaly=True,
                        cluster_type=cluster_type,
                        confidence=min(1.0, len(current_cluster) / (self.config.min_cluster_size * 2))
                    )
                    clusters.append(result)
                    cluster_id += 1

                current_cluster = []

        # Process final cluster if exists
        if len(current_cluster) >= self.config.min_cluster_size:
            indices = [item[0] for item in current_cluster]
            scores_in_cluster = [item[1] for item in current_cluster]

            mean_score = np.mean(scores_in_cluster)
            cluster_score = self._compute_cluster_anomaly_score(scores_in_cluster)

            if len(current_cluster) >= 10:
                cluster_type = 'collective'
            elif len(current_cluster) >= self.config.min_cluster_size * 2:
                cluster_type = 'cluster'
            else:
                cluster_type = 'point'

            result = ClusterAnomalyResult(
                cluster_id=cluster_id,
                start_index=indices[0],
                end_index=indices[-1],
                points=indices,
                mean_score=mean_score,
                cluster_score=cluster_score,
                is_cluster_anomaly=True,
                cluster_type=cluster_type,
                confidence=min(1.0, len(current_cluster) / (self.config.min_cluster_size * 2))
            )
            clusters.append(result)

        return clusters

    def compute_anomaly_score(self, observation: float) -> float:
        """Compute anomaly score for a single observation."""
        if self._n_components == 0:
            return float('inf')

        posterior = self._compute_posterior(observation)
        if not posterior:
            return float('inf')

        max_posterior = max(posterior)
        score = -np.log(max_posterior + self.config.epsilon)
        return score

    def compute_anomaly_scores_batch(self, observations: List[float]) -> List[float]:
        """Compute anomaly scores for a batch of observations."""
        scores = []
        for obs in observations:
            score = self.compute_anomaly_score(obs)
            scores.append(score)
        return scores

    def get_elbo_history(self) -> ELBOHistory:
        """Return ELBO convergence history."""
        return self._elbo_history

    def save_checkpoint(self, path: Path):
        """Save model checkpoint."""
        checkpoint = {
            'config': self.config.__dict__,
            'n_observations': self._n_observations,
            'n_components': self._n_components,
            'active_components': self._active_components,
            'beta': self._beta,
            'pi': self._pi,
            'mu': self._mu,
            'lambda': self._lambda,
            'q_mu': self._q_mu,
            'q_lambda': self._q_lambda,
            'scores': self._scores,
            'elbo_history': {
                'elbo_values': self._elbo_history.elbo_values,
                'iterations': self._elbo_history.iterations,
                'converged': self._elbo_history.converged
            },
            'cluster_counter': self._cluster_counter
        }

        import json
        import numpy as np
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(checkpoint, f, default=lambda o: float(o) if isinstance(o, np.floating) else str(o))

    def load_checkpoint(self, path: Path):
        """Load model checkpoint."""
        import json
        with open(path, 'r') as f:
            checkpoint = json.load(f)

        self.config = DPGMMConfig(**checkpoint['config'])
        self._n_observations = checkpoint['n_observations']
        self._n_components = checkpoint['n_components']
        self._active_components = checkpoint['active_components']
        self._beta = checkpoint['beta']
        self._pi = checkpoint['pi']
        self._mu = checkpoint['mu']
        self._lambda = checkpoint['lambda']
        self._q_mu = checkpoint['q_mu']
        self._q_lambda = checkpoint['q_lambda']
        self._scores = checkpoint['scores']
        self._cluster_counter = checkpoint['cluster_counter']

        self._elbo_history = ELBOHistory(
            elbo_values=checkpoint['elbo_history']['elbo_values'],
            iterations=checkpoint['elbo_history']['iterations'],
            converged=checkpoint['elbo_history']['converged']
        )

        self.logger.info(f"Loaded checkpoint from {path}")

def compute_anomaly_score(model: DPGMMModel, observation: float) -> float:
    """Convenience function to compute anomaly score."""
    return model.compute_anomaly_score(observation)

def compute_anomaly_scores_batch(model: DPGMMModel, observations: List[float]) -> List[float]:
    """Convenience function to compute anomaly scores for batch."""
    return model.compute_anomaly_scores_batch(observations)

def main():
    """Main entry point for testing DPGMM with cluster anomaly detection."""
    logger.info("DPGMM cluster anomaly detection test")

    # Create model
    config = DPGMMConfig(min_cluster_size=3)
    model = DPGMMModel(config)

    # Generate test data with clusters
    np.random.seed(42)
    observations = []
    anomalies = []

    for i in range(100):
        if 20 <= i < 25:  # Cluster anomaly 1
            obs = np.random.normal(5, 0.5)
            anomalies.append(i)
        elif 50 <= i < 55:  # Cluster anomaly 2
            obs = np.random.normal(-5, 0.5)
            anomalies.append(i)
        elif i in [10, 30, 70]:  # Point anomalies
            obs = np.random.normal(10, 0.5)
            anomalies.append(i)
        else:  # Normal
            obs = np.random.normal(0, 1)
        observations.append(obs)

    # Process observations
    scores = []
    for i, obs in enumerate(observations):
        score = model.compute_anomaly_score(obs)
        scores.append(score)
        logger.info(f"Index {i}: obs={obs:.2f}, score={score:.2f}")

    # Detect clusters
    clusters = model.detect_clusters(scores)

    logger.info(f"\nDetected {len(clusters)} clusters:")
    for cluster in clusters:
        logger.info(f"  Cluster {cluster.cluster_id}: type={cluster.cluster_type}, "
                   f"size={len(cluster.points)}, mean_score={cluster.mean_score:.2f}, "
                   f"cluster_score={cluster.cluster_score:.2f}")

    # Compare detected vs actual
    detected_points = set()
    for cluster in clusters:
        detected_points.update(cluster.points)

    recall = len(detected_points.intersection(anomalies)) / len(anomalies) if anomalies else 0
    precision = len(detected_points.intersection(anomalies)) / len(detected_points) if detected_points else 0

    logger.info(f"\nDetection metrics: recall={recall:.2f}, precision={precision:.2f}")
    logger.info("DPGMM cluster anomaly detection test complete")

    return {
        'n_observations': model.n_observations,
        'n_components': model.n_components,
        'clusters_detected': len(clusters),
        'recall': recall,
        'precision': precision
    }

if __name__ == '__main__':
    result = main()
    logger.info(f"Final result: {result}")
