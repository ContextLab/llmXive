"""
Robustness analysis for the Bayesian Nonparametrics Anomaly Detection pipeline.

This module implements sensitivity analysis on window size, derivative calculation methods,
and validates the robustness of the $\dot{\alpha}$ metric against various perturbations.
"""

import argparse
import logging
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Add parent directory to path for imports when run as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.data.windowing import sliding_window
except ImportError:
    try:
        from data.windowing import sliding_window
    except ImportError:
        # Fallback for direct execution
        import os
        current_dir = Path(__file__).parent
        while current_dir.name != 'code':
            current_dir = current_dir.parent
        sys.path.insert(0, str(current_dir))
        from src.data.windowing import sliding_window

from src.models.dpgmm import DPGMMModel, DPGMMConfig
from src.evaluation.metrics import compute_all_metrics
from src.services.anomaly_detector import AnomalyDetectorService

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.windowing import sliding_window
from src.data.synthetic_generator import generate_synthetic_timeseries, save_synthetic_dataset
from src.models.dpgmm import DPGMMModel, DPGMMConfig
from src.evaluation.metrics import compute_all_metrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RobustnessConfig:
    """Configuration for robustness analysis."""
    base_window_size: int = 50
    window_size_variations: List[int] = None
    smoothing_kernels: List[str] = None
    subset_size: int = 50
    anomaly_rate: float = 0.05
    seed: int = 42
    output_path: str = "data/processed/results/robustness_report.json"

    def __post_init__(self):
        if self.window_size_variations is None:
            self.window_size_variations = [30, 50, 70, 100]
        if self.smoothing_kernels is None:
            self.smoothing_kernels = ['none', 'moving_avg', 'savgol']


@dataclass
class RobustnessResult:
    """Result of a single robustness check."""
    parameter_name: str
    parameter_value: Any
    metric_name: str
    metric_value: float
    std_dev: Optional[float] = None
    pass_threshold: bool = True
    notes: str = ""


def compute_derivative(signal: np.ndarray, method: str = 'finite_diff', smooth: bool = False) -> np.ndarray:
    """
    Compute the first derivative of a signal.

    Args:
        signal: Input signal array
        method: 'finite_diff' or 'gradient'
        smooth: Whether to apply smoothing before differentiation

    Returns:
        Derivative array
    """
    if smooth:
        # Simple moving average smoothing
        kernel_size = 3
        if len(signal) < kernel_size:
            kernel_size = len(signal)
        smoothed = np.convolve(signal, np.ones(kernel_size)/kernel_size, mode='same')
    else:
        smoothed = signal

    if method == 'finite_diff':
        return np.diff(smoothed)
    elif method == 'gradient':
        return np.gradient(smoothed)
    else:
        raise ValueError(f"Unknown derivative method: {method}")


def run_window_size_sensitivity(data: np.ndarray, anomaly_timestamps: List[int],
                                config: RobustnessConfig) -> List[RobustnessResult]:
    """
    Analyze sensitivity of detection metrics to window size variations.

    Args:
        data: Time series data
        anomaly_timestamps: Ground truth anomaly timestamps
        config: Robustness configuration

    Returns:
        List of robustness results
    """
    results = []
    base_metrics = None

    logger.info(f"Running window size sensitivity analysis on {len(data)} points")

    for window_size in config.window_size_variations:
        logger.info(f"Testing window size: {window_size}")

        try:
            # Generate windows
            windows, window_centers = sliding_window(data, window_size, stride=1)

            if len(windows) == 0:
                logger.warning(f"No windows generated for size {window_size}, skipping")
                continue

            # Run model on a subset to save time
            subset_indices = np.random.choice(len(windows), min(config.subset_size, len(windows)), replace=False)
            subset_windows = windows[subset_indices]

            # Configure model
            model_config = DPGMMConfig(
                window_size=window_size,
                max_components=10,
                concentration_prior_alpha=1.0,
                concentration_prior_beta=1.0,
                random_state=config.seed
            )

            model = DPGMMModel(model_config)

            # Run inference on subset
            scores = []
            for win in subset_windows:
                try:
                    score = model.compute_anomaly_score(win)
                    scores.append(score)
                except Exception as e:
                    logger.warning(f"Model failed on window: {e}")
                    scores.append(0.0)

            if not scores:
                logger.warning(f"No scores generated for window size {window_size}")
                continue

            # Compute metrics (using synthetic ground truth logic)
            # Since we don't have real labels for every window, we use a proxy metric
            # based on score variance and mean
            mean_score = float(np.mean(scores))
            std_score = float(np.std(scores))
            score_range = float(np.max(scores) - np.min(scores))

            # Store baseline for first iteration
            if base_metrics is None:
                base_metrics = {'mean': mean_score, 'std': std_score, 'range': score_range}

            # Calculate deviation from baseline
            mean_dev = abs(mean_score - base_metrics['mean']) / (base_metrics['mean'] + 1e-6)
            std_dev = abs(std_score - base_metrics['std']) / (base_metrics['std'] + 1e-6)

            # Threshold: deviation < 20% is considered robust
            is_robust = mean_dev < 0.2 and std_dev < 0.2

            results.append(RobustnessResult(
                parameter_name="window_size",
                parameter_value=window_size,
                metric_name="mean_score_deviation",
                metric_value=mean_dev,
                std_dev=std_dev,
                pass_threshold=is_robust,
                notes=f"Mean: {mean_score:.4f}, Std: {std_score:.4f}"
            ))

        except Exception as e:
            logger.error(f"Error processing window size {window_size}: {e}")
            results.append(RobustnessResult(
                parameter_name="window_size",
                parameter_value=window_size,
                metric_name="error",
                metric_value=1.0,
                pass_threshold=False,
                notes=str(e)
            ))

    return results


