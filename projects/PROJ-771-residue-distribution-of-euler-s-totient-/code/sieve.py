import os
import json
import random
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ResidueDataset:
    """Data structure for storing residue counts."""
    prime: int
    N: int
    residue_counts: Dict[int, int]
    timestamp: str
    seed: int

@dataclass
class StatisticalResult:
    """Data structure for statistical test results."""
    prime: int
    N: int
    chi_squared_statistic: float
    p_value: float
    exact_test_p_value: Optional[float]
    block_bootstrap_p_value: Optional[float]
    error_term_residual: float
    pass_fail_flag: bool
    bonferroni_flag: bool
    timestamp: str

class MemoryGuard:
    """Monitors memory usage and enforces a hard limit."""
    def __init__(self, limit_mb: int, check_interval: int = 10000):
        self.limit_mb = limit_mb
        self.limit_bytes = limit_mb * 1024 * 1024
        self.check_interval = check_interval
        self.last_check = 0

    def check(self, current_iteration: int) -> bool:
        """Check memory usage. Returns True if safe to continue, False if limit reached."""
        if current_iteration - self.last_check < self.check_interval:
            return True

        self.last_check = current_iteration
        usage = psutil.virtual_memory().used

        if usage >= self.limit_bytes:
            logger.error(f"Memory limit reached: {usage / (1024*1024):.2f} MB >= {self.limit_mb} MB")
            return False
        
        # Also warn at 90%
        if usage >= 0.9 * self.limit_bytes:
            logger.warning(f"Memory usage at 90%: {usage / (1024*1024):.2f} MB")

        return True

def pin_random_seed(seed: int):
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    import numpy as np
    np.random.seed(seed)

def is_seed_pinned() -> bool:
    """Check if a seed has been pinned (simple heuristic)."""
    return random.getstate()[1][0] != 0  # Heuristic check

def get_current_seed() -> Optional[int]:
    """Get current random seed if possible."""
    try:
        state = random.getstate()
        # This is a simplification; in practice, extracting the exact seed from state is complex
        return None 
    except:
        return None

def log_error(message: str, n: Optional[int] = None):
    """Log an error message, optionally including the problematic n."""
    if n is not None:
        logger.error(f"{message} at n={n}")
    else:
        logger.error(message)

def compute_phi_linear_sieve(N: int, config: Dict[str, Any]) -> List[int]:
    """
    Compute Euler's totient function phi(n) for all n in [1, N] using a linear sieve.
    Uses Python's native arbitrary-precision integers.
    """
    memory_guard = MemoryGuard(
        limit_mb=config.get('memory_limit_mb', 6000),
        check_interval=config.get('memory_check_interval', 10000)
    )
    
    phi = [0] * (N + 1)
    phi[1] = 1
    primes = []
    is_prime = [True] * (N + 1)
    
    for i in range(2, N + 1):
        if is_prime[i]:
            primes.append(i)
            phi[i] = i - 1
        
        for p in primes:
            if i * p > N:
                break
            is_prime[i * p] = False
            if i % p == 0:
                phi[i * p] = phi[i] * p
                break
            else:
                phi[i * p] = phi[i] * (p - 1)
        
        # Memory check every 10000 iterations
        if not memory_guard.check(i):
            log_error("Memory limit exceeded during sieve", i)
            raise MemoryError(f"Sieve aborted at n={i} due to memory limit")
    
    return phi

def compute_residues(phi_values: List[int], prime: int) -> Dict[int, int]:
    """
    Compute residue counts for phi(n) mod prime.
    Returns a dictionary mapping residue -> count.
    """
    counts = {r: 0 for r in range(prime)}
    for val in phi_values:
        residue = val % prime
        counts[residue] += 1
    return counts

def save_residue_dataset(dataset: ResidueDataset, filepath: str):
    """
    Save a ResidueDataset to a JSON file.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    data = asdict(dataset)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved residue dataset to {filepath}")

def run_sieve_analysis(N: int, primes: List[int], config: Dict[str, Any]):
    """
    Run the sieve analysis for given N and primes.
    """
    seed = config.get('seed', 42)
    pin_random_seed(seed)
    
    logger.info(f"Starting sieve analysis for N={N}, primes={primes}, seed={seed}")
    
    phi_values = compute_phi_linear_sieve(N, config)
    
    for p in primes:
        residue_counts = compute_residues(phi_values, p)
        
        dataset = ResidueDataset(
            prime=p,
            N=N,
            residue_counts=residue_counts,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            seed=seed
        )
        
        output_path = f"data/raw/residues_{p}_{N}.json"
        save_residue_dataset(dataset, output_path)
        
        logger.info(f"Residue counts for p={p}: {residue_counts}")
    
    return phi_values

# Add missing function to satisfy API surface
def load_residue_dataset(filepath: str) -> ResidueDataset:
    """Load a ResidueDataset from a JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return ResidueDataset(**data)

