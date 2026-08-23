"""
Parallel execution of robustness iterations using multiprocessing.

This module implements parallel processing for the robustness analysis tasks
(T030: Cross-validation and T031: Uncertainty inflation) to speed up
the computation of multiple inference iterations.
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from multiprocessing import Pool, cpu_count, current_process
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_logger, setup_logging
from robustness.cross_val import perform_leave_one_out, perform_bootstrap_resampling, calculate_cv, run_single_inference
from robustness.uncertainty import inflate_covariance, compute_bayes_factor
from data.state_manager import check_bootstrap_flag
from data.loaders import HarmonizedDataset

# Configure logging
logger = get_logger(__name__)

def _worker_leave_one_out(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker function for leave-one-out cross-validation.
    
    Args:
        args: Dictionary containing 'run_id', 'leave_out_index', and other parameters.
    
    Returns:
        Dictionary with results for this iteration.
    """
    run_id = args['run_id']
    leave_out_index = args['leave_out_index']
    data_path = args['data_path']
    
    logger.info(f"Worker {current_process().name}: Processing LOO run {run_id}, leaving out index {leave_out_index}")
    start_time = time.time()
    
    try:
        # Load data
        dataset = HarmonizedDataset.from_npy(data_path)
        
        # Create mask for leave-one-out
        mask = np.ones(len(dataset.separation), dtype=bool)
        mask[leave_out_index] = False
        
        # Filter dataset
        filtered_dataset = HarmonizedDataset(
            separation=dataset.separation[mask],
            force=dataset.force[mask],
            covariance=dataset.covariance[np.ix_(mask, mask)],
            metadata=dataset.metadata
        )
        
        # Run inference
        result = run_single_inference(filtered_dataset, run_id=run_id)
        
        elapsed = time.time() - start_time
        logger.info(f"Worker {current_process().name}: Completed run {run_id} in {elapsed:.2f}s")
        
        return {
            'run_id': run_id,
            'leave_out_index': leave_out_index,
            'success': True,
            'alpha_upper_limit': result.get('alpha_upper_limit'),
            'bayes_factor': result.get('bayes_factor'),
            'time_elapsed': elapsed,
            'error': None
        }
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Worker {current_process().name}: Failed run {run_id}: {str(e)}")
        return {
            'run_id': run_id,
            'leave_out_index': leave_out_index,
            'success': False,
            'alpha_upper_limit': None,
            'bayes_factor': None,
            'time_elapsed': elapsed,
            'error': str(e)
        }

