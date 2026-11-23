"""
Bootstrap Aggregator for Power Analysis.

Consumes lists of replication results per configuration and computes
empirical rates and confidence intervals.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def aggregate_power_results(
    results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate power analysis results from multiple bootstrap iterations.

    Args:
        results: List of result dictionaries from bootstrap iterations

    Returns:
        Aggregated statistics
    """
    if not results:
        return {
            'total_iterations': 0,
            'successful_replications': 0,
            'empirical_power': 0.0,
            'confidence_interval': (0.0, 0.0),
            'convergence_rate': 0.0
        }

    total_iterations = len(results)
    successful_replications = sum(1 for r in results if r.get('replication_success', False))
    converged_iterations = sum(1 for r in results if r.get('converged', True))

    # Calculate empirical power (only from converged iterations)
    if converged_iterations > 0:
        empirical_power = successful_replications / converged_iterations
        convergence_rate = converged_iterations / total_iterations
    else:
        empirical_power = 0.0
        convergence_rate = 0.0

    # Calculate confidence interval (Wilson score interval)
    if converged_iterations > 0:
        z = 1.96  # 95% CI
        p = successful_replications / converged_iterations
        n = converged_iterations

        # Wilson score interval
        denominator = 1 + z**2 / n
        center = (p + z**2 / (2 * n)) / denominator
        margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator

        ci_lower = max(0, center - margin)
        ci_upper = min(1, center + margin)
        confidence_interval = (ci_lower, ci_upper)
    else:
        confidence_interval = (0.0, 0.0)

    return {
        'total_iterations': total_iterations,
        'successful_replications': successful_replications,
        'converged_iterations': converged_iterations,
        'empirical_power': empirical_power,
        'confidence_interval': confidence_interval,
        'convergence_rate': convergence_rate,
        'timestamp': datetime.now().isoformat()
    }

def compute_confidence_intervals(
    results: List[Dict[str, Any]],
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Compute confidence intervals for power estimates.

    Args:
        results: List of result dictionaries
        confidence_level: Confidence level (default 0.95)

    Returns:
        Tuple of (lower, upper) confidence bounds
    """
    if not results:
        return (0.0, 0.0)

    # Filter for converged iterations
    converged_results = [r for r in results if r.get('converged', True)]

    if not converged_results:
        return (0.0, 0.0)

    successful = sum(1 for r in converged_results if r.get('replication_success', False))
    n = len(converged_results)
    p = successful / n

    # Calculate z-score for confidence level
    from scipy.stats import norm
    z = norm.ppf((1 + confidence_level) / 2)

    # Wilson score interval
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator

    return (max(0, center - margin), min(1, center + margin))

def save_aggregated_results(
    aggregated_data: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save aggregated results to a JSON file.

    Args:
        aggregated_data: Dictionary of aggregated results
        output_path: Path to save the file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(aggregated_data, f, indent=2)
    logger.info(f"Aggregated results saved to {output_path}")

def main():
    """Main entry point for the bootstrap aggregator."""
    parser = argparse.ArgumentParser(description='Aggregate bootstrap power analysis results')
    parser.add_argument('--input', type=str, required=True, help='Input JSON file with results')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file for aggregated results')

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file does not exist: {input_path}")
        sys.exit(1)

    try:
        with open(input_path, 'r') as f:
            data = json.load(f)

        # Aggregate results
        aggregated = aggregate_power_results(data.get('results', []))

        # Save
        save_aggregated_results(aggregated, output_path)

        logger.info("Aggregation completed successfully")

    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
