"""
Robustness evaluation module for Bayesian Nonparametric Anomaly Detection.

Implements sensitivity analysis, stability checks, and validation of the
DP-GMM model against perturbations and alternative configurations.

This module is invoked by the quickstart run-book to verify model robustness.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.synthetic_generator import generate_synthetic_timeseries, AnomalyConfig, SignalConfig, SyntheticDataset
from models.dp_gmm import DPGMMModel, DPGMMConfig
from evaluation.metrics import compute_all_metrics, EvaluationMetrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'robustness.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SUBSET_SIZE = 50
DEFAULT_SEED = 42
DEFAULT_ANOMALY_RATE = 0.05
OUTPUT_DIR = project_root / 'data' / 'processed' / 'results'
OUTPUT_FILE = OUTPUT_DIR / 'robustness_report.csv'

class RobustnessConfig:
    """Configuration for robustness evaluation."""
    
    def __init__(
        self,
        subset_size: int = DEFAULT_SUBSET_SIZE,
        seed: int = DEFAULT_SEED,
        anomaly_rate: float = DEFAULT_ANOMALY_RATE,
        n_replications: int = 10,
        perturbation_levels: List[float] = None,
        window_sizes: List[int] = None
    ):
        self.subset_size = subset_size
        self.seed = seed
        self.anomaly_rate = anomaly_rate
        self.n_replications = n_replications
        self.perturbation_levels = perturbation_levels or [0.0, 0.01, 0.05, 0.1, 0.2]
        self.window_sizes = window_sizes or [30, 50, 70]
    
    @classmethod
    def from_args(cls, args: argparse.Namespace) -> 'RobustnessConfig':
        return cls(
            subset_size=args.subset_size,
            seed=args.seed,
            anomaly_rate=args.anomaly_rate,
            n_replications=args.n_replications,
            perturbation_levels=args.perturbation_levels,
            window_sizes=args.window_sizes
        )

class RobustnessResult:
    """Container for robustness evaluation results."""
    
    def __init__(
        self,
        perturbation_level: float,
        window_size: int,
        replication: int,
        metrics: EvaluationMetrics,
        stability_score: float,
        runtime_seconds: float
    ):
        self.perturbation_level = perturbation_level
        self.window_size = window_size
        self.replication = replication
        self.metrics = metrics
        self.stability_score = stability_score
        self.runtime_seconds = runtime_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'perturbation_level': self.perturbation_level,
            'window_size': self.window_size,
            'replication': self.replication,
            'precision': self.metrics.precision,
            'recall': self.metrics.recall,
            'f1_score': self.metrics.f1_score,
            'auc': self.metrics.auc,
            'stability_score': self.stability_score,
            'runtime_seconds': self.runtime_seconds
        }

def inject_noise(
    data: np.ndarray,
    noise_level: float,
    rng: np.random.Generator
) -> np.ndarray:
    """Inject Gaussian noise into data at specified level."""
    noise = rng.normal(0, noise_level * np.std(data), size=data.shape)
    return data + noise

def compute_stability_score(
    results: List[RobustnessResult],
    metric_name: str = 'f1_score'
) -> float:
    """
    Compute stability score as inverse of coefficient of variation.
    Higher score = more stable.
    """
    if len(results) < 2:
        return 1.0
    
    values = [getattr(r.metrics, metric_name) for r in results]
    mean_val = np.mean(values)
    std_val = np.std(values)
    
    if mean_val == 0:
        return 0.0
    
    cv = std_val / mean_val
    stability = 1.0 / (1.0 + cv)
    return stability

def run_robustness_evaluation(
    config: RobustnessConfig,
    model_config: Optional[DPGMMConfig] = None
) -> List[RobustnessResult]:
    """
    Execute robustness evaluation across perturbation levels and window sizes.
    
    Returns list of RobustnessResult objects for all combinations.
    """
    results = []
    rng = np.random.default_rng(config.seed)
    
    # Generate base synthetic dataset
    logger.info(f"Generating synthetic dataset with seed={config.seed}, anomaly_rate={config.anomaly_rate}")
    signal_config = SignalConfig(
        n_samples=config.subset_size * 10,
        n_components=3,
        noise_level=0.1
    )
    anomaly_config = AnomalyConfig(
        anomaly_rate=config.anomaly_rate,
        anomaly_types=['point', 'contextual', 'collective']
    )
    
    try:
        dataset: SyntheticDataset = generate_synthetic_timeseries(
            signal_config, anomaly_config, config.subset_size * 10
        )
    except AttributeError as e:
        # Fallback for missing attributes in AnomalyConfig
        logger.warning(f"AttributeError in dataset generation: {e}. Using fallback config.")
        anomaly_config.anomaly_duration_min = 5
        anomaly_config.anomaly_duration_max = 20
        anomaly_config.magnitude_min = 3.0
        anomaly_config.magnitude_max = 5.0
        dataset: SyntheticDataset = generate_synthetic_timeseries(
            signal_config, anomaly_config, config.subset_size * 10
        )
    
    data = dataset.values
    ground_truth = dataset.anomaly_labels
    
    # Default model config if not provided
    if model_config is None:
        model_config = DPGMMConfig(
            max_components=10,
            convergence_threshold=0.01,
            max_iterations=500,
            seed=config.seed
        )
    
    # Iterate over perturbation levels and window sizes
    for perturbation_level in config.perturbation_levels:
        for window_size in config.window_sizes:
            replication_results = []
            
            for rep in range(config.n_replications):
                start_time = datetime.now()
                
                # Inject noise
                noisy_data = inject_noise(data, perturbation_level, rng)
                
                # Create and train model
                model = DPGMMModel(model_config)
                
                try:
                    # Fit model on noisy data
                    model.fit(noisy_data, window_size=window_size)
                    
                    # Compute predictions
                    predictions = model.predict(noisy_data)
                    anomaly_scores = model.compute_anomaly_scores(noisy_data)
                    
                    # Compute metrics
                    metrics = compute_all_metrics(
                        y_true=ground_truth,
                        y_pred=(anomaly_scores > np.percentile(anomaly_scores, 95)).astype(int)
                    )
                    
                    end_time = datetime.now()
                    runtime = (end_time - start_time).total_seconds()
                    
                    result = RobustnessResult(
                        perturbation_level=perturbation_level,
                        window_size=window_size,
                        replication=rep,
                        metrics=metrics,
                        stability_score=0.0,  # Will be computed later
                        runtime_seconds=runtime
                    )
                    replication_results.append(result)
                    results.append(result)
                    
                    logger.info(
                        f"Rep {rep+1}/{config.n_replications} | "
                        f"Perturbation: {perturbation_level:.2f} | "
                        f"Window: {window_size} | "
                        f"F1: {metrics.f1_score:.4f} | "
                        f"Runtime: {runtime:.2f}s"
                    )
                    
                except Exception as e:
                    logger.error(f"Error in replication {rep}: {e}")
                    continue
            
            # Compute stability score for this configuration
            if replication_results:
                stability = compute_stability_score(replication_results)
                for r in replication_results:
                    r.stability_score = stability
            
            logger.info(
                f"Configuration (Perturbation={perturbation_level}, "
                f"Window={window_size}) completed. "
                f"Stability score: {stability:.4f}"
            )
    
    return results

def save_results(results: List[RobustnessResult], output_path: Path):
    """Save robustness results to CSV file."""
    if not results:
        logger.warning("No results to save.")
        return
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to DataFrame and save
    data = [r.to_dict() for r in results]
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Results saved to {output_path}")
    
    # Generate summary statistics
    summary = df.groupby(['perturbation_level', 'window_size']).agg({
        'f1_score': ['mean', 'std'],
        'precision': ['mean', 'std'],
        'recall': ['mean', 'std'],
        'stability_score': ['mean'],
        'runtime_seconds': ['mean', 'std']
    }).reset_index()
    
    summary_path = output_path.parent / 'robustness_summary.csv'
    summary.to_csv(summary_path, index=False)
    logger.info(f"Summary saved to {summary_path}")

def main():
    """Main entry point for robustness evaluation."""
    parser = argparse.ArgumentParser(
        description='Run robustness evaluation for DP-GMM anomaly detection.'
    )
    parser.add_argument(
        '--subset-size',
        type=int,
        default=DEFAULT_SUBSET_SIZE,
        help='Size of data subset to evaluate'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=DEFAULT_SEED,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--anomaly-rate',
        type=float,
        default=DEFAULT_ANOMALY_RATE,
        help='Rate of anomalies in synthetic data'
    )
    parser.add_argument(
        '--n-replications',
        type=int,
        default=10,
        help='Number of replications per configuration'
    )
    parser.add_argument(
        '--perturbation-levels',
        type=float,
        nargs='+',
        default=[0.0, 0.01, 0.05, 0.1, 0.2],
        help='Noise perturbation levels to test'
    )
    parser.add_argument(
        '--window-sizes',
        type=int,
        nargs='+',
        default=[30, 50, 70],
        help='Window sizes to test'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path (default: data/processed/results/robustness_report.csv)'
    )
    
    args = parser.parse_args()
    config = RobustnessConfig.from_args(args)
    
    logger.info("=" * 60)
    logger.info("Starting Robustness Evaluation")
    logger.info("=" * 60)
    logger.info(f"Configuration: {config.__dict__}")
    
    # Run evaluation
    results = run_robustness_evaluation(config)
    
    # Save results
    output_path = Path(args.output) if args.output else OUTPUT_FILE
    save_results(results, output_path)
    
    logger.info("=" * 60)
    logger.info("Robustness Evaluation Complete")
    logger.info("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
