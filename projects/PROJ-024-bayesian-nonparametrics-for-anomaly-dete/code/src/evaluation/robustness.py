"""
Robustness analysis for the Bayesian Nonparametric Anomaly Detection pipeline.

This module implements sensitivity analysis for:
- Window size variations
- Derivative calculation methods (smoothing, lag)
- Threshold sensitivity
- Model stability under perturbation

It is invoked by the run-book to verify that the detection pipeline produces
consistent results under reasonable variations of hyperparameters and data
processing choices.
"""

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np

# Ensure code/src is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models.dp_gmm import DPGMMModel, DPGMMConfig
from data.synthetic_generator import generate_synthetic_timeseries, SyntheticDataset
from evaluation.metrics import compute_all_metrics, EvaluationMetrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class RobustnessConfig:
    """Configuration for robustness analysis."""
    base_window_size: int = 50
    window_size_variations: List[int] = field(default_factory=lambda: [40, 50, 60, 70])
    derivative_smoothing: List[int] = field(default_factory=lambda: [1, 3, 5])
    lag_variations: List[int] = field(default_factory=lambda: [1, 2, 3])
    subset_size: int = 100  # Number of samples to use for speed
    n_runs: int = 5  # Number of independent runs per configuration
    random_seed_base: int = 42
    output_path: Path = Path("data/processed/results/robustness_report.json")

@dataclass
class RobustnessResult:
    """Result of a single robustness test run."""
    config_name: str
    window_size: int
    smoothing: int
    lag: int
    run_id: int
    runtime_seconds: float
    metrics: EvaluationMetrics
    stability_score: float  # Variance of scores across windows
    anomaly_count: int
    is_stable: bool

def generate_test_data(config: RobustnessConfig, seed: int) -> SyntheticDataset:
    """Generate synthetic time series with anomalies for robustness testing."""
    np.random.seed(seed)
    
    # Generate base signal
    n_samples = config.subset_size * 4  # Enough for multiple windows
    dataset = generate_synthetic_timeseries(
        n_samples=n_samples,
        anomaly_fraction=0.1,
        anomaly_type="point",
        seed=seed
    )
    return dataset

def compute_derivative(signal: np.ndarray, smoothing: int, lag: int) -> np.ndarray:
    """
    Compute first derivative with optional smoothing and lag.
    
    Args:
        signal: Input time series
        smoothing: Window size for moving average smoothing (1 = no smoothing)
        lag: Lag for derivative calculation
        
    Returns:
        First derivative of the signal
    """
    # Apply smoothing if requested
    if smoothing > 1:
        kernel = np.ones(smoothing) / smoothing
        smoothed = np.convolve(signal, kernel, mode='same')
    else:
        smoothed = signal
    
    # Compute derivative with lag
    if lag >= len(smoothed):
        # Fallback to simple difference if lag is too large
        derivative = np.diff(smoothed)
    else:
        derivative = (smoothed[lag:] - smoothed[:-lag]) / lag
    
    # Pad to match original length
    pad_width = len(signal) - len(derivative)
    if pad_width > 0:
        derivative = np.pad(derivative, (0, pad_width), mode='edge')
    
    return derivative

def run_single_test(
    config: RobustnessConfig,
    window_size: int,
    smoothing: int,
    lag: int,
    run_id: int,
    dataset: SyntheticDataset
) -> RobustnessResult:
    """Run a single robustness test configuration."""
    
    start_time = time.time()
    
    # Configure DPGMM with specific window size
    dpgmm_config = DPGMMConfig(
        window_size=window_size,
        alpha_prior_mean=1.0,
        alpha_prior_std=0.5,
        max_components=10,
        random_seed=config.random_seed_base + run_id
    )
    
    model = DPGMMModel(dpgmm_config)
    
    # Prepare data with specific derivative settings
    signal = dataset.signal
    derivative = compute_derivative(signal, smoothing, lag)
    
    # Create sliding windows
    n_windows = len(derivative) - window_size + 1
    scores = []
    uncertainties = []
    
    for i in range(n_windows):
        window_data = derivative[i:i + window_size]
        
        try:
            # Run inference on window
            result = model.fit_predict(window_data)
            score = result.anomaly_score
            uncertainty = result.uncertainty
            
            scores.append(score)
            uncertainties.append(uncertainty)
        except Exception as e:
            logger.warning(f"Window {i} failed: {e}")
            scores.append(0.0)
            uncertainties.append(1.0)
    
    runtime = time.time() - start_time
    
    # Compute metrics
    # Use ground truth from dataset if available
    if hasattr(dataset, 'anomaly_labels') and dataset.anomaly_labels is not None:
        # Align labels with windows (simplified: assume labels are per-sample)
        window_labels = []
        for i in range(n_windows):
            # Check if any point in window is anomalous
            window_label = np.max(dataset.anomaly_labels[i:i + window_size])
            window_labels.append(window_label)
        
        y_true = np.array(window_labels)
        y_scores = np.array(scores)
        
        metrics = compute_all_metrics(y_true, y_scores)
    else:
        # Fallback: compute internal stability metrics
        metrics = EvaluationMetrics(
            f1_score=0.0,
            precision=0.0,
            recall=0.0,
            auc=0.0,
            note="No ground truth available for this run"
        )
    
    # Compute stability score (variance of scores)
    stability_score = float(np.var(scores)) if len(scores) > 0 else 0.0
    anomaly_count = sum(1 for s in scores if s > 0.5)
    
    # Determine stability (low variance = stable)
    is_stable = stability_score < 0.1
    
    config_name = f"window_{window_size}_smooth_{smoothing}_lag_{lag}"
    
    return RobustnessResult(
        config_name=config_name,
        window_size=window_size,
        smoothing=smoothing,
        lag=lag,
        run_id=run_id,
        runtime_seconds=runtime,
        metrics=metrics,
        stability_score=stability_score,
        anomaly_count=anomaly_count,
        is_stable=is_stable
    )