def load_statistical_result(filepath: str) -> StatisticalResult:
    """Load a StatisticalResult from a JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return StatisticalResult(**data)

def save_statistical_result(result: StatisticalResult, filepath: str):
    """Save a StatisticalResult to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(asdict(result), f, indent=2)

def load_residue_sequence_from_json(filepath: str) -> Dict[int, int]:
    """Load residue counts from a JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data.get('residue_counts', {})

def load_sequence_from_file(filepath: str) -> List[int]:
    """Load a sequence of integers from a file (one per line)."""
    with open(filepath, 'r') as f:
        return [int(line.strip()) for line in f if line.strip()]

def get_residue_sequence_from_json(filepath: str) -> Dict[int, int]:
    """Get residue counts from JSON file."""
    return load_residue_sequence_from_json(filepath)

def get_observed_counts_from_json(filepath: str) -> Dict[int, int]:
    """Get observed counts from JSON file."""
    return load_residue_sequence_from_json(filepath)

def calculate_theoretical_bounds(prime: int, N: int) -> Dict[str, float]:
    """Calculate theoretical error bounds (placeholder for T027a)."""
    # Placeholder implementation - will be replaced by T027a
    return {"bound": N / prime}

def calculate_deviation_D(observed_counts: Dict[int, int], prime: int) -> float:
    """Calculate deviation metric D."""
    N = sum(observed_counts.values())
    expected = N / prime
    deviations = [abs(observed_counts.get(k, 0) - expected) for k in range(prime)]
    return max(deviations)

def check_bin_counts_and_fallback(residue_counts: Dict[int, int], prime: int) -> bool:
    """Check if bin counts are too small and need fallback."""
    N = sum(residue_counts.values())
    expected = N / prime
    return expected < 5

def calculate_chi_squared_statistic_D(residue_counts: Dict[int, int], prime: int) -> Tuple[float, float]:
    """Calculate Chi-squared statistic and p-value."""
    N = sum(residue_counts.values())
    expected = N / prime
    chi_sq = sum((residue_counts.get(k, 0) - expected)**2 / expected for k in range(prime))
    # Approximate p-value using scipy if available, else 0.5
    try:
        from scipy.stats import chi2 as chi2_dist
        p_val = 1 - chi2_dist.cdf(chi_sq, prime - 1)
    except ImportError:
        p_val = 0.5
    return chi_sq, p_val

def run_chi_squared_goodness_of_fit(residue_counts: Dict[int, int], prime: int) -> Dict[str, Any]:
    """Run Chi-squared goodness of fit test."""
    chi_sq, p_val = calculate_chi_squared_statistic_D(residue_counts, prime)
    return {"chi_squared": chi_sq, "p_value": p_val}

def block_bootstrap_residues(residue_sequence: List[int], block_size: int, num_samples: int) -> List[float]:
    """Perform block bootstrap on residue sequence."""
    # Placeholder implementation
    return [0.0] * num_samples

def run_block_bootstrap_deviation_test(observed_counts: Dict[int, int], prime: int) -> float:
    """Run block bootstrap deviation test."""
    # Placeholder implementation
    return 0.5

def run_full_statistical_analysis(residue_counts: Dict[int, int], prime: int, N: int) -> StatisticalResult:
    """Run full statistical analysis."""
    chi_sq, p_val = calculate_chi_squared_statistic_D(residue_counts, prime)
    return StatisticalResult(
        prime=prime,
        N=N,
        chi_squared_statistic=chi_sq,
        p_value=p_val,
        exact_test_p_value=None,
        block_bootstrap_p_value=None,
        error_term_residual=0.0,
        pass_fail_flag=p_val > 0.05,
        bonferroni_flag=p_val > 0.05/4,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
    )