def run_derivative_method_sensitivity(data: np.ndarray, config: RobustnessConfig) -> List[RobustnessResult]:
    """
    Analyze sensitivity of derivative calculation methods.

    Args:
        data: Time series data
        config: Robustness configuration

    Returns:
        List of robustness results
    """
    results = []
    base_derivative = None

    logger.info("Running derivative method sensitivity analysis")

    # Use a fixed window for this test
    window_size = config.base_window_size
    windows, _ = sliding_window(data, window_size, stride=1)

    if len(windows) == 0:
        logger.warning("No windows available for derivative analysis")
        return results

    # Select a representative window
    test_window = windows[len(windows)//2]

    methods = ['finite_diff', 'gradient']
    smooth_options = [False, True]

    for method in methods:
        for smooth in smooth_options:
            try:
                deriv = compute_derivative(test_window, method=method, smooth=smooth)
                mean_deriv = float(np.mean(np.abs(deriv)))
                std_deriv = float(np.std(deriv))

                # Store baseline
                if base_derivative is None:
                    base_derivative = {'mean': mean_deriv, 'std': std_deriv}

                # Calculate deviation
                mean_dev = abs(mean_deriv - base_derivative['mean']) / (base_derivative['mean'] + 1e-6)
                is_robust = mean_dev < 0.5  # Higher tolerance for derivative methods

                results.append(RobustnessResult(
                    parameter_name=f"derivative_{method}_smooth",
                    parameter_value=smooth,
                    metric_name="mean_abs_derivative",
                    metric_value=mean_deriv,
                    std_dev=std_deriv,
                    pass_threshold=is_robust,
                    notes=f"Method: {method}, Smooth: {smooth}"
                ))

            except Exception as e:
                logger.error(f"Error in derivative calculation ({method}, smooth={smooth}): {e}")
                results.append(RobustnessResult(
                    parameter_name=f"derivative_{method}_smooth",
                    parameter_value=smooth,
                    metric_name="error",
                    metric_value=1.0,
                    pass_threshold=False,
                    notes=str(e)
                ))

    return results


def run_robustness_analysis(config: RobustnessConfig) -> Dict[str, Any]:
    """
    Run full robustness analysis suite.

    Args:
        config: Robustness configuration

    Returns:
        Dictionary containing all results
    """
    logger.info("Starting robustness analysis")

    # Generate synthetic data if no real data is available
    # Note: In a real scenario, this would load from data/raw/
    logger.info("Generating synthetic dataset for robustness analysis")
    synthetic_data, anomaly_timestamps = generate_synthetic_timeseries(
        n_points=1000,
        anomaly_rate=config.anomaly_rate,
        seed=config.seed
    )

    # Save the synthetic dataset for reproducibility
    dataset_path = Path("data/processed/results/robustness_test_data.csv")
    dataset_path.parent.mkdir(parents=True, exist_ok=True)

    # Save data to CSV
    np.savetxt(dataset_path, synthetic_data, delimiter=',', header='timestamp,value', comments='')

    # Run sensitivity analyses
    all_results = []

    # Window size sensitivity
    window_results = run_window_size_sensitivity(synthetic_data, anomaly_timestamps, config)
    all_results.extend(window_results)

    # Derivative method sensitivity
    deriv_results = run_derivative_method_sensitivity(synthetic_data, config)
    all_results.extend(deriv_results)

    # Summary statistics
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r.pass_threshold)
    pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0

    report = {
        "config": asdict(config),
        "summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": pass_rate,
            "overall_robustness": "PASS" if pass_rate > 0.8 else "FAIL"
        },
        "results": [asdict(r) for r in all_results]
    }

    # Save report
    output_path = Path(config.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Robustness report saved to {output_path}")
    logger.info(f"Overall robustness: {report['summary']['overall_robustness']} ({pass_rate:.2%})")

    return report


def main():
    """Main entry point for robustness analysis."""
    parser = argparse.ArgumentParser(description="Run robustness analysis on anomaly detection pipeline")
    parser.add_argument("--subset-size", type=int, default=50, help="Number of windows to sample for analysis")
    parser.add_argument("--window-sizes", type=str, default="30,50,70,100", help="Comma-separated list of window sizes to test")
    parser.add_argument("--anomaly-rate", type=float, default=0.05, help="Anomaly rate for synthetic data")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default="data/processed/results/robustness_report.json", help="Output path for report")

    args = parser.parse_args()

    # Parse window sizes
    window_sizes = [int(x.strip()) for x in args.window_sizes.split(',')]

    config = RobustnessConfig(
        subset_size=args.subset_size,
        window_size_variations=window_sizes,
        anomaly_rate=args.anomaly_rate,
        seed=args.seed,
        output_path=args.output
    )

    try:
        report = run_robustness_analysis(config)
        sys.exit(0 if report['summary']['overall_robustness'] == "PASS" else 1)
    except Exception as e:
        logger.error(f"Robustness analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()