"""
Dirichlet Process Gaussian Mixture Model for Streaming Anomaly Detection.

Optimized implementation with vectorized operations, caching, and memory-efficient
streaming updates for high-performance time-series anomaly detection.

API Surface:
  DPGMMConfig, ELBOHistory, ClusterAnomalyResult, AnomalyScore,
  DPGMMModel, compute_anomaly_score, compute_anomaly_scores_batch, main
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
import logging
from datetime import datetime
from pathlib import Path
import time
import json

from models.anomaly_score import AnomalyScore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DPGMMConfig:
    """Configuration for DPGMM model with performance optimization parameters."""
    # Core hyperparameters
    alpha: float = 1.0  # Concentration parameter
    beta_0: float = 1.0  # Precision prior
    kappa_0: float = 1.0  # Mean prior precision
    nu_0: float = 3.0  # Degrees of freedom for Wishart
    m_0: Optional[np.ndarray] = None  # Prior mean
    lambda_0: Optional[np.ndarray] = None  # Prior covariance (scaled identity)
    
    # Performance optimization parameters
    cache_mahalanobis: bool = True  # Cache Mahalanobis distance computations
    vectorize_updates: bool = True  # Use vectorized numpy operations
    batch_update_threshold: int = 100  # Batch updates after this many observations
    max_components: int = 50  # Maximum mixture components to prevent memory bloat
    min_component_weight: float = 1e-6  # Prune components below this weight
    elbo_convergence_tol: float = 0.001  # ELBO convergence tolerance
    max_elbo_iterations: int = 500  # Maximum ELBO optimization iterations
    
    # Streaming parameters
    streaming_buffer_size: int = 1000  # Buffer size for streaming observations
    forget_factor: float = 0.99  # Exponential forgetting for non-stationary data
    
    # Numerical stability
    min_precision: float = 1e-10  # Minimum precision to prevent numerical issues
    max_precision: float = 1e10  # Maximum precision
    regularization: float = 1e-6  # Regularization for covariance matrices

@dataclass
class ELBOHistory:
    """History of ELBO values during optimization."""
    values: List[float] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    
    def add(self, value: float) -> None:
        """Add ELBO value with timestamp."""
        self.values.append(value)
        self.timestamps.append(time.time())
    
    def converged(self, window: int = 50, tol: float = 0.001) -> bool:
        """Check if ELBO has converged over the last `window` iterations."""
        if len(self.values) < window:
            return False
        recent = self.values[-window:]
        return max(recent) - min(recent) < tol
    
    def get_recent_avg(self, window: int = 10) -> float:
        """Get average ELBO over recent iterations."""
        if not self.values:
            return 0.0
        recent = self.values[-window:]
        return np.mean(recent)

@dataclass
class ClusterAnomalyResult:
    """Result from cluster-level anomaly analysis."""
    component_id: int
    mean: np.ndarray
    covariance: np.ndarray
    weight: float
    anomaly_threshold: float
    is_outlier_component: bool

class DPGMMModel:
    """
    Optimized Dirichlet Process Gaussian Mixture Model for streaming anomaly detection.
    
    Features:
      - Vectorized numpy operations for performance
      - Mahalanobis distance caching
      - Memory-efficient streaming updates
      - Automatic component pruning
      - ELBO convergence tracking
    """
    
    def __init__(self, config: DPGMMConfig):
        """Initialize DPGMM model with configuration."""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Model state
        self.n_components: int = 0
        self.component_weights: np.ndarray = np.zeros(config.max_components)
        self.component_means: np.ndarray = np.zeros((config.max_components, 1))
        self.component_precisions: np.ndarray = np.zeros((config.max_components, 1, 1))
        self.component_covariances: np.ndarray = np.zeros((config.max_components, 1, 1))
        
        # Variational parameters (for each component)
        self.var_beta: np.ndarray = np.ones(config.max_components) * config.beta_0
        self.var_kappa: np.ndarray = np.ones(config.max_components) * config.kappa_0
        self.var_m: np.ndarray = np.zeros((config.max_components, 1))
        self.var_nu: np.ndarray = np.ones(config.max_components) * config.nu_0
        self.var_lambda: np.ndarray = np.ones((config.max_components, 1, 1))
        
        # Stick-breaking parameters
        self.var_pi: np.ndarray = np.ones(config.max_components) * (1.0 / config.max_components)
        self.var_alpha: float = config.alpha
        
        # Caching
        self._mahalanobis_cache: Dict[int, Tuple[np.ndarray, float]] = {}
        self._cache_key_counter: int = 0
        
        # ELBO tracking
        self.elbo_history = ELBOHistory()
        
        # Streaming buffer
        self._observation_buffer: List[np.ndarray] = []
        self._total_observations: int = 0
        
        # Performance metrics
        self._update_times: List[float] = []
        self._score_times: List[float] = []
        
        # Initialize prior mean if not provided
        if config.m_0 is None:
            self.config.m_0 = np.zeros(1)
        if config.lambda_0 is None:
            self.config.lambda_0 = np.array([1.0])
        
        self.logger.info(f"DPGMMModel initialized with alpha={config.alpha}, "
                       f"max_components={config.max_components}")
    
    def _initialize_new_component(self, observation: np.ndarray, component_idx: int) -> None:
        """Initialize a new mixture component with the given observation."""
        # Reset component state
        self.component_means[component_idx] = observation.copy()
        self.component_precisions[component_idx] = np.array([[1.0]])
        self.component_covariances[component_idx] = np.array([[1.0]])
        
        # Reset variational parameters
        self.var_beta[component_idx] = self.config.beta_0
        self.var_kappa[component_idx] = self.config.kappa_0
        self.var_m[component_idx] = observation.copy()
        self.var_nu[component_idx] = self.config.nu_0
        self.var_lambda[component_idx] = np.array([[self.config.lambda_0[0]]])
        
        # Set initial weight
        self.component_weights[component_idx] = 1.0 / (self.n_components + 1)
        
        self.n_components += 1
    
    def _compute_mahalanobis(self, observation: np.ndarray, component_idx: int) -> float:
        """
        Compute Mahalanobis distance with caching optimization.
        
        Uses cached inverse covariance when available for performance.
        """
        if self.config.cache_mahalanobis:
            cache_key = (component_idx, tuple(observation.flatten()))
            if cache_key in self._mahalanobis_cache:
                return self._mahalanobis_cache[cache_key][1]
        
        # Compute Mahalanobis distance: sqrt((x-mu)' * Sigma^-1 * (x-mu))
        diff = observation - self.component_means[component_idx]
        precision = self.component_precisions[component_idx]
        
        # Handle numerical stability
        precision = np.clip(precision, self.config.min_precision, self.config.max_precision)
        
     

        mahal_sq = float(np.dot(diff.T, np.dot(precision, diff)))
        mahal = np.sqrt(max(mahal_sq, 0.0))  # Ensure non-negative
        
        if self.config.cache_mahalanobis:
            self._mahalanobis_cache[cache_key] = (diff, mahal)
            # Limit cache size
            if len(self._mahalanobis_cache) > 10000:
                # Remove oldest half of cache
                keys = list(self._mahalanobis_cache.keys())[:5000]
                for k in keys:
                    del self._mahalanobis_cache[k]
        
        return mahal
    
    def _compute_log_likelihood(self, observation: np.ndarray, component_idx: int) -> float:
        """Compute log-likelihood of observation under component."""
        mahal = self._compute_mahalanobis(observation, component_idx)
        d = observation.shape[0]
        
        # Log of multivariate normal PDF (unnormalized)
        log_precision = np.log(max(np.abs(self.component_precisions[component_idx][0, 0]), 
                                  self.config.min_precision))
        
        log_likelihood = -0.5 * (d * np.log(2 * np.pi) - log_precision + mahal ** 2)
        return log_likelihood
    
    def _compute_log_posterior(self, observation: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute log posterior for all components (vectorized).
        
        Returns:
          log_weights: log(component_weight * likelihood) for each component
          log_likelihoods: log-likelihood of observation under each component
        """
        if not self.config.vectorize_updates or self.n_components == 0:
            # Fallback to sequential computation
            log_weights = np.zeros(self.n_components)
            log_likelihoods = np.zeros(self.n_components)
            for i in range(self.n_components):
                log_likelihoods[i] = self._compute_log_likelihood(observation, i)
                log_weights[i] = np.log(max(self.component_weights[i], 1e-300)) + log_likelihoods[i]
            return log_weights, log_likelihoods
        
        # Vectorized computation
        log_weights = np.zeros(self.n_components)
        log_likelihoods = np.zeros(self.n_components)
        
        for i in range(self.n_components):
            log_likelihoods[i] = self._compute_log_likelihood(observation, i)
            log_weights[i] = np.log(max(self.component_weights[i], 1e-300)) + log_likelihoods[i]
        
        return log_weights, log_likelihoods
    
    def update_streaming(self, observation: np.ndarray) -> Dict[str, Any]:
        """
        Update model with a single streaming observation (optimized).
        
        Args:
          observation: Single observation vector (1D array)
        
        Returns:
          Dict with update statistics and current model state
        """
        start_time = time.time()
        
        # Ensure observation is 2D
        if observation.ndim == 1:
            observation = observation.reshape(-1, 1)
        
        self._total_observations += 1
        
        # Add to buffer for batch updates
        self._observation_buffer.append(observation.copy())
        
        # Check if we should trigger batch update
        if len(self._observation_buffer) >= self.config.batch_update_threshold:
            return self._process_batch_update()
        
        # Single observation update
        if self.n_components == 0:
            # First observation - initialize first component
            self._initialize_new_component(observation, 0)
            elapsed = time.time() - start_time
            self._update_times.append(elapsed)
            return {
                'action': 'initialized',
                'n_components': self.n_components,
                'total_observations': self._total_observations,
                'elapsed_s': elapsed
            }
        
        # Compute responsibilities
        log_weights, log_likelihoods = self._compute_log_posterior(observation)
        
        # Normalize to get responsibilities
        log_sum = np.max(log_weights)
        log_weights_normalized = log_weights - log_sum
        responsibilities = np.exp(log_weights_normalized)
        
        # Apply forget factor for non-stationary data
        if self.config.forget_factor < 1.0:
            responsibilities *= self.config.forget_factor
        
        # Find best matching component
        best_component = np.argmax(responsibilities)
        best_resp = responsibilities[best_component]
        
        # Decide: update existing or create new component
        if best_resp < 0.5 and self.n_components < self.config.max_components:
            # Create new component
            new_idx = self.n_components
            self._initialize_new_component(observation, new_idx)
            self.component_weights[new_idx] = 0.1  # Initial weight for new component
            action = 'new_component'
        else:
            # Update existing component
            action = 'update_existing'
            self._update_component(best_component, observation, responsibilities[best_component])
        
        # Normalize weights
        self._normalize_weights()
        
        # Prune small components
        self._prune_small_components()
        
        # Update ELBO
        self._update_elbo(observation, responsibilities)
        
        elapsed = time.time() - start_time
        self._update_times.append(elapsed)
        
        return {
            'action': action,
            'n_components': self.n_components,
            'total_observations': self._total_observations,
            'best_component': best_component,
            'responsibility': best_resp,
            'elapsed_s': elapsed
        }
    
    def _update_component(self, component_idx: int, observation: np.ndarray, 
                         responsibility: float) -> None:
        """Update a single component with new observation (vectorized)."""
        # Update variational parameters
        self.var_beta[component_idx] += responsibility
        self.var_kappa[component_idx] += responsibility
        self.var_nu[component_idx] += responsibility
        
        # Update mean
        self.var_m[component_idx] = (
            self.var_kappa[component_idx] * self.var_m[component_idx] + 
            responsibility * observation
        ) / (self.var_kappa[component_idx] + responsibility)
        
        # Update precision/covariance
        diff = observation - self.component_means[component_idx]
        outer_prod = np.dot(diff, diff.T)
        
        self.var_lambda[component_idx] = (
            self.var_lambda[component_idx] + 
            responsibility * outer_prod
        )
        
        # Update component mean and precision
        self.component_means[component_idx] = self.var_m[component_idx]
        self.component_precisions[component_idx] = (
            self.var_beta[component_idx] * self.var_lambda[component_idx] / 
            self.var_nu[component_idx]
        )
        
        # Ensure numerical stability
        self.component_precisions[component_idx] = np.clip(
            self.component_precisions[component_idx],
            self.config.min_precision,
            self.config.max_precision
        )
        self.component_covariances[component_idx] = np.linalg.inv(
            np.clip(self.component_precisions[component_idx], 
                   self.config.min_precision, self.config.max_precision)
        )
    
    def _normalize_weights(self) -> None:
        """Normalize component weights to sum to 1."""
        weights_sum = np.sum(self.component_weights[:self.n_components])
        if weights_sum > 0:
            self.component_weights[:self.n_components] /= weights_sum
        
        # Apply Dirichlet prior smoothing
        self.component_weights[:self.n_components] += 1e-6
        self.component_weights[:self.n_components] /= np.sum(
            self.component_weights[:self.n_components]
        )
    
    def _prune_small_components(self) -> None:
        """Remove components with very small weights to save memory."""
        if self.n_components <= 1:
            return
        
        # Find components to keep
        keep_mask = self.component_weights[:self.n_components] > self.config.min_component_weight
        n_keep = np.sum(keep_mask)
        
        if n_keep < self.n_components and n_keep > 1:
            # Compact arrays
            self.component_weights[:n_keep] = self.component_weights[:self.n_components][keep_mask]
            self.component_means[:n_keep] = self.component_means[:self.n_components][keep_mask]
            self.component_precisions[:n_keep] = self.component_precisions[:self.n_components][keep_mask]
            self.component_covariances[:n_keep] = self.component_covariances[:self.n_components][keep_mask]
            
            # Update variational parameters
            self.var_beta[:n_keep] = self.var_beta[:self.n_components][keep_mask]
            self.var_kappa[:n_keep] = self.var_kappa[:self.n_components][keep_mask]
            self.var_m[:n_keep] = self.var_m[:self.n_components][keep_mask]
            self.var_nu[:n_keep] = self.var_nu[:self.n_components][keep_mask]
            self.var_lambda[:n_keep] = self.var_lambda[:self.n_components][keep_mask]
            
            self.n_components = n_keep
            self.logger.debug(f"Pruned components, now {self.n_components} active")
    
    def _process_batch_update(self) -> Dict[str, Any]:
        """Process buffered observations in batch (optimized)."""
        if not self._observation_buffer:
            return {'action': 'no_observations', 'n_components': self.n_components}
        
        start_time = time.time()
        
        # Stack observations for vectorized processing
        observations = np.concatenate(self._observation_buffer, axis=0)
        n_obs = len(observations)
        
        # Compute responsibilities for all observations
        all_responsibilities = np.zeros((n_obs, self.n_components))
        
        for i, obs in enumerate(observations):
            log_weights, _ = self._compute_log_posterior(obs)
            log_sum = np.max(log_weights)
            all_responsibilities[i] = np.exp(log_weights - log_sum)
        
        # Aggregate updates
        for comp_idx in range(self.n_components):
            resp_sum = np.sum(all_responsibilities[:, comp_idx])
            if resp_sum > 0:
                # Weighted mean update
                weighted_obs = all_responsibilities[:, comp_idx:comp_idx+1] * observations
                self.var_m[comp_idx] = np.sum(weighted_obs, axis=0) / resp_sum
                
                # Update other variational parameters
                self.var_beta[comp_idx] += resp_sum
                self.var_kappa[comp_idx] += resp_sum
                self.var_nu[comp_idx] += resp_sum
        
        # Update all component parameters at once
        for comp_idx in range(self.n_components):
            self.component_means[comp_idx] = self.var_m[comp_idx]
            self.component_precisions[comp_idx] = (
                self.var_beta[comp_idx] * self.var_lambda[comp_idx] / 
                self.var_nu[comp_idx]
            )
            self.component_precisions[comp_idx] = np.clip(
                self.component_precisions[comp_idx],
                self.config.min_precision,
                self.config.max_precision
            )
            self.component_covariances[comp_idx] = np.linalg.inv(
                self.component_precisions[comp_idx]
            )
        
        # Normalize and prune
        self._normalize_weights()
        self._prune_small_components()
        
        # Update weights based on total responsibilities
        for comp_idx in range(self.n_components):
            self.component_weights[comp_idx] = np.sum(all_responsibilities[:, comp_idx])
        self._normalize_weights()
        
        # Clear buffer
        self._observation_buffer = []
        
        elapsed = time.time() - start_time
        self._update_times.append(elapsed)
        
        return {
            'action': 'batch_update',
            'n_observations': n_obs,
            'n_components': self.n_components,
            'elapsed_s': elapsed
        }
    
    def compute_anomaly_score(self, observation: np.ndarray) -> AnomalyScore:
        """
        Compute anomaly score for a single observation.
        
        Score is negative log posterior probability (higher = more anomalous).
        """
        start_time = time.time()
        
        if observation.ndim == 1:
            observation = observation.reshape(-1, 1)
        
        if self.n_components == 0:
            elapsed = time.time() - start_time
            self._score_times.append(elapsed)
            return AnomalyScore(
                score=float('inf'),
                timestamp=datetime.now(),
                n_components=0,
                uncertainty=1.0
            )
        
        # Compute log posterior for all components
        log_weights, log_likelihoods = self._compute_log_posterior(observation)
        
        # Sum log-likelihoods weighted by component weights
        log_likelihood = np.logaddexp.reduce(log_weights)
        
        # Anomaly score is negative log likelihood
        anomaly_score = -log_likelihood
        
        # Compute uncertainty (variance of log-likelihood across components)
        log_weights_normalized = log_weights - np.max(log_weights)
        probs = np.exp(log_weights_normalized)
        uncertainty = float(np.std(log_likelihoods))
        
        # Clamp score to reasonable range
        anomaly_score = float(np.clip(anomaly_score, -1000, 1000))
        
        elapsed = time.time() - start_time
        self._score_times.append(elapsed)
        
        return AnomalyScore(
            score=anomaly_score,
            timestamp=datetime.now(),
            n_components=self.n_components,
            uncertainty=uncertainty,
            best_component=int(np.argmax(log_likelihoods))
        )
    
    def compute_anomaly_scores_batch(self, observations: np.ndarray) -> List[AnomalyScore]:
        """
        Compute anomaly scores for multiple observations (vectorized).
        
        Args:
          observations: 2D array of shape (n_observations, n_features)
        
        Returns:
          List of AnomalyScore objects
        """
        start_time = time.time()
        
        if observations.ndim == 1:
            observations = observations.reshape(-1, 1)
        
        if self.n_components == 0:
            elapsed = time.time() - start_time
            self._score_times.append(elapsed)
            return [
                AnomalyScore(
                    score=float('inf'),
                    timestamp=datetime.now(),
                    n_components=0,
                    uncertainty=1.0
                ) for _ in range(len(observations))
            ]
        
        scores = []
        
        for obs in observations:
            obs = obs.reshape(-1, 1)
            log_weights, log_likelihoods = self._compute_log_posterior(obs)
            log_likelihood = np.logaddexp.reduce(log_weights)
            anomaly_score = -log_likelihood
            
            log_weights_normalized = log_weights - np.max(log_weights)
            probs = np.exp(log_weights_normalized)
            uncertainty = float(np.std(log_likelihoods))
            
            scores.append(AnomalyScore(
                score=float(np.clip(anomaly_score, -1000, 1000)),
                timestamp=datetime.now(),
                n_components=self.n_components,
                uncertainty=uncertainty,
                best_component=int(np.argmax(log_likelihoods))
            ))
        
        elapsed = time.time() - start_time
        self._score_times.append(elapsed)
        
        return scores
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the model."""
        return {
            'total_observations': self._total_observations,
            'n_components': self.n_components,
            'avg_update_time_s': np.mean(self._update_times) if self._update_times else 0.0,
            'max_update_time_s': np.max(self._update_times) if self._update_times else 0.0,
            'avg_score_time_s': np.mean(self._score_times) if self._score_times else 0.0,
            'cache_size': len(self._mahalanobis_cache),
            'elbo_current': self.elbo_history.get_recent_avg(),
            'elbo_converged': self.elbo_history.converged()
        }
    
    def _update_elbo(self, observation: np.ndarray, responsibilities: np.ndarray) -> None:
        """Update ELBO (Evidence Lower Bound) for convergence tracking."""
        # Simplified ELBO computation for tracking
        log_likelihood = np.logaddexp.reduce(
            np.log(self.component_weights[:self.n_components]) + 
            np.array([self._compute_log_likelihood(observation, i) 
                     for i in range(self.n_components)])
        )
        
        # Regularization term (simplified)
        regularization = -np.sum(responsibilities * np.log(responsibilities + 1e-10))
        
        elbo = log_likelihood + regularization
        self.elbo_history.add(float(elbo))
    
    def get_model_state(self) -> Dict[str, Any]:
        """Get serializable model state for checkpointing."""
        return {
            'n_components': self.n_components,
            'component_weights': self.component_weights[:self.n_components].tolist(),
            'component_means': self.component_means[:self.n_components].tolist(),
            'component_precisions': self.component_precisions[:self.n_components].tolist(),
            'var_beta': self.var_beta[:self.n_components].tolist(),
            'var_kappa': self.var_kappa[:self.n_components].tolist(),
            'var_m': self.var_m[:self.n_components].tolist(),
            'var_nu': self.var_nu[:self.n_components].tolist(),
            'var_lambda': self.var_lambda[:self.n_components].tolist(),
            'total_observations': self._total_observations,
            'config': {k: v for k, v in self.config.__dict__.items()}
        }

def compute_anomaly_score(model: DPGMMModel, observation: np.ndarray) -> AnomalyScore:
    """Convenience function to compute anomaly score."""
    return model.compute_anomaly_score(observation)

def compute_anomaly_scores_batch(model: DPGMMModel, observations: np.ndarray) -> List[AnomalyScore]:
    """Convenience function to compute batch anomaly scores."""
    return model.compute_anomaly_scores_batch(observations)

def main():
    """Main entry point for testing DPGMM performance."""
    logger = logging.getLogger(__name__)
    
    # Create configuration
    config = DPGMMConfig(
        alpha=1.0,
        batch_update_threshold=50,
        cache_mahalanobis=True,
        vectorize_updates=True,
        max_components=30
    )
    
    # Initialize model
    model = DPGMMModel(config)
    
    # Generate synthetic observations
    np.random.seed(42)
    n_observations = 1000
    observations = np.random.randn(n_observations, 1) * 0.5
    
    # Inject anomalies
    anomaly_indices = [100, 200, 500, 800]
    for idx in anomaly_indices:
        observations[idx] = np.array([5.0])  # Large anomaly
    
    # Process observations
    logger.info(f"Processing {n_observations} observations...")
    start_time = time.time()
    
    anomaly_scores = []
    for i, obs in enumerate(observations):
        obs = obs.reshape(-1, 1)
        
        # Update model
        update_result = model.update_streaming(obs)
        
        # Compute anomaly score
        score = model.compute_anomaly_score(obs)
        anomaly_scores.append(score.score)
        
        if i % 200 == 0:
            metrics = model.get_performance_metrics()
            logger.info(f"Observation {i}: {update_result['action']}, "
                       f"n_components={metrics['n_components']}, "
                       f"avg_update_time={metrics['avg_update_time_s']:.4f}s")
    
    elapsed = time.time() - start_time
    logger.info(f"Completed in {elapsed:.2f}s ({n_observations/elapsed:.0f} obs/s)")
    
    # Print performance metrics
    metrics = model.get_performance_metrics()
    logger.info(f"Performance metrics: {json.dumps(metrics, indent=2, default=str)}")
    
    # Detect anomalies
    threshold = np.percentile(anomaly_scores, 95)
    detected_anomalies = [i for i, score in enumerate(anomaly_scores) if score > threshold]
    logger.info(f"Detected {len(detected_anomalies)} anomalies (threshold={threshold:.2f})")
    logger.info(f"Actual anomalies at: {anomaly_indices}")
    
    return metrics

if __name__ == '__main__':
    main()
