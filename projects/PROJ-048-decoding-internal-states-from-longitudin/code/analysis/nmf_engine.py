import numpy as np
import logging
from typing import Tuple, Optional, Dict, Any, List
from pathlib import Path
import json
import time
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

from config import get_config_value, get_random_seed, get_all_config
from utils.logger import get_logger, log_stage_start, log_stage_end, log_memory_usage, log_error
from utils.memory_monitor import check_memory_limit, MemoryExceededError

class NMFError(Exception):
    """Custom exception for NMF-related errors."""
    pass

def run_nmf_with_regularization(
    data: np.ndarray,
    k: int,
    seed: int,
    max_iter: int = 1000,
    tol: float = 1e-4,
    alpha: float = 0.1,
    l1_ratio: float = 0.5
) -> Dict[str, Any]:
    """
    Run NMF with temporal smoothness regularization.
    
    Args:
        data: Input data matrix (n_samples, n_features)
        k: Number of components
        seed: Random seed for reproducibility
        max_iter: Maximum iterations
        tol: Convergence tolerance
        alpha: Regularization strength
        l1_ratio: L1 vs L2 regularization ratio (0=elastic net, 1=L1, 0=L2)
    
    Returns:
        Dictionary with W, H, n_iter, seed, and convergence status
    """
    logger = get_logger(__name__)
    logger.info(f"Starting NMF with k={k}, seed={seed}")
    
    # Set random seed
    np.random.seed(seed)
    
    # Check memory
    check_memory_limit(data.nbytes)
    
    n_samples, n_features = data.shape
    
    # Initialize W and H randomly
    W = np.random.rand(n_samples, k)
    H = np.random.rand(k, n_features)
    
    # Ensure non-negativity
    W = np.abs(W)
    H = np.abs(H)
    
    # Add small epsilon to avoid division by zero
    eps = 1e-10
    W = W + eps
    H = H + eps
    
    prev_cost = float('inf')
    converged = False
    
    for i in range(max_iter):
        # Update H (with regularization)
        # Standard multiplicative update for H
        numerator = W.T @ data
        denominator = (W.T @ W) @ H + eps
        H = H * (numerator / denominator)
        
        # Apply L1/L2 regularization to H
        if alpha > 0:
            # L2 regularization (ridge)
            H = H / (1 + alpha * (1 - l1_ratio))
            # L1 regularization (lasso)
            H = np.maximum(H - alpha * l1_ratio, 0)
        
        # Ensure non-negativity
        H = np.maximum(H, eps)
        
        # Update W (with regularization)
        numerator = data @ H.T
        denominator = W @ (H @ H.T) + eps
        W = W * (numerator / denominator)
        
        # Apply L1/L2 regularization to W
        if alpha > 0:
            W = W / (1 + alpha * (1 - l1_ratio))
            W = np.maximum(W - alpha * l1_ratio, 0)
        
        # Ensure non-negativity
        W = np.maximum(W, eps)
        
        # Check for convergence
        # Compute reconstruction error (Frobenius norm)
        reconstruction = W @ H
        cost = np.linalg.norm(data - reconstruction, 'fro')
        
        if abs(prev_cost - cost) < tol:
            converged = True
            logger.info(f"Converged at iteration {i+1}, cost={cost:.6f}")
            break
        
        prev_cost = cost
        
        if (i + 1) % 100 == 0:
            logger.info(f"Iteration {i+1}/{max_iter}, cost={cost:.6f}")
    
    return {
        'W': W,
        'H': H,
        'n_iter': i + 1,
        'seed': seed,
        'converged': converged,
        'final_cost': cost
    }

def run_sensitivity_sweep(
    data: np.ndarray,
    k_values: List[int],
    seed: int,
    max_iter: int = 1000,
    tol: float = 1e-4,
    alpha: float = 0.1,
    l1_ratio: float = 0.5
) -> Dict[str, Any]:
    """
    Run NMF sensitivity sweep across different k values.
    
    Args:
        data: Input data matrix
        k_values: List of k values to test
        seed: Base random seed
        max_iter: Maximum iterations per run
        tol: Convergence tolerance
        alpha: Regularization strength
        l1_ratio: L1 vs L2 ratio
    
    Returns:
        Dictionary mapping k values to their results
    """
    logger = get_logger(__name__)
    log_stage_start(logger, "sensitivity_sweep", {"k_values": k_values, "seed": seed})
    
    results = {}
    
    for k in k_values:
        logger.info(f"Running sensitivity sweep for k={k}")
        try:
            result = run_nmf_with_regularization(
                data, k, seed, max_iter, tol, alpha, l1_ratio
            )
            results[k] = result
        except Exception as e:
            logger.error(f"Failed for k={k}: {str(e)}")
            results[k] = {
                'error': str(e),
                'seed': seed,
                'k': k
            }
    
    log_stage_end(logger, "sensitivity_sweep", {"status": "complete", "results_count": len(results)})
    
    return results

def _run_single_seed(args):
    """Helper function for parallel execution."""
    data, k, seed, max_iter, tol, alpha, l1_ratio = args
    return run_nmf_with_regularization(data, k, seed, max_iter, tol, alpha, l1_ratio)

