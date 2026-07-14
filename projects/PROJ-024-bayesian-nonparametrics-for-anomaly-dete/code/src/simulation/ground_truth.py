"""
Ground Truth Simulation for Bayesian Nonparametrics Anomaly Detection.

This module implements a simulation study to verify the Signal-to-Noise Ratio (SNR)
of the derivative of the concentration parameter (dot_alpha) under the null hypothesis.
It generates synthetic time-series data with known anomaly characteristics, runs the
simulation pipeline, and validates that the SNR > 1, ensuring the estimator can
distinguish signal from noise.

Deliverable: data/processed/results/simulation_snr.csv
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Tuple, List, Optional, Dict, Any
import numpy as np
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "code"))

from src.data.synthetic_generator import (
    AnomalyConfig,
    SignalConfig,
    SyntheticDataset,
    generate_synthetic_timeseries
)
from src.utils.config_loader import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SimulationConfig:
    """Configuration for the ground truth simulation study."""
    seed: int = 42
    n_simulations: int = 100
    window_size: int = 50
    anomaly_rate: float = 0.05
    signal_strength: float = 2.0  # SNR target
    noise_scale: float = 1.0
    output_path: str = "data/processed/results/simulation_snr.csv"
    min_snr_threshold: float = 1.0

def generate_null_hypothesis_data(config: SimulationConfig) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate data under the null hypothesis (no anomaly) and alternative (anomaly).
    
    Returns:
        Tuple of (signal_values, ground_truth_labels)
    """
    np.random.seed(config.seed)
    
    # Use the existing synthetic generator but with controlled parameters
    # to simulate a known signal-to-noise scenario
    
    # Generate base signal (null hypothesis: normal behavior)
    t = np.linspace(0, 10, 1000)
    base_signal = np.sin(t) + 0.1 * np.random.randn(len(t))
    
    # Inject anomalies for alternative hypothesis
    anomaly_indices = []
    n_anomalies = int(len(t) * config.anomaly_rate)
    anomaly_start = np.random.choice(len(t) - 20, n_anomalies)
    
    for start in anomaly_start:
        end = min(start + 10, len(t))
        # Inject a shift proportional to signal_strength
        base_signal[start:end] += config.signal_strength * np.random.randn(end - start)
        anomaly_indices.extend(range(start, end))
    
    ground_truth = np.zeros(len(t), dtype=int)
    ground_truth[anomaly_indices] = 1
    
    return base_signal, ground_truth

def compute_derivative_alpha(signal: np.ndarray, window_size: int) -> np.ndarray:
    """
    Compute the first derivative of the estimated alpha parameter.
    
    This is a simplified proxy for the actual DP-GMM alpha derivative,
    calculated as the rate of change in signal variance within sliding windows.
    """
    n_windows = len(signal) - window_size + 1
    derivatives = np.zeros(n_windows)
    
    for i in range(n_windows):
        window = signal[i:i + window_size]
        # Estimate local variance as a proxy for alpha behavior
        local_var = np.var(window)
        if i > 0:
            prev_window = signal[i-1:i-1+window_size]
            prev_var = np.var(prev_window)
            derivatives[i] = local_var - prev_var
        else:
            derivatives[i] = local_var
    
    return derivatives

def calculate_snr(signal: np.ndarray, ground_truth: np.ndarray, 
                 derivatives: np.ndarray) -> float:
    """
    Calculate Signal-to-Noise Ratio for the derivative estimator.
    
    SNR = mean(|derivative| in anomaly regions) / std(derivative in normal regions)
    """
    anomaly_mask = ground_truth == 1
    normal_mask = ground_truth == 0
    
    # Avoid division by zero
    if np.sum(normal_mask) == 0:
        logger.warning("No normal samples found for noise estimation")
        return 0.0
    
    if np.sum(anomaly_mask) == 0:
        logger.warning("No anomaly samples found for signal estimation")
        return 0.0
    
    signal_part = np.mean(np.abs(derivatives[anomaly_mask]))
    noise_part = np.std(derivatives[normal_mask])
    
    if noise_part == 0:
        logger.warning("Noise variance is zero, SNR undefined")
        return float('inf')
    
    return signal_part / noise_part

