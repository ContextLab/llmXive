import os
import json
import random
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict, field
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/sieve.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ResidueDataset:
    """Dataclass to hold residue counts for a specific prime and range."""
    prime: int
    N: int
    residue_counts: Dict[int, int]
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    seed: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResidueDataset':
        return cls(**data)


@dataclass
class StatisticalResult:
    """Dataclass to hold statistical test results."""
    prime: int
    N: int
    chi_squared_statistic: Optional[float] = None
    chi_squared_p_value: Optional[float] = None
    exact_test_p_value: Optional[float] = None
    block_bootstrap_p_value: Optional[float] = None
    deviation_metric_D: Optional[float] = None
    error_term_residual: Optional[float] = None
    pass_fail_flag: Optional[bool] = None
    bonferroni_pass_fail_flag: Optional[bool] = None
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatisticalResult':
        return cls(**data)


class MemoryGuard:
    """Monitors memory usage and enforces a hard limit."""
    def __init__(self, limit_mb: int, check_interval: int = 10000):
        self.limit_mb = limit_mb
        self.check_interval = check_interval
        self.limit_bytes = limit_mb * 1024 * 1024

    def check(self, iteration: int) -> bool:
        """Check memory usage. Returns True if safe, False if limit exceeded."""
        if iteration % self.check_interval == 0:
            usage = psutil.virtual_memory()
            used_bytes = usage.used
            if used_bytes >= self.limit_bytes:
                logger.warning(f"Memory limit reached at iteration {iteration}: {used_bytes / (1024**2):.2f}MB / {self.limit_mb}MB")
                return False
            if usage.percent >= 90:
                logger.warning(f"Memory usage critical at iteration {iteration}: {usage.percent}%")
                return False
        return True


def pin_random_seed(seed: int):
    """Pin the random seed for reproducibility."""
    random.seed(seed)
    # Note: numpy seed handled in run_analysis.py as per API surface
    import numpy as np
    np.random.seed(seed)


def is_seed_pinned() -> bool:
    """Check if a seed has been pinned (simple heuristic)."""
    # In a real scenario, we might track this with a global flag
    return True


def get_current_seed() -> Optional[int]:
    """Get the current seed (placeholder implementation)."""
    return 42


def log_error(message: str, n: Optional[int] = None):
    """Log an error message, optionally including the problematic n."""
    if n is not None:
        logger.error(f"Error at n={n}: {message}")
    else:
        logger.error(f"{message}")


def compute_phi_linear_sieve(N: int, memory_guard: MemoryGuard) -> List[int]:
    """
    Compute Euler's totient function phi(n) for all n in [1, N]
    using a linear sieve algorithm.
    
    Args:
        N: Upper bound of the range
        memory_guard: MemoryGuard instance to check memory usage
        
    Returns:
        List of phi values where index i corresponds to phi(i)
        
    Raises:
        MemoryError: If memory limit is exceeded
        RuntimeError: If sieve fails or overflow detected
    """
    if N < 1:
        raise ValueError("N must be at least 1")
        
    phi = [0] * (N + 1)
    phi[0] = 0
    phi[1] = 1
    primes = []
    is_prime = [True] * (N + 1)
    
    for i in range(2, N + 1):
        # Check memory every check_interval iterations
        if not memory_guard.check(i):
            raise MemoryError(f"Memory limit exceeded at iteration {i}")
        
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
    
    # Final check for large N
    if not memory_guard.check(N):
        raise MemoryError(f"Memory limit exceeded at final iteration {N}")
        
    return phi


def compute_residues(phi_values: List[int], prime: int) -> Dict[int, int]:
    """
    Compute residue counts for phi(n) mod p.
    
    Args:
        phi_values: List of phi values from compute_phi_linear_sieve
        prime: The prime modulus
        
    Returns:
        Dictionary mapping residue class to count
    """
    counts = {k: 0 for k in range(prime)}
    for i in range(1, len(phi_values)):
        residue = phi_values[i] % prime
        counts[residue] += 1
    return counts


def save_residue_dataset(dataset: ResidueDataset, output_path: str) -> None:
    """
    Save a ResidueDataset to a JSON file.
    
    Args:
        dataset: The ResidueDataset to save
        output_path: Path to the output JSON file
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(dataset.to_dict(), f, indent=2)
    
    logger.info(f"Saved residue dataset to {output_path}")


def load_residue_dataset(input_path: str) -> ResidueDataset:
    """
    Load a ResidueDataset from a JSON file.
    
    Args:
        input_path: Path to the input JSON file
        
    Returns:
        ResidueDataset instance
    """
    with open(input_path, 'r') as f:
        data = json.load(f)
    return ResidueDataset.from_dict(data)


def save_statistical_result(result: StatisticalResult, output_path: str) -> None:
    """Save a StatisticalResult to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    logger.info(f"Saved statistical result to {output_path}")


def load_statistical_result(input_path: str) -> StatisticalResult:
    """Load a StatisticalResult from a JSON file."""
    with open(input_path, 'r') as f:
        data = json.load(f)
    return StatisticalResult.from_dict(data)


def load_residue_sequence_from_json(input_path: str) -> List[int]:
    """Load residue sequence from a JSON file (helper)."""
    with open(input_path, 'r') as f:
        data = json.load(f)
    # Assuming data structure matches what we save
    return data.get('residue_counts', {})


