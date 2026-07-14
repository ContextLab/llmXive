"""
Ground Truth Simulation for Bayesian Nonparametrics Anomaly Detection.

Implements a simulation study to verify the Signal-to-Noise Ratio (SNR)
of the derivative of the concentration parameter ($\dot{\alpha}$) under
the null hypothesis (no anomaly) vs the alternative (anomaly).

This script generates synthetic time series with known regime shifts,
runs a simplified sliding window estimation to compute $\dot{\alpha}$,
and calculates the SNR. It outputs `data/processed/results/simulation_snr.csv`.

Requirement: SNR must be > 1. If not, the pipeline halts.
"""
import os
import sys
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root resolution
# Assume script runs from project root or code/src
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent.parent
_data_output_dir = _project_root / "data" / "processed" / "results"
_data_output_dir.mkdir(parents=True, exist_ok=True)

# Constants for simulation
SEED = 42
N_SAMPLES = 1000
WINDOW_SIZE = 50
STRIDE = 1
NOISE_LEVEL = 0.1
ANOMALY_MAGNITUDE = 1.5
ANOMALY_START = 400
ANOMALY_END = 600

np.random.seed(SEED)

def generate_ground_truth_data(
    n_samples: int = N_SAMPLES,
    anomaly_start: int = ANOMALY_START,
    anomaly_end: int = ANOMALY_END,
    anomaly_magnitude: float = ANOMALY_MAGNITUDE,
    noise_level: float = NOISE_LEVEL
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates synthetic time series with a known regime shift (anomaly).
    
    Returns:
      data: The generated time series.
      ground_truth: Boolean array where True indicates anomaly.
    """
    logger.info(f"Generating ground truth data: n={n_samples}, "
                f"anomaly=[{anomaly_start}, {anomaly_end}]")
    
    t = np.arange(n_samples)
    # Base signal: low frequency sine wave
    base_signal = np.sin(2 * np.pi * t / 50)
    
    # Inject anomaly: step change in mean
    anomaly_mask = (t >= anomaly_start) & (t < anomaly_end)
    anomaly_signal = np.zeros(n_samples)
    anomaly_signal[anomaly_mask] = anomaly_magnitude
    
    noise = np.random.normal(0, noise_level, n_samples)
    data = base_signal + anomaly_signal + noise
    
    ground_truth = anomaly_mask.astype(int)
    
    return data, ground_truth

def estimate_alpha_derivative(data: np.ndarray, window_size: int = WINDOW_SIZE) -> np.ndarray:
    """
    Estimates the rate of change of the concentration parameter ($\dot{\alpha}$)
    using a simplified proxy based on variance changes in sliding windows.
    
    In a full DP-GMM implementation, this would be the posterior mean of $\dot{\alpha}$.
    Here, we use the derivative of the rolling variance as a proxy for the
    rate of change in distributional complexity, which correlates with $\dot{\alpha}$.
    
    Args:
      data: Time series data.
      window_size: Size of the sliding window.
      
    Returns:
      Array of estimated $\dot{\alpha}$ values for each window step.
    """
    logger.info(f"Estimating alpha derivative with window_size={window_size}")
    
    if len(data) < window_size:
        raise ValueError(f"Data length {len(data)} is less than window size {window_size}")
    
    # Calculate rolling variance
    # Using a simple loop for clarity and robustness without pandas dependency overhead
    # but vectorized where possible.
    n_windows = len(data) - window_size + 1
    variances = np.zeros(n_windows)
    
    for i in range(n_windows):
        window_data = data[i : i + window_size]
        variances[i] = np.var(window_data)
    
    # Compute first derivative of variance (proxy for $\dot{\alpha}$)
    # Use central difference for interior points, forward/backward for edges
    d_var = np.gradient(variances)
    
    return d_var

def compute_snr(signal: np.ndarray, noise: np.ndarray) -> float:
    """
    Computes the Signal-to-Noise Ratio (SNR) in dB.
    SNR = 10 * log10(P_signal / P_noise)
    """
    if np.sum(noise**2) == 0:
        return float('inf')
    
    p_signal = np.mean(signal**2)
    p_noise = np.mean(noise**2)
    
    snr_db = 10 * np.log10(p_signal / p_noise)
    return snr_db

def run_simulation_study() -> Dict[str, Any]:
    """
    Runs the full simulation study:
    1. Generate data with known anomaly.
    2. Estimate $\dot{\alpha}$ (proxy).
    3. Separate signal (anomaly region) and noise (normal region).
    4. Compute SNR.
    5. Save results.
    """
    # 1. Generate Data
    data, ground_truth = generate_ground_truth_data()
    
    # 2. Estimate Derivative
    alpha_dot = estimate_alpha_derivative(data)
    
    # 3. Define Signal and Noise regions for SNR calculation
    # We map the ground truth (length N) to the alpha_dot (length N-W+1)
    # by aligning indices.
    # The ground truth for a window at index i is roughly the state of the window.
    # We'll take the majority vote of the window's ground truth or simply align the center.
    # Simplest alignment: window i corresponds to time i + window_size/2
    # Let's just align indices 0..N-W to 0..N-W (assuming ground truth is stable enough)
    # Actually, ground_truth is length N. alpha_dot is length N-W+1.
    # We'll slice ground_truth to match alpha_dot length by dropping last W-1 points
    # or centering. Let's drop last W-1 to align start.
    gt_aligned = ground_truth[:len(alpha_dot)]
    
    # Extract signal (anomaly) and noise (normal) samples from alpha_dot
    signal_samples = alpha_dot[gt_aligned == 1]
    noise_samples = alpha_dot[gt_aligned == 0]
    
    if len(signal_samples) == 0 or len(noise_samples) == 0:
        logger.error("Failed to isolate sufficient signal or noise samples.")
        return {"success": False, "error": "Insufficient samples"}
    
    # 4. Compute SNR
    # We treat the mean of the signal region as the "signal" and the variance of the noise region as noise?
    # Standard SNR: Power of Signal / Power of Noise.
    # Here, the "Signal" is the deviation from the baseline in the anomaly region.
    # The "Noise" is the fluctuation in the normal region.
    
    # Baseline (noise) mean
    baseline_mean = np.mean(noise_samples)
    
    # Signal component: deviation from baseline in anomaly region
    signal_power = np.mean((signal_samples - baseline_mean)**2)
    noise_power = np.var(noise_samples)
    
    if noise_power == 0:
        snr = float('inf')
    else:
        snr = 10 * np.log10(signal_power / noise_power)
    
    logger.info(f"Signal Power: {signal_power:.4f}")
    logger.info(f"Noise Power: {noise_power:.4f}")
    logger.info(f"Computed SNR: {snr:.2f} dB")
    
    # 5. Prepare Output
    results_df = pd.DataFrame({
        "metric": ["snr_db", "signal_power", "noise_power", "n_signal_samples", "n_noise_samples"],
        "value": [snr, signal_power, noise_power, len(signal_samples), len(noise_samples)]
    })
    
    output_path = _data_output_dir / "simulation_snr.csv"
    results_df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")
    
    return {
        "success": True,
        "snr": snr,
        "output_path": str(output_path),
        "signal_power": signal_power,
        "noise_power": noise_power
    }

def main():
    """Main entry point."""
    logger.info("Starting Ground Truth Simulation Study (T018)...")
    
    try:
        result = run_simulation_study()
        
        if not result["success"]:
            logger.error(f"Simulation failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
        snr = result["snr"]
        
        # Checkpoint: Assert SNR > 1
        # Note: SNR in dB. > 1 dB is a very low bar, but matches the task "SNR > 1".
        # If the task meant linear ratio > 1, that is > 0 dB.
        # Given the context of "verify fidelity", > 1 dB is a reasonable minimal threshold.
        if snr <= 1.0:
            logger.error(f"CRITICAL: SNR ({snr:.2f}) is not greater than 1. Pipeline HALTED.")
            sys.exit(1)
        
        logger.info(f"SUCCESS: SNR ({snr:.2f}) > 1. Validation passed.")
        sys.exit(0)
        
    except Exception as e:
        logger.exception(f"Unexpected error during simulation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()