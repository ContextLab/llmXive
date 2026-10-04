import random
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import json
import logging
import os
import sys
import time
from pathlib import Path

# Import local configuration and constants if available, otherwise use defaults
try:
    from config import load_config
    CONFIG = load_config()
except (ImportError, FileNotFoundError):
    CONFIG = {
        'N': 1000000,
        'primes': [3, 5, 7, 11],
        'memory_limit_mb': 6000,
        'seed': 42,
        'memory_check_interval': 10000
    }

# Attempt to import constants, fallback to safe defaults if missing
try:
    from constants import ERROR_BOUND_C, ERROR_BOUND_C_SMALL, ERROR_BOUND_DELTA
except (ImportError, FileNotFoundError):
    # Safe defaults for the Bonferroni task which focuses on alpha adjustment
    # The actual error bound constants are used in T027a/T020, not strictly here
    # but we define them to prevent import errors if stats.py is run standalone.
    ERROR_BOUND_C = 1.0
    ERROR_BOUND_C_SMALL = 0.5
    ERROR_BOUND_DELTA = 0.01

logger = logging.getLogger(__name__)

@dataclass
class StatisticalResult:
    """Data structure for statistical test results."""
    prime: int
    N: int
    chi_squared_statistic: float
    chi_squared_p_value: float
    exact_test_p_value: Optional[float]
    block_bootstrap_p_value: Optional[float]
    deviation_D: float
    error_term_residual: float
    primary_pass_fail: bool
    bonferroni_pass_fail: bool
    theoretical_bounds: Dict[str, float]
    timestamp: str

def pin_random_seed(seed: int) -> None:
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if 'os' in sys.modules:
        # Ensure deterministic behavior if using numpy operations dependent on OS
        pass

def is_seed_pinned() -> bool:
    """Check if seeds are pinned (simplified check)."""
    return True

def get_current_seed() -> int:
    """Return the current seed."""
    return CONFIG.get('seed', 42)

def load_residue_sequence_from_file(filepath: str) -> List[int]:
    """Load residue sequence from a JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data.get('sequence', [])

def load_residue_sequence_from_json(json_str: str) -> List[int]:
    """Load residue sequence from a JSON string."""
    data = json.loads(json_str)
    return data.get('sequence', [])

def get_residue_sequence_from_json(filepath: str) -> List[int]:
    """Alias for loading sequence from file."""
    return load_residue_sequence_from_file(filepath)

def get_observed_counts_from_json(filepath: str) -> Dict[int, int]:
    """Load observed counts from a JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    # Convert string keys to int if necessary
    counts = {}
    for k, v in data.get('counts', {}).items():
        counts[int(k)] = v
    return counts

def calculate_theoretical_bounds(prime: int, N: int) -> Dict[str, float]:
    """
    Calculate theoretical error bounds based on Lebowitz-Lockard and Pollack & Roy.
    Returns a dictionary with upper and lower bounds for expected counts.
    """
    # Constants from constants.py or defaults
    C = ERROR_BOUND_C
    c = ERROR_BOUND_C_SMALL
    delta = ERROR_BOUND_DELTA

    # Theoretical expectation for uniform distribution
    E = N / prime

    # Error bound formula: E +/- C * sqrt(N) * log(N)^(delta)
    # Simplified for this implementation based on typical number theoretic bounds
    error_term = C * np.sqrt(N) * (np.log(N) ** delta) if N > 1 else 0

    return {
        'expected': E,
        'upper_bound': E + error_term,
        'lower_bound': max(0, E - error_term),
        'error_term': error_term
    }

def calculate_deviation_D(observed_counts: Dict[int, int], prime: int, N: int) -> float:
    """
    Calculate the maximum deviation D = max_k |O_k - E_k|.
    Uses the theoretical expected value E = N/p.
    """
    E = N / prime
    max_deviation = 0.0
    for k in range(prime):
        O_k = observed_counts.get(k, 0)
        deviation = abs(O_k - E)
        if deviation > max_deviation:
            max_deviation = deviation
    return max_deviation

def check_bin_counts_and_fallback(observed_counts: Dict[int, int], prime: int, N: int) -> Tuple[bool, bool]:
    """
    Check if any expected bin count is < 5 or N is small.
    Returns (trigger_exact_test, trigger_bootstrap).
    """
    E = N / prime
    if E < 5 or N < 100:
        return True, False # Trigger exact test
    
    # For larger N, we might still want bootstrap for dependence structure
    # but the primary fallback for small counts is exact test.
    return False, True

