"""
Ground Truth Simulation Study for Bayesian Nonparametric Anomaly Detection.

This module implements the simulation study to verify the Signal-to-Noise Ratio (SNR)
of the time-varying concentration parameter derivative (d_alpha/dt) under the null
hypothesis (no anomaly) and alternative hypothesis (anomaly present).

Deliverable: Generates `data/processed/results/simulation_snr.csv` and asserts SNR > 1.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure paths are relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "results"
DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class SimulationConfig:
    """Configuration for the ground truth simulation study."""
    n_windows: int = 100
    window_size: int = 50
    anomaly_duration: int = 10
    anomaly_magnitude: float = 3.0
    noise_std: float = 1.0
    seed: int = 42
    n_replications: int = 5  # Number of simulation runs for averaging

def generate_null_hypothesis_data(config: SimulationConfig) -> np.ndarray:
    """
    Generate time series data under the null hypothesis (no anomaly).
    Returns a 1D array of length n_windows * window_size.
    """
    np.random.seed(config.seed)
    total_length = config.n_windows * config.window_size
    # Simple Gaussian noise process
    data = np.random.normal(loc=0.0, scale=config.noise_std, size=total_length)
    return data

def generate_alternative_hypothesis_data(config: SimulationConfig) -> np.ndarray:
    """
    Generate time series data under the alternative hypothesis (anomaly present).
    Injects a collective anomaly (shift in mean) at a random location.
    """
    np.random.seed(config.seed + 1)  # Different seed for anomaly injection
    total_length = config.n_windows * config.window_size
    data = np.random.normal(loc=0.0, scale=config.noise_std, size=total_length)

    # Inject anomaly in the middle third of the series
    start_idx = total_length // 3
    end_idx = start_idx + config.anomaly_duration * config.window_size

    # Ensure bounds
    end_idx = min(end_idx, total_length)

    # Inject a mean shift
    data[start_idx:end_idx] += config.anomaly_magnitude * config.noise_std

    return data

def simulate_window_statistics(data: np.ndarray, config: SimulationConfig) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulate the extraction of window-level statistics that would be produced
    by the DPGMM model. Specifically, we simulate the posterior mean of alpha
    and its first derivative (d_alpha/dt).

    Under the null hypothesis, alpha is stable (low derivative).
    Under the alternative, alpha changes rapidly (high derivative).

    We simulate this by:
    1. Computing a simple rolling mean of the data as a proxy for the 'signal'.
    2. Adding noise to simulate posterior uncertainty.
    3. Computing the first difference (derivative) of this signal.

    Returns:
        alpha_means: Simulated posterior mean of alpha for each window.
        alpha_derivatives: Simulated first derivative of alpha for each window.
    """
    window_size = config.window_size
    n_windows = config.n_windows

    # Extract windows
    windows = []
    for i in range(n_windows):
        start = i * window_size
        end = start + window_size
        if end > len(data):
            break
        windows.append(data[start:end])

    windows = np.array(windows)

    # Simulate alpha_mean: proportional to the mean of the window + noise
    # Under null: mean ~ 0
    # Under alt: mean ~ magnitude
    window_means = np.mean(windows, axis=1)
    alpha_means = window_means + np.random.normal(0, 0.1, size=n_windows)

    # Simulate alpha_derivative: first difference of alpha_means
    # We pad the first value to keep length consistent
    alpha_derivatives = np.diff(alpha_means, prepend=alpha_means[0])

    return alpha_means, alpha_derivatives

def compute_snr(alpha_derivatives: np.ndarray, label: str) -> float:
    """
    Compute the Signal-to-Noise Ratio (SNR) for the derivative series.

    SNR = |Mean(derivatives)| / Std(derivatives)

    Under the null hypothesis, the mean derivative should be close to 0,
    resulting in a low SNR.
    Under the alternative hypothesis, the mean derivative should be non-zero,
    resulting in a higher SNR.

    Note: This is a simplified SNR definition for the simulation study.
    In practice, the 'signal' is the systematic change in alpha, and 'noise'
    is the stochastic variation.
    """
    mean_deriv = np.mean(alpha_derivatives)
    std_deriv = np.std(alpha_derivatives)

    if std_deriv == 0:
        return float('inf') if mean_deriv != 0 else 0.0

    snr = abs(mean_deriv) / std_deriv
    return snr

def run_simulation_study(config: SimulationConfig) -> pd.DataFrame:
    """
    Run the full simulation study across null and alternative hypotheses.
    """
    logger.info(f"Starting simulation study with config: {config}")

    results = []

    for rep in range(config.n_replications):
        logger.info(f"Running replication {rep + 1}/{config.n_replications}")

        # 1. Null Hypothesis (No Anomaly)
        data_null = generate_null_hypothesis_data(config)
        alpha_means_null, alpha_derivs_null = simulate_window_statistics(data_null, config)
        snr_null = compute_snr(alpha_derivs_null, "null")

        # 2. Alternative Hypothesis (Anomaly Present)
        data_alt = generate_alternative_hypothesis_data(config)
        alpha_means_alt, alpha_derivs_alt = simulate_window_statistics(data_alt, config)
        snr_alt = compute_snr(alpha_derivs_alt, "alternative")

        results.append({
            "replication": rep + 1,
            "hypothesis": "null",
            "snr": snr_null,
            "mean_derivative": np.mean(alpha_derivs_null),
            "std_derivative": np.std(alpha_derivs_null)
        })
        results.append({
            "replication": rep + 1,
            "hypothesis": "alternative",
            "snr": snr_alt,
            "mean_derivative": np.mean(alpha_derivs_alt),
            "std_derivative": np.std(alpha_derivs_alt)
        })

    df = pd.DataFrame(results)
    return df

def validate_results(df: pd.DataFrame) -> bool:
    """
    Validate the simulation results.
    The task requires that the SNR under the alternative hypothesis is > 1.
    (Note: The prompt says "assert SNR > 1 in logs", implying the metric
    of interest is the ability to detect the anomaly. We check the average
    SNR across replications for the alternative hypothesis).
    """
    alt_snr = df[df["hypothesis"] == "alternative"]["snr"].mean()
    null_snr = df[df["hypothesis"] == "null"]["snr"].mean()

    logger.info(f"Average SNR (Null): {null_snr:.4f}")
    logger.info(f"Average SNR (Alternative): {alt_snr:.4f}")

    if alt_snr <= 1.0:
        logger.error(f"VALIDATION FAILED: Average SNR ({alt_snr:.4f}) is not > 1.0 under alternative hypothesis.")
        return False

    logger.info("VALIDATION PASSED: SNR > 1 under alternative hypothesis.")
    return True

def main():
    """Main entry point for the simulation study."""
    config = SimulationConfig(
        n_windows=100,
        window_size=50,
        anomaly_duration=10,
        anomaly_magnitude=3.0,
        noise_std=1.0,
        seed=42,
        n_replications=5
    )

    try:
        df_results = run_simulation_study(config)

        # Save to CSV
        output_path = DATA_OUTPUT_DIR / "simulation_snr.csv"
        df_results.to_csv(output_path, index=False)
        logger.info(f"Simulation results saved to: {output_path}")

        # Validate
        is_valid = validate_results(df_results)

        if not is_valid:
            logger.error("Simulation study failed validation. Exiting with error.")
            sys.exit(1)

        logger.info("Ground Truth Simulation Study completed successfully.")

    except Exception as e:
        logger.error(f"Simulation study failed with exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()