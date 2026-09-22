from __future__ import annotations

import hashlib
import json
import logging
import multiprocessing
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
from scipy import stats

from .exceptions import HighDimensionalInstabilityError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    """Configuration for a single simulation run."""
    n: int  # Sample size
    p: int  # Number of features
    rho: float  # Correlation parameter
    distribution_type: str  # 'normal', 't_dist', 'skewed_normal'
    seed: int
    iteration: int


@dataclass
class SyntheticDataset:
    """Container for generated synthetic data."""
    data: np.ndarray
    config: SimulationConfig
    correlation_matrix: np.ndarray


class RNGWrapper:
    """
    Deterministic RNG Wrapper to ensure bit-for-bit reproducibility.
    Ensures that resetting seed + advancing 'step' count produces identical sequences.
    """
    _current_seed: Optional[int] = None
    _step_count: int = 0

    @classmethod
    def reset(cls, seed: int) -> None:
        """Reset the global numpy random state to a specific seed."""
        np.random.seed(seed)
        cls._current_seed = seed
        cls._step_count = 0

    @classmethod
    def advance(cls, steps: int = 1) -> None:
        """Advance the RNG state by consuming 'steps' random draws (no-op for state, just bookkeeping)."""
        # In this context, we rely on np.random.seed(seed) before generation.
        # This method is a placeholder for complex state tracking if needed later.
        cls._step_count += steps

    @classmethod
    def get_state(cls) -> Any:
        """Return the current random state."""
        return np.random.get_state()

    @classmethod
    def set_state(cls, state: Any) -> None:
        """Set the random state."""
        np.random.set_state(state)


class MemoryMonitor:
    """
    Monitor memory usage (RSS) and abort if it exceeds a hard threshold.
    Satisfies SC-004 (Computational feasibility) as a hard constraint.
    """
    def __init__(self, threshold_gb: float = 7.0):
        self.threshold_bytes = int(threshold_gb * 1024 * 1024 * 1024)

    def check_and_abort(self) -> None:
        """Check current RSS memory. If > threshold, exit immediately."""
        try:
            # Use resource module for Unix-like systems (Linux/Mac)
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            rss_bytes = usage.ru_maxrss * 1024  # ru_maxrss is in KB on Linux

            if rss_bytes > self.threshold_bytes:
                logger.error(
                    f"CRITICAL: Memory usage ({rss_bytes / (1024**3):.2f} GB) "
                    f"exceeds threshold ({self.threshold_bytes / (1024**3):.2f} GB). "
                    "Aborting simulation to satisfy SC-004."
                )
                sys.exit(1)
        except ImportError:
            # Fallback for Windows or if resource is unavailable
            logger.warning("Resource module not available. Skipping memory check.")

