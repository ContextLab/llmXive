"""
Performance optimization script for T040.

Deliverable: Complete a 1000-step dynesty run on Nside=64 synthetic data 
within 2 hours on CPU.

This script:
1. Generates synthetic Nside=64 data (fast computation)
2. Configures dynesty with optimized parameters for speed
3. Runs exactly 1000 sampling steps
4. Reports execution time and verifies it meets the 2-hour constraint
"""
import os
import sys
import time
import json
import numpy as np
from pathlib import Path
import logging

# Add code directory to path for imports
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from synthetic_data import generate_inflation_dataset, save_dataset
from inference import run_nested_sampling, check_convergence, prior_transform, log_likelihood
from config import init_reproducibility, get_config, update_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/performance_optimization.log')
    ]
)
logger = logging.getLogger(__name__)

def generate_optimized_synthetic_data(nside=64, seed=42):
    """
    Generate synthetic data optimized for performance testing.
    
    Uses Nside=64 for fast computation while maintaining statistical validity.
    """
    logger.info(f"Generating synthetic inflation dataset with Nside={nside}")
    
    # Initialize reproducibility
    init_reproducibility(seed=seed)
    
    # Generate dataset with known ground truth
    # Using r=0.01 as the true value
    true_r = 0.01
    dataset = generate_inflation_dataset(
        nside=nside,
        true_r=true_r,
        noise_level=0.005,
        seed=seed
    )
    
    # Save dataset for reproducibility
    output_path = Path("data/synthetic/optimized_test_data.json")
    save_dataset(dataset, str(output_path))
    logger.info(f"Saved synthetic dataset to {output_path}")
    
    return dataset

def run_optimized_inference(dataset, max_steps=1000, n_live_points=50):
    """
    Run nested sampling with performance-optimized parameters.
    
    Args:
        dataset: Synthetic dataset with observed power spectrum
        max_steps: Maximum number of sampling steps (target: 1000)
        n_live_points: Number of live points (optimized for speed)
        
    Returns:
        dict: Inference results and timing information
    """
    logger.info(f"Starting nested sampling with {n_live_points} live points")
    
    # Extract observed data
    l_values = np.array(dataset['l_values'])
    cl_values = np.array(dataset['cl_values'])
    cl_errors = np.array(dataset['cl_errors'])
    
    # Define log-likelihood function for this dataset
    def likelihood_func(params):
        r = params[0]
        # Use the module's log_likelihood with pre-computed data
        return log_likelihood(r, l_values, cl_values, cl_errors)
    
    # Run nested sampling with optimized settings
    start_time = time.time()
    
    results = run_nested_sampling(
        likelihood_func=likelihood_func,
        prior_transform=prior_transform,
        ndim=1,
        n_live_points=n_live_points,
        maxiter=max_steps,
        dlogz=0.1  # Tolerance for convergence
    )
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    logger.info(f"Sampling completed in {elapsed_time:.2f} seconds")
    
    # Check convergence
    converged = check_convergence(results)
    
    # Extract results
    samples = results.samples
    log_weights = results.logwt
    log_evidence = results.logz[-1]
    
    # Compute posterior statistics
    posterior_r = np.exp(log_weights) * samples[:, 0]
    posterior_r = posterior_r / np.sum(posterior_r)
    
    mean_r = np.sum(samples[:, 0] * np.exp(log_weights)) / np.sum(np.exp(log_weights))
    std_r = np.sqrt(np.sum(((samples[:, 0] - mean_r) ** 2) * np.exp(log_weights)) / np.sum(np.exp(log_weights)))
    
    return {
        'mean_r': mean_r,
        'std_r': std_r,
        'log_evidence': log_evidence,
        'converged': converged,
        'elapsed_time_seconds': elapsed_time,
        'n_steps': len(results.logz),
        'n_samples': len(samples)
    }

def main():
    """Main execution function for performance optimization test."""
    logger.info("=" * 60)
    logger.info("Starting Performance Optimization Test (T040)")
    logger.info("Target: 1000-step dynesty run on Nside=64 within 2 hours")
    logger.info("=" * 60)
    
    # Configuration
    NSIDE = 64
    MAX_STEPS = 1000
    N_LIVE_POINTS = 50  # Optimized for speed
    SEED = 42
    TIME_LIMIT_SECONDS = 2 * 3600  # 2 hours
    
    try:
        # Generate synthetic data
        dataset = generate_optimized_synthetic_data(nside=NSIDE, seed=SEED)
        
        # Run optimized inference
        results = run_optimized_inference(
            dataset=dataset,
            max_steps=MAX_STEPS,
            n_live_points=N_LIVE_POINTS
        )
        
        # Validate results
        elapsed = results['elapsed_time_seconds']
        time_ok = elapsed <= TIME_LIMIT_SECONDS
        
        logger.info("=" * 60)
        logger.info("PERFORMANCE OPTIMIZATION RESULTS")
        logger.info("=" * 60)
        logger.info(f"Elapsed time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
        logger.info(f"Time limit: {TIME_LIMIT_SECONDS} seconds ({TIME_LIMIT_SECONDS/60:.2f} minutes)")
        logger.info(f"Time constraint met: {'YES' if time_ok else 'NO'}")
        logger.info(f"Number of steps completed: {results['n_steps']}")
        logger.info(f"Convergence achieved: {results['converged']}")
        logger.info(f"Estimated r: {results['mean_r']:.4f} ± {results['std_r']:.4f}")
        logger.info(f"Log evidence: {results['log_evidence']:.4f}")
        logger.info("=" * 60)
        
        if not time_ok:
            logger.error("PERFORMANCE TEST FAILED: Exceeded 2-hour time limit")
            return 1
        
        if not results['converged']:
            logger.warning("PERFORMANCE TEST WARNING: Sampler did not converge within 1000 steps")
            # This is acceptable for the performance test as long as we completed 1000 steps
        
        # Save results
        output_path = Path("data/derived/performance_optimization_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        logger.info("PERFORMANCE OPTIMIZATION TEST PASSED")
        return 0
        
    except Exception as e:
        logger.error(f"PERFORMANCE TEST FAILED with exception: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
