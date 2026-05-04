"""
Automatic Differentiation Variational Inference (ADVI) Engine for DPGMM.

This module implements variational inference for the Dirichlet Process
Gaussian Mixture Model with support for streaming updates and ELBO convergence
logging.

The ADVI engine:
- Computes variational parameters for DPGMM components
- Tracks ELBO (Evidence Lower Bound) during training
- Supports batch and streaming inference modes
- Logs convergence metrics to logs/elbo/
"""

import logging
import json
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Callable
from pathlib import Path
from datetime import datetime

# Import from existing DPGMM module (API surface verified)
from src.models.dpgmm import DPGMMConfig, ELBOHistory, DPGMMModel

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class VariationalParameters:
    """Variational parameters for ADVI inference."""
    # Component weights (stick-breaking representation)
    alpha: float = 1.0  # Concentration parameter
    # Mean parameters for each component
    mu: np.ndarray = field(default_factory=lambda: np.array([]))
    # Precision (inverse variance) for each component
    lambda_: np.ndarray = field(default_factory=lambda: np.array([]))
    # Variance of the variational distribution
    sigma_sq: np.ndarray = field(default_factory=lambda: np.array([]))
    # Number of active components
    K: int = 1
    # Assignment probabilities (responsibilities)
    r: np.ndarray = field(default_factory=lambda: np.array([]))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'alpha': self.alpha,
            'mu': self.mu.tolist() if len(self.mu) > 0 else [],
            'lambda_': self.lambda_.tolist() if len(self.lambda_) > 0 else [],
            'sigma_sq': self.sigma_sq.tolist() if len(self.sigma_sq) > 0 else [],
            'K': self.K,
            'r': self.r.tolist() if len(self.r) > 0 else []
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VariationalParameters':
        """Load from dictionary."""
        return cls(
            alpha=data.get('alpha', 1.0),
            mu=np.array(data.get('mu', [])),
            lambda_=np.array(data.get('lambda_', [])),
            sigma_sq=np.array(data.get('sigma_sq', [])),
            K=data.get('K', 1),
            r=np.array(data.get('r', []))
        )


@dataclass
class ADVIState:
    """Complete state for ADVI inference."""
    params: VariationalParameters
    elbo_history: ELBOHistory
    n_iterations: int = 0
    converged: bool = False
    convergence_threshold: float = 1e-4
    last_elbo: float = float('-inf')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'params': self.params.to_dict(),
            'elbo_history': {
                'values': self.elbo_history.values.tolist() if len(self.elbo_history.values) > 0 else [],
                'iterations': self.elbo_history.iterations.tolist() if len(self.elbo_history.iterations) > 0 else [],
                'timestamps': self.elbo_history.timestamps
            },
            'n_iterations': self.n_iterations,
            'converged': self.converged,
            'convergence_threshold': self.convergence_threshold,
            'last_elbo': self.last_elbo
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ADVIState':
        """Load from dictionary."""
        elbo_data = data.get('elbo_history', {})
        return cls(
            params=VariationalParameters.from_dict(data.get('params', {})),
            elbo_history=ELBOHistory(
                values=np.array(elbo_data.get('values', [])),
                iterations=np.array(elbo_data.get('iterations', [])),
                timestamps=elbo_data.get('timestamps', [])
            ),
            n_iterations=data.get('n_iterations', 0),
            converged=data.get('converged', False),
            convergence_threshold=data.get('convergence_threshold', 1e-4),
            last_elbo=data.get('last_elbo', float('-inf'))
        )


