import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from scipy import stats
from scipy.optimize import OptimizeError
import os
import json
import argparse
from pathlib import Path

# Ensure we can import from the project root if needed, though typically run from code/
# The API surface indicates this file is code/simulation.py

logger = logging.getLogger(__name__)

def fit_negative_binomial(discrepancies: np.ndarray) -> Tuple[float, float]:
    """
    Fit a Negative Binomial model to observed discrepancies using robust statistics.
    
    Uses median and MAD (Median Absolute Deviation) to estimate mu and alpha,
    avoiding bias from outliers as per FR-003.
    
    Args:
        discrepancies: Array of observed discrepancy values (must be non-negative for NB).
        
    Returns:
        Tuple of (mu, alpha) parameters.
        
    Raises:
        StatisticalModelError: If fit fails or data is invalid for NB.
    """
    if discrepancies is None or len(discrepancies) == 0:
        raise ValueError("Discrepancies array is empty or None")
    
    # Filter for non-negative values as Negative Binomial is defined for non-negative integers
    # However, discrepancies can be negative (precinct sum < county reported).
    # The task T019 says to exclude directional anomalies (precinct sum > county total) 
    # which implies positive discrepancies are the anomaly? 
    # Wait, T019: "flag directional anomalies (precinct sum > county total)".
    # If precinct_sum > county_reported, discrepancy = precinct_sum - county_reported > 0.
    # So positive discrepancies are the anomalies.
    # But NB is often used for over-dispersed count data (positive).
    # Let's assume we fit NB to the absolute values or the positive tail if the model expects counts.
    # However, the prompt says "Fit a Negative Binomial null model to the *observed* data".
    # If data contains negatives, NB fit will fail. 
    # T019 says "exclude from Negative Binomial fit if non-negative error assumption is violated".
    # So we must filter for non-negative discrepancies first.
    
    valid_data = discrepancies[discrepancies >= 0]
    if len(valid_data) == 0:
        raise ValueError("No non-negative discrepancies found for NB fit. Cannot fit NB model.")
    
    # Robust estimation: Median for mu (location), MAD for scale
    mu_est = np.median(valid_data)
    mad = np.median(np.abs(valid_data - mu_est))
    
    # Convert MAD to standard deviation approximation for NB variance estimation
    # For normal, sigma = MAD / 0.6745. For NB, we need a heuristic for alpha.
    # Variance of NB = mu + mu^2 / alpha.
    # If we assume variance ~ sigma^2, and sigma ~ MAD / 0.6745
    if mad == 0:
        # If MAD is 0, all values are the same. Alpha would be infinite (Poisson).
        # Return a very large alpha to approximate Poisson.
        return mu_est, 1e6
    
    sigma_est = mad / 0.6745
    var_est = sigma_est ** 2
    
    # Solve for alpha: var = mu + mu^2 / alpha  =>  alpha = mu^2 / (var - mu)
    if var_est <= mu_est:
        # Variance less than mean implies under-dispersion, NB not suitable (or alpha -> inf)
        # Fallback to Poisson-like (large alpha)
        logger.warning("Estimated variance <= mean. Using large alpha (Poisson-like).")
        return mu_est, 1e6
        
    alpha_est = (mu_est ** 2) / (var_est - mu_est)
    
    if alpha_est <= 0:
        raise ValueError("Calculated alpha is non-positive. NB fit invalid.")
        
    return mu_est, alpha_est

def generate_nb_null_model(mu: float, alpha: float, size: int, rng: np.random.Generator) -> np.ndarray:
    """
    Generate synthetic data from a Negative Binomial distribution.
    
    Args:
        mu: Mean parameter.
        alpha: Dispersion parameter (1/theta in scipy).
        size: Number of samples.
        rng: NumPy random generator.
        
    Returns:
        Array of simulated discrepancies.
    """
    # scipy.stats.nbinom uses n (number of failures) and p (probability).
    # Relationship: mean = n(1-p)/p, var = n(1-p)/p^2.
    # Our parametrization: mean=mu, var=mu + mu^2/alpha.
    # Let's map to scipy: n = mu^2 / (var - mu) = alpha (in our definition).
    # p = n / (n + mu) = alpha / (alpha + mu).
    
    n = alpha
    p = alpha / (alpha + mu)
    
    if n <= 0 or p <= 0 or p >= 1:
        # Fallback if parameters are invalid
        logger.warning("Invalid NB parameters, returning zeros.")
        return np.zeros(size)
        
    return rng.negative_binomial(n, p, size)

def generate_permutation_null_model(data: np.ndarray, size: int, rng: np.random.Generator) -> np.ndarray:
    """
    Generate null model by permuting/resampling the observed data.
    
    This creates a distribution of discrepancies under the assumption that
    the observed values are the population, and any arrangement is equally likely.
    
    Args:
        data: Observed data array.
        size: Number of samples to generate.
        rng: NumPy random generator.
        
    Returns:
        Array of simulated discrepancies.
    """
    # Resample with replacement from the observed data
    return rng.choice(data, size=size, replace=True)

