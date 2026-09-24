import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from scipy import stats
from scipy.optimize import OptimizeError
import os
import json
from pathlib import Path

from logger import get_logger
from exceptions import StatisticalModelError, ConfigurationError

logger = get_logger(__name__)

def fit_negative_binomial(
    discrepancies: np.ndarray,
    seed: int = 42
) -> Tuple[Optional[Dict[str, float]], Optional[Any]]:
    """
    Fit a Negative Binomial distribution to the observed discrepancies.

    Args:
        discrepancies: Array of observed discrepancy values (must be non-negative).
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (params_dict, fitted_distribution_object).
        Returns (None, None) if fitting fails (e.g., convergence error).
    """
    np.random.seed(seed)

    # Filter for non-negative values as NB requires
    clean_data = discrepancies[discrepancies >= 0]

    if len(clean_data) == 0:
        logger.warning("No non-negative discrepancies found for NB fit.")
        return None, None

    try:
        # Fit Negative Binomial: stats.nbinom.fit returns (n, p, loc, scale)
        # We assume loc=0, scale=1 for count data, fitting n and p
        # Note: scipy.stats.nbinom parameterization: n (number of failures), p (prob of success)
        # The mean is n*(1-p)/p and variance is n*(1-p)/p^2
        
        # Attempt fit
        fitted_params = stats.nbinom.fit(clean_data)
        
        if len(fitted_params) < 2:
            logger.error("Negative Binomial fit returned insufficient parameters.")
            return None, None

        n, p = fitted_params[0], fitted_params[1]
        
        # Validate parameters
        if n <= 0 or p <= 0 or p > 1:
            logger.warning(f"Invalid NB parameters: n={n}, p={p}. Fitting failed.")
            return None, None

        logger.info(f"Negative Binomial fit successful: n={n:.4f}, p={p:.4f}")
        
        params_dict = {'n': n, 'p': p}
        dist_obj = stats.nbinom(n, p)
        
        return params_dict, dist_obj

    except (OptimizeError, RuntimeError, ValueError) as e:
        logger.warning(f"Negative Binomial fit failed: {type(e).__name__}: {e}")
        return None, None
    except Exception as e:
        logger.error(f"Unexpected error during NB fit: {type(e).__name__}: {e}")
        return None, None

def generate_nb_null_model(
    params: Dict[str, float],
    n_samples: int,
    seed: int = 42
) -> np.ndarray:
    """
    Generate samples from a fitted Negative Binomial distribution.

    Args:
        params: Dictionary with 'n' and 'p' parameters.
        n_samples: Number of samples to generate.
        seed: Random seed.

    Returns:
        Array of simulated discrepancy values.
    """
    np.random.seed(seed)
    n, p = params['n'], params['p']
    return stats.nbinom.rvs(n, p, size=n_samples)

def generate_permutation_null_model(
    observed_discrepancies: np.ndarray,
    n_permutations: int,
    seed: int = 42
) -> np.ndarray:
    """
    Generate a permutation-based null model.
    
    This simulates random clerical error by shuffling the observed discrepancies
    across jurisdictions, assuming the set of discrepancies is fixed but their
    assignment to specific jurisdictions is random. This serves as a fallback
    when the Negative Binomial fit fails.

    Args:
        observed_discrepancies: The actual observed discrepancy values.
        n_permutations: Number of permutation iterations.
        seed: Random seed.

    Returns:
        Array of simulated discrepancy values from the permutation model.
        For a single realization, we return one shuffled array. 
        For Monte Carlo, we typically aggregate statistics, but here we return 
        the raw simulated distribution of one "null universe" realization 
        if n_permutations=1, or a flattened array of samples if used for 
        aggregate statistics.
        
        To align with the task of "generating a null model" for comparison:
        We will generate `n_permutations` samples of the *same size* as observed,
        but since we need a distribution of the *statistic* (e.g., sum or max),
        the standard approach is to calculate the statistic for each permutation.
        
        However, the task asks for a "null model" (a distribution of values).
        We will return a flattened array of `n_permutations` samples drawn 
        from the empirical distribution of the observed discrepancies, 
        effectively resampling with replacement (bootstrap) or without 
        (permutation of values). 
        
        Given the context of "random clerical error", we assume the magnitude 
        of errors is fixed but location is random. A simple null model for 
        the *distribution of values* is the empirical distribution itself 
        (if we assume the set of errors is the universe). 
        
        To provide a distinct "null" distribution that can be compared via KS/AD:
        We will perform a Monte Carlo resampling of the observed discrepancies 
        to create a synthetic dataset of the same size, representing the 
        "random assignment" hypothesis.
        
        We return a single large array of samples if n_permutations is large, 
        or a list of arrays if we want to keep them separate. 
        For compatibility with downstream analysis (KS/AD), we return a single 
        1D array of simulated values.
        
        Strategy:
        1. If n_permutations is 1, return one shuffled version of observed (if size matches).
        2. If we need a larger distribution to compare against observed (which might be small),
           we can sample with replacement from the observed values `n_permutations` times.
           
        Let's interpret "n_permutations" as the number of samples to draw from the 
        empirical distribution to build the null distribution curve.
    """
    np.random.seed(seed)
    
    if len(observed_discrepancies) == 0:
        logger.warning("No observed discrepancies for permutation model.")
        return np.array([])
    
    # We will generate a null distribution by resampling (with replacement) 
    # from the observed discrepancies. This represents the hypothesis that 
    # the observed discrepancies are just a random draw from the underlying 
    # error process, and we are simulating what that process looks like.
    # This is effectively a bootstrap of the empirical distribution.
    
    # Total samples to generate for the null distribution
    total_samples = n_permutations
    
    null_samples = np.random.choice(
        observed_discrepancies, 
        size=total_samples, 
        replace=True
    )
    
    logger.info(f"Generated permutation null model with {total_samples} samples.")
    return null_samples

