"""
Simulation study for validating the ADVI estimator's fidelity and measuring SNR under the null hypothesis.
This script generates synthetic time series with known anomaly characteristics and evaluates the detection performance.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/simulation.log')
    ]
)
logger = logging.getLogger(__name__)

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from data.synthetic_generator import generate_synthetic_timeseries, AnomalyConfig, SignalConfig
from models.dpgmm import DPGMMModel, DPGMMConfig
from evaluation.metrics import compute_all_metrics

@dataclass
class SimulationConfig:
    """Configuration for the simulation study."""
    seed: int = 42
    n_samples: int = 1000
    window_size: int = 50
    stride: int = 1
    anomaly_rate: float = 0.05
    n_simulations: int = 10
    snr_threshold: float = 1.0

@dataclass
class SimulationResult:
    """Result of a single simulation run."""
    snr: float
    detection_rate: float
    false_positive_rate: float
    precision: float
    recall: float
    f1_score: float
    anomaly_count: int
    detection_count: int

def run_single_simulation(
    config: SimulationConfig,
    anomaly_cfg: AnomalyConfig
) -> SimulationResult:
    """Run a single simulation with given configuration."""
    logger.info(f"Running simulation with seed={config.seed}, n_samples={config.n_samples}")

    # Generate synthetic time series
    np.random.seed(config.seed)
    signal_cfg = SignalConfig(
        length=config.n_samples,
        frequency=1.0,
        noise_level=0.1
    )

    data, ground_truth = generate_synthetic_timeseries(
        signal_config=signal_cfg,
        anomaly_config=anomaly_cfg,
        seed=config.seed
    )

    # Prepare data for model
    X = data['values'].reshape(-1, 1)
    timestamps = data['timestamps']

    # Initialize DPGMM model
    dpgmm_config = DPGMMConfig(
        window_size=config.window_size,
        max_components=10,
        convergence_threshold=0.01,
        max_iterations=500,
        seed=config.seed
    )

    model = DPGMMModel(config=dpgmm_config)

    # Run inference
    logger.info("Running DPGMM inference...")
    results = model.fit_predict(X)

    # Compute anomaly scores
    anomaly_scores = results['anomaly_scores']

    # Determine anomalies based on threshold
    threshold = np.percentile(anomaly_scores, 95)
    detected = (anomaly_scores > threshold).astype(int)

    # Calculate metrics
    true_anomalies = ground_truth['is_anomaly']

    # Ensure arrays are aligned
    min_len = min(len(detected), len(true_anomalies))
    detected = detected[:min_len]
    true_anomalies = true_anomalies[:min_len]

    anomaly_count = int(np.sum(true_anomalies))
    detection_count = int(np.sum(detected))

    if anomaly_count == 0:
        # No ground truth anomalies, use a default SNR calculation
        snr = 1.0  # Default SNR when no anomalies present
        detection_rate = 0.0
        false_positive_rate = float(np.mean(detected))
        precision = 0.0 if detection_count == 0 else 1.0
        recall = 0.0
        f1_score = 0.0
    else:
        # Calculate SNR based on signal-to-noise ratio of detected vs actual anomalies
        # Using a simple ratio of true positives to false positives as a proxy for SNR
        tp = np.sum((detected == 1) & (true_anomalies == 1))
        fp = np.sum((detected == 1) & (true_anomalies == 0))
        fn = np.sum((detected == 0) & (true_anomalies == 1))

        if fp == 0:
            snr = float(tp) + 1.0  # Avoid division by zero
        else:
            snr = float(tp) / fp

        detection_rate = float(tp) / anomaly_count if anomaly_count > 0 else 0.0
        false_positive_rate = float(fp) / (len(true_anomalies) - anomaly_count) if (len(true_anomalies) - anomaly_count) > 0 else 0.0

        precision = float(tp) / detection_count if detection_count > 0 else 0.0
        recall = float(tp) / anomaly_count if anomaly_count > 0 else 0.0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return SimulationResult(
        snr=snr,
        detection_rate=detection_rate,
        false_positive_rate=false_positive_rate,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        anomaly_count=anomaly_count,
        detection_count=detection_count
    )

def run_simulation_study(
    config: SimulationConfig,
    anomaly_cfg: AnomalyConfig
) -> List[SimulationResult]:
    """Run the full simulation study."""
    logger.info(f"Starting simulation study with {config.n_simulations} iterations")

    results = []
    for i in range(config.n_simulations):
        seed = config.seed + i
        result = run_single_simulation(
            SimulationConfig(
                seed=seed,
                n_samples=config.n_samples,
                window_size=config.window_size,
                stride=config.stride,
                anomaly_rate=config.anomaly_rate,
                n_simulations=1,
                snr_threshold=config.snr_threshold
            ),
            anomaly_cfg
        )
        results.append(result)
        logger.info(f"Simulation {i+1}/{config.n_simulations}: SNR={result.snr:.4f}, F1={result.f1_score:.4f}")

    return results

def save_results(results: List[SimulationResult], output_path: Path) -> None:
    """Save simulation results to CSV."""
    data = {
        'simulation_id': range(1, len(results) + 1),
        'snr': [r.snr for r in results],
        'detection_rate': [r.detection_rate for r in results],
        'false_positive_rate': [r.false_positive_rate for r in results],
        'precision': [r.precision for r in results],
        'recall': [r.recall for r in results],
        'f1_score': [r.f1_score for r in results],
        'anomaly_count': [r.anomaly_count for r in results],
        'detection_count': [r.detection_count for r in results]
    }

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for the simulation study."""
    parser = argparse.ArgumentParser(description='Run simulation study for ADVI validation')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--n-samples', type=int, default=1000, help='Number of samples')
    parser.add_argument('--window-size', type=int, default=50, help='Window size for DPGMM')
    parser.add_argument('--anomaly-rate', type=float, default=0.05, help='Anomaly rate')
    parser.add_argument('--n-simulations', type=int, default=10, help='Number of simulation iterations')
    parser.add_argument('--output', type=str, default='data/processed/results/simulation_snr.csv',
                      help='Output file path')

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure anomaly injection
    anomaly_cfg = AnomalyConfig(
        anomaly_type='point',
        anomaly_start=int(args.n_samples * 0.6),
        anomaly_end=int(args.n_samples * 0.8),
        magnitude=3.0
    )

    # Configure simulation
    sim_config = SimulationConfig(
        seed=args.seed,
        n_samples=args.n_samples,
        window_size=args.window_size,
        stride=1,
        anomaly_rate=args.anomaly_rate,
        n_simulations=args.n_simulations,
        snr_threshold=1.0
    )

    # Run simulation study
    results = run_simulation_study(sim_config, anomaly_cfg)

    # Save results
    save_results(results, output_path)

    # Calculate and log summary statistics
    avg_snr = np.mean([r.snr for r in results])
    avg_f1 = np.mean([r.f1_score for r in results])

    logger.info("=" * 60)
    logger.info("Simulation Study Summary")
    logger.info("=" * 60)
    logger.info(f"Average SNR: {avg_snr:.4f}")
    logger.info(f"Average F1 Score: {avg_f1:.4f}")
    logger.info(f"SNR Threshold: {sim_config.snr_threshold}")

    if avg_snr > sim_config.snr_threshold:
        logger.info("✓ PASS: SNR exceeds threshold")
    else:
        logger.warning("✗ FAIL: SNR does not exceed threshold")

    return 0 if avg_snr > sim_config.snr_threshold else 1

if __name__ == '__main__':
    sys.exit(main())