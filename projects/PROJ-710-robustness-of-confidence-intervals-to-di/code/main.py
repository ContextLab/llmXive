import os
import sys
import json
import logging
import tempfile
import shutil
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

# Project imports
from config import Config, get_artifact_path, get_data_path, get_figure_path
from data.dp_noise import inject_laplace_noise, inject_gaussian_noise
from data.synthetic_pop import generate_adult_population, generate_iris_population, generate_wine_population
from analysis.edge_cases import clamp_noise_scale, detect_collinearity, enforce_min_sample_size, get_edge_case_status
from analysis.ci_builder import bootstrap_resample, compute_percentile_ci, build_ci_for_mean, build_ci_for_regression_coefficient
from analysis.adjustments import apply_adjustments, compute_adjusted_ci

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_artifact_path('simulation.log'))
    ]
)
logger = logging.getLogger(__name__)

def load_population(dataset_name: str) -> pd.DataFrame:
    """
    Load the synthetic population for the specified dataset.
    The populations are generated on-the-fly based on config parameters.
    """
    logger.info(f"Loading population for dataset: {dataset_name}")
    if dataset_name == 'adult':
        return generate_adult_population()
    elif dataset_name == 'iris':
        return generate_iris_population()
    elif dataset_name == 'wine':
        return generate_wine_population()
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")

def run_simulation_condition(
    dataset_name: str,
    statistic_type: str,
    epsilon: float,
    noise_type: str,
    n_sim: int = 1000,
    bootstrap_n: int = 1000,
    confidence_level: float = 0.95
) -> List[Dict[str, Any]]:
    """
    Run the simulation loop for a single condition (dataset, statistic, epsilon, noise).
    
    This function implements the core logic:
    1. Load population
    2. Iterate N_sim times:
       a. Sample data
       b. Inject DP noise
       c. Apply bias/variance adjustments (T021b integration)
       d. Bootstrap resampling
       e. Construct CIs
       f. Check coverage
    3. Aggregate results
    """
    logger.info(f"Starting simulation for {dataset_name}, {statistic_type}, epsilon={epsilon}, {noise_type}")
    
    # Load population
    population = load_population(dataset_name)
    
    # Determine sample size (can be configurable)
    sample_size = min(1000, len(population))
    
    results = []
    
    # Pre-compute ground truth for coverage check
    if statistic_type == 'mean':
        # Assuming the target variable is 'income' for adult, or specific columns for others
        target_col = 'income' if dataset_name == 'adult' else population.columns[0]
        true_param = population[target_col].mean()
    elif statistic_type == 'regression':
        # For regression, we need to define X and y
        # Simplified: use first numeric column as y, second as X
        numeric_cols = population.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            raise ValueError(f"Need at least 2 numeric columns for regression in {dataset_name}")
        y_col, x_col = numeric_cols[0], numeric_cols[1]
        # Fit OLS on full population to get true coefficient
        from scipy import stats
        slope, intercept, r_value, p_value, std_err = stats.linregress(population[x_col], population[y_col])
        true_param = slope
    else:
        raise ValueError(f"Unknown statistic type: {statistic_type}")
    
    logger.info(f"True parameter value: {true_param}")
    
    for sim_idx in range(n_sim):
        # 1. Sample data
        sample = population.sample(n=sample_size, random_state=sim_idx)
        
        # 2. Inject DP noise
        if noise_type == 'laplace':
            noisy_data = inject_laplace_noise(sample, epsilon=epsilon, sensitivity=1.0)
        elif noise_type == 'gaussian':
            noisy_data = inject_gaussian_noise(sample, epsilon=epsilon, delta=1e-5, sensitivity=1.0)
        else:
            raise ValueError(f"Unknown noise type: {noise_type}")
        
        # 3. Apply adjustments (T021b Integration)
        # Calculate point estimate and SE from noisy data BEFORE bootstrap for adjustment
        if statistic_type == 'mean':
            target_col = 'income' if dataset_name == 'adult' else noisy_data.columns[0]
            point_est = noisy_data[target_col].mean()
            se_est = noisy_data[target_col].std() / np.sqrt(sample_size)
        elif statistic_type == 'regression':
            numeric_cols = noisy_data.select_dtypes(include=[np.number]).columns
            y_col, x_col = numeric_cols[0], numeric_cols[1]
            from scipy import stats
            slope, intercept, r_value, p_value, std_err = stats.linregress(noisy_data[x_col], noisy_data[y_col])
            point_est = slope
            se_est = std_err
        
        noise_params = {'epsilon': epsilon, 'noise_type': noise_type, 'sensitivity': 1.0}
        
        # Apply adjustments based on statistic_type
        try:
            adj_result = apply_adjustments(
                point_estimate=point_est,
                standard_error=se_est,
                statistic_type=statistic_type,
                noise_params=noise_params
            )
            adjusted_point_est = adj_result['adjusted_estimate']
            adjusted_se = adj_result['adjusted_se']
            adjustment_method = adj_result['method']
        except Exception as e:
            logger.warning(f"Adjustment failed for sim {sim_idx}: {e}. Using unadjusted.")
            adjusted_point_est = point_est
            adjusted_se = se_est
            adjustment_method = 'none'
        
        # 4. Bootstrap resampling on NOISY data
        bootstrap_estimates = []
        for _ in range(bootstrap_n):
            resample = noisy_data.sample(n=sample_size, replace=True, random_state=np.random.randint(0, 1000000))
            if statistic_type == 'mean':
                target_col = 'income' if dataset_name == 'adult' else resample.columns[0]
                boot_est = resample[target_col].mean()
            elif statistic_type == 'regression':
                numeric_cols = resample.select_dtypes(include=[np.number]).columns
                y_col, x_col = numeric_cols[0], numeric_cols[1]
                slope, _, _, _, _ = stats.linregress(resample[x_col], resample[y_col])
                boot_est = slope
            bootstrap_estimates.append(boot_est)
        
        # 5. Construct CIs
        ci_lower, ci_upper = compute_percentile_ci(bootstrap_estimates, confidence_level=confidence_level)
        
        # 6. Check coverage (Unadjusted)
        covered = (true_param >= ci_lower) and (true_param <= ci_upper)
        
        # 7. Check coverage (Adjusted)
        adj_ci_lower, adj_ci_upper = compute_adjusted_ci(
            adjusted_point_est, 
            adjusted_se, 
            confidence_level=confidence_level,
            bootstrap_dist=bootstrap_estimates
        )
        adj_covered = (true_param >= adj_ci_lower) and (true_param <= adj_ci_upper)
        
        results.append({
            'dataset': dataset_name,
            'statistic': statistic_type,
            'epsilon': epsilon,
            'noise_type': noise_type,
            'simulation_id': sim_idx,
            'true_param': true_param,
            'point_estimate': point_est,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'covered': covered,
            'adjusted_point_estimate': adjusted_point_est,
            'adjusted_ci_lower': adj_ci_lower,
            'adjusted_ci_upper': adj_ci_upper,
            'adjusted_coverage': adj_covered,
            'adjustment_method': adjustment_method
        })
        
        if (sim_idx + 1) % 100 == 0:
            logger.info(f"Completed {sim_idx + 1}/{n_sim} simulations")
    
    return results

