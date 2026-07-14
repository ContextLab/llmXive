"""
Ground Truth Simulation Study for Bayesian Nonparametric Anomaly Detection.

This module implements a simulation study to verify the Signal-to-Noise Ratio (SNR)
of the derivative of the concentration parameter ($\dot{\alpha}$) under the null
hypothesis (no anomaly) and alternative hypothesis (anomaly injected).

It generates synthetic time series with known regime shifts, runs a simplified
proxy for the DP-GMM inference (to estimate $\alpha$), computes the numerical
derivative, and calculates the SNR.

Deliverable: Generates `data/processed/results/simulation_snr.csv` and asserts SNR > 1.
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "results"
OUTPUT_FILE = OUTPUT_DIR / "simulation_snr.csv"

@dataclass
class SimulationConfig:
    """Configuration for the simulation study."""
    n_samples: int = 1000
    window_size: int = 50
    stride: int = 1
    n_windows: int = 100
    anomaly_start_idx: int = 500
    anomaly_duration: int = 100
    noise_std: float = 0.1
    shift_magnitude: float = 2.0
    seed: int = 42
    n_replications: int = 10  # Number of independent runs for averaging

@dataclass
class SimulationResult:
    """Container for simulation results."""
    snr_null: float = 0.0
    snr_alt: float = 0.0
    mean_alpha_null: float = 0.0
    mean_alpha_alt: float = 0.0
    std_alpha_null: float = 0.0
    std_alpha_alt: float = 0.0
    n_windows_anomaly: int = 0
    n_windows_total: int = 0

def generate_synthetic_timeseries(config: SimulationConfig) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a synthetic time series with an injected anomaly.

    Returns:
        Tuple of (time_series, ground_truth_labels)
        ground_truth_labels: 1 if anomaly, 0 otherwise.
    """
    np.random.seed(config.seed)
    t = np.arange(config.n_samples)

    # Base signal: slow drift + noise
    base_signal = 0.01 * t + np.random.normal(0, config.noise_std, config.n_samples)

    # Ground truth labels
    labels = np.zeros(config.n_samples, dtype=int)

    # Inject anomaly (regime shift)
    end_idx = min(config.anomaly_start_idx + config.anomaly_duration, config.n_samples)
    shift = config.shift_magnitude
    base_signal[config.anomaly_start_idx:end_idx] += shift
    labels[config.anomaly_start_idx:end_idx] = 1

    return base_signal, labels

def estimate_alpha_proxy(window_data: np.ndarray) -> float:
    """
    Estimate a proxy for the concentration parameter $\alpha$ for a given window.

    In a full DP-GMM, $\alpha$ controls the number of clusters.
    Here, we use a simplified heuristic:
    $\hat{\alpha} \propto \text{variance}(window) / \text{noise\_variance}$
    This proxy captures the "complexity" or "spread" of the data in the window,
    which should change when an anomaly (shift) is present.

    Note: This is a surrogate for the actual ADVI inference on $\alpha$ to keep
    the simulation script lightweight and executable without heavy PyMC overhead
    for the ground truth validation step.
    """
    if len(window_data) < 2:
        return 0.0
    variance = np.var(window_data)
    # Assume noise variance is known or estimated from pre-anomaly data
    # For this simulation, we normalize by the expected noise variance
    # Using a small epsilon to avoid division by zero
    return float(variance) + 1e-6

def compute_derivative_alpha(alpha_series: List[float]) -> List[float]:
    """
    Compute the first derivative of the alpha series ($\dot{\alpha}$).
    Uses simple finite differences.
    """
    if len(alpha_series) < 2:
        return [0.0]
    derivatives = []
    for i in range(1, len(alpha_series)):
        derivatives.append(alpha_series[i] - alpha_series[i-1])
    return derivatives

