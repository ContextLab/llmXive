from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import json
import hashlib
from pathlib import Path
import psutil
import os

@dataclass
class SyntheticDataset:
    """Container for a generated synthetic dataset and its metadata."""
    data: np.ndarray  # Shape (n, p)
    n: int
    p: int
    rho: float
    distribution_type: str
    seed: int
    sha256: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n": self.n,
            "p": self.p,
            "rho": self.rho,
            "distribution_type": self.distribution_type,
            "seed": self.seed,
            "sha256": self.sha256
        }

@dataclass
class SimulationConfig:
    """Configuration for a simulation run."""
    n_values: List[int]
    p_values: List[int]
    rho_values: List[float]
    distribution_types: List[str]
    n_iterations: int
    seed: int = 42
    memory_limit_gb: float = 6.0

@dataclass
class SimulationResult:
    """Result of a single simulation iteration or batch."""
    config: Dict[str, Any]
    p_values: List[float]
    ks_statistic: Optional[float] = None
    bootstrap_ci: Optional[Tuple[float, float]] = None
    seed: int = 0

def get_current_rss_mb() -> float:
    """Return current Resident Set Size in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def check_memory_limit(limit_gb: float = 6.0) -> bool:
    """
    Check if current RSS exceeds the limit.
    Returns True if limit exceeded, False otherwise.
    Logs a warning if exceeded (does not raise).
    """
    current_mb = get_current_rss_mb()
    limit_mb = limit_gb * 1024
    if current_mb > limit_mb:
        import warnings
        warnings.warn(f"Memory usage {current_mb:.2f} MB exceeds limit {limit_mb:.2f} MB")
        return True
    return False

class SimulationOrchestrator:
    """Manages simulation iterations, seeds, and parameter sweeps."""
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.rng = np.random.default_rng(config.seed)

    def generate_seeds(self, count: int) -> List[int]:
        """Generate deterministic seeds for iterations."""
        return [int(self.rng.integers(0, 2**31)) for _ in range(count)]

def calculate_minimum_iterations(effect_size: float = 0.05, power: float = 0.8, alpha: float = 0.05) -> int:
    """
    Calculate the minimum simulation iteration count required to achieve
    statistical power >= `power` for detecting a KS statistic deviation > `effect_size`.

    Uses the normal approximation for the Kolmogorov-Smirnov statistic.
    Under the null (uniform p-values), KS ~ N(0, 1/sqrt(N)).
    To detect a deviation of `effect_size`, we need:
    Power = P(Z > z_alpha - effect_size * sqrt(N))
    
    Solving for N:
    z_beta = z_alpha - effect_size * sqrt(N)
    sqrt(N) = (z_alpha - z_beta) / effect_size
    N = ((z_alpha - z_beta) / effect_size)^2

    Where:
    - z_alpha is the critical value for significance level alpha (one-sided)
    - z_beta is the critical value for power (1 - beta), where beta is Type II error

    Parameters:
    - effect_size: Minimum detectable KS deviation (e.g., 0.05)
    - power: Desired statistical power (e.g., 0.8)
    - alpha: Significance level (e.g., 0.05)

    Returns:
    - int: Minimum number of iterations (simulations) required.
    """
    from scipy.stats import norm

    # Critical values
    z_alpha = norm.ppf(1 - alpha)
    z_beta = norm.ppf(power)

    # Calculate N
    # Note: The formula for sample size in KS test context often involves
    # the standard deviation of the KS statistic. For uniform distribution,
    # the asymptotic variance is 1/(12*N) for the mean, but for the max deviation
    # (KS), the distribution is complex. However, a common approximation for
    # power analysis in simulation studies (detecting a shift in the distribution)
    # treats the KS statistic as a mean-like estimator with std dev ~ 1/sqrt(N).
    
    # Standard approximation for detecting a shift D:
    # N >= ( (z_alpha + z_beta) / D )^2
    
    numerator = z_alpha + z_beta
    n_iterations = (numerator / effect_size) ** 2

    return int(np.ceil(n_iterations))

# Example usage if run directly (for verification)
if __name__ == "__main__":
    min_iters = calculate_minimum_iterations(effect_size=0.05, power=0.8)
    print(f"Minimum iterations for power 0.8 detecting KS > 0.05: {min_iters}")
    # Expected output: approx 1083 ( (1.645 + 0.84) / 0.05 )^2 ≈ 2485?
    # Let's re-verify the standard formula:
    # z_0.95 = 1.645, z_0.80 = 0.8416
    # (1.645 + 0.8416) / 0.05 = 49.732
    # 49.732^2 ≈ 2473.
    # The code implements this standard approximation.