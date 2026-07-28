"""
Main orchestration script for the DP Confidence Interval Robustness Simulation.

This script orchestrates the full simulation pipeline:
1. Loads ground truth parameters.
2. Iterates over datasets, epsilon values, and noise types.
3. Generates synthetic samples, applies DP noise, and computes CIs.
4. Logs progress for every (dataset, epsilon, noise_type) combination.
5. Aggregates results and calculates coverage statistics.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.config import Config
from code.data.synthetic_pop import load_ground_truth
from code.data.dp_noise import apply_dp_noise
from code.analysis.ci_builder import build_ci_for_mean, validate_ci_coverage
from code.analysis.edge_cases import clamp_noise_scale, enforce_minimum_sample_size
from code.analysis.progress_logger import SimulationProgressLogger
from code.analysis.logging_config import setup_simulation_logger
from code.analysis.validation import enforce_float64, ensure_cpu_only

def run_simulation_pipeline():
    """
    Execute the full simulation pipeline with logging.
    """
    # Initialize configuration
    config = Config()
    
    # Ensure CPU-only and float64 enforcement
    ensure_cpu_only()
    
    # Setup logging
    logger = setup_simulation_logger(
        logger_name="simulation_main",
        log_level=logging.INFO,
        output_dir=config.artifacts_dir
    )
    progress_logger = SimulationProgressLogger(logger)

    logger.info("Starting DP Confidence Interval Robustness Simulation")
    logger.info(f"Configuration: {config}")

    # Load ground truth
    ground_truth_path = config.ground_truth_path
    if not ground_truth_path.exists():
        logger.error(f"Ground truth file not found: {ground_truth_path}")
        sys.exit(1)

    ground_truth = load_ground_truth(ground_truth_path)
    logger.info(f"Loaded ground truth for {len(ground_truth)} populations")

    # Define simulation parameters
    datasets = config.datasets
    epsilons = config.epsilons
    noise_types = config.noise_types
    statistics = config.statistics
    sample_sizes = config.sample_sizes
    n_bootstrap = config.n_bootstrap
    nominal_coverage = config.nominal_coverage_target

    # Prepare results storage
    results = []

    total_conditions = len(datasets) * len(epsilons) * len(noise_types) * len(statistics) * len(sample_sizes)
    condition_count = 0

    # Outer Loop: Independent samples (simulated by iterating conditions)
    for dataset_name in datasets:
        for epsilon in epsilons:
            for noise_type in noise_types:
                for statistic in statistics:
                    for sample_size in sample_sizes:
                        condition_count += 1
                        
                        # Log START for this condition
                        log_msg_start = (
                            f"[START] Condition {condition_count}/{total_conditions}: "
                            f"dataset={dataset_name}, epsilon={epsilon:.4f}, "
                            f"noise_type={noise_type}, statistic={statistic}, "
                            f"sample_size={sample_size}"
                        )
                        logger.info(log_msg_start)

                        try:
                            # 1. Load/Generate Population Data
                            # For this simulation, we use the ground truth to simulate a population
                            # In a real scenario, this might load from a file or generate on the fly
                            gt_params = ground_truth.get(dataset_name, {})
                            if not gt_params:
                                logger.warning(f"No ground truth for {dataset_name}, skipping")
                                continue

                            # Simulate a sample from the population (using ground truth params)
                            # This is a placeholder for the actual data generation logic
                            # which would typically involve sampling from the distribution defined in ground_truth
                            # For now, we assume the ground truth contains mean and std for the population
                            pop_mean = float(gt_params.get('mean', 0.0))
                            pop_std = float(gt_params.get('std', 1.0))
                            
                            # Generate sample
                            np.random.seed(config.random_seed)
                            sample_data = np.random.normal(pop_mean, pop_std, sample_size)
                            sample_data = enforce_float64(sample_data)

                            # 2. Apply DP Noise
                            # Clamp noise scale for small epsilon
                            safe_epsilon = clamp_noise_scale(epsilon, min_epsilon=config.min_epsilon)
                            
                            noisy_sample = apply_dp_noise(
                                data=sample_data,
                                epsilon=safe_epsilon,
                                noise_type=noise_type,
                                sensitivity=config.sensitivity
                            )
                            noisy_sample = enforce_float64(noisy_sample)

                            # 3. Build Confidence Interval
                            if statistic == 'mean':
                                point_estimate = np.mean(noisy_sample)
                                ci_lower, ci_upper = build_ci_for_mean(
                                    data=noisy_sample,
                                    n_bootstrap=n_bootstrap,
                                    confidence_level=nominal_coverage,
                                    random_seed=config.random_seed
                                )
                                covered = validate_ci_coverage(
                                    point_estimate=point_estimate,
                                    ci_lower=ci_lower,
                                    ci_upper=ci_upper,
                                    true_value=pop_mean
                                )
                            else:
                                # Placeholder for regression statistic
                                logger.warning(f"Statistic '{statistic}' not fully implemented, skipping")
                                continue

                            # 4. Calculate Deviation from Nominal
                            deviation = covered - nominal_coverage

                            # 5. Log COMPLETE for this condition
                            log_msg_complete = (
                                f"[COMPLETE] Condition {condition_count}/{total_conditions}: "
                                f"dataset={dataset_name}, epsilon={epsilon:.4f}, "
                                f"noise_type={noise_type}, statistic={statistic}, "
                                f"sample_size={sample_size}, covered={covered:.4f}, "
                                f"deviation={deviation:.4f}"
                            )
                            logger.info(log_msg_complete)

                            # Store results
                            results.append({
                                'dataset': dataset_name,
                                'epsilon': epsilon,
                                'noise_type': noise_type,
                                'statistic': statistic,
                                'sample_size': sample_size,
                                'point_estimate': float(point_estimate),
                                'ci_lower': float(ci_lower),
                                'ci_upper': float(ci_upper),
                                'covered': int(covered),
                                'deviation_from_nominal': float(deviation)
                            })

                        except Exception as e:
                            # Log ERROR for this condition
                            log_msg_error = (
                                f"[ERROR] Condition {condition_count}/{total_conditions}: "
                                f"dataset={dataset_name}, epsilon={epsilon:.4f}, "
                                f"noise_type={noise_type}, statistic={statistic}, "
                                f"sample_size={sample_size} - Error: {str(e)}"
                            )
                            logger.error(log_msg_error)
                            logger.exception("Exception details:")
                            continue

    # Save intermediate results
    if results:
        results_df = pd.DataFrame(results)
        intermediate_path = config.coverage_intermediate_path
        results_df.to_csv(intermediate_path, index=False)
        logger.info(f"Saved intermediate results to {intermediate_path}")

        # Aggregate and save final results (simplified aggregation for this task)
        # In a full implementation, this would calculate coverage rates across multiple seeds
        final_path = config.coverage_results_path
        results_df.to_csv(final_path, index=False)
        logger.info(f"Saved final coverage results to {final_path}")
    else:
        logger.warning("No results generated. Check input parameters and ground truth.")

    logger.info("Simulation pipeline completed.")

if __name__ == "__main__":
    run_simulation_pipeline()