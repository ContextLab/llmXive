import os
import sys
import json
import logging
import argparse
import math
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_model_metrics(metrics_path: str) -> dict:
    """Load model metrics from JSON file."""
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

    with open(metrics_path, 'r') as f:
        return json.load(f)

def calculate_variance_from_metrics(metrics: dict) -> float:
    """Calculate variance from multiple model runs if available."""
    # If we have multiple runs, calculate variance
    if 'runs' in metrics and len(metrics['runs']) > 1:
        r2_values = [run['r2'] for run in metrics['runs']]
        mean_r2 = sum(r2_values) / len(r2_values)
        variance = sum((x - mean_r2) ** 2 for x in r2_values) / len(r2_values)
        return variance
    # Otherwise estimate from single run metrics
    # Use a conservative estimate based on R2
    r2 = metrics.get('r2', 0.5)
    # Variance of prediction error is related to (1 - R2)
    return 1.0 - r2

def calculate_mde(variance: float, sample_size: int, alpha: float = 0.05, power: float = 0.8) -> float:
    """
    Calculate Minimum Detectable Effect (MDE).

    MDE = Z_alpha/2 + Z_beta * sqrt(2 * variance / n)

    Where:
    - Z_alpha/2 is the critical value for significance level alpha
    - Z_beta is the critical value for power (1 - beta)
    - variance is the variance of the estimator
    - n is the sample size
    """
    # Critical values for standard normal distribution
    z_alpha = 1.96  # For alpha = 0.05 (two-tailed)
    z_beta = 0.84   # For power = 0.8

    # Standard error
    se = math.sqrt(2 * variance / sample_size)

    # MDE
    mde = (z_alpha + z_beta) * se
    return mde

def calculate_required_sample_size(mde: float, variance: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """
    Calculate required sample size for a given MDE.

    n = 2 * (Z_alpha/2 + Z_beta)^2 * variance / MDE^2
    """
    z_alpha = 1.96  # For alpha = 0.05
    z_beta = 0.84   # For power = 0.8

    numerator = 2 * ((z_alpha + z_beta) ** 2) * variance
    denominator = mde ** 2

    if denominator == 0:
        raise ValueError("MDE cannot be zero")

    return math.ceil(numerator / denominator)

def run_power_analysis(metrics_path: str, output_path: str, target_mde: float = 0.1) -> dict:
    """
    Run power analysis based on model metrics.

    Args:
        metrics_path: Path to model metrics JSON
        output_path: Path to save power analysis report
        target_mde: Target minimum detectable effect size

    Returns:
        Dictionary with power analysis results
    """
    logger.info(f"Loading metrics from: {metrics_path}")
    metrics = load_model_metrics(metrics_path)

    logger.info("Calculating variance from metrics...")
    variance = calculate_variance_from_metrics(metrics)
    logger.info(f"Estimated variance: {variance:.4f}")

    # Get current sample size from metrics if available
    current_sample_size = metrics.get('sample_size', 1000)

    logger.info(f"Current sample size: {current_sample_size}")

    # Calculate MDE for current sample size
    mde_current = calculate_mde(variance, current_sample_size)
    logger.info(f"Current MDE: {mde_current:.4f}")

    # Calculate required sample size for target MDE
    required_size = calculate_required_sample_size(target_mde, variance)
    logger.info(f"Required sample size for MDE={target_mde}: {required_size}")

    # Power analysis report
    report = {
        'variance': variance,
        'current_sample_size': current_sample_size,
        'current_mde': mde_current,
        'target_mde': target_mde,
        'required_sample_size': required_size,
        'power_analysis': {
            'alpha': 0.05,
            'power': 0.8,
            'z_alpha': 1.96,
            'z_beta': 0.84
        }
    }

    # Determine if current sample is sufficient
    if current_sample_size >= required_size:
        report['sufficient'] = True
        report['message'] = f"Current sample size ({current_sample_size}) is sufficient for MDE={target_mde}"
    else:
        report['sufficient'] = False
        report['message'] = f"Current sample size ({current_sample_size}) is insufficient. Need {required_size} for MDE={target_mde}"

    # Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Power analysis report saved to: {output_path}")
    return report

def main():
    parser = argparse.ArgumentParser(description='Run power analysis on model metrics')
    parser.add_argument('--metrics', type=str, required=True, help='Path to model metrics JSON')
    parser.add_argument('--output', type=str, required=True, help='Path to output report')
    parser.add_argument('--target-mde', type=float, default=0.1, help='Target MDE')

    args = parser.parse_args()

    try:
        report = run_power_analysis(args.metrics, args.output, args.target_mde)
        print(json.dumps(report, indent=2))
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
