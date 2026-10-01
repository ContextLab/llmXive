import os
import sys
import logging
import csv
import math
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple
import scipy.stats as stats

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)
config = get_config()

def load_correlation_sequence(drift_metrics_path: str) -> List[float]:
    """Load the sequence of rho values from drift metrics."""
    rhos = []
    if not os.path.exists(drift_metrics_path):
        logger.warning(f"Drift metrics file not found: {drift_metrics_path}")
        return rhos
    
    with open(drift_metrics_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rhos.append(float(row['rho']))
    return rhos

def mann_kendall_test(data: List[float]) -> Tuple[float, str, float]:
    """
    Perform Mann-Kendall trend test.
    Returns: (Kendall's Tau, trend_direction, p_value)
    """
    if len(data) < 2:
        return 0.0, "insufficient_data", 1.0
    
    # Use scipy.stats.kendalltau for the test
    tau, p_value = stats.kendalltau(data, range(len(data)))
    
    if tau < -0.1:
        direction = "monotonic decrease"
    elif tau > 0.1:
        direction = "monotonic increase"
    else:
        direction = "no trend"
    
    return float(tau), direction, float(p_value)

def block_permutation_test(rhos: List[float], n_resamples: int = 1000, block_size: int = 2) -> float:
    """
    Perform block permutation test to assess significance of the correlation sequence.
    Returns p-value for the observed trend (mean rho) against null distribution.
    """
    if len(rhos) < 2:
        return 1.0
    
    # Observed statistic: mean of rho values
    observed_stat = sum(rhos) / len(rhos)
    
    # Block permutation: shuffle blocks of the sequence
    n_blocks = len(rhos) // block_size
    if n_blocks == 0:
        n_blocks = 1
        block_size = len(rhos)
    
    # Create blocks
    blocks = []
    for i in range(n_blocks):
        start = i * block_size
        end = start + block_size
        blocks.append(rhos[start:end])
    if len(rhos) > n_blocks * block_size:
        blocks.append(rhos[n_blocks * block_size:])
    
    permuted_stats = []
    for _ in range(n_resamples):
        random.shuffle(blocks)
        permuted_sequence = [val for block in blocks for val in block]
        permuted_stat = sum(permuted_sequence) / len(permuted_sequence)
        permuted_stats.append(permuted_stat)
    
    # Calculate p-value (two-tailed)
    count_extreme = sum(1 for s in permuted_stats if abs(s) >= abs(observed_stat))
    p_value = count_extreme / n_resamples
    
    return float(p_value)

def run_significance_tests(drift_metrics_path: str, output_path: str):
    """Run Mann-Kendall and block permutation tests on drift metrics."""
    rhos = load_correlation_sequence(drift_metrics_path)
    
    if not rhos:
        logger.warning("No correlation data found. Skipping significance tests.")
        # Write empty or minimal output
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['window_t', 'kendall_tau', 'trend_direction', 'p_value_mann_kendall', 'p_value_permutation'])
            writer.writeheader()
        return
    
    # Mann-Kendall test on the sequence
    tau, direction, p_mk = mann_kendall_test(rhos)
    logger.info(f"Mann-Kendall: Tau={tau:.4f}, Direction={direction}, p={p_mk:.4f}")
    
    # Block permutation test
    p_perm = block_permutation_test(rhos, n_resamples=1000, block_size=2)
    logger.info(f"Block Permutation: p={p_perm:.4f}")
    
    # Save results
    fieldnames = ['window_t', 'kendall_tau', 'trend_direction', 'p_value_mann_kendall', 'p_value_permutation']
    
    # For simplicity, we report the global test results on the first row
    # In a more complex scenario, we might report per-window or sliding window results
    results = [{
        'window_t': 'global',
        'kendall_tau': tau,
        'trend_direction': direction,
        'p_value_mann_kendall': p_mk,
        'p_value_permutation': p_perm
    }]
    
    # If we have enough windows, we could also report per-transition stats
    # But FR-008 specifies handling small sample sizes (n<10) by relying on permutation p-values
    # The global test covers the overall trend.
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved significance test results to {output_path}")
    
    return results

def main():
    """Entry point for significance tests."""
    config = get_config()
    drift_metrics_path = config.get('paths', {}).get('drift_metrics', 'outputs/drift_metrics.csv')
    output_path = config.get('paths', {}).get('significance_results', 'outputs/significance_test_results.csv')
    
    run_significance_tests(drift_metrics_path, output_path)

if __name__ == '__main__':
    main()
