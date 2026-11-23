import os
import sys
import json
import logging
import tempfile
import shutil
import tracemalloc
import gc
from pathlib import Path
from typing import Generator, List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Local imports
from config import Config, get_artifact_path, get_data_path
from data.download_utils import load_real_dataset, DataFetchError
from data.dp_noise import inject_laplace_noise, inject_gaussian_noise
from analysis.edge_cases import clamp_noise_scale, detect_collinearity, enforce_min_sample_size
from analysis.ci_builder import build_ci_for_mean, validate_ci_coverage
from analysis.adjustments import apply_adjustments
from utils.feasibility_check import run_micro_benchmark

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
MAX_MEMORY_GB = 7.0
N_SIM = Config.N_SIM
BOOTSTRAP_B = Config.BOOTSTRAP_B

def get_memory_usage_gb() -> float:
    """
    Returns current memory usage in GB using tracemalloc.
    """
    if not tracemalloc.is_tracing():
        return 0.0
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 ** 3)

def check_feasibility_gate() -> bool:
    """
    Runs the feasibility check micro-benchmark.
    Returns True if the gate passes, False otherwise.
    """
    try:
        result = run_micro_benchmark()
        if result.get('status') == 'failed':
            logger.error(f"Feasibility check failed: {result.get('reason')}")
            return False
        logger.info(f"Feasibility check passed: {result}")
        return True
    except Exception as e:
        logger.error(f"Feasibility check error: {e}")
        return False

def load_real_dataset(dataset_name: str) -> pd.DataFrame:
    """
    Wrapper to load real UCI datasets.
    Raises DataFetchError if fetch fails (no synthetic fallback).
    """
    return load_real_dataset(dataset_name)

def run_simulation_condition(
    dataset_name: str,
    epsilon: float,
    noise_type: str,
    statistic_type: str = 'mean'
) -> Generator[Dict[str, Any], None, None]:
    """
    Generator that yields simulation results for a single condition.
    Implements memory optimization by yielding results immediately instead of storing all.
    
    Yields:
        Dict containing simulation results for one run.
    """
    logger.info(f"Starting simulation for {dataset_name}, epsilon={epsilon}, noise={noise_type}")
    
    # Load real data
    try:
        df = load_real_dataset(dataset_name)
    except DataFetchError as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise
    
    # Determine target column based on dataset and statistic
    if dataset_name == 'adult':
        target_col = 'hours-per-week' # Example numeric target
    elif dataset_name == 'iris':
        target_col = 'sepal length (cm)'
    elif dataset_name == 'wine':
        target_col = 'alcohol'
    else:
        raise ValueError(f"Unsupported dataset for simulation: {dataset_name}")
    
    # Validate data
    df = df.dropna(subset=[target_col])
    if len(df) < 10:
        raise ValueError(f"Dataset {dataset_name} has insufficient samples after cleaning.")
    
    true_mean = df[target_col].mean()
    logger.info(f"Ground truth mean for {dataset_name}: {true_mean:.4f}")
    
    for i in range(N_SIM):
        # Periodic memory check and cleanup
        if i > 0 and i % 100 == 0:
            gc.collect()
            mem_gb = get_memory_usage_gb()
            if mem_gb > MAX_MEMORY_GB:
                logger.warning(f"Memory usage at {mem_gb:.2f}GB exceeded threshold at iteration {i}")
        
        # 1. Draw sample
        sample_size = min(100, len(df))
        sample = df[target_col].sample(n=sample_size, replace=False).values
        
        # 2. Add DP Noise
        if noise_type == 'laplace':
            noisy_sample = inject_laplace_noise(sample, epsilon, sensitivity=1.0)
        elif noise_type == 'gaussian':
            noisy_sample = inject_gaussian_noise(sample, epsilon, sensitivity=1.0)
        else:
            raise ValueError(f"Unknown noise type: {noise_type}")
        
        # 3. Edge case handling
        noisy_sample = clamp_noise_scale(noisy_sample, sample)
        
        # 4. Compute Point Estimate
        point_estimate = np.mean(noisy_sample)
        
        # 5. Apply Adjustments
        adjusted_estimate, adj_se = apply_adjustments(
            point_estimate=point_estimate,
            standard_error=np.std(noisy_sample) / np.sqrt(len(noisy_sample)),
            statistic_type=statistic_type,
            noise_params={'epsilon': epsilon, 'type': noise_type}
        )
        
        # 6. Bootstrap CI
        ci_lower, ci_upper = build_ci_for_mean(
            noisy_sample,
            n_bootstrap=BOOTSTRAP_B,
            confidence_level=0.95
        )
        
        # 7. Check Coverage
        covered = 1 if (ci_lower <= true_mean <= ci_upper) else 0
        
        result = {
            'dataset': dataset_name,
            'epsilon': epsilon,
            'noise_type': noise_type,
            'statistic': statistic_type,
            'iteration': i,
            'point_estimate': float(point_estimate),
            'adjusted_estimate': float(adjusted_estimate),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'true_value': float(true_mean),
            'covered': covered
        }
        
        yield result

def run_simulation_pipeline() -> None:
    """
    Orchestrates the full simulation pipeline across all conditions.
    Writes results incrementally to avoid memory bloat.
    """
    # Define conditions
    datasets = ['adult', 'iris', 'wine']
    epsilons = [0.1, 0.5, 1.0, 5.0]
    noise_types = ['laplace', 'gaussian']
    statistic_types = ['mean']
    
    output_path = get_artifact_path('coverage_results.csv')
    temp_path = output_path + '.tmp'
    
    logger.info(f"Writing results to {output_path}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        with open(temp_path, 'w') as f:
            # Write header
            header = "dataset,epsilon,noise_type,statistic,iteration,point_estimate,adjusted_estimate,ci_lower,ci_upper,true_value,covered\n"
            f.write(header)
            
            for ds in datasets:
                for eps in epsilons:
                    for nt in noise_types:
                        for st in statistic_types:
                            logger.info(f"Running condition: {ds}, eps={eps}, {nt}, {st}")
                            
                            gen = run_simulation_condition(ds, eps, nt, st)
                            
                            for res in gen:
                                line = f"{res['dataset']},{res['epsilon']},{res['noise_type']},{res['statistic']},{res['iteration']},{res['point_estimate']:.6f},{res['adjusted_estimate']:.6f},{res['ci_lower']:.6f},{res['ci_upper']:.6f},{res['true_value']:.6f},{res['covered']}\n"
                                f.write(line)
                            
                            # Force flush periodically
                            f.flush()
                            
        # Atomic move
        shutil.move(temp_path, output_path)
        logger.info(f"Simulation complete. Results written to {output_path}")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise

def main():
    """
    Entry point for the simulation pipeline.
    """
    logger.info("Starting llmXive Robustness CI Pipeline")
    
    # 1. Check Feasibility
    if not check_feasibility_gate():
        logger.error("Feasibility gate failed. Aborting.")
        sys.exit(1)
    
    # 2. Start Memory Tracing
    tracemalloc.start()
    
    try:
        # 3. Run Pipeline
        run_simulation_pipeline()
    finally:
        # 4. Cleanup
        current, peak = tracemalloc.get_traced_memory()
        logger.info(f"Peak memory usage: {peak / 1024 ** 3:.4f} GB")
        tracemalloc.stop()

if __name__ == '__main__':
    main()