def run_monte_carlo_chunked(
    observed_discrepancies: np.ndarray,
    n_iterations: int,
    chunk_size: int = 1000,
    seed: int = 42,
    use_permutation_fallback: bool = False,
    nb_params: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation with chunked processing to manage memory.
    
    This function orchestrates the generation of the null distribution.
    If `use_permutation_fallback` is True or `nb_params` is None, it uses
    the permutation-based model. Otherwise, it uses the Negative Binomial model.
    
    Args:
        observed_discrepancies: Array of observed discrepancies.
        n_iterations: Total number of simulation iterations (samples).
        chunk_size: Number of samples per batch.
        seed: Random seed.
        use_permutation_fallback: Force use of permutation model.
        nb_params: Parameters for NB model. If None, NB is skipped.
        
    Returns:
        Dictionary containing the simulated null distribution and metadata.
    """
    np.random.seed(seed)
    logger.info(f"Starting Monte Carlo simulation: {n_iterations} iterations, chunk_size={chunk_size}")
    
    null_samples = []
    n_chunks = (n_iterations + chunk_size - 1) // chunk_size
    
    # Determine model strategy
    if use_permutation_fallback or nb_params is None:
        logger.info("Using Permutation-based null model (Fallback).")
        model_type = "permutation"
    else:
        logger.info("Using Negative Binomial null model.")
        model_type = "negative_binomial"
    
    for i in range(n_chunks):
        current_chunk_size = min(chunk_size, n_iterations - (i * chunk_size))
        
        if model_type == "permutation":
            chunk_data = generate_permutation_null_model(
                observed_discrepancies, 
                current_chunk_size, 
                seed=seed + i
            )
        else:
            chunk_data = generate_nb_null_model(
                nb_params, 
                current_chunk_size, 
                seed=seed + i
            )
        
        null_samples.append(chunk_data)
        
        if (i + 1) % 10 == 0:
            logger.debug(f"Processed {i+1}/{n_chunks} chunks.")
    
    final_null_distribution = np.concatenate(null_samples)
    
    return {
        "null_distribution": final_null_distribution,
        "model_type": model_type,
        "n_samples": len(final_null_distribution),
        "nb_params": nb_params if model_type == "negative_binomial" else None
    }

def save_simulation_results(
    results: Dict[str, Any],
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save simulation results to a JSON file.
    
    Args:
        results: Dictionary containing simulation results.
        output_path: Path to save the file.
        metadata: Additional metadata to include.
    """
    # Convert numpy types to native Python types for JSON serialization
    serializable_results = {}
    for key, value in results.items():
        if isinstance(value, np.ndarray):
            serializable_results[key] = value.tolist()
        elif isinstance(value, dict):
            serializable_results[key] = {
                k: float(v) if isinstance(v, (np.floating, np.integer)) else v 
                for k, v in value.items()
            }
        else:
            serializable_results[key] = value
    
    if metadata:
        serializable_results["metadata"] = metadata
    
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"Simulation results saved to {output_path}")

def main():
    """
    Main entry point for the simulation module.
    Demonstrates the fallback logic:
    1. Attempt NB fit.
    2. If NB fit fails, switch to Permutation model.
    3. Run Monte Carlo.
    4. Save results.
    """
    # Setup
    seed = 42
    np.random.seed(seed)
    
    # Create sample data for demonstration (In real pipeline, this comes from data/processed/)
    # Simulating a case where NB fit might fail (e.g., all zeros or very small variance)
    # For this demo, we'll use a dataset that forces the fallback path if we artificially 
    # trigger a failure, or we just run the logic.
    
    # Let's create a realistic but small dataset for testing the flow
    # We will simulate a scenario where NB fit fails by providing data with 0 variance or 
    # extreme outliers that cause convergence issues.
    
    # Scenario A: Normal data (NB should work)
    # Scenario B: Data that breaks NB (e.g., all zeros) -> Fallback to Permutation
    
    # We will implement the logic to automatically detect and fallback.
    
    # Example: Load from a file if it exists, else create synthetic for demo
    # NOTE: In the real pipeline, this data comes from `data/processed/discrepancies.csv`
    # For this module's `main` function, we will simulate the fallback behavior 
    # by attempting fit on a dataset that we know might fail or by forcing the flag.
    
    # Let's create a dataset that mimics a "failed fit" scenario for demonstration
    # e. g., all zeros.
    test_data = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
    
    logger.info("=== Simulation Module Fallback Demo ===")
    logger.info("Attempting Negative Binomial fit on test data (all zeros)...")
    
    nb_params, nb_dist = fit_negative_binomial(test_data, seed=seed)
    
    if nb_params is None:
        logger.info("NB Fit failed as expected. Switching to Permutation Fallback.")
        use_fallback = True
        nb_params = None
    else:
        logger.info("NB Fit succeeded. Using NB model.")
        use_fallback = False
    
    # Run Monte Carlo
    results = run_monte_carlo_chunked(
        observed_discrepancies=test_data,
        n_iterations=1000,
        chunk_size=100,
        seed=seed,
        use_permutation_fallback=use_fallback,
        nb_params=nb_params
    )
    
    # Save results
    output_path = "data/processed/null_distributions.json"
    save_simulation_results(results, output_path)
    
    logger.info(f"Demo complete. Model used: {results['model_type']}")
    logger.info(f"Null distribution size: {results['n_samples']}")

if __name__ == "__main__":
    main()