def run_single_simulation(config: SimulationConfig) -> SimulationResult:
    """Run a single simulation replication."""
    data, labels = generate_synthetic_timeseries(config)

    # Sliding window extraction
    windows = []
    window_labels = []
    for i in range(0, len(data) - config.window_size + 1, config.stride):
        window_data = data[i : i + config.window_size]
        window_labels.append(np.mean(labels[i : i + config.window_size]))
        windows.append(window_data)

    # Estimate alpha for each window
    alpha_series = [estimate_alpha_proxy(w) for w in windows]

    # Compute derivative
    dot_alpha_series = compute_derivative_alpha(alpha_series)

    # Separate into Null (no anomaly in window) and Alt (anomaly in window)
    # A window is considered "anomaly" if > 50% of its points are labeled as anomaly
    null_derivs = []
    alt_derivs = []

    for i, label_mean in enumerate(window_labels):
        if i < len(dot_alpha_series):
            if label_mean < 0.5:
                null_derivs.append(dot_alpha_series[i])
            else:
                alt_derivs.append(dot_alpha_series[i])

    if not null_derivs:
        null_derivs = [0.0]
    if not alt_derivs:
        alt_derivs = [0.0]

    # Calculate statistics
    mean_null = np.mean(null_derivs)
    std_null = np.std(null_derivs)
    mean_alt = np.mean(alt_derivs)
    std_alt = np.std(alt_derivs) if len(alt_derivs) > 1 else 1e-6

    # SNR Calculation: (Mean_Alt - Mean_Null) / Std_Null
    # We expect a significant change in alpha derivative when anomaly is present.
    snr = (mean_alt - mean_null) / (std_null + 1e-9)

    return SimulationResult(
        snr_null=mean_null,
        snr_alt=snr,
        mean_alpha_null=np.mean(alpha_series[:len(null_derivs)]),
        mean_alpha_alt=np.mean(alpha_series[len(null_derivs):]),
        std_alpha_null=std_null,
        std_alpha_alt=std_alt,
        n_windows_anomaly=len(alt_derivs),
        n_windows_total=len(dot_alpha_series)
    )

def run_simulation_study(config: SimulationConfig) -> pd.DataFrame:
    """
    Run the full simulation study with multiple replications.

    Returns:
        DataFrame with aggregated results.
    """
    results = []
    logger.info(f"Starting simulation study with seed={config.seed}, n_replications={config.n_replications}")

    for i in range(config.n_replications):
        # Vary seed slightly for each replication
        current_config = SimulationConfig(
            n_samples=config.n_samples,
            window_size=config.window_size,
            stride=config.stride,
            n_windows=config.n_windows,
            anomaly_start_idx=config.anomaly_start_idx,
            anomaly_duration=config.anomaly_duration,
            noise_std=config.noise_std,
            shift_magnitude=config.shift_magnitude,
            seed=config.seed + i,
            n_replications=1
        )
        res = run_single_simulation(current_config)
        results.append({
            'replication': i,
            'snr': res.snr_alt,
            'mean_alpha_null': res.mean_alpha_null,
            'mean_alpha_alt': res.mean_alpha_alt,
            'std_alpha_null': res.std_alpha_null,
            'n_windows_anomaly': res.n_windows_anomaly,
            'n_windows_total': res.n_windows_total
        })

    df = pd.DataFrame(results)
    return df

def main():
    """Main entry point for the simulation study."""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    config = SimulationConfig(
        n_samples=2000,
        window_size=50,
        stride=10,
        anomaly_start_idx=800,
        anomaly_duration=200,
        noise_std=0.1,
        shift_magnitude=3.0,
        seed=42,
        n_replications=20
    )

    logger.info("Running simulation study...")
    df_results = run_simulation_study(config)

    # Calculate aggregate statistics
    mean_snr = df_results['snr'].mean()
    std_snr = df_results['snr'].std()

    logger.info(f"Simulation Complete.")
    logger.info(f"Mean SNR: {mean_snr:.4f} (+/- {std_snr:.4f})")

    # Save results to CSV
    df_results.to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Results saved to {OUTPUT_FILE}")

    # Validate SNR > 1
    if mean_snr <= 1.0:
        logger.error(f"VALIDATION FAILED: Mean SNR ({mean_snr:.4f}) is not > 1.0")
        logger.error("The detector is not sensitive enough to the injected anomaly under the null hypothesis.")
        sys.exit(1)
    else:
        logger.info(f"VALIDATION PASSED: Mean SNR ({mean_snr:.4f}) > 1.0")

    return 0

if __name__ == "__main__":
    main()