def _worker_bootstrap_resample(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker function for bootstrap resampling.
    
    Args:
        args: Dictionary containing 'run_id', 'sample_indices', and other parameters.
    
    Returns:
        Dictionary with results for this iteration.
    """
    run_id = args['run_id']
    sample_indices = args['sample_indices']
    data_path = args['data_path']
    
    logger.info(f"Worker {current_process().name}: Processing bootstrap run {run_id}")
    start_time = time.time()
    
    try:
        # Load data
        dataset = HarmonizedDataset.from_npy(data_path)
        
        # Sample with replacement
        sampled_separation = dataset.separation[sample_indices]
        sampled_force = dataset.force[sample_indices]
        # For covariance, we need to recompute or approximate
        # Using a simplified approach: recompute covariance for sampled points
        n_samples = len(sample_indices)
        sampled_covariance = np.zeros((n_samples, n_samples))
        for i, idx_i in enumerate(sample_indices):
            for j, idx_j in enumerate(sample_indices):
                sampled_covariance[i, j] = dataset.covariance[idx_i, idx_j]
        
        sampled_dataset = HarmonizedDataset(
            separation=sampled_separation,
            force=sampled_force,
            covariance=sampled_covariance,
            metadata=dataset.metadata
        )
        
        # Run inference
        result = run_single_inference(sampled_dataset, run_id=run_id)
        
        elapsed = time.time() - start_time
        logger.info(f"Worker {current_process().name}: Completed bootstrap run {run_id} in {elapsed:.2f}s")
        
        return {
            'run_id': run_id,
            'sample_size': len(sample_indices),
            'success': True,
            'alpha_upper_limit': result.get('alpha_upper_limit'),
            'bayes_factor': result.get('bayes_factor'),
            'time_elapsed': elapsed,
            'error': None
        }
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Worker {current_process().name}: Failed bootstrap run {run_id}: {str(e)}")
        return {
            'run_id': run_id,
            'sample_size': len(sample_indices),
            'success': False,
            'alpha_upper_limit': None,
            'bayes_factor': None,
            'time_elapsed': elapsed,
            'error': str(e)
        }

def _worker_uncertainty_inflation(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker function for uncertainty inflation test.
    
    Args:
        args: Dictionary containing 'run_id', 'inflation_factor', and other parameters.
    
    Returns:
        Dictionary with results for this iteration.
    """
    run_id = args['run_id']
    inflation_factor = args['inflation_factor']
    data_path = args['data_path']
    
    logger.info(f"Worker {current_process().name}: Processing uncertainty inflation run {run_id} with factor {inflation_factor}")
    start_time = time.time()
    
    try:
        # Load data
        dataset = HarmonizedDataset.from_npy(data_path)
        
        # Inflate covariance
        inflated_covariance = inflate_covariance(dataset.covariance, inflation_factor)
        
        inflated_dataset = HarmonizedDataset(
            separation=dataset.separation,
            force=dataset.force,
            covariance=inflated_covariance,
            metadata=dataset.metadata
        )
        
        # Run inference
        result = run_single_inference(inflated_dataset, run_id=run_id)
        
        # Compute Bayes factor
        bayes_factor = compute_bayes_factor(dataset, inflated_dataset)
        
        elapsed = time.time() - start_time
        logger.info(f"Worker {current_process().name}: Completed uncertainty inflation run {run_id} in {elapsed:.2f}s")
        
        return {
            'run_id': run_id,
            'inflation_factor': inflation_factor,
            'success': True,
            'alpha_upper_limit': result.get('alpha_upper_limit'),
            'bayes_factor': bayes_factor,
            'time_elapsed': elapsed,
            'error': None
        }
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Worker {current_process().name}: Failed uncertainty inflation run {run_id}: {str(e)}")
        return {
            'run_id': run_id,
            'inflation_factor': inflation_factor,
            'success': False,
            'alpha_upper_limit': None,
            'bayes_factor': None,
            'time_elapsed': elapsed,
            'error': str(e)
        }

def run_parallel_leave_one_out(
    data_path: str,
    n_iterations: int,
    n_workers: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Run leave-one-out cross-validation in parallel.
    
    Args:
        data_path: Path to the harmonized dataset file.
        n_iterations: Number of iterations (number of points to leave out).
        n_workers: Number of worker processes. Defaults to CPU count.
    
    Returns:
        List of results from each iteration.
    """
    if n_workers is None:
        n_workers = cpu_count()
    
    logger.info(f"Starting parallel LOO with {n_workers} workers")
    
    # Prepare arguments for each worker
    args_list = [
        {
            'run_id': i,
            'leave_out_index': i,
            'data_path': data_path
        }
        for i in range(n_iterations)
    ]
    
    results = []
    with Pool(processes=n_workers) as pool:
        results = pool.map(_worker_leave_one_out, args_list)
    
    logger.info(f"Completed {len(results)} LOO iterations")
    return results

def run_parallel_bootstrap(
    data_path: str,
    n_iterations: int,
    n_workers: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Run bootstrap resampling in parallel.
    
    Args:
        data_path: Path to the harmonized dataset file.
        n_iterations: Number of bootstrap iterations.
        n_workers: Number of worker processes. Defaults to CPU count.
    
    Returns:
        List of results from each iteration.
    """
    if n_workers is None:
        n_workers = cpu_count()
    
    logger.info(f"Starting parallel bootstrap with {n_workers} workers")
    
    # Load dataset to get size
    dataset = HarmonizedDataset.from_npy(data_path)
    n_points = len(dataset.separation)
    
    # Prepare arguments for each worker
    args_list = []
    for i in range(n_iterations):
        # Generate random sample indices with replacement
        sample_indices = np.random.choice(n_points, size=n_points, replace=True)
        args_list.append({
            'run_id': i,
            'sample_indices': sample_indices.tolist(),
            'data_path': data_path
        })
    
    results = []
    with Pool(processes=n_workers) as pool:
        results = pool.map(_worker_bootstrap_resample, args_list)
    
    logger.info(f"Completed {len(results)} bootstrap iterations")
    return results

def run_parallel_uncertainty_inflation(
    data_path: str,
    inflation_factors: List[float],
    n_workers: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Run uncertainty inflation tests in parallel.
    
    Args:
        data_path: Path to the harmonized dataset file.
        inflation_factors: List of inflation factors to test.
        n_workers: Number of worker processes. Defaults to CPU count.
    
    Returns:
        List of results from each inflation factor test.
    """
    if n_workers is None:
        n_workers = cpu_count()
    
    logger.info(f"Starting parallel uncertainty inflation with {n_workers} workers")
    
    # Prepare arguments for each worker
    args_list = [
        {
            'run_id': i,
            'inflation_factor': factor,
            'data_path': data_path
        }
        for i, factor in enumerate(inflation_factors)
    ]
    
    results = []
    with Pool(processes=n_workers) as pool:
        results = pool.map(_worker_uncertainty_inflation, args_list)
    
    logger.info(f"Completed {len(results)} uncertainty inflation tests")
    return results

def main():
    """
    Main entry point for parallel robustness execution.
    
    This function demonstrates the parallel execution capabilities by running
    a small-scale test of each robustness method.
    """
    setup_logging()
    logger.info("Starting parallel robustness execution")
    
    # Paths
    data_path = str(PROJECT_ROOT / "data" / "processed" / "harmonized_dataset.npy")
    results_dir = PROJECT_ROOT / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    if not Path(data_path).exists():
        logger.error(f"Dataset not found at {data_path}. Please run harmonization first.")
        return
    
    # Check bootstrap flag
    use_bootstrap = check_bootstrap_flag()
    
    # Determine which method to run
    if use_bootstrap:
        logger.info("Bootstrap mode detected - running parallel bootstrap resampling")
        n_iterations = 10  # Small number for demo
        results = run_parallel_bootstrap(data_path, n_iterations)
        output_file = results_dir / "parallel_bootstrap_results.json"
    else:
        logger.info("Standard mode - running parallel leave-one-out cross-validation")
        dataset = HarmonizedDataset.from_npy(data_path)
        n_iterations = len(dataset.separation)
        # Limit for demo purposes if dataset is large
        n_iterations = min(n_iterations, 10)
        results = run_parallel_leave_one_out(data_path, n_iterations)
        output_file = results_dir / "parallel_loo_results.json"
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_file}")
    
    # Calculate CV if we have valid results
    valid_results = [r for r in results if r['success'] and r['alpha_upper_limit'] is not None]
    if valid_results:
        alpha_limits = [r['alpha_upper_limit'] for r in valid_results]
        cv = calculate_cv(np.array(alpha_limits))
        logger.info(f"Coefficient of Variation: {cv:.2f}%")
        
        # Update results with CV
        cv_report = {
            'cv_percentage': cv,
            'valid_iterations': len(valid_results),
            'total_iterations': len(results)
        }
        
        cv_file = results_dir / "parallel_cv_report.json"
        with open(cv_file, 'w') as f:
            json.dump(cv_report, f, indent=2)
        logger.info(f"CV report saved to {cv_file}")

if __name__ == "__main__":
    main()