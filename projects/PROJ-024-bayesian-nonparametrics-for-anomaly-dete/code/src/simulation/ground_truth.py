"""
Ground Truth Simulation for Bayesian Nonparametrics Anomaly Detection.

This module implements a simulation study to verify the Signal-to-Noise Ratio (SNR)
of the derivative of the concentration parameter ($\dot{\alpha}$) under the null hypothesis.

Per FR-020, this study validates the ADVI estimator's fidelity before main inference.

Deliverable: data/processed/results/simulation_snr.csv
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "results"

def simulate_null_hypothesis(n_windows: int = 500, n_obs_per_window: int = 50, seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulates time series data under the null hypothesis (no anomaly).
    
    Generates a stable signal where the concentration parameter alpha should remain
    relatively constant, resulting in a derivative close to zero.
    
    Args:
        n_windows: Number of sliding windows to simulate.
        n_obs_per_window: Number of observations per window.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (true_alpha_trajectory, observed_alpha_trajectory)
    """
    np.random.seed(seed)
    
    # True alpha under null hypothesis: stable around 1.0 with small noise
    true_alpha = np.ones(n_windows) * 1.0
    
    # Simulate observed alpha with measurement noise (mimicking ADVI estimation error)
    # We assume the estimator has some variance but is unbiased under the null
    noise_std = 0.05
    observed_alpha = true_alpha + np.random.normal(0, noise_std, n_windows)
    
    return true_alpha, observed_alpha

def compute_derivative(alpha_trajectory: np.ndarray) -> np.ndarray:
    """
    Computes the first derivative of the alpha trajectory using finite differences.
    
    Args:
        alpha_trajectory: Array of alpha values over time.
        
    Returns:
        Array of derivative values (length n-1).
    """
    return np.diff(alpha_trajectory)

def compute_snr(signal: np.ndarray, noise: np.ndarray) -> float:
    """
    Computes the Signal-to-Noise Ratio (SNR).
    
    SNR = mean(signal^2) / var(noise)
    
    Under the null hypothesis, the signal (derivative of true alpha) should be near zero,
    but we measure the SNR of the estimator's ability to detect deviations.
    
    Args:
        signal: The true signal (derivative of true alpha).
        noise: The noise in the estimation (derivative of observed alpha - derivative of true alpha).
        
    Returns:
        SNR value.
    """
    signal_power = np.mean(signal ** 2)
    noise_power = np.var(noise)
    
    if noise_power == 0:
        return float('inf')
        
    return signal_power / noise_power

def run_simulation_study(n_windows: int = 500, n_obs_per_window: int = 50, seed: int = 42) -> Dict[str, Any]:
    """
    Runs the full simulation study to validate the ADVI estimator.
    
    This function:
    1. Generates synthetic data under the null hypothesis.
    2. Simulates the ADVI estimation of alpha.
    3. Computes the derivative of alpha.
    4. Calculates the SNR.
    
    Args:
        n_windows: Number of windows to simulate.
        n_obs_per_window: Observations per window.
        seed: Random seed.
        
    Returns:
        Dictionary containing simulation results.
    """
    logger.info(f"Starting simulation study with {n_windows} windows, seed={seed}")
    
    # Simulate data
    true_alpha, observed_alpha = simulate_null_hypothesis(n_windows, n_obs_per_window, seed)
    
    # Compute derivatives
    true_derivative = compute_derivative(true_alpha)
    observed_derivative = compute_derivative(observed_alpha)
    
    # Compute noise in derivative estimation
    derivative_noise = observed_derivative - true_derivative
    
    # Calculate SNR
    snr = compute_snr(true_derivative, derivative_noise)
    
    # Prepare results
    results = {
        "n_windows": n_windows,
        "n_obs_per_window": n_obs_per_window,
        "seed": seed,
        "snr": float(snr),
        "mean_true_derivative": float(np.mean(true_derivative)),
        "mean_observed_derivative": float(np.mean(observed_derivative)),
        "var_derivative_noise": float(np.var(derivative_noise)),
        "validation_passed": snr > 1.0
    }
    
    logger.info(f"Simulation complete. SNR: {snr:.4f}")
    logger.info(f"Validation {'PASSED' if results['validation_passed'] else 'FAILED'}: SNR > 1.0")
    
    return results

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Saves simulation results to a CSV file.
    
    Args:
        results: Dictionary of simulation results.
        output_path: Path to save the CSV file.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to DataFrame for consistent CSV output
    df = pd.DataFrame([results])
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for the ground truth simulation.
    """
    logger.info("=" * 60)
    logger.info("Ground Truth Simulation Study (FR-020)")
    logger.info("=" * 60)
    
    # Configuration
    n_windows = 500
    n_obs_per_window = 50
    seed = 42
    
    # Run simulation
    results = run_simulation_study(n_windows, n_obs_per_window, seed)
    
    # Define output path
    output_path = DATA_OUTPUT_DIR / "simulation_snr.csv"
    
    # Save results
    save_results(results, output_path)
    
    # Validate
    if not results["validation_passed"]:
        logger.error("CRITICAL: SNR <= 1.0. Pipeline validation failed.")
        sys.exit(1)
    else:
        logger.info("SUCCESS: Simulation study passed validation.")
        sys.exit(0)

if __name__ == "__main__":
    main()