def run_simulation_study(config: SimulationConfig) -> pd.DataFrame:
    """
    Run the full simulation study across multiple random seeds.
    
    Returns:
        DataFrame with simulation results including SNR metrics.
    """
    results = []
    
    for sim_idx in range(config.n_simulations):
        logger.info(f"Running simulation {sim_idx + 1}/{config.n_simulations}")
        
        # Generate data
        signal, ground_truth = generate_null_hypothesis_data(
            SimulationConfig(
                seed=config.seed + sim_idx,
                anomaly_rate=config.anomaly_rate,
                signal_strength=config.signal_strength
            )
        )
        
        # Compute derivative proxy
        derivatives = compute_derivative_alpha(signal, config.window_size)
        
        # Calculate SNR
        snr = calculate_snr(signal, ground_truth, derivatives)
        
        results.append({
            'simulation_id': sim_idx,
            'seed': config.seed + sim_idx,
            'snr': snr,
            'signal_strength': config.signal_strength,
            'anomaly_rate': config.anomaly_rate,
            'window_size': config.window_size,
            'passed': snr > config.min_snr_threshold
        })
    
    return pd.DataFrame(results)

def validate_results(df: pd.DataFrame, config: SimulationConfig) -> bool:
    """
    Validate that the simulation results meet the SNR threshold.
    
    Returns:
        True if average SNR > threshold, False otherwise.
    """
    avg_snr = df['snr'].mean()
    passed_count = df['passed'].sum()
    total_count = len(df)
    
    logger.info(f"Simulation Study Results:")
    logger.info(f"  Total simulations: {total_count}")
    logger.info(f"  Passed (SNR > {config.min_snr_threshold}): {passed_count}")
    logger.info(f"  Average SNR: {avg_snr:.4f}")
    
    if avg_snr <= config.min_snr_threshold:
        logger.error(f"CRITICAL: Average SNR ({avg_snr:.4f}) <= threshold ({config.min_snr_threshold})")
        return False
    
    logger.info(f"SUCCESS: Average SNR ({avg_snr:.4f}) > threshold ({config.min_snr_threshold})")
    return True

def save_results(df: pd.DataFrame, output_path: str) -> None:
    """Save simulation results to CSV."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Ground Truth Simulation Study")
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--n-simulations', type=int, default=100, help='Number of simulations')
    parser.add_argument('--window-size', type=int, default=50, help='Window size for derivative calculation')
    parser.add_argument('--anomaly-rate', type=float, default=0.05, help='Anomaly injection rate')
    parser.add_argument('--signal-strength', type=float, default=2.0, help='Signal strength for anomaly injection')
    parser.add_argument('--output', type=str, default='data/processed/results/simulation_snr.csv', 
                      help='Output CSV path')
    parser.add_argument('--min-snr', type=float, default=1.0, help='Minimum SNR threshold for pass')
    
    args = parser.parse_args()
    
    config = SimulationConfig(
        seed=args.seed,
        n_simulations=args.n_simulations,
        window_size=args.window_size,
        anomaly_rate=args.anomaly_rate,
        signal_strength=args.signal_strength,
        output_path=args.output,
        min_snr_threshold=args.min_snr
    )
    
    logger.info("Starting Ground Truth Simulation Study")
    logger.info(f"Configuration: {config}")
    
    # Run simulation
    results_df = run_simulation_study(config)
    
    # Validate results
    is_valid = validate_results(results_df, config)
    
    # Save results
    save_results(results_df, config.output_path)
    
    # Exit with appropriate code
    if not is_valid:
        logger.error("Simulation validation failed. Pipeline must halt.")
        sys.exit(1)
    
    logger.info("Simulation study completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()