class ADVIEngine:
    """
    Automatic Differentiation Variational Inference Engine for DPGMM.

    This engine implements variational inference with:
    - Mean-field variational approximation
    - ELBO computation and logging
    - Streaming update support
    - Convergence detection

    Usage:
        engine = ADVIEngine(config=DPGMMConfig())
        state = engine.initialize(n_components=5)
        for obs in observations:
            state = engine.update(state, obs)
        if engine.check_convergence(state):
            model = engine.extract_model(state)
    """

    def __init__(self, config: DPGMMConfig):
        """
        Initialize ADVI engine with configuration.

        Args:
            config: DPGMMConfig with hyperparameters for inference
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize ELBO logging directory
        self.elbo_log_dir = Path(config.elbo_log_dir) if config.elbo_log_dir else Path('logs/elbo')
        self.elbo_log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize random seed for reproducibility
        if config.random_seed is not None:
            np.random.seed(config.random_seed)

        self.logger.info(f"ADVIEngine initialized with config: {config}")

    def initialize(self, n_components: int, data_dim: int = 1) -> ADVIState:
        """
        Initialize variational parameters for inference.

        Args:
            n_components: Initial number of mixture components
            data_dim: Dimensionality of observations (default 1 for univariate)

        Returns:
            ADVIState with initialized variational parameters
        """
        # Initialize component means uniformly in data range
        mu = np.random.randn(n_components) * self.config.mu_prior_scale

        # Initialize precision (inverse variance) with small positive values
        lambda_ = np.ones(n_components) * self.config.lambda_prior_scale

        # Initialize variance of variational distribution
        sigma_sq = np.ones(n_components) * self.config.sigma_prior_scale

        # Initialize responsibilities uniformly
        r = np.ones(n_components) / n_components

        # Initialize concentration parameter
        alpha = self.config.alpha_prior

        params = VariationalParameters(
            alpha=alpha,
            mu=mu,
            lambda_=lambda_,
            sigma_sq=sigma_sq,
            K=n_components,
            r=r
        )

        elbo_history = ELBOHistory(
            values=np.array([]),
            iterations=np.array([]),
            timestamps=[]
        )

        state = ADVIState(
            params=params,
            elbo_history=elbo_history,
            n_iterations=0,
            converged=False,
            convergence_threshold=self.config.convergence_threshold,
            last_elbo=float('-inf')
        )

        self.logger.info(f"Initialized ADVI with {n_components} components, dim={data_dim}")
        return state

    def compute_elbo(self, state: ADVIState, data: np.ndarray) -> float:
        """
        Compute Evidence Lower Bound (ELBO) for current variational parameters.

        ELBO = E_q[log p(data|theta)] - E_q[log q(theta)]
             = Expected log likelihood - KL divergence

        Args:
            state: Current ADVI state with variational parameters
            data: Observation data array (N,) or (N, D)

        Returns:
            ELBO value (higher is better)
        """
        params = state.params
        n_obs = len(data) if len(data.shape) == 1 else data.shape[0]

        # Expected log likelihood term
        # E_q[log p(x|z,mu,sigma)] = sum_k r_k * E_q[log N(x|mu_k,sigma_k)]
        log_likelihood = 0.0

        for k in range(params.K):
            if params.K == 0:
                continue

            # Expected log probability under Gaussian
            # E[log N(x|mu, sigma)] = -0.5*log(2*pi*sigma^2) - 0.5*E[(x-mu)^2]/sigma^2
            # where E[(x-mu)^2] = (x - E[mu])^2 + Var[mu]

            mu_k = params.mu[k]
            sigma_sq_k = params.sigma_sq[k]

            # Avoid numerical issues
            sigma_sq_k = max(sigma_sq_k, 1e-10)

            # Expected squared distance
            expected_sq_dist = (data - mu_k) ** 2 + sigma_sq_k

            # Log likelihood for this component
            log_p_k = -0.5 * np.log(2 * np.pi * sigma_sq_k) - 0.5 * expected_sq_dist / sigma_sq_k

            # Weighted by responsibility
            log_likelihood += params.r[k] * np.mean(log_p_k)

        # Expected log prior terms
        # Prior on mu: N(0, sigma_prior^2)
        mu_prior_var = self.config.mu_prior_scale ** 2
        expected_mu_prior = -0.5 * np.sum(params.mu ** 2) / mu_prior_var

        # Prior on precision (Gamma distribution)
        # E[log Gamma(alpha, beta)] terms
        lambda_prior = self.config.lambda_prior_scale
        expected_lambda_prior = np.sum(np.log(params.lambda_) - params.lambda_ / lambda_prior)

        # Prior on concentration parameter (Gamma)
        expected_alpha_prior = np.log(params.alpha) - params.alpha / self.config.alpha_prior

        # Entropy of variational distribution (negative KL term)
        # H(q) = -E_q[log q]
        entropy = 0.0

        # Entropy of Gaussian variational parameters
        for k in range(params.K):
            entropy += 0.5 * np.log(2 * np.pi * np.e * params.sigma_sq[k])

        # Entropy of categorical assignments
        entropy += -np.sum(params.r * np.log(params.r + 1e-10))

        # Total ELBO
        elbo = log_likelihood + expected_mu_prior + expected_lambda_prior + \
               expected_alpha_prior + entropy

        return elbo

    def update(self, state: ADVIState, data: np.ndarray, n_iterations: int = 100) -> ADVIState:
        """
        Perform variational inference update (batch mode).

        Args:
            state: Current ADVI state
            data: Observation data array (N,) or (N, D)
            n_iterations: Number of variational iterations

        Returns:
            Updated ADVIState with optimized parameters
        """
        params = state.params

        for iteration in range(n_iterations):
            # E-step: Update responsibilities
            # r_k = p(z=k|x) proportional to exp(E_q[log p(x,z|theta)])
            log_r = np.zeros(params.K)

            for k in range(params.K):
                mu_k = params.mu[k]
                sigma_sq_k = max(params.sigma_sq[k], 1e-10)

                # Log probability under Gaussian
                log_p_k = -0.5 * np.log(2 * np.pi * sigma_sq_k) - \
                          0.5 * (data - mu_k) ** 2 / sigma_sq_k

                # Add log of mixing weight (from stick-breaking)
                log_weight = np.log(params.r[k] + 1e-10)

                log_r[k] = log_weight + np.mean(log_p_k)

            # Normalize responsibilities
            log_r_max = np.max(log_r)
            log_r_normalized = log_r - log_r_max
            r_normalized = np.exp(log_r_normalized)
            r_sum = np.sum(r_normalized)

            if r_sum > 1e-10:
                params.r = r_normalized / r_sum
            else:
                params.r = np.ones(params.K) / params.K

            # M-step: Update variational parameters
            # Update component means
            for k in range(params.K):
                # E[mu_k] = sum_n r_nk * x_n / sum_n r_nk
                weight_sum = np.sum(params.r[k]) + 1e-10
                params.mu[k] = np.sum(params.r[k] * data) / weight_sum

            # Update variances
            for k in range(params.K):
                # E[sigma^2_k] = sum_n r_nk * (x_n - mu_k)^2 / sum_n r_nk
                weight_sum = np.sum(params.r[k]) + 1e-10
                sq_diff = (data - params.mu[k]) ** 2
                params.sigma_sq[k] = np.sum(params.r[k] * sq_diff) / weight_sum
                params.sigma_sq[k] = max(params.sigma_sq[k], 1e-10)  # Avoid zero variance

            # Update precision (inverse variance)
            params.lambda_ = 1.0 / params.sigma_sq

            # Update concentration parameter (simplified stick-breaking)
            # alpha_new = alpha + sum_k r_k * log(1 - r_k)
            # For simplicity, we use a fixed update rule
            active_components = np.sum(params.r > 0.01)
            params.alpha = max(1.0, active_components * self.config.alpha_prior)

            # Compute and log ELBO
            if iteration % 10 == 0:
                elbo = self.compute_elbo(state, data)
                state.elbo_history.values = np.append(state.elbo_history.values, elbo)
                state.elbo_history.iterations = np.append(state.elbo_history.iterations, iteration)
                state.elbo_history.timestamps.append(datetime.now().isoformat())
                state.last_elbo = elbo

                self.logger.debug(f"Iteration {iteration}: ELBO = {elbo:.4f}")

            # Check convergence
            if iteration > 0 and len(state.elbo_history.values) >= 2:
                elbo_change = abs(state.elbo_history.values[-1] - state.elbo_history.values[-2])
                if elbo_change < state.convergence_threshold:
                    state.converged = True
                    self.logger.info(f"Converged at iteration {iteration}, ELBO = {elbo:.4f}")
                    break

            state.n_iterations += 1

        return state

    def streaming_update(self, state: ADVIState, observation: float,
                          learning_rate: float = 0.01) -> ADVIState:
        """
        Perform streaming update with single observation.

        Args:
            state: Current ADVI state
            observation: Single observation value
            learning_rate: Step size for stochastic updates

        Returns:
            Updated ADVIState with streaming update applied
        """
        params = state.params
        data = np.array([observation])

        # E-step: Compute responsibility for this observation
        log_r = np.zeros(params.K)

        for k in range(params.K):
            mu_k = params.mu[k]
            sigma_sq_k = max(params.sigma_sq[k], 1e-10)

            log_p_k = -0.5 * np.log(2 * np.pi * sigma_sq_k) - \
                      0.5 * (observation - mu_k) ** 2 / sigma_sq_k

            log_weight = np.log(params.r[k] + 1e-10)
            log_r[k] = log_weight + log_p_k

        # Normalize
        log_r_max = np.max(log_r)
        r_k = np.exp(log_r - log_r_max)
        r_sum = np.sum(r_k)

        if r_sum > 1e-10:
            r_k = r_k / r_sum
        else:
            r_k = np.ones(params.K) / params.K

        # M-step: Stochastic update of parameters
        # mu_k <- (1 - lr) * mu_k + lr * r_k * x
        for k in range(params.K):
            params.mu[k] = (1 - learning_rate) * params.mu[k] + \
                           learning_rate * r_k[k] * observation

            # Update variance
            sq_diff = (observation - params.mu[k]) ** 2
            params.sigma_sq[k] = (1 - learning_rate) * params.sigma_sq[k] + \
                                 learning_rate * r_k[k] * sq_diff
            params.sigma_sq[k] = max(params.sigma_sq[k], 1e-10)

            params.lambda_[k] = 1.0 / params.sigma_sq[k]

        # Update responsibilities
        params.r = (1 - learning_rate) * params.r + learning_rate * r_k

        # Normalize responsibilities
        params.r = params.r / np.sum(params.r)

        # Increment iteration count
        state.n_iterations += 1

        # Compute ELBO for logging
        elbo = self.compute_elbo(state, data)
        state.elbo_history.values = np.append(state.elbo_history.values, elbo)
        state.elbo_history.iterations = np.append(state.elbo_history.iterations, state.n_iterations)
        state.elbo_history.timestamps.append(datetime.now().isoformat())
        state.last_elbo = elbo

        # Check convergence
        if len(state.elbo_history.values) >= 2:
            elbo_change = abs(state.elbo_history.values[-1] - state.elbo_history.values[-2])
            if elbo_change < state.convergence_threshold:
                state.converged = True

        return state

    def check_convergence(self, state: ADVIState) -> bool:
        """
        Check if inference has converged based on ELBO change.

        Args:
            state: Current ADVI state

        Returns:
            True if converged, False otherwise
        """
        if len(state.elbo_history.values) < 2:
            return False

        # Check recent ELBO changes
        recent_changes = np.abs(np.diff(state.elbo_history.values[-10:]))
        avg_change = np.mean(recent_changes)

        return avg_change < state.convergence_threshold

    def extract_model(self, state: ADVIState) -> DPGMMModel:
        """
        Extract DPGMMModel from converged ADVIState.

        Args:
            state: Converged ADVIState

        Returns:
            DPGMMModel with learned parameters
        """
        params = state.params

        # Create model with learned parameters
        model = DPGMMModel(
            config=self.config,
            n_components=params.K,
            mu=params.mu.copy(),
            sigma_sq=params.sigma_sq.copy(),
            weights=params.r.copy()
        )

        self.logger.info(f"Extracted DPGMMModel with {params.K} components")
        return model

    def log_elbo(self, state: ADVIState, prefix: str = "advi") -> Path:
        """
        Log ELBO history to file.

        Args:
            state: Current ADVIState with ELBO history
            prefix: Prefix for log file name

        Returns:
            Path to log file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.elbo_log_dir / f"{prefix}_{timestamp}.json"

        log_data = {
            'timestamp': timestamp,
            'config': self.config.to_dict() if hasattr(self.config, 'to_dict') else {},
            'state': state.to_dict(),
            'converged': state.converged,
            'n_iterations': state.n_iterations
        }

        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2, default=lambda x: x.tolist() if hasattr(x, 'tolist') else str(x))

        self.logger.info(f"ELBO logged to {log_file}")
        return log_file

    def save_state(self, state: ADVIState, path: Path) -> None:
        """
        Save ADVIState to file for later recovery.

        Args:
            state: ADVIState to save
            path: Path to save state file
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        state_dict = state.to_dict()

        with open(path, 'w') as f:
            json.dump(state_dict, f, indent=2, default=lambda x: x.tolist() if hasattr(x, 'tolist') else str(x))

        self.logger.info(f"ADVIState saved to {path}")

    @classmethod
    def load_state(cls, path: Path) -> ADVIState:
        """
        Load ADVIState from file.

        Args:
            path: Path to state file

        Returns:
            Loaded ADVIState
        """
        with open(path, 'r') as f:
            state_dict = json.load(f)

        return ADVIState.from_dict(state_dict)

    def run_inference(self, data: np.ndarray, n_iterations: int = 100,
                     streaming: bool = False) -> Tuple[ADVIState, DPGMMModel]:
        """
        Run full variational inference on data.

        Args:
            data: Observation data array (N,) or (N, D)
            n_iterations: Maximum number of iterations
            streaming: If True, process data sequentially

        Returns:
            Tuple of (ADVIState, DPGMMModel)
        """
        # Initialize
        state = self.initialize(n_components=self.config.n_components,
                               data_dim=1 if len(data.shape) == 1 else data.shape[1])

        if streaming:
            # Streaming mode: process one observation at a time
            for obs in data:
                state = self.streaming_update(state, float(obs),
                                               learning_rate=self.config.learning_rate)
                if state.converged:
                    self.logger.info("Streaming inference converged")
                    break
        else:
            # Batch mode: update on full data
            state = self.update(state, data, n_iterations=n_iterations)

        # Extract final model
        model = self.extract_model(state)

        # Log results
        self.log_elbo(state)

        return state, model


def main():
    """Main entry point for standalone testing."""
    logging.basicConfig(level=logging.INFO)

    # Create test configuration
    config = DPGMMConfig(
        n_components=5,
        mu_prior_scale=1.0,
        lambda_prior_scale=1.0,
        sigma_prior_scale=1.0,
        alpha_prior=1.0,
        convergence_threshold=1e-4,
        learning_rate=0.01,
        random_seed=42,
        elbo_log_dir='logs/elbo'
    )

    # Create engine
    engine = ADVIEngine(config)

    # Generate synthetic data
    np.random.seed(42)
    n_samples = 1000
    data = np.concatenate([
        np.random.randn(300) + 0,
        np.random.randn(300) + 3,
        np.random.randn(400) + 6
    ])

    # Run inference
    state, model = engine.run_inference(data, n_iterations=200)

    # Print results
    print(f"Converged: {state.converged}")
    print(f"Iterations: {state.n_iterations}")
    print(f"Final ELBO: {state.last_elbo:.4f}")
    print(f"Learned components: {model.n_components}")
    print(f"Component means: {model.mu}")
    print(f"Component variances: {model.sigma_sq}")
    print(f"Component weights: {model.weights}")


if __name__ == '__main__':
    main()