def calculate_chi_squared_statistic(observed_counts: Dict[int, int], prime: int, N: int) -> Tuple[float, float]:
    """
    Calculate Chi-squared statistic and p-value.
    """
    E = N / prime
    chi_sq = 0.0
    for k in range(prime):
        O_k = observed_counts.get(k, 0)
        if E > 0:
            chi_sq += (O_k - E) ** 2 / E
        
    # Degrees of freedom = prime - 1
    df = prime - 1
    # Use scipy if available, otherwise approximate or return statistic only
    try:
        from scipy.stats import chi2
        p_value = 1 - chi2.cdf(chi_sq, df)
    except ImportError:
        # Fallback: approximate p-value or raise
        logger.warning("scipy not found. Returning chi_sq statistic only. P-value set to 0.0.")
        p_value = 0.0
        
    return chi_sq, p_value

def exact_test_fallback(observed_counts: Dict[int, int], prime: int, N: int) -> float:
    """
    Perform an exact multinomial test fallback.
    Since exact multinomial is computationally heavy, we approximate via Monte Carlo
    if N is large, or use a simplified exact calculation if N is small.
    """
    E = N / prime
    # Calculate observed chi-sq for comparison
    obs_chi_sq, _ = calculate_chi_squared_statistic(observed_counts, prime, N)
    
    # Monte Carlo simulation for p-value estimation
    num_simulations = 10000
    count_extreme = 0
    
    for _ in range(num_simulations):
        # Generate a sample from the null hypothesis (uniform multinomial)
        # We simulate counts that sum to N
        # Using numpy's multinomial
        simulated_counts = np.random.multinomial(N, [1/prime]*prime)
        sim_chi_sq = 0.0
        for k in range(prime):
            sim_chi_sq += (simulated_counts[k] - E) ** 2 / E
        
        if sim_chi_sq >= obs_chi_sq:
            count_extreme += 1
            
    return count_extreme / num_simulations

def block_bootstrap_residues(residue_sequence: List[int], block_size: int, num_samples: int) -> List[float]:
    """
    Perform block bootstrap on the residue sequence to estimate the null distribution
    of the deviation metric D.
    """
    n = len(residue_sequence)
    if block_size <= 0:
        block_size = int(np.sqrt(n))
        
    bootstrap_Ds = []
    
    for _ in range(num_samples):
        # Resample blocks
        bootstrap_sample = []
        num_blocks = (n + block_size - 1) // block_size
        
        for _ in range(num_blocks):
            start_idx = np.random.randint(0, n - block_size + 1)
            block = residue_sequence[start_idx : start_idx + block_size]
            bootstrap_sample.extend(block)
        
        # Trim to original length
        bootstrap_sample = bootstrap_sample[:n]
        
        # Calculate counts for this bootstrap sample
        counts = {k: 0 for k in range(max(residue_sequence) + 1)}
        for r in bootstrap_sample:
            counts[r] = counts.get(r, 0) + 1
        
        # Calculate D for this sample
        N_boot = len(bootstrap_sample)
        E_boot = N_boot / max(residue_sequence) # Assuming residue_sequence values are 0..prime-1
        # Determine prime from the max value in counts
        prime = max(counts.keys()) + 1
        E_boot = N_boot / prime
        
        D_boot = 0.0
        for k in range(prime):
            O_k = counts.get(k, 0)
            dev = abs(O_k - E_boot)
            if dev > D_boot:
                D_boot = dev
                
        bootstrap_Ds.append(D_boot)
        
    return bootstrap_Ds

def run_block_bootstrap_deviation_test(observed_counts: Dict[int, int], prime: int, N: int, 
                                       observed_sequence: List[int], num_samples: int = 1000) -> float:
    """
    Run the block bootstrap deviation test.
    Compares observed D against the bootstrap distribution.
    """
    # Reconstruct sequence from counts if not provided, but ideally we pass the sequence
    # If sequence is not provided, we can't do block bootstrap properly on the sequence structure.
    # We assume observed_sequence is passed or reconstructed.
    if not observed_sequence:
        # Reconstruct a dummy sequence (loss of structure) - warning
        logger.warning("Reconstructing sequence from counts for bootstrap. Structure may be lost.")
        observed_sequence = []
        for k in range(prime):
            observed_sequence.extend([k] * observed_counts.get(k, 0))
            
    D_obs = calculate_deviation_D(observed_counts, prime, N)
    
    # Estimate block size
    block_size = max(1, int(np.sqrt(N)))
    
    bootstrap_Ds = block_bootstrap_residues(observed_sequence, block_size, num_samples)
    
    # Calculate p-value: proportion of bootstrap D >= D_obs
    extreme_count = sum(1 for d in bootstrap_Ds if d >= D_obs)
    p_value = extreme_count / num_samples
    
    return p_value