def run_simulation_pipeline() -> None:
    """
    Run the full simulation pipeline across all datasets, statistics, and epsilon values.
    Writes results to artifacts/coverage_results.csv with atomic writes.
    """
    config = Config()
    datasets = config.datasets
    statistics = config.statistics
    epsilons = config.epsilons
    noise_types = config.noise_types
    n_sim = config.N_sim
    bootstrap_n = config.bootstrap_n
    confidence_level = config.confidence_level
    
    output_path = get_artifact_path('coverage_results.csv')
    temp_path = output_path + '.tmp'
    
    logger.info(f"Starting full simulation pipeline. Output: {output_path}")
    
    all_results = []
    
    for dataset in datasets:
        for stat in statistics:
            for eps in epsilons:
                for noise in noise_types:
                    logger.info(f"Running condition: {dataset}, {stat}, eps={eps}, {noise}")
                    results = run_simulation_condition(
                        dataset_name=dataset,
                        statistic_type=stat,
                        epsilon=eps,
                        noise_type=noise,
                        n_sim=n_sim,
                        bootstrap_n=bootstrap_n,
                        confidence_level=confidence_level
                    )
                    all_results.extend(results)
    
    # Atomic write
    logger.info(f"Writing {len(all_results)} results to {output_path}")
    df = pd.DataFrame(all_results)
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temp file first
    df.to_csv(temp_path, index=False)
    
    # Atomic rename
    shutil.move(temp_path, output_path)
    
    logger.info(f"Pipeline complete. Results saved to {output_path}")

def main():
    """Main entry point."""
    try:
        run_simulation_pipeline()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()