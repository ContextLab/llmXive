"""
Simulation study for Ground Truth SNR validation (FR-020).

This script generates synthetic time-series data with known anomaly injection
points to validate the signal-to-noise ratio (SNR) of the derivative estimator
under the null hypothesis and against known signal shifts.

It produces `data/processed/results/simulation_snr.csv` containing the measured
SNR values for the simulation study.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
import json

import numpy as np
import pandas as pd

# Ensure code/src is in path for imports if run as script
# but rely on package structure for standard execution
try:
    from data.synthetic_generator import generate_synthetic_timeseries, AnomalyConfig, SignalConfig
except ImportError:
    # Fallback for direct script execution without package setup
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data.synthetic_generator import generate_synthetic_timeseries, AnomalyConfig, SignalConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for simulation
DEFAULT_SEED = 42
DEFAULT_N_SAMPLES = 1000
DEFAULT_ANOMALY_RATE = 0.05
DEFAULT_WINDOW_SIZE = 50
SNR_THRESHOLD = 1.0

def compute_derivative_signal(x, window_size=50):
    """
    Compute a smoothed first derivative (rate of change) using a moving window.
    This simulates the $\dot{\alpha}$ extraction logic.
    """
    if len(x) < window_size:
        return np.zeros_like(x)
    
    # Simple centered difference with smoothing
    # Using a rolling mean of differences to approximate the derivative
    diff = np.diff(x)
    # Pad to match original length
    diff = np.concatenate(([0], diff))
    
    # Apply rolling window smoothing to the derivative
    kernel = np.ones(window_size) / window_size
    smoothed_diff = np.convolve(diff, kernel, mode='same')
    
    return smoothed_diff

def compute_snr(signal, noise):
    """
    Compute Signal-to-Noise Ratio (SNR) in dB.
    SNR = 10 * log10(P_signal / P_noise)
    """
    if np.sum(noise**2) == 0:
        return float('inf')
    
    power_signal = np.mean(signal**2)
    power_noise = np.mean(noise**2)
    
    if power_noise == 0:
        return float('inf')
        
    snr_db = 10 * np.log10(power_signal / power_noise)
    return snr_db

def run_simulation_study(n_samples, anomaly_rate, seed, window_size):
    """
    Run the simulation study to verify $\dot{\alpha}$ SNR.
    
    1. Generate synthetic data with known anomalies.
    2. Inject a known signal shift.
    3. Compute the derivative estimate.
    4. Calculate SNR between the known signal change and the estimation noise.
    """
    logger.info(f"Starting simulation study with seed={seed}, n_samples={n_samples}")
    
    np.random.seed(seed)
    
    # Generate base signal (pre-anomaly dynamics)
    signal_config = SignalConfig(
        signal_type='ar1',
        length=n_samples,
        noise_scale=0.1,
        ar_coefficient=0.9
    )
    
    anomaly_config = AnomalyConfig(
        anomaly_rate=anomaly_rate,
        anomaly_type='level_shift',
        shift_magnitude=2.0,  # Known shift magnitude for SNR calculation
        duration=window_size  # Anomaly lasts for at least one window
    )
    
    # Generate dataset
    data = generate_synthetic_timeseries(
        signal_config=signal_config,
        anomaly_config=anomaly_config,
        seed=seed
    )
    
    time_series = data['values']
    ground_truth = data['anomaly_mask']  # Boolean array: True where anomaly exists
    
    # Compute the derivative estimate
    derivative_estimate = compute_derivative_signal(time_series, window_size)
    
    # Isolate the signal component (anomaly region) and noise component (normal region)
    # We define "signal" as the derivative magnitude in anomaly regions
    # and "noise" as the derivative magnitude in normal regions
    
    anomaly_indices = np.where(ground_truth)[0]
    normal_indices = np.where(~ground_truth)[0]
    
    if len(anomaly_indices) == 0:
        logger.warning("No anomalies generated. Cannot compute SNR.")
        return None
        
    if len(normal_indices) == 0:
        logger.warning("No normal data generated. Cannot compute SNR.")
        return None
    
    signal_magnitude = np.abs(derivative_estimate[anomaly_indices])
    noise_magnitude = np.abs(derivative_estimate[normal_indices])
    
    # Calculate SNR
    # We treat the mean derivative in anomaly regions as "signal"
    # and the standard deviation in normal regions as "noise"
    mean_signal = np.mean(signal_magnitude)
    std_noise = np.std(noise_magnitude)
    
    if std_noise == 0:
        snr = float('inf')
    else:
        snr = mean_signal / std_noise
        
    logger.info(f"Mean Signal Magnitude (Anomaly): {mean_signal:.4f}")
    logger.info(f"Std Noise Magnitude (Normal): {std_noise:.4f}")
    logger.info(f"Computed SNR: {snr:.4f}")
    
    return {
        'seed': seed,
        'n_samples': n_samples,
        'anomaly_rate': anomaly_rate,
        'window_size': window_size,
        'mean_signal': mean_signal,
        'std_noise': std_noise,
        'snr': snr,
        'timestamp': datetime.now().isoformat()
    }

def main():
    parser = argparse.ArgumentParser(description='Run Ground Truth Simulation Study (FR-020)')
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED, help='Random seed')
    parser.add_argument('--n-samples', type=int, default=DEFAULT_N_SAMPLES, help='Number of samples')
    parser.add_argument('--anomaly-rate', type=float, default=DEFAULT_ANOMALY_RATE, help='Anomaly injection rate')
    parser.add_argument('--window-size', type=int, default=DEFAULT_WINDOW_SIZE, help='Window size for derivative')
    parser.add_argument('--output', type=str, default='data/processed/results/simulation_snr.csv',
                        help='Output CSV path')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run simulation
    result = run_simulation_study(
        n_samples=args.n_samples,
        anomaly_rate=args.anomaly_rate,
        seed=args.seed,
        window_size=args.window_size
    )
    
    if result is None:
        logger.error("Simulation failed to produce valid SNR.")
        sys.exit(1)
    
    # Save results
    df = pd.DataFrame([result])
    df.to_csv(output_path, index=False)
    
    logger.info(f"Simulation results saved to {output_path}")
    
    # Validation Check
    if result['snr'] <= SNR_THRESHOLD:
        logger.error(f"CRITICAL: SNR ({result['snr']:.4f}) is below threshold ({SNR_THRESHOLD}).")
        logger.error("The estimator does not distinguish signal from noise effectively.")
        sys.exit(1)
    else:
        logger.info(f"SUCCESS: SNR ({result['snr']:.4f}) > {SNR_THRESHOLD}. Estimator validated.")
        
    return 0

if __name__ == '__main__':
    sys.exit(main())