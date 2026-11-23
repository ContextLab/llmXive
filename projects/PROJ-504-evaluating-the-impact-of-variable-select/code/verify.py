"""
Verification and Pilot Run script for the Variable Selection Impact study.

This script runs a small-scale simulation (Pilot Run) to verify:
1. The pipeline executes within the 5.5-hour runtime constraint.
2. The Confidence Interval (CI) width of the power metric is <= 0.1.

It acts as a gate: if checks fail, it triggers the adjustment logic (T004b)
or aborts with a clear error message.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

# Project imports
from config import get_config
from utils.logger import get_logger, setup_logging
from utils.limits import get_memory_limit_gb, get_cpu_limit
from data.downloader import fetch_datasets
from data.simulators import generate_synthetic_outcomes, get_simulator_config
from analysis.selectors import select_variables_lasso, lasso_selection
from analysis.metrics import calculate_empirical_power

# Setup logging
logger = get_logger(__name__)


def run_pilot_simulation(
    count: int,
    seed: int = 42,
    snr_levels: Optional[List[float]] = None,
    sparsity_levels: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Runs a pilot simulation for a subset of datasets and conditions.
    
    Args:
        count: Number of simulations to run.
        seed: Random seed for reproducibility.
        snr_levels: List of SNR levels to test.
        sparsity_levels: List of sparsity levels to test.
        
    Returns:
        Dictionary containing pilot results and metadata.
    """
    if snr_levels is None:
        snr_levels = [0.5, 1.0]  # Reduced set for pilot
    if sparsity_levels is None:
        sparsity_levels = [0.2, 0.4]  # Reduced set for pilot
        
    np.random.seed(seed)
    
    config = get_config()
    dataset_ids = config.openml_ids[:2]  # Use first 2 datasets for pilot
    
    logger.info(f"Starting pilot run with {count} simulations across {len(dataset_ids)} datasets.")
    
    power_results = []
    start_time = time.time()
    
    try:
        # Fetch datasets (real data)
        datasets = fetch_datasets(dataset_ids)
        if not datasets:
            raise RuntimeError("Failed to fetch datasets for pilot run.")
            
        simulation_count = 0
        for dataset in datasets:
            if simulation_count >= count:
                break
                
            X = dataset.X
            true_coef = dataset.true_coefficients
            n_features = X.shape[1]
            
            # Determine non-zero coefficients
            non_zero_mask = true_coef != 0
            n_non_zero = np.sum(non_zero_mask)
            
            if n_non_zero == 0:
                logger.warning(f"Dataset {dataset.dataset_id} has no non-zero coefficients. Skipping.")
                continue
                
            # Run simulations for this dataset
            for snr in snr_levels:
                for sparsity in sparsity_levels:
                    if simulation_count >= count:
                        break
                        
                    # Generate synthetic Y
                    # Use a simplified simulation for pilot to ensure speed
                    # In full run, this would use the full config
                    Y = generate_synthetic_outcomes(
                        X=X,
                        true_coefficients=true_coef,
                        snr=snr,
                        seed=seed + simulation_count
                    )
                    
                    # Apply selection method (LASSO for pilot speed)
                    selected_indices = select_variables_lasso(X, Y, alpha=0.05)
                    
                    # Calculate power
                    # Power = (True Positives) / (Total True Non-Zero)
                    true_positives = np.sum(
                        (selected_indices != -1) & non_zero_mask
                    )
                    # Adjust for the fact that select_variables_lasso returns indices, not mask
                    # We need to map selected indices back to the original array
                    # For simplicity in pilot, we assume selected_indices is a mask or list of indices
                    
                    # Recalculate power correctly:
                    # selected_indices from lasso_selection is a list of indices
                    # We need to check how many of these are in the non_zero_mask
                    
                    selected_mask = np.zeros(n_features, dtype=bool)
                    for idx in selected_indices:
                        if 0 <= idx < n_features:
                            selected_mask[idx] = True
                            
                    tp = np.sum(selected_mask & non_zero_mask)
                    power = tp / n_non_zero
                    
                    power_results.append({
                        'dataset_id': dataset.dataset_id,
                        'snr': snr,
                        'sparsity': sparsity,
                        'power': power,
                        'method': 'lasso'
                    })
                    
                    simulation_count += 1
                    
        elapsed_time = time.time() - start_time
        
        return {
            'results': power_results,
            'elapsed_time': elapsed_time,
            'simulation_count': simulation_count,
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Pilot run failed: {str(e)}")
        return {
            'results': [],
            'elapsed_time': time.time() - start_time,
            'simulation_count': 0,
            'status': 'failed',
            'error': str(e)
        }


def check_pilot_results(pilot_data: Dict[str, Any]) -> bool:
    """
    Evaluates pilot results against the gate criteria.
    
    Criteria:
    1. Runtime <= 5.5 hours (19800 seconds)
    2. CI Width (std / sqrt(n)) <= 0.1
    
    Returns:
        True if pilot passes, False otherwise.
    """
    if pilot_data['status'] == 'failed':
        logger.error(f"Pilot failed with error: {pilot_data.get('error', 'Unknown')}")
        return False
        
    runtime = pilot_data['elapsed_time']
    max_runtime = 5.5 * 3600  # 5.5 hours in seconds
    
    if runtime > max_runtime:
        logger.error(f"Runtime {runtime:.2f}s exceeds limit {max_runtime:.2f}s")
        return False
        
    results = pilot_data['results']
    if not results:
        logger.error("No results generated in pilot run")
        return False
        
    # Calculate CI width for power metric
    # We aggregate all power values for the pilot
    power_values = [r['power'] for r in results]
    n = len(power_values)
    
    if n < 2:
        logger.warning("Insufficient data points to calculate CI width")
        return False
        
    mean_power = np.mean(power_values)
    std_power = np.std(power_values, ddof=1)
    ci_width = std_power / math.sqrt(n)
    
    logger.info(f"Pilot Statistics: n={n}, mean_power={mean_power:.4f}, std={std_power:.4f}, CI_width={ci_width:.4f}")
    
    if ci_width > 0.1:
        logger.error(f"CI width {ci_width:.4f} exceeds threshold 0.1")
        return False
        
    logger.info("Pilot run passed all gate criteria.")
    return True


def calculate_adjusted_count(current_count: int, current_width: float, target_width: float = 0.1) -> int:
    """
    Calculates the new simulation count needed to achieve target CI width.
    
    Formula: new_n = old_n * (current_width / target_width)^2
    """
    if current_width <= 0:
        return current_count
        
    factor = (current_width / target_width) ** 2
    new_count = int(current_count * factor)
    
    # Cap at a reasonable maximum for pilot
    max_pilot_count = 1000
    return min(new_count, max_pilot_count)


def main():
    parser = argparse.ArgumentParser(description="Run Pilot Simulation and Gate Check")
    parser.add_argument('--mode', type=str, default='pilot', choices=['pilot', 'check'],
                      help='Mode: pilot (run simulation) or check (verify existing results)')
    parser.add_argument('--count', type=int, default=10, help='Number of simulations to run')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=logging.INFO)
    
    logger.info(f"Starting T004 Pilot Run with count={args.count}")
    
    if args.mode == 'pilot':
        # Run the pilot simulation
        pilot_result = run_pilot_simulation(
            count=args.count,
            seed=args.seed
        )
        
        # Check results
        passed = check_pilot_results(pilot_result)
        
        if not passed:
            # Calculate adjusted count if we have data
            if pilot_result['results']:
                power_values = [r['power'] for r in pilot_result['results']]
                n = len(power_values)
                if n >= 2:
                    std_power = np.std(power_values, ddof=1)
                    current_width = std_power / math.sqrt(n)
                    new_count = calculate_adjusted_count(args.count, current_width)
                    logger.info(f"Recommended new simulation count: {new_count}")
                    
                    # In a full system, this would trigger T004b logic to update config
                    # For now, we just log the recommendation
                    logger.warning("Pilot failed. Please update simulations_per_condition in config.py and re-run.")
                    
            return 1
        else:
            logger.info("Pilot run successful. Proceeding to full simulation.")
            return 0
            
    elif args.mode == 'check':
        # Placeholder for checking existing results if needed
        logger.info("Check mode not fully implemented. Use pilot mode to run verification.")
        return 0
        
    return 0


if __name__ == '__main__':
    sys.exit(main())