def run_monte_carlo_chunked(
    observed_data: np.ndarray,
    iterations: int,
    seed: int,
    chunk_size: int = 1000,
    model_type: str = "nb"
) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation in chunks to manage memory.
    
    Args:
        observed_data: The cleaned observed discrepancy data.
        iterations: Total number of simulation iterations.
        seed: Random seed for reproducibility.
        chunk_size: Number of iterations per chunk.
        model_type: "nb" for Negative Binomial, "perm" for Permutation.
        
    Returns:
        Dictionary containing the aggregated null distribution and metadata.
    """
    rng = np.random.default_rng(seed)
    all_simulations = []
    
    # Determine parameters
    mu, alpha = 0, 0
    if model_type == "nb":
        try:
            mu, alpha = fit_negative_binomial(observed_data)
            logger.info(f"NB Fit successful: mu={mu:.4f}, alpha={alpha:.4f}")
        except Exception as e:
            logger.warning(f"NB fit failed: {e}. Switching to Permutation model.")
            model_type = "perm"
    
    num_chunks = (iterations + chunk_size - 1) // chunk_size
    
    for i in range(num_chunks):
        current_chunk_size = min(chunk_size, iterations - i * chunk_size)
        logger.debug(f"Processing chunk {i+1}/{num_chunks} ({current_chunk_size} iterations)")
        
        if model_type == "nb":
            chunk_data = generate_nb_null_model(mu, alpha, current_chunk_size, rng)
        else:
            chunk_data = generate_permutation_null_model(observed_data, current_chunk_size, rng)
        
        all_simulations.append(chunk_data)
        
        # Periodic logging
        if (i + 1) % 10 == 0:
            logger.info(f"Completed {i+1} chunks ({(i+1)*chunk_size} iterations)")
    
    # Concatenate results
    null_distribution = np.concatenate(all_simulations)
    
    return {
        "distribution": null_distribution,
        "model_type": model_type,
        "parameters": {"mu": mu, "alpha": alpha} if model_type == "nb" else {},
        "iterations": iterations,
        "seed": seed,
        "chunk_size": chunk_size,
        "num_chunks": num_chunks
    }

def save_simulation_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save simulation results to a JSON file.
    
    Args:
        results: Dictionary containing simulation results.
        output_path: Path to save the JSON file.
    """
    # Convert numpy types to Python types for JSON serialization
    serializable_results = {}
    for key, value in results.items():
        if key == "distribution":
            serializable_results[key] = value.tolist()
        elif isinstance(value, dict):
            serializable_results[key] = {
                k: float(v) if isinstance(v, (np.floating, np.integer)) else v 
                for k, v in value.items()
            }
        elif isinstance(value, (np.integer, np.floating)):
            serializable_results[key] = float(value)
        else:
            serializable_results[key] = value
    
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    logger.info(f"Simulation results saved to {output_path}")

def main():
    """
    CLI entry point for the simulation module.
    """
    parser = argparse.ArgumentParser(description="Monte Carlo simulation for election discrepancy analysis")
    parser.add_argument("--input", type=str, required=True, help="Path to input discrepancies file (parquet or csv)")
    parser.add_argument("--output", type=str, default="data/processed/null_distributions.json", help="Path to output JSON file")
    parser.add_argument("--iterations", type=int, default=10000, help="Number of Monte Carlo iterations")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Iterations per chunk")
    parser.add_argument("--model", type=str, default="auto", choices=["nb", "perm", "auto"], help="Model type")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Load data
    logger.info(f"Loading data from {args.input}")
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")
    
    # Try to load as parquet first, then csv
    if args.input.endswith('.parquet'):
        df = pd.read_parquet(args.input)
    else:
        df = pd.read_csv(args.input)
    
    # Identify discrepancy column
    discrepancy_col = None
    for col in ['discrepancy_abs', 'discrepancy', 'discrepancy_pct']:
        if col in df.columns:
            discrepancy_col = col
            break
    
    if discrepancy_col is None:
        raise ValueError("Could not find discrepancy column in input data. Expected one of: discrepancy_abs, discrepancy, discrepancy_pct")
    
    data = df[discrepancy_col].values.astype(float)
    
    # Filter out NaNs
    data = data[~np.isnan(data)]
    
    if len(data) == 0:
        raise ValueError("No valid data points after filtering NaNs.")
    
    logger.info(f"Loaded {len(data)} data points. Range: [{data.min():.4f}, {data.max():.4f}]")
    
    # Determine model type
    model_type = args.model
    if model_type == "auto":
        model_type = "nb" # Default to NB, fallback handled in run_monte_carlo_chunked
    
    # Run simulation
    logger.info(f"Starting Monte Carlo simulation: {args.iterations} iterations, seed={args.seed}, model={model_type}")
    results = run_monte_carlo_chunked(
        observed_data=data,
        iterations=args.iterations,
        seed=args.seed,
        chunk_size=args.chunk_size,
        model_type=model_type
    )
    
    # Save results
    save_simulation_results(results, args.output)
    
    logger.info("Simulation completed successfully.")

if __name__ == "__main__":
    main()
