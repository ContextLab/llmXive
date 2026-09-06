import os
import json
import random
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict

import numpy as np
import psutil

# Configuration and Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Random Seed Management (T007a) ---
_seed_pinned = False
_current_seed = None

def pin_random_seed(seed: int = 42) -> None:
    """Pin the random seed for reproducibility."""
    global _seed_pinned, _current_seed
    random.seed(seed)
    np.random.seed(seed)
    _current_seed = seed
    _seed_pinned = True
    logger.info(f"Random seed pinned to {_current_seed}")

def is_seed_pinned() -> bool:
    return _seed_pinned

def get_current_seed() -> Optional[int]:
    return _current_seed

# --- Data Classes ---
@dataclass
class ResidueDataset:
    """Container for residue counts and metadata."""
    prime: int
    N: int
    residue_counts: Dict[int, int]
    total_computed: int
    seed: Optional[int]
    timestamp: str

@dataclass
class StatisticalResult:
    """Container for statistical test results."""
    prime: int
    N: int
    statistic: float
    p_value: float
    passed: bool
    method: str
    timestamp: str

# --- Memory Guard (T004) ---
class MemoryGuard:
    """Monitors system memory usage and raises an error if limits are exceeded."""
    def __init__(self, limit_percent: float = 90.0):
        self.limit_percent = limit_percent
        self._process = psutil.Process(os.getpid())

    def check(self) -> None:
        """Check current memory usage. Raises MemoryError if >= limit."""
        mem_info = self._process.memory_info()
        # psutil.virtual_memory().percent is system-wide, process is per-process
        # The spec mentions "configured system limit" but typically in sieve we watch process to avoid OOM kill
        # We will use psutil.virtual_memory().percent as the primary guard for system pressure as per FR-007 interpretation
        mem_percent = psutil.virtual_memory().percent
        if mem_percent >= self.limit_percent:
            raise MemoryError(f"Memory usage ({mem_percent:.1f}%) exceeded limit ({self.limit_percent}%). Aborting.")

# --- Error Handling (T014) ---
def log_error(n: int, error: Exception) -> None:
    """Log specific error context including the value of n."""
    logger.error(f"Error detected at n={n}: {type(error).__name__}: {error}")
    # In a real pipeline, we might write this to a dedicated error log file
    # For now, logging to stderr/stdout via logger is sufficient

# --- Core Algorithms (T010, T011) ---
def compute_phi_linear_sieve(N: int) -> List[int]:
    """
    Compute Euler's totient function phi(n) for all n in [1, N] using a linear sieve.
    Returns a list where index i corresponds to phi(i).
    """
    if N < 1:
        return []

    phi = [0] * (N + 1)
    phi[1] = 1
    primes = []
    is_prime = [True] * (N + 1)

    # Linear Sieve
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

        # T012: Memory Guard Polling
        # Poll every 100,000 iterations or if memory is critically high
        if i % 100000 == 0:
            guard = MemoryGuard(limit_percent=90.0)
            guard.check()

    return phi

def compute_residues(phi_values: List[int], prime: int) -> Dict[int, int]:
    """
    Compute residue counts for phi(n) modulo `prime`.
    Returns a dictionary mapping residue -> count.
    """
    counts = {k: 0 for k in range(prime)}
    for val in phi_values[1:]: # Skip index 0 as phi is 1-based
        residue = val % prime
        counts[residue] += 1
    return counts

# --- Persistence (T013) ---
def save_residue_dataset(dataset: ResidueDataset, filepath: str) -> None:
    """
    Save a ResidueDataset to a JSON file.
    Ensures the directory exists before writing.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(asdict(dataset), f, indent=2)
    logger.info(f"Saved residue dataset to {filepath}")

def run_sieve_analysis(N: int, prime: int, seed: Optional[int] = None) -> ResidueDataset:
    """
    Orchestrates the sieve, residue computation, error handling, and saving.
    """
    if seed is not None:
        pin_random_seed(seed)

    start_time = time.time()
    logger.info(f"Starting sieve analysis for N={N}, prime={prime}")

    try:
        phi_values = compute_phi_linear_sieve(N)
        residue_counts = compute_residues(phi_values, prime)
    except MemoryError as e:
        logger.critical("Memory limit reached during sieve.")
        raise
    except Exception as e:
        # T014: Error Handling - Log the specific n if possible
        # Since the sieve returns a full list, we might not know the exact failing 'n'
        # without more granular tracking, but we log the general failure.
        log_error(N, e)
        raise

    end_time = time.time()
    logger.info(f"Computation finished in {end_time - start_time:.2f}s")

    dataset = ResidueDataset(
        prime=prime,
        N=N,
        residue_counts=residue_counts,
        total_computed=N,
        seed=get_current_seed(),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    # T013: Save the dataset
    # Construct path as per task: data/raw/residues_{prime}_{N}.json
    output_path = f"data/raw/residues_{prime}_{N}.json"
    save_residue_dataset(dataset, output_path)

    return dataset