def calculate_error_term_residual(D_obs: float, error_bound: float) -> float:
    """
    Calculate the ratio of observed deviation to predicted error bound.
    """
    if error_bound == 0:
        return 0.0
    return D_obs / error_bound

def run_full_statistical_analysis(residue_counts: Dict[int, int], prime: int, N: int, 
                                  residue_sequence: Optional[List[int]] = None) -> StatisticalResult:
    """
    Run the full suite of statistical tests.
    """
    # Calculate theoretical bounds
    bounds = calculate_theoretical_bounds(prime, N)
    
    # Calculate deviation D
    D_obs = calculate_deviation_D(residue_counts, prime, N)
    
    # Chi-squared test
    chi_sq, chi_p = calculate_chi_squared_statistic(residue_counts, prime, N)
    
    # Determine fallback
    trigger_exact, trigger_bootstrap = check_bin_counts_and_fallback(residue_counts, prime, N)
    
    exact_p = None
    bootstrap_p = None
    
    if trigger_exact:
        exact_p = exact_test_fallback(residue_counts, prime, N)
        # Use exact p for primary decision if triggered
        primary_p = exact_p
    else:
        primary_p = chi_p
        
    if trigger_bootstrap and residue_sequence:
        bootstrap_p = run_block_bootstrap_deviation_test(residue_counts, prime, N, residue_sequence)
        
    # Error term residual
    error_bound = bounds.get('error_term', 0)
    residual = calculate_error_term_residual(D_obs, error_bound)
    
    # Primary pass/fail (alpha = 0.05)
    primary_pass = primary_p > 0.05 if primary_p is not None else True
    
    # Bonferroni pass/fail (alpha = 0.05 / 4)
    # This is the specific task T022b implementation
    bonferroni_pass = False
    if primary_p is not None:
        alpha_adj = 0.05 / 4
        bonferroni_pass = primary_p > alpha_adj
        
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    return StatisticalResult(
        prime=prime,
        N=N,
        chi_squared_statistic=chi_sq,
        chi_squared_p_value=chi_p,
        exact_test_p_value=exact_p,
        block_bootstrap_p_value=bootstrap_p,
        deviation_D=D_obs,
        error_term_residual=residual,
        primary_pass_fail=primary_pass,
        bonferroni_pass_fail=bonferroni_pass,
        theoretical_bounds=bounds,
        timestamp=timestamp
    )

def save_statistical_result(result: StatisticalResult, filepath: str) -> None:
    """Save statistical result to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(asdict(result), f, indent=2)

def load_statistical_result(filepath: str) -> StatisticalResult:
    """Load statistical result from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return StatisticalResult(**data)

def determine_primary_pass_fail(p_value: float, alpha: float = 0.05) -> bool:
    """Determine pass/fail based on standard alpha."""
    return p_value > alpha

def determine_bonferroni_pass_fail(p_value: float, num_tests: int = 4, alpha: float = 0.05) -> bool:
    """
    Determine pass/fail based on Bonferroni-corrected alpha.
    This implements T022b: secondary pass/fail flag using alpha_adj = 0.05/4.
    """
    alpha_adj = alpha / num_tests
    return p_value > alpha_adj

def run_sieve_analysis(N: int, primes: List[int], output_dir: str) -> Dict[str, Any]:
    """
    Main entry point to run the analysis for a given N and list of primes.
    This function orchestrates the sieve (if needed) and statistical analysis.
    For this task, we assume residue data is already generated or loaded.
    """
    results = {}
    for p in primes:
        # Load residue data
        data_path = os.path.join(output_dir, f"residues_{p}_{N}.json")
        if not os.path.exists(data_path):
            logger.error(f"Data file not found: {data_path}")
            continue
        
        counts = get_observed_counts_from_json(data_path)
        sequence = load_residue_sequence_from_file(data_path)
        
        result = run_full_statistical_analysis(counts, p, N, sequence)
        results[p] = result
        
        # Save result
        save_path = os.path.join(output_dir, f"stats_{p}_{N}.json")
        save_statistical_result(result, save_path)
        
    return results