def generate_correlated_data(n: int, p: int, rho: float, dist_type: str, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic high-dimensional data with controlled correlation.
    Returns: (data_matrix, correlation_matrix)
    """
    rng = np.random.default_rng(seed)
    
    # Construct correlation matrix: Compound Symmetry
    # Sigma_ij = rho if i != j, 1 if i == j
    if p == 1:
        corr_matrix = np.array([[1.0]])
    else:
        corr_matrix = np.full((p, p), rho)
        np.fill_diagonal(corr_matrix, 1.0)

    # Ensure positive semi-definiteness (critical for Cholesky)
    # Check eigenvalues
    eigvals = np.linalg.eigvalsh(corr_matrix)
    if np.min(eigvals) < -1e-10:
        # Attempt simple regularization if slightly negative
        if np.min(eigvals) > -0.1:
            corr_matrix += np.eye(p) * (abs(np.min(eigvals)) + 1e-6)
        else:
            raise HighDimensionalInstabilityError(
                f"Correlation matrix not PSD for n={n}, p={p}, rho={rho}. Min eig: {np.min(eigvals)}"
            )

    # Cholesky decomposition
    try:
        L = np.linalg.cholesky(corr_matrix)
    except np.linalg.LinAlgError:
        # Fallback regularization
        corr_matrix += np.eye(p) * 1e-6
        L = np.linalg.cholesky(corr_matrix)

    # Generate standard normal data
    Z = rng.standard_normal((n, p))
    
    # Transform to correlated normal
    X = Z @ L.T

    # Apply distribution violations if requested
    if dist_type == 't_dist':
        # Heavy-tailed: transform to t-distribution
        # Use inverse CDF or direct sampling
        # Direct sampling: X_t = Z_t / sqrt(Chi2/df)
        df = 3.0
        chi2 = rng.chisquare(df, size=(n, p))
        X = X / np.sqrt(chi2 / df)
    elif dist_type == 'skewed_normal':
        # Skewed: Add skewness
        skew_param = 2.0
        # Simple skewing: X_skew = X + skew * X^2 (approx)
        # Better: Use SN distribution logic
        # For simplicity in this context, we apply a skew transformation
        X = X + skew_param * (X**2 - 1)
        # Re-center to mean 0
        X -= np.mean(X, axis=0)

    return X, corr_matrix


def calculate_power_for_iterations(
    target_power: float = 0.8,
    threshold: float = 0.05,
    max_iterations: int = 10000,
    step: int = 100
) -> int:
    """
    Calculate the minimum number of iterations required to achieve statistical power >= target_power
    for detecting a KS statistic deviation > threshold.
    
    This function performs a power analysis by simulating the distribution of the KS statistic
    under the alternative hypothesis (deviation exists) and estimating the sample size (iterations)
    needed to reject the null hypothesis (KS <= threshold) with the specified power.
    
    Parameters:
        target_power: Desired statistical power (default 0.8)
        threshold: The KS deviation threshold to detect (default 0.05)
        max_iterations: Upper bound for search
        step: Step size for iteration search
        
    Returns:
        int: Minimum iterations required
    """
    # We simulate the KS statistic distribution for a known deviation.
    # Assumption: Under high-dimensional noise with correlation, the KS statistic
    # typically deviates from 0. We simulate this "effect size" based on a small pilot.
    
    pilot_iterations = 500
    pilot_results = []
    
    # Run a pilot to estimate the effect size (mean KS and std dev)
    # We assume a "worst-case" scenario (high rho, high p/n) to be conservative
    pilot_n, pilot_p, pilot_rho = 50, 5000, 0.9
    pilot_seed = 12345
    
    for i in range(pilot_iterations):
        seed = pilot_seed + i
        X, _ = generate_correlated_data(pilot_n, pilot_p, pilot_rho, 'normal', seed)
        
        # Simulate p-values under null (t-test on columns of X, comparing to 0 mean)
        # Since data is centered, p-values should be uniform if theory holds.
        # We compute KS statistic against Uniform(0,1)
        pvals = []
        for j in range(X.shape[1]):
            col = X[:, j]
            t_stat, p_val = stats.ttest_1samp(col, 0.0)
            pvals.append(p_val)
        
        pvals = np.array(pvals)
        # KS statistic against uniform
        ks_stat, _ = stats.kstest(pvals, 'uniform')
        pilot_results.append(ks_stat)
    
    pilot_ks = np.array(pilot_results)
    effect_mean = np.mean(pilot_ks)
    effect_std = np.std(pilot_ks)
    
    # If the pilot shows no deviation (unlikely in high-dim), we can't calculate power meaningfully.
    if effect_mean <= threshold:
        logger.warning("Pilot study shows no significant deviation. Assuming conservative estimate.")
        effect_mean = threshold + 0.02 # Assume a small effect exists
        effect_std = 0.01

    # Power calculation logic:
    # We want P(KS > threshold | H1) >= target_power
    # Assuming KS statistics are approximately normal (Central Limit Theorem for the mean of KS stats? 
    # Actually, we are looking at the distribution of the KS statistic itself across iterations).
    # We treat the observed KS values as samples from N(mu, sigma).
    # We need to find N such that the probability of observing a mean KS > threshold is >= power.
    # However, the task asks for "iterations" to detect a deviation.
    # Standard power analysis for a mean:
    # Z = (threshold - mu) / (sigma / sqrt(N))
    # We want P(Z < (threshold - mu)/(sigma/sqrt(N))) = 1 - power (for one-sided test)
    # Actually, we want to detect deviation > threshold.
    # H0: mu <= threshold, H1: mu > threshold.
    # We reject H0 if observed_mean > threshold + Z_alpha * (sigma/sqrt(N)).
    # Power = P(reject H0 | H1 is true) = P(observed_mean > threshold + Z_alpha * sigma/sqrt(N) | mu = effect_mean)
    # Z_beta = (threshold + Z_alpha * sigma/sqrt(N) - effect_mean) / (sigma/sqrt(N))
    # We want Z_beta = -Z_power (where Z_power is the z-score for the desired power).
    # Solving for N:
    # (effect_mean - threshold) / (sigma/sqrt(N)) = Z_alpha + Z_power
    # sqrt(N) = (Z_alpha + Z_power) * sigma / (effect_mean - threshold)
    # N = ((Z_alpha + Z_power) * sigma / (effect_mean - threshold))^2
    
    # Standard alpha = 0.05
    alpha = 0.05
    z_alpha = stats.norm.ppf(1 - alpha)
    z_power = stats.norm.ppf(target_power)
    
    diff = effect_mean - threshold
    if diff <= 0:
        # Effect is not distinguishable from threshold
        return max_iterations
        
    n_required = ((z_alpha + z_power) * effect_std / diff) ** 2
    n_required = int(np.ceil(n_required))
    
    # Ensure it's within bounds
    if n_required < 10:
        n_required = 10
    if n_required > max_iterations:
        n_required = max_iterations
        
    logger.info(f"Power analysis result: Estimated iterations = {n_required} "
                f"(Effect mean={effect_mean:.4f}, threshold={threshold}, std={effect_std:.4f})")
    return n_required


def run_power_analysis(output_path: str = "data/sweep/power_analysis_result.json") -> Dict[str, Any]:
    """
    Run the power analysis and write the result to the specified JSON file.
    """
    iterations = calculate_power_for_iterations()
    power = 0.8 # Target power
    threshold = 0.05
    
    result = {
        "iterations": iterations,
        "power": power,
        "threshold": threshold
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Power analysis result written to {output_path}")
    return result


class SimulationOrchestrator:
    """Manages iterations, seeds, and parameter sweeps."""
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.memory_monitor = MemoryMonitor()

    def run_iteration(self, iteration_idx: int) -> SyntheticDataset:
        """Run a single iteration of the simulation."""
        self.memory_monitor.check_and_abort()
        
        # Deterministic seed generation
        seed = self.config.seed + (iteration_idx * 10000)
        
        # Generate data
        data, corr_matrix = generate_correlated_data(
            self.config.n, 
            self.config.p, 
            self.config.rho, 
            self.config.distribution_type,
            seed
        )
        
        return SyntheticDataset(
            data=data,
            config=SimulationConfig(
                n=self.config.n,
                p=self.config.p,
                rho=self.config.rho,
                distribution_type=self.config.distribution_type,
                seed=seed,
                iteration=iteration_idx
            ),
            correlation_matrix=corr_matrix
        )

def main():
    """Entry point for direct execution (e.g., for power analysis)."""
    import argparse
    parser = argparse.ArgumentParser(description="Run power analysis or simulation.")
    parser.add_argument('--mode', choices=['power', 'sim'], default='power', help='Mode to run')
    parser.add_argument('--output', type=str, default='data/sweep/power_analysis_result.json', help='Output path for power analysis')
    
    args = parser.parse_args()
    
    if args.mode == 'power':
        run_power_analysis(args.output)
    else:
        logger.error("Simulation mode not fully implemented in this snippet.")

if __name__ == "__main__":
    main()