def load_sequence_from_file(input_path: str) -> List[int]:
    """Load sequence from a file (placeholder)."""
    # This would need specific format handling
    raise NotImplementedError("Format not specified")


def get_residue_sequence_from_json(input_path: str) -> Dict[int, int]:
    """Get residue sequence from JSON file."""
    data = load_residue_dataset(input_path)
    return data.residue_counts


def get_observed_counts_from_json(input_path: str) -> Dict[int, int]:
    """Get observed counts from JSON file."""
    return get_residue_sequence_from_json(input_path)


def calculate_theoretical_bounds(prime: int, N: int) -> Dict[str, float]:
    """Calculate theoretical error bounds (placeholder)."""
    # This would use formulas from literature
    return {"upper": N / prime, "lower": N / prime}


def calculate_deviation_D(observed_counts: Dict[int, int], expected_counts: Dict[int, float]) -> float:
    """Calculate deviation metric D."""
    max_deviation = 0.0
    for k, observed in observed_counts.items():
        expected = expected_counts.get(k, 0)
        deviation = abs(observed - expected)
        if deviation > max_deviation:
            max_deviation = deviation
    return max_deviation


def check_bin_counts_and_fallback(residue_counts: Dict[int, int], prime: int) -> bool:
    """Check if any expected bin count < 5 to trigger fallback."""
    N = sum(residue_counts.values())
    expected = N / prime
    return expected < 5


def calculate_chi_squared_statistic_D(residue_counts: Dict[int, int], prime: int) -> Tuple[float, float]:
    """Calculate Chi-squared statistic and p-value."""
    N = sum(residue_counts.values())
    expected = N / prime
    
    chi_sq = 0.0
    for k, observed in residue_counts.items():
        chi_sq += (observed - expected) ** 2 / expected
    
    # Degrees of freedom = prime - 1
    from scipy.stats import chi2
    p_value = 1 - chi2.cdf(chi_sq, prime - 1)
    
    return chi_sq, p_value


def run_chi_squared_goodness_of_fit(residue_counts: Dict[int, int], prime: int) -> Dict[str, Any]:
    """Run Chi-squared goodness of fit test."""
    chi_sq, p_value = calculate_chi_squared_statistic_D(residue_counts, prime)
    return {"chi_squared": chi_sq, "p_value": p_value}


def block_bootstrap_residues(residue_sequence: List[int], block_size: int, num_samples: int) -> List[float]:
    """Perform block bootstrap on residue sequence."""
    # Placeholder implementation
    return [0.0] * num_samples


def run_block_bootstrap_deviation_test(observed_counts: Dict[int, int], prime: int) -> float:
    """Run block bootstrap deviation test."""
    # Placeholder implementation
    return 0.5


def run_full_statistical_analysis(residue_counts: Dict[int, int], prime: int) -> StatisticalResult:
    """Run full statistical analysis."""
    chi_sq, p_value = calculate_chi_squared_statistic_D(residue_counts, prime)
    return StatisticalResult(
        prime=prime,
        N=sum(residue_counts.values()),
        chi_squared_statistic=chi_sq,
        chi_squared_p_value=p_value,
        pass_fail_flag=(p_value >= 0.05)
    )


def exact_test_fallback(residue_counts: Dict[int, int], prime: int) -> float:
    """Exact test fallback for small bin counts."""
    # Placeholder implementation
    return 0.5


def run_sieve_analysis(N: int, primes: List[int], config: Dict[str, Any]) -> None:
    """
    Run the full sieve analysis for given N and primes.
    
    Args:
        N: Upper bound for phi calculation
        primes: List of primes to compute residues for
        config: Configuration dictionary
    """
    seed = config.get('seed', 42)
    memory_limit_mb = config.get('memory_limit_mb', 6000)
    check_interval = config.get('memory_check_interval', 10000)
    
    pin_random_seed(seed)
    memory_guard = MemoryGuard(memory_limit_mb, check_interval)
    
    logger.info(f"Starting sieve analysis for N={N}, primes={primes}")
    
    try:
        phi_values = compute_phi_linear_sieve(N, memory_guard)
        logger.info(f"Computed phi values for N={N}")
    except MemoryError as e:
        log_error(str(e))
        raise
    except Exception as e:
        log_error(f"Sieve failed: {str(e)}")
        raise
    
    for prime in primes:
        try:
            residue_counts = compute_residues(phi_values, prime)
            
            # Error handling before save (T014 requirement)
            if any(v < 0 for v in residue_counts.values()):
                log_error("Negative residue count detected", n=N)
                raise RuntimeError("Invalid residue counts detected")
            
            # Create dataset
            dataset = ResidueDataset(
                prime=prime,
                N=N,
                residue_counts=residue_counts,
                seed=seed
            )
            
            # Save to JSON (T013 requirement)
            output_path = f"data/raw/residues_{prime}_{N}.json"
            save_residue_dataset(dataset, output_path)
            
            logger.info(f"Saved residue counts for prime={prime}, N={N} to {output_path}")
            
        except Exception as e:
            log_error(f"Failed to process prime={prime}: {str(e)}", n=N)
            raise
    
    logger.info("Sieve analysis completed successfully")
