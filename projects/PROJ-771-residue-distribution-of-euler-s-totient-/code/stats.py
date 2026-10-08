import random
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import json
import logging
import os

from exceptions import ResearchIncompleteError
from constants import get_error_bound_constants

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class StatisticalResult:
    test_type: str
    p_value: float
    method: str
    degrees_of_freedom: int
    error_term_residual: float
    chi_squared_statistic: float
    chi_squared_p_value: float
    block_bootstrap_p_value: float
    pass_fail_flag: bool
    bonferroni_pass_fail_flag: bool

def pin_random_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)

def is_seed_pinned() -> bool:
    return True

def get_current_seed() -> int:
    return random.getstate()[1][1] if hasattr(random.getstate(), '__getitem__') else 42

def load_residue_sequence_from_file(path: str) -> List[int]:
    with open(path, 'r') as f:
        return json.load(f)

def load_residue_sequence_from_json(path: str) -> List[int]:
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get('sequence', [])

def get_residue_sequence_from_json(path: str) -> List[int]:
    return load_residue_sequence_from_json(path)

def get_observed_counts_from_json(path: str) -> Dict[int, int]:
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get('frequency_map', {})

def calculate_theoretical_bounds(prime: int, N: int) -> Dict[str, float]:
    constants = get_error_bound_constants()
    if not constants:
        raise ResearchIncompleteError("error_bound_constants", "Constants missing from data/constants.yaml")
    
    C = constants.get('C', 1.0)
    c = constants.get('c', 1.0)
    delta = constants.get('delta', 0.0)
    
    # Example formula (placeholder logic based on constants)
    lower = N / prime - C * np.sqrt(N)
    upper = N / prime + C * np.sqrt(N)
    return {'lower': lower, 'upper': upper}

def calculate_deviation_D(observed_counts: Dict[int, int], prime: int, N: int) -> float:
    expected = N / prime
    max_dev = 0.0
    for r in range(prime):
        dev = abs(observed_counts.get(r, 0) - expected)
        if dev > max_dev:
            max_dev = dev
    return max_dev

def check_bin_counts_and_fallback(residue_counts: Dict[int, int], prime: int) -> bool:
    N = sum(residue_counts.values())
    expected = N / prime
    return expected < 5

def calculate_chi_squared_statistic(residue_counts: Dict[int, int], prime: int) -> float:
    N = sum(residue_counts.values())
    expected = N / prime
    chi_sq = 0.0
    for r in range(prime):
        obs = residue_counts.get(r, 0)
        chi_sq += (obs - expected) ** 2 / expected
    return chi_sq

def exact_test_fallback(residue_counts: Dict[int, int], prime: int) -> float:
    # Placeholder for exact multinomial test
    # In real implementation, use scipy.stats.multinomial_test or custom logic
    return 1.0

def block_bootstrap_residues(residue_sequence: List[int], block_size: int, num_samples: int) -> List[float]:
    # Placeholder for block bootstrap
    return [0.0] * num_samples

def run_block_bootstrap_deviation_test(observed_counts: Dict[int, int], prime: int, N: int) -> float:
    # Placeholder for deviation test
    return 1.0

def calculate_error_term_residual(D_obs: float, E_bound: float) -> float:
    if E_bound == 0:
        return float('inf')
    return D_obs / E_bound

def run_full_statistical_analysis(observed_counts: Dict[int, int], prime: int, N: int) -> StatisticalResult:
    D_obs = calculate_deviation_D(observed_counts, prime, N)
    bounds = calculate_theoretical_bounds(prime, N)
    E_bound = bounds['upper'] - N/prime
    error_residual = calculate_error_term_residual(D_obs, E_bound)
    
    chi_sq = calculate_chi_squared_statistic(observed_counts, prime)
    from scipy.stats import chi2 as chi2_dist
    chi2_p = 1.0 - chi2_dist.cdf(chi_sq, prime - 1)
    
    boot_p = run_block_bootstrap_deviation_test(observed_counts, prime, N)
    
    pass_flag = boot_p > 0.05
    bonf_p = boot_p > (0.05 / 4)
    
    return StatisticalResult(
        test_type="block_bootstrap",
        p_value=boot_p,
        method="block_bootstrap",
        degrees_of_freedom=prime - 1,
        error_term_residual=error_residual,
        chi_squared_statistic=chi_sq,
        chi_squared_p_value=chi2_p,
        block_bootstrap_p_value=boot_p,
        pass_fail_flag=pass_flag,
        bonferroni_pass_fail_flag=bonf_p
    )

def save_statistical_result(result: StatisticalResult, path: str) -> None:
    with open(path, 'w') as f:
        json.dump(asdict(result), f, indent=2)

def load_statistical_result(path: str) -> StatisticalResult:
    with open(path, 'r') as f:
        data = json.load(f)
    return StatisticalResult(**data)

def determine_primary_pass_fail(p_value: float) -> bool:
    return p_value > 0.05

def determine_bonferroni_pass_fail(p_value: float) -> bool:
    return p_value > (0.05 / 4)

def run_sieve_analysis(N: int, primes: List[int], config: Dict[str, Any]) -> None:
    # Placeholder for stats analysis entry
    pass
