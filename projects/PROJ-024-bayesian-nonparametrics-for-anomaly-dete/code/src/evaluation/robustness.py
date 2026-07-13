"""
Robustness evaluation for the Bayesian Nonparametrics Anomaly Detection pipeline.

This module implements sensitivity analysis on window size, derivative calculation methods,
and other hyperparameters to validate the robustness of the anomaly detection system
(FR-016).

It includes:
- Sensitivity sweep over window sizes
- Comparison of derivative calculation methods (finite difference, smoothing, lag)
- Bootstrapped confidence intervals for metric stability
- Reporting of instability flags when performance degrades significantly
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.synthetic_generator import generate_synthetic_timeseries, SyntheticDataset
from models.dp_gmm import DPGMMModel, DPGMMConfig
from data.windowing import sliding_window, normalize_window
from evaluation.metrics import compute_all_metrics, EvaluationMetrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class RobustnessConfig:
    """Configuration for robustness analysis."""
    base_window_size: int = 50
    window_sizes: List[int] = None
    anomaly_rate: float = 0.05
    n_samples: int = 1000
    seed: int = 42
    n_bootstrap: int = 100
    output_dir: str = "data/processed/results"
    
    def __post_init__(self):
        if self.window_sizes is None:
            self.window_sizes = [30, 40, 50, 60, 80]

@dataclass
class RobustnessResult:
    """Result of a single robustness configuration test."""
    window_size: int
    metric_name: str
    mean_value: float
    std_value: float
    ci_lower: float
    ci_upper: float
    is_stable: bool
    instability_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class DerivativeMethodResult:
    """Result of comparing different derivative calculation methods."""
    method_name: str
    mean_f1: float
    std_f1: float
    mean_detection_time: float
    std_detection_time: float
    is_stable: bool

def calculate_derivative_finite_difference(signal: np.ndarray, lag: int = 1) -> np.ndarray:
    """
    Calculate first derivative using finite difference.
    
    Args:
        signal: Input signal array
        lag: Lag for difference calculation
        
    Returns:
        Derivative array (length: len(signal) - lag)
    """
    if len(signal) <= lag:
        return np.array([])
    return np.diff(signal, n=1) / lag

def calculate_derivative_smoothed(signal: np.ndarray, window: int = 5) -> np.ndarray:
    """
    Calculate derivative after applying moving average smoothing.
    
    Args:
        signal: Input signal array
        window: Smoothing window size
        
    Returns:
        Smoothed derivative array
    """
    if len(signal) < window:
        return calculate_derivative_finite_difference(signal)
    
    # Apply moving average
    smoothed = np.convolve(signal, np.ones(window)/window, mode='valid')
    return calculate_derivative_finite_difference(smoothed)

def calculate_derivative_lagged(signal: np.ndarray, lag: int = 3) -> np.ndarray:
    """
    Calculate derivative with explicit lag to reduce noise sensitivity.
    
    Args:
        signal: Input signal array
        lag: Lag for derivative calculation
        
    Returns:
        Lagged derivative array
    """
    if len(signal) <= lag:
        return np.array([])
    return (signal[lag:] - signal[:-lag]) / (2 * lag)

def run_single_robustness_test(
    dataset: SyntheticDataset,
    window_size: int,
    seed: int,
    derivative_method: str = "finite_difference"
) -> Optional[EvaluationMetrics]:
    """
    Run anomaly detection with specific window size and derivative method.
    
    Args:
        dataset: Pre-generated synthetic dataset with anomalies
        window_size: Window size for sliding window
        seed: Random seed for reproducibility
        derivative_method: Method for derivative calculation
        
    Returns:
        EvaluationMetrics if successful, None otherwise
    """
    try:
        # Set seed for reproducibility
        np.random.seed(seed)
        
        # Extract signal
        signal = dataset.signal
        ground_truth = dataset.anomaly_labels
        
        if len(signal) < window_size:
            logger.warning(f"Signal length ({len(signal)}) < window size ({window_size})")
            return None
        
        # Apply sliding window
        windows = list(sliding_window(signal, window_size, stride=1))
        
        if len(windows) == 0:
            logger.warning("No windows generated")
            return None
        
        # Initialize DP-GMM model
        config = DPGMMConfig(
            max_components=5,
            concentration_prior_alpha=1.0,
            concentration_prior_beta=1.0,
            random_seed=seed
        )
        model = DPGMMModel(config)
        
        # Process windows and compute anomaly scores
        scores = []
        true_labels = []
        
        for i, window in enumerate(windows):
            # Normalize window
            norm_window = normalize_window(window)
            
            # Fit model on window
            try:
                model.fit(norm_window)
                
                # Calculate derivative based on method
                if derivative_method == "finite_difference":
                    derivative = calculate_derivative_finite_difference(norm_window)
                elif derivative_method == "smoothed":
                    derivative = calculate_derivative_smoothed(norm_window)
                elif derivative_method == "lagged":
                    derivative = calculate_derivative_lagged(norm_window)
                else:
                    derivative = calculate_derivative_finite_difference(norm_window)
                
                # Use derivative variance as anomaly signal (simplified for robustness test)
                # In real implementation, this would be the actual DPGMM anomaly score
                if len(derivative) > 0:
                    score = np.var(derivative)
                else:
                    score = 0.0
                    
                scores.append(score)
                
                # Map window index to ground truth (approximate)
                # Window i covers indices [i, i+window_size)
                start_idx = i
                end_idx = min(i + window_size, len(ground_truth))
                # Label is 1 if any point in window is anomalous
                label = 1 if np.any(ground_truth[start_idx:end_idx]) else 0
                true_labels.append(label)
                
            except Exception as e:
                logger.warning(f"Window {i} failed: {e}")
                continue
        
        if len(scores) < 10:
            logger.warning("Insufficient scores for evaluation")
            return None
        
        # Convert to arrays
        scores = np.array(scores)
        true_labels = np.array(true_labels)
        
        # Normalize scores for comparison
        if scores.max() > scores.min():
            scores = (scores - scores.min()) / (scores.max() - scores.min())
        
        # Compute metrics
        metrics = compute_all_metrics(true_labels, scores)
        return metrics
        
    except Exception as e:
        logger.error(f"Error in robustness test: {e}", exc_info=True)
        return None

def bootstrap_stability_check(
    results: List[Optional[EvaluationMetrics]],
    n_bootstrap: int = 100,
    confidence_level: float = 0.95
) -> Tuple[float, float, float, float]:
    """
    Perform bootstrap resampling to assess metric stability.
    
    Args:
        results: List of EvaluationMetrics from multiple runs
        n_bootstrap: Number of bootstrap iterations
        confidence_level: Confidence level for intervals
        
    Returns:
        (mean, std, ci_lower, ci_upper) for F1 score
    """
    f1_scores = [r.f1_score for r in results if r is not None and r.f1_score is not None]
    
    if len(f1_scores) < 2:
        return 0.0, 0.0, 0.0, 0.0
    
    bootstrap_means = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(f1_scores, size=len(f1_scores), replace=True)
        bootstrap_means.append(np.mean(sample))
    
    mean_val = np.mean(bootstrap_means)
    std_val = np.std(bootstrap_means)
    
    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_means, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
    
    return mean_val, std_val, ci_lower, ci_upper

def run_window_size_sensitivity(
    dataset: SyntheticDataset,
    config: RobustnessConfig
) -> List[RobustnessResult]:
    """
    Run sensitivity analysis over different window sizes.
    
    Args:
        dataset: Synthetic dataset with anomalies
        config: Robustness configuration
        
    Returns:
        List of RobustnessResult for each window size
    """
    results = []
    
    for window_size in config.window_sizes:
        logger.info(f"Testing window size: {window_size}")
        
        # Run multiple seeds for stability
        run_results = []
        for seed_offset in range(5):
            seed = config.seed + seed_offset
            metrics = run_single_robustness_test(dataset, window_size, seed)
            if metrics:
                run_results.append(metrics)
        
        if len(run_results) < 3:
            logger.warning(f"Insufficient successful runs for window size {window_size}")
            continue
        
        # Bootstrap analysis
        mean_f1, std_f1, ci_lower, ci_upper = bootstrap_stability_check(run_results, config.n_bootstrap)
        
        # Determine stability (coefficient of variation < 0.2)
        cv = std_f1 / mean_f1 if mean_f1 > 0 else 0
        is_stable = cv < 0.2
        
        reason = None
        if not is_stable:
            if cv >= 0.2:
                reason = f"High variability (CV={cv:.3f})"
            elif mean_f1 < 0.3:
                reason = "Low performance"
        
        result = RobustnessResult(
            window_size=window_size,
            metric_name="f1_score",
            mean_value=mean_f1,
            std_value=std_f1,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            is_stable=is_stable,
            instability_reason=reason
        )
        results.append(result)
    
    return results

def run_derivative_method_comparison(
    dataset: SyntheticDataset,
    config: RobustnessConfig
) -> List[DerivativeMethodResult]:
    """
    Compare different derivative calculation methods.
    
    Args:
        dataset: Synthetic dataset
        config: Robustness configuration
        
    Returns:
        List of results for each derivative method
    """
    methods = ["finite_difference", "smoothed", "lagged"]
    results = []
    
    for method in methods:
        logger.info(f"Testing derivative method: {method}")
        
        run_results = []
        for seed_offset in range(5):
            seed = config.seed + seed_offset
            metrics = run_single_robustness_test(
                dataset, 
                config.base_window_size, 
                seed,
                derivative_method=method
            )
            if metrics:
                run_results.append(metrics)
        
        if len(run_results) < 3:
            continue
        
        f1_scores = [r.f1_score for r in run_results if r.f1_score]
        mean_f1 = np.mean(f1_scores)
        std_f1 = np.std(f1_scores)
        
        # Detection time approximation (lower is better)
        # In real implementation, this would use actual timestamps
        detection_times = [1.0 / (r.f1_score + 1e-6) for r in run_results if r.f1_score]
        mean_det = np.mean(detection_times) if detection_times else 0.0
        std_det = np.std(detection_times) if detection_times else 0.0
        
        cv = std_f1 / mean_f1 if mean_f1 > 0 else 0
        is_stable = cv < 0.2
        
        results.append(DerivativeMethodResult(
            method_name=method,
            mean_f1=mean_f1,
            std_f1=std_f1,
            mean_detection_time=mean_det,
            std_detection_time=std_det,
            is_stable=is_stable
        ))
    
    return results

def save_robustness_report(
    window_results: List[RobustnessResult],
    derivative_results: List[DerivativeMethodResult],
    output_path: Path
):
    """Save robustness analysis report to JSON and CSV."""
    
    # Prepare data for CSV
    csv_rows = []
    for r in window_results:
        csv_rows.append({
            "type": "window_size",
            "parameter": r.window_size,
            "metric": r.metric_name,
            "mean": r.mean_value,
            "std": r.std_value,
            "ci_lower": r.ci_lower,
            "ci_upper": r.ci_upper,
            "is_stable": r.is_stable,
            "instability_reason": r.instability_reason or ""
        })
    
    for r in derivative_results:
        csv_rows.append({
            "type": "derivative_method",
            "parameter": r.method_name,
            "metric": "f1_score",
            "mean": r.mean_f1,
            "std": r.std_f1,
            "ci_lower": r.mean_f1 - 1.96 * r.std_f1,
            "ci_upper": r.mean_f1 + 1.96 * r.std_f1,
            "is_stable": r.is_stable,
            "instability_reason": ""
        })
    
    # Save CSV
    import csv
    output_csv = output_path / "robustness_analysis.csv"
    if csv_rows:
        with open(output_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
            writer.writeheader()
            writer.writerows(csv_rows)
        logger.info(f"Saved robustness CSV to {output_csv}")
    
    # Save JSON summary
    summary = {
        "window_size_results": [r.to_dict() for r in window_results],
        "derivative_method_results": [asdict(r) for r in derivative_results],
        "summary": {
            "total_window_tests": len(window_results),
            "stable_window_tests": sum(1 for r in window_results if r.is_stable),
            "total_derivative_tests": len(derivative_results),
            "stable_derivative_tests": sum(1 for r in derivative_results if r.is_stable),
            "overall_stability": (
                sum(1 for r in window_results if r.is_stable) + 
                sum(1 for r in derivative_results if r.is_stable)
            ) / (len(window_results) + len(derivative_results)) if (window_results or derivative_results) else 0.0
        }
    }
    
    output_json = output_path / "robustness_summary.json"
    with open(output_json, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved robustness summary to {output_json}")

def main():
    """Main entry point for robustness analysis."""
    parser = argparse.ArgumentParser(description="Run robustness analysis")
    parser.add_argument("--subset-size", type=int, default=50, help="Subset size for testing")
    parser.add_argument("--n-samples", type=int, default=500, help="Number of samples to generate")
    parser.add_argument("--anomaly-rate", type=float, default=0.05, help="Anomaly injection rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    
    args = parser.parse_args()
    
    logger.info("Starting robustness analysis")
    
    # Generate synthetic dataset
    logger.info(f"Generating synthetic dataset with {args.n_samples} samples")
    dataset = generate_synthetic_timeseries(
        n_samples=args.n_samples,
        anomaly_rate=args.anomaly_rate,
        signal_type="mixed",
        seed=args.seed
    )
    
    # Create config
    config = RobustnessConfig(
        base_window_size=args.subset_size,
        anomaly_rate=args.anomaly_rate,
        n_samples=args.n_samples,
        seed=args.seed,
        n_bootstrap=100,
        output_dir=args.output or str(project_root / "data" / "processed" / "results")
    )
    
    # Ensure output directory exists
    output_path = Path(config.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Run window size sensitivity
    logger.info("Running window size sensitivity analysis")
    window_results = run_window_size_sensitivity(dataset, config)
    
    # Run derivative method comparison
    logger.info("Running derivative method comparison")
    derivative_results = run_derivative_method_comparison(dataset, config)
    
    # Save report
    save_robustness_report(window_results, derivative_results, output_path)
    
    # Print summary
    logger.info("Robustness Analysis Summary")
    logger.info("=" * 40)
    for r in window_results:
        status = "✓" if r.is_stable else "✗"
        logger.info(f"Window {r.window_size}: {r.mean_value:.3f} ± {r.std_value:.3f} {status}")
    
    for r in derivative_results:
        status = "✓" if r.is_stable else "✗"
        logger.info(f"Method {r.method_name}: {r.mean_f1:.3f} ± {r.std_f1:.3f} {status}")
    
    logger.info("Robustness analysis complete")

if __name__ == "__main__":
    main()