def aggregate_results(results: List[RobustnessResult]) -> Dict[str, Any]:
    """Aggregate results from multiple runs."""
    if not results:
        return {"error": "No results to aggregate"}
    
    # Group by configuration
    config_groups: Dict[str, List[RobustnessResult]] = {}
    for r in results:
        key = f"{r.window_size}_{r.smoothing}_{r.lag}"
        if key not in config_groups:
            config_groups[key] = []
        config_groups[key].append(r)
    
    aggregated = []
    for key, group in config_groups.items():
        avg_runtime = np.mean([r.runtime_seconds for r in group])
        avg_stability = np.mean([r.stability_score for r in group])
        avg_anomaly_count = np.mean([r.anomaly_count for r in group])
        stability_rate = sum(1 for r in group if r.is_stable) / len(group)
        
        # Aggregate metrics
        if group[0].metrics.f1_score != 0.0 or "No ground truth" not in str(group[0].metrics.note):
            avg_f1 = np.mean([r.metrics.f1_score for r in group])
            avg_precision = np.mean([r.metrics.precision for r in group])
            avg_recall = np.mean([r.metrics.recall for r in group])
            avg_auc = np.mean([r.metrics.auc for r in group])
        else:
            avg_f1 = avg_precision = avg_recall = avg_auc = 0.0
        
        aggregated.append({
            "config_key": key,
            "window_size": group[0].window_size,
            "smoothing": group[0].smoothing,
            "lag": group[0].lag,
            "n_runs": len(group),
            "avg_runtime_seconds": float(avg_runtime),
            "avg_stability_score": float(avg_stability),
            "avg_anomaly_count": float(avg_anomaly_count),
            "stability_rate": float(stability_rate),
            "avg_f1_score": float(avg_f1),
            "avg_precision": float(avg_precision),
            "avg_recall": float(avg_recall),
            "avg_auc": float(avg_auc)
        })
    
    # Overall summary
    overall_stability = np.mean([r.stability_score for r in results])
    overall_stability_rate = sum(1 for r in results if r.is_stable) / len(results)
    
    return {
        "summary": {
            "total_runs": len(results),
            "overall_avg_stability": float(overall_stability),
            "overall_stability_rate": float(overall_stability_rate)
        },
        "configurations": aggregated
    }

def main():
    """Main entry point for robustness analysis."""
    parser = argparse.ArgumentParser(description="Robustness analysis for anomaly detection")
    parser.add_argument("--subset-size", type=int, default=100, help="Size of data subset to use")
    parser.add_argument("--n-runs", type=int, default=3, help="Number of independent runs per config")
    parser.add_argument("--output", type=str, default="data/processed/results/robustness_report.json",
                      help="Output path for results")
    args = parser.parse_args()
    
    logger.info("Starting robustness analysis...")
    
    config = RobustnessConfig(
        subset_size=args.subset_size,
        n_runs=args.n_runs,
        output_path=Path(args.output)
    )
    
    # Ensure output directory exists
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate test data once
    dataset = generate_test_data(config, seed=config.random_seed_base)
    logger.info(f"Generated test dataset with {len(dataset.signal)} samples")
    
    # Run all configurations
    all_results: List[RobustnessResult] = []
    
    for window_size in config.window_size_variations:
        for smoothing in config.derivative_smoothing:
            for lag in config.lag_variations:
                logger.info(f"Testing: window={window_size}, smooth={smoothing}, lag={lag}")
                
                for run_id in range(config.n_runs):
                    result = run_single_test(
                        config, window_size, smoothing, lag, run_id, dataset
                    )
                    all_results.append(result)
    
    # Aggregate results
    report = aggregate_results(all_results)
    
    # Save report
    with open(config.output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Robustness report saved to {config.output_path}")
    logger.info(f"Total runs: {report['summary']['total_runs']}")
    logger.info(f"Overall stability rate: {report['summary']['overall_stability_rate']:.2%}")
    
    # Print summary
    print("\n" + "="*60)
    print("ROBUSTNESS ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total configurations tested: {len(report['configurations'])}")
    print(f"Total runs: {report['summary']['total_runs']}")
    print(f"Overall stability rate: {report['summary']['overall_stability_rate']:.2%}")
    print(f"Average stability score: {report['summary']['overall_avg_stability']:.4f}")
    print("="*60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())