def run_parallel_seed_sweep(
    data: np.ndarray,
    k: int,
    seeds: List[int],
    max_iter: int = 1000,
    tol: float = 1e-4,
    alpha: float = 0.1,
    l1_ratio: float = 0.5,
    n_workers: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run NMF decomposition in parallel across multiple random seeds.
    
    Args:
        data: Input data matrix (n_samples, n_features)
        k: Number of components
        seeds: List of random seeds to use
        max_iter: Maximum iterations per run
        tol: Convergence tolerance
        alpha: Regularization strength
        l1_ratio: L1 vs L2 ratio
        n_workers: Number of parallel workers (default: number of CPU cores)
    
    Returns:
        Dictionary with:
            - 'results': List of result dictionaries (one per seed)
            - 'seeds': List of seeds used
            - 'k': Number of components
            - 'status': 'complete' or 'partial'
            - 'errors': List of error messages if any
    """
    logger = get_logger(__name__)
    log_stage_start(logger, "parallel_seed_sweep", {
        "k": k,
        "num_seeds": len(seeds),
        "n_workers": n_workers
    })
    
    if n_workers is None:
        n_workers = multiprocessing.cpu_count()
    
    # Prepare arguments for each seed
    task_args = [
        (data, k, seed, max_iter, tol, alpha, l1_ratio)
        for seed in seeds
    ]
    
    results = []
    errors = []
    status = "complete"
    
    try:
        # Use ProcessPoolExecutor for parallel execution
        # Note: We need to handle data serialization carefully
        # For large data, we might need to use shared memory or file-based passing
        # For now, we assume data fits in memory for each worker
        
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = {
                executor.submit(_run_single_seed, args): seed 
                for args, seed in zip(task_args, seeds)
            }
            
            completed_count = 0
            for future in as_completed(futures):
                seed = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed_count += 1
                    logger.info(f"Completed seed {seed} (progress: {completed_count}/{len(seeds)})")
                except Exception as e:
                    error_msg = f"Seed {seed} failed: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    results.append({
                        'error': str(e),
                        'seed': seed,
                        'k': k
                    })
    
    except Exception as e:
        status = "failed"
        logger.error(f"Parallel execution failed: {str(e)}")
        errors.append(f"Execution error: {str(e)}")
    
    log_stage_end(logger, "parallel_seed_sweep", {
        "status": status,
        "completed": len([r for r in results if 'error' not in r]),
        "failed": len(errors)
    })
    
    return {
        'results': results,
        'seeds': seeds,
        'k': k,
        'status': status if not errors else 'partial',
        'errors': errors
    }

def main():
    """
    Main entry point for NMF engine.
    
    This function:
    1. Loads configuration
    2. Loads preprocessed data
    3. Runs parallel multi-seed sweep for NMF
    4. Saves results to disk
    """
    logger = get_logger(__name__)
    logger.info("Starting NMF Engine main")
    
    # Initialize config
    config = get_all_config()
    
    # Get parameters
    k = get_config_value('NMF_K', 10, int)
    num_seeds = get_config_value('NMF_NUM_SEEDS', 5, int)
    base_seed = get_random_seed()
    max_iter = get_config_value('NMF_MAX_ITER', 1000, int)
    tol = get_config_value('NMF_TOL', 1e-4, float)
    alpha = get_config_value('NMF_ALPHA', 0.1, float)
    l1_ratio = get_config_value('NMF_L1_RATIO', 0.5, float)
    
    # Generate seeds
    seeds = [base_seed + i for i in range(num_seeds)]
    logger.info(f"Using seeds: {seeds}")
    
    # Load preprocessed data
    data_path = Path(config.get('DATA_DIR', 'data')) / 'preprocessed' / 'deconvolved_data.npy'
    
    if not data_path.exists():
        error_msg = f"Preprocessed data not found at {data_path}. Run preprocessing first."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.info(f"Loading data from {data_path}")
    data = np.load(data_path)
    logger.info(f"Loaded data with shape: {data.shape}")
    
    # Check memory
    check_memory_limit(data.nbytes)
    
    # Run parallel seed sweep
    logger.info(f"Running parallel seed sweep with k={k}, {num_seeds} seeds")
    sweep_results = run_parallel_seed_sweep(
        data=data,
        k=k,
        seeds=seeds,
        max_iter=max_iter,
        tol=tol,
        alpha=alpha,
        l1_ratio=l1_ratio
    )
    
    # Save results
    output_dir = Path(config.get('OUTPUT_DIR', 'data')) / 'nmf_results'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save individual component results
    for i, result in enumerate(sweep_results['results']):
        if 'error' not in result:
            W_path = output_dir / f'W_seed_{result["seed"]}.npy'
            H_path = output_dir / f'H_seed_{result["seed"]}.npy'
            np.save(W_path, result['W'])
            np.save(H_path, result['H'])
            logger.info(f"Saved W and H for seed {result['seed']}")
    
    # Save summary report
    report = {
        'k': k,
        'seeds': seeds,
        'num_seeds': num_seeds,
        'config': {
            'max_iter': max_iter,
            'tol': tol,
            'alpha': alpha,
            'l1_ratio': l1_ratio
        },
        'status': sweep_results['status'],
        'completed': len([r for r in sweep_results['results'] if 'error' not in r]),
        'failed': len(sweep_results['errors']),
        'errors': sweep_results['errors'],
        'results_summary': [
            {
                'seed': r['seed'],
                'n_iter': r.get('n_iter'),
                'converged': r.get('converged'),
                'final_cost': r.get('final_cost'),
                'has_error': 'error' in r
            }
            for r in sweep_results['results']
        ]
    }
    
    report_path = output_dir / 'seed_sweep_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved seed sweep report to {report_path}")
    log_stage_end(logger, "nmf_main", {"status": "complete", "output_path": str(report_path)})
    
    return sweep_results

if __name__ == "__main__":
    main()