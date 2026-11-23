"""
Injection-Recovery Test Implementation (FR-008)

This module implements the injection-recovery test to validate that a known
non-zero Yukawa coupling constant (alpha) injected into simulated data
is recovered within the 95% credible interval by the inference pipeline.

Workflow:
1. Load the real harmonized dataset from disk.
2. Inject a synthetic Yukawa signal with known alpha_true and lambda_true.
3. Run MCMC inference on the injected data.
4. Check if the true alpha lies within the 95% posterior credible interval.
5. Save results to data/results/injection_recovery_results.json.
"""
import os
import sys
import json
import logging
import time
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

# Project imports based on API surface
from config import get_logger, setup_logging
from data.loaders import HarmonizedDataset
from models.physics import newtonian_force, yukawa_force, log_likelihood_yukawa
from inference.mcmc import run_mcmc, compute_gelman_rubin

# Setup logging
logger = get_logger(__name__)

def load_harmonized_data(data_path: Path) -> HarmonizedDataset:
    """
    Load the harmonized dataset from the specified path.
    
    Args:
        data_path: Path to the harmonized dataset JSON/CSV file.
        
    Returns:
        HarmonizedDataset object.
        
    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If the data cannot be loaded or validated.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Harmonized data not found at {data_path}. "
                                "Please run the data pipeline first.")
    
    # Assuming HarmonizedDataset can be loaded from a JSON or CSV
    # The exact loading logic depends on how HarmonizedDataset is serialized.
    # For this implementation, we assume a JSON structure with numpy arrays.
    try:
        with open(data_path, 'r') as f:
            data_dict = json.load(f)
        
        # Reconstruct HarmonizedDataset
        # Note: Adjust keys based on actual HarmonizedDataset serialization
        dataset = HarmonizedDataset(
            separation_m=np.array(data_dict['separation_m']),
            force_n=np.array(data_dict['force_n']),
            covariance_matrix=np.array(data_dict['covariance_matrix']),
            metadata=data_dict.get('metadata', {})
        )
        return dataset
    except Exception as e:
        raise ValueError(f"Failed to load harmonized data: {e}")

def inject_yukawa_signal(
    dataset: HarmonizedDataset,
    alpha_true: float,
    lambda_true: float,
    seed: Optional[int] = None
) -> HarmonizedDataset:
    """
    Inject a Yukawa signal into the force data of the dataset.
    
    This adds a synthetic Yukawa force component to the existing force measurements.
    The noise structure (covariance) is preserved, but the mean force is shifted.
    
    Args:
        dataset: The original harmonized dataset.
        alpha_true: The true Yukawa coupling constant to inject.
        lambda_true: The true range parameter (in meters) to inject.
        seed: Random seed for reproducibility (if noise is added, though here 
              we shift the mean directly).
            
    Returns:
        A new HarmonizedDataset with the injected signal.
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Calculate the Yukawa force contribution at each separation distance
    # Yukawa force model: F_yuk = alpha * G * M1 * M2 * (1/r^2) * exp(-r/lambda)
    # However, our physics module likely has a simplified or normalized version.
    # We use the yukawa_force function from models.physics.
    
    # Assuming yukawa_force takes (r, alpha, lambda, normalization_factor)
    # Since we don't have the exact signature, we infer from context:
    # It likely computes the additional force due to Yukawa interaction.
    
    # Calculate the shift in force
    # We need to know the normalization. If the dataset has forces in Newtons,
    # we need to compute the Yukawa force in Newtons.
    # Let's assume the physics module has a function that computes the force
    # given separation, alpha, lambda, and maybe a mass product factor.
    # Since we don't have the exact masses, we might need to infer or assume
    # a normalization. For this implementation, we'll assume the yukawa_force
    # function takes (r, alpha, lambda) and returns the force in Newtons,
    # assuming some standard normalization (e.g., G*M1*M2 = 1).
    
    # If the actual physics module requires a mass product, we would need to
    # extract it from the dataset metadata or assume a value.
    
    # For now, we assume yukawa_force(r, alpha, lambda) returns the force shift.
    force_shift = yukawa_force(
        dataset.separation_m, 
        alpha_true, 
        lambda_true
    )
    
    # Inject the signal by adding the force shift to the existing force data
    injected_force_n = dataset.force_n + force_shift
    
    # Create a new dataset with the injected force
    injected_dataset = HarmonizedDataset(
        separation_m=dataset.separation_m,
        force_n=injected_force_n,
        covariance_matrix=dataset.covariance_matrix,
        metadata={
            **dataset.metadata,
            'injected_alpha': alpha_true,
            'injected_lambda': lambda_true,
            'injection_timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
    )
    
    logger.info(f"Injected Yukawa signal: alpha={alpha_true}, lambda={lambda_true} m")
    return injected_dataset

def run_inference_on_injected_data(
    dataset: HarmonizedDataset,
    n_walkers: int = 50,
    n_steps: int = 1000,
    burn_in: int = 200,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run MCMC inference on the injected dataset to recover the parameters.
    
    Args:
        dataset: The dataset with injected Yukawa signal.
        n_walkers: Number of MCMC walkers.
        n_steps: Total number of steps per walker.
        burn_in: Number of burn-in steps to discard.
        seed: Random seed for reproducibility.
            
    Returns:
        Dictionary containing MCMC results (samples, diagnostics, etc.).
    """
    if seed is not None:
        np.random.seed(seed)
    
    logger.info("Running MCMC inference on injected data...")
    start_time = time.time()
    
    # Define prior bounds for alpha and lambda
    # alpha: typically between 0 and 10^4 (or some large number)
    # lambda: between 1e-5 and 1e-3 meters (sub-millimeter scale)
    lower_bounds = np.array([0.0, 1e-5])   # alpha, lambda
    upper_bounds = np.array([1e4, 1e-3])   # alpha, lambda
    
    # Run MCMC
    # The run_mcmc function should handle the likelihood calculation using
    # the injected dataset's force and covariance.
    result = run_mcmc(
        separation_m=dataset.separation_m,
        force_n=dataset.force_n,
        covariance_matrix=dataset.covariance_matrix,
        n_walkers=n_walkers,
        n_steps=n_steps,
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
        seed=seed
    )
    
    elapsed_time = time.time() - start_time
    logger.info(f"MCMC inference completed in {elapsed_time:.2f} seconds")
    
    # Extract posterior samples
    # Assuming result contains 'samples' with shape (n_walkers * (n_steps - burn_in), 2)
    samples = result['samples']
    
    # Discard burn-in
    if burn_in > 0:
        samples = samples[:, burn_in:, :]
        samples = samples.reshape(-1, samples.shape[-1])
    
    # Compute statistics
    alpha_samples = samples[:, 0]
    lambda_samples = samples[:, 1]
    
    alpha_mean = np.mean(alpha_samples)
    alpha_std = np.std(alpha_samples)
    alpha_median = np.median(alpha_samples)
    alpha_ci_95 = np.percentile(alpha_samples, [2.5, 97.5])
    
    lambda_mean = np.mean(lambda_samples)
    lambda_std = np.std(lambda_samples)
    lambda_median = np.median(lambda_samples)
    lambda_ci_95 = np.percentile(lambda_samples, [2.5, 97.5])
    
    # Compute Gelman-Rubin statistic if multiple chains are available
    gelman_rubin = compute_gelman_rubin(samples)
    
    return {
        'alpha_samples': alpha_samples,
        'lambda_samples': lambda_samples,
        'alpha_mean': alpha_mean,
        'alpha_std': alpha_std,
        'alpha_median': alpha_median,
        'alpha_ci_95': alpha_ci_95,
        'lambda_mean': lambda_mean,
        'lambda_std': lambda_std,
        'lambda_median': lambda_median,
        'lambda_ci_95': lambda_ci_95,
        'gelman_rubin': gelman_rubin,
        'elapsed_time': elapsed_time,
        'n_samples': len(alpha_samples)
    }

def check_recovery(
    inference_results: Dict[str, Any],
    alpha_true: float,
    lambda_true: float,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Check if the true injected parameters are recovered within the credible interval.
    
    Args:
        inference_results: Results from the MCMC inference.
        alpha_true: The true injected alpha value.
        lambda_true: The true injected lambda value.
        confidence_level: The confidence level for the credible interval (default 0.95).
            
    Returns:
        Dictionary with recovery status and details.
    """
    alpha_ci = inference_results['alpha_ci_95']
    lambda_ci = inference_results['lambda_ci_95']
    
    alpha_recovered = alpha_ci[0] <= alpha_true <= alpha_ci[1]
    lambda_recovered = lambda_ci[0] <= lambda_true <= lambda_ci[1]
    
    # Calculate the distance of the true value from the median estimate
    alpha_distance = abs(alpha_true - inference_results['alpha_median'])
    lambda_distance = abs(lambda_true - inference_results['lambda_median'])
    
    # Calculate the width of the credible interval
    alpha_ci_width = alpha_ci[1] - alpha_ci[0]
    lambda_ci_width = lambda_ci[1] - lambda_ci[0]
    
    # Relative error
    alpha_relative_error = alpha_distance / alpha_true if alpha_true != 0 else float('inf')
    lambda_relative_error = lambda_distance / lambda_true if lambda_true != 0 else float('inf')
    
    recovery_status = {
        'alpha_recovered': alpha_recovered,
        'lambda_recovered': lambda_recovered,
        'alpha_true': alpha_true,
        'lambda_true': lambda_true,
        'alpha_median': inference_results['alpha_median'],
        'lambda_median': inference_results['lambda_median'],
        'alpha_ci_95': alpha_ci,
        'lambda_ci_95': lambda_ci,
        'alpha_distance': alpha_distance,
        'lambda_distance': lambda_distance,
        'alpha_relative_error': alpha_relative_error,
        'lambda_relative_error': lambda_relative_error,
        'alpha_ci_width': alpha_ci_width,
        'lambda_ci_width': lambda_ci_width,
        'overall_recovery': alpha_recovered and lambda_recovered
    }
    
    logger.info(f"Recovery check: alpha_recovered={alpha_recovered}, "
                f"lambda_recovered={lambda_recovered}")
    
    return recovery_status

def save_results(
  injection_results: Dict[str, Any],
  output_path: Path
):
    """
    Save the injection-recovery results to a JSON file.
    
    Args:
        injection_results: Dictionary containing all results and metadata.
        output_path: Path to save the results JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(injection_results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main function to run the injection-recovery test.
    
    This function:
    1. Loads the real harmonized dataset.
    2. Injects a known Yukawa signal.
    3. Runs MCMC inference.
    4. Checks if the true parameters are recovered.
    5. Saves the results.
    """
    # Configuration
    DATA_PATH = Path("data/processed/harmonized_dataset.json")
    OUTPUT_PATH = Path("data/results/injection_recovery_results.json")
    
    # Injected parameters (example values - can be adjusted)
    ALPHA_TRUE = 100.0  # Example coupling constant
    LAMBDA_TRUE = 5.0e-5  # 50 micrometers
    SEED = 42
    
    # Initialize logging
    setup_logging()
    
    try:
        logger.info("Starting injection-recovery test...")
        
        # Step 1: Load the real harmonized dataset
        logger.info(f"Loading harmonized dataset from {DATA_PATH}...")
        dataset = load_harmonized_data(DATA_PATH)
        logger.info(f"Loaded dataset with {len(dataset.separation_m)} data points")
        
        # Step 2: Inject the Yukawa signal
        logger.info(f"Injecting Yukawa signal: alpha={ALPHA_TRUE}, lambda={LAMBDA_TRUE} m")
        injected_dataset = inject_yukawa_signal(
            dataset, 
            alpha_true=ALPHA_TRUE, 
            lambda_true=LAMBDA_TRUE, 
            seed=SEED
        )
        
        # Step 3: Run MCMC inference
        logger.info("Running MCMC inference on injected data...")
        inference_results = run_inference_on_injected_data(
            injected_dataset,
            n_walkers=50,
            n_steps=2000,  # Increased steps for better convergence
            burn_in=500,
            seed=SEED
        )
        
        # Step 4: Check recovery
        logger.info("Checking parameter recovery...")
        recovery_status = check_recovery(
            inference_results,
            alpha_true=ALPHA_TRUE,
            lambda_true=LAMBDA_TRUE,
            confidence_level=0.95
        )
        
        # Step 5: Compile and save results
        results = {
            'injected_parameters': {
                'alpha_true': ALPHA_TRUE,
                'lambda_true': LAMBDA_TRUE
            },
            'inference_results': {
                'alpha_mean': inference_results['alpha_mean'],
                'alpha_std': inference_results['alpha_std'],
                'alpha_ci_95': inference_results['alpha_ci_95'].tolist(),
                'lambda_mean': inference_results['lambda_mean'],
                'lambda_std': inference_results['lambda_std'],
                'lambda_ci_95': inference_results['lambda_ci_95'].tolist(),
                'gelman_rubin': float(inference_results['gelman_rubin']),
                'n_samples': inference_results['n_samples'],
                'elapsed_time': inference_results['elapsed_time']
            },
            'recovery_status': {
                'alpha_recovered': recovery_status['alpha_recovered'],
                'lambda_recovered': recovery_status['lambda_recovered'],
                'overall_recovery': recovery_status['overall_recovery'],
                'alpha_distance': recovery_status['alpha_distance'],
                'lambda_distance': recovery_status['lambda_distance'],
                'alpha_relative_error': recovery_status['alpha_relative_error'],
                'lambda_relative_error': recovery_status['lambda_relative_error']
            },
            'metadata': {
                'test_type': 'injection_recovery',
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'seed': SEED
            }
        }
        
        save_results(results, OUTPUT_PATH)
        
        # Final status
        if recovery_status['overall_recovery']:
            logger.info("SUCCESS: Injected parameters recovered within 95% CI.")
            return 0
        else:
            logger.warning("FAILURE: Injected parameters NOT recovered within 95% CI.")
            return 1
            
    except Exception as e:
        logger.error(f"Injection-recovery test failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
