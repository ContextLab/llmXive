import os
import json
import random
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict, field
import psutil
import sys

# Seed management
_seed_pinned = False
_current_seed = None

def pin_random_seed(seed: int = 42) -> None:
    global _seed_pinned, _current_seed
    random.seed(seed)
    _current_seed = seed
    _seed_pinned = True

def is_seed_pinned() -> bool:
    return _seed_pinned

def get_current_seed() -> Optional[int]:
    return _current_seed

# Data Models
@dataclass
class ResidueDataset:
    prime: int
    N: int
    residue_counts: Dict[int, int]
    total_computed: int
    timestamp: str
    seed_used: Optional[int] = None
    error_log: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class StatisticalResult:
    prime: int
    N: int
    p_value: float
    statistic: float
    passed: bool
    method: str
    timestamp: str

# Memory Guard
class MemoryGuard:
    def __init__(self, limit_percent: float = 90.0):
        self.limit_percent = limit_percent
        self.check_interval = 100000  # Check every N iterations

    def check(self, iteration: int) -> None:
        if iteration % self.check_interval == 0:
            mem = psutil.virtual_memory()
            if mem.percent >= self.limit_percent:
                raise MemoryError(
                    f"Memory usage {mem.percent}% exceeds limit {self.limit_percent}% at iteration {iteration}"
                )

# Logging
def log_error(message: str, n: Optional[int] = None) -> None:
    logger = logging.getLogger(__name__)
    if n is not None:
        logger.error(f"Error at n={n}: {message}")
    else:
        logger.error(message)

# Core Algorithms
def compute_phi_linear_sieve(N: int, guard: Optional[MemoryGuard] = None) -> List[int]:
    if N < 1:
        return []

    phi = [0] * (N + 1)
    phi[1] = 1
    primes = []
    is_prime = [True] * (N + 1)

    for i in range(2, N + 1):
        if guard:
            guard.check(i)

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

    return phi

def compute_residues(phi_values: List[int], prime: int) -> Dict[int, int]:
    counts = {k: 0 for k in range(prime)}
    for val in phi_values[1:]:  # Skip index 0
        r = val % prime
        counts[r] += 1
    return counts

def save_residue_dataset(dataset: ResidueDataset, filepath: str) -> None:
    """
    Serializes the ResidueDataset to a JSON file.
    Ensures directory exists before writing.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(dataset.to_dict(), f, indent=2)

def run_sieve_analysis(N: int, prime: int, output_path: str, seed: int = 42) -> ResidueDataset:
    """
    Orchestrates the sieve, residue calculation, error handling, and saving.
    """
    pin_random_seed(seed)
    timestamp = time.strftime("%Y-%m-%dT%H-%M-%S")
    guard = MemoryGuard(limit_percent=90.0)
    
    try:
        phi_values = compute_phi_linear_sieve(N, guard)
        counts = compute_residues(phi_values, prime)
        
        dataset = ResidueDataset(
            prime=prime,
            N=N,
            residue_counts=counts,
            total_computed=len(phi_values) - 1,
            timestamp=timestamp,
            seed_used=get_current_seed()
        )
        
        save_residue_dataset(dataset, output_path)
        return dataset

    except MemoryError as e:
        log_error(str(e))
        dataset = ResidueDataset(
            prime=prime,
            N=N,
            residue_counts={},
            total_computed=0,
            timestamp=timestamp,
            seed_used=get_current_seed(),
            error_log=str(e)
        )
        # Still save the failure record if path is valid, or re-raise
        if output_path:
            save_residue_dataset(dataset, output_path)
        raise e
    except Exception as e:
        log_error(f"Unexpected error: {str(e)}")
        dataset = ResidueDataset(
            prime=prime,
            N=N,
            residue_counts={},
            total_computed=0,
            timestamp=timestamp,
            seed_used=get_current_seed(),
            error_log=str(e)
        )
        if output_path:
            save_residue_dataset(dataset, output_path)
        raise e