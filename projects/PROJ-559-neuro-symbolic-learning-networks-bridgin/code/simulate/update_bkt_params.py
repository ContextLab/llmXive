"""
Update BKT parameters based on calibration metrics.

This script reads calibration metrics from T032 and updates the BKT parameters
in bkt_params.yaml to improve model fit. It implements a simple gradient-like
adjustment based on the RMSE difference between simulated and observed performance.

Deliverable: Updated code/simulate/bkt_params.yaml
Dependency: T032 (calibration_metrics.json)
"""

import os
import sys
import json
import logging
import argparse
import yaml
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METRICS_PATH = os.path.join(PROJECT_ROOT, 'data', 'pilot', 'calibration_metrics.json')
PARAMS_PATH = os.path.join(PROJECT_ROOT, 'code', 'simulate', 'bkt_params.yaml')
REPORT_PATH = os.path.join(PROJECT_ROOT, 'data', 'pilot', 'param_update_report.json')


def load_metrics(metrics_path: str) -> Dict[str, Any]:
    """Load calibration metrics from JSON file."""
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

    with open(metrics_path, 'r') as f:
        metrics = json.load(f)

    logger.info(f"Loaded metrics from {metrics_path}")
    return metrics


def load_params(params_path: str) -> Dict[str, float]:
    """Load current BKT parameters from YAML file."""
    if not os.path.exists(params_path):
        raise FileNotFoundError(f"Parameters file not found: {params_path}")

    with open(params_path, 'r') as f:
        params = yaml.safe_load(f)

    logger.info(f"Loaded parameters from {params_path}")
    return params


def calculate_adjustment(
    rmse_diff: float,
    current_params: Dict[str, float],
    learning_rate: float = 0.05
) -> Dict[str, float]:
    """
    Calculate parameter adjustments based on RMSE difference.

    The adjustment logic:
    - If RMSE_diff > 0 (model underestimates performance):
      * Increase P_L0 (initial knowledge)
      * Decrease P_S (slipping probability)
    - If RMSE_diff < 0 (model overestimates performance):
      * Decrease P_L0
      * Increase P_S

    Parameters are clamped to valid probability ranges [0, 1].
    """
    adjusted_params = current_params.copy()

    # Adjust learning rate based on magnitude of error
    effective_lr = learning_rate * min(abs(rmse_diff) * 10, 1.0)

    if rmse_diff > 0:
        # Model underestimates - increase knowledge, decrease slipping
        adjusted_params['P_L0'] = min(1.0, current_params['P_L0'] + effective_lr)
        adjusted_params['P_S'] = max(0.0, current_params['P_S'] - effective_lr * 0.5)
    elif rmse_diff < 0:
        # Model overestimates - decrease knowledge, increase slipping
        adjusted_params['P_L0'] = max(0.0, current_params['P_L0'] - effective_lr)
        adjusted_params['P_S'] = min(1.0, current_params['P_S'] + effective_lr * 0.5)

    # P_G and P_T remain unchanged in this simple adjustment
    # They could be adjusted similarly if needed

    logger.info(f"Calculated adjustments with learning rate {effective_lr:.4f}")
    return adjusted_params


def validate_params(params: Dict[str, float]) -> bool:
    """Validate that all parameters are valid probabilities."""
    required_keys = ['P_G', 'P_L0', 'P_S', 'P_T']
    for key in required_keys:
        if key not in params:
            logger.error(f"Missing required parameter: {key}")
            return False
        if not (0.0 <= params[key] <= 1.0):
            logger.error(f"Parameter {key}={params[key]} out of range [0, 1]")
            return False
    return True


def save_params(params: Dict[str, float], params_path: str) -> None:
    """Save updated parameters to YAML file."""
    with open(params_path, 'w') as f:
        yaml.dump(params, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Saved updated parameters to {params_path}")


def save_report(
    original_params: Dict[str, float],
    updated_params: Dict[str, float],
    metrics: Dict[str, Any],
    report_path: str
) -> None:
    """Save a report of the parameter update."""
    report = {
        'original_params': original_params,
        'updated_params': updated_params,
        'metrics': metrics,
        'changes': {
            key: f"{updated_params[key]:.4f} (was {original_params[key]:.4f})"
            for key in original_params
            if abs(updated_params[key] - original_params[key]) > 1e-6
        }
    }

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved update report to {report_path}")


def run_update(
    metrics_path: Optional[str] = None,
    params_path: Optional[str] = None,
    report_path: Optional[str] = None,
    learning_rate: float = 0.05
) -> Dict[str, Any]:
    """
    Main function to update BKT parameters based on calibration metrics.

    Args:
        metrics_path: Path to calibration_metrics.json
        params_path: Path to bkt_params.yaml
        report_path: Path for the update report
        learning_rate: Step size for parameter adjustment

    Returns:
        Dictionary with update status and details
    """
    # Use defaults if not provided
    metrics_path = metrics_path or METRICS_PATH
    params_path = params_path or PARAMS_PATH
    report_path = report_path or REPORT_PATH

    try:
        # Load metrics
        metrics = load_metrics(metrics_path)
        rmse_diff = metrics.get('rmse_difference', 0.0)
        logger.info(f"RMSE difference: {rmse_diff:.4f}")

        # Load current parameters
        current_params = load_params(params_path)
        original_params = current_params.copy()

        # Calculate adjusted parameters
        adjusted_params = calculate_adjustment(
            rmse_diff,
            current_params,
            learning_rate=learning_rate
        )

        # Validate adjusted parameters
        if not validate_params(adjusted_params):
            raise ValueError("Adjusted parameters are invalid")

        # Save updated parameters
        save_params(adjusted_params, params_path)

        # Save report
        save_report(original_params, adjusted_params, metrics, report_path)

        return {
            'status': 'success',
            'original_params': original_params,
            'updated_params': adjusted_params,
            'rmse_difference': rmse_diff,
            'report_path': report_path
        }

    except Exception as e:
        logger.error(f"Parameter update failed: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }


def main() -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description='Update BKT parameters based on calibration metrics'
    )
    parser.add_argument(
        '--metrics',
        type=str,
        default=METRICS_PATH,
        help='Path to calibration metrics JSON'
    )
    parser.add_argument(
        '--params',
        type=str,
        default=PARAMS_PATH,
        help='Path to BKT parameters YAML'
    )
    parser.add_argument(
        '--report',
        type=str,
        default=REPORT_PATH,
        help='Path for update report JSON'
    )
    parser.add_argument(
        '--learning-rate',
        type=float,
        default=0.05,
        help='Learning rate for parameter adjustment'
    )

    args = parser.parse_args()

    result = run_update(
        metrics_path=args.metrics,
        params_path=args.params,
        report_path=args.report,
        learning_rate=args.learning_rate
    )

    if result['status'] == 'success':
        logger.info("Parameter update completed successfully")
        logger.info(f"Updated parameters: {result['updated_params']}")
        return 0
    else:
        logger.error(f"Parameter update failed: {result['error']}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
