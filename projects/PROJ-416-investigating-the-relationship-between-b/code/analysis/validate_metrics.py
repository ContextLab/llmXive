import csv
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from code.config import Config
from code.utils.logging import setup_logging, log_provenance

logger = logging.getLogger(__name__)

def load_metrics_from_csv(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load metrics from a CSV file.

    Args:
        csv_path (str): Path to the CSV file.

    Returns:
        List[Dict[str, Any]]: List of metric dictionaries.
    """
    metrics = []
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                metrics.append(row)
        logger.info(f"Loaded {len(metrics)} metrics from {csv_path}")
    except FileNotFoundError:
        logger.error(f"Metrics file not found: {csv_path}")
    except Exception as e:
        logger.error(f"Error loading metrics: {e}")
    return metrics

def validate_metric_value(value: float, min_val: float, max_val: float) -> bool:
    """
    Validate a metric value is within bounds.

    Args:
        value (float): The metric value.
        min_val (float): Minimum allowed value.
        max_val (float): Maximum allowed value.

    Returns:
        bool: True if valid, False otherwise.
    """
    if value is None or value != value: # Check for NaN
        return False
    return min_val <= value <= max_val

def validate_metrics(metrics: List[Dict[str, Any]]) -> bool:
    """
    Validate all metrics in a list.

    Args:
        metrics (List[Dict[str, Any]]): List of metrics.

    Returns:
        bool: True if all metrics are valid, False otherwise.
    """
    valid = True
    for i, metric in enumerate(metrics):
        # Example validation for Modularity (Q >= 0)
        if 'modularity' in metric:
            try:
                val = float(metric['modularity'])
                if not validate_metric_value(val, 0.0, 1.0):
                    logger.warning(f"Invalid modularity value {val} for subject {metric.get('subject_id', i)}")
                    valid = False
            except (ValueError, TypeError):
                logger.warning(f"Non-numeric modularity value for subject {metric.get('subject_id', i)}")
                valid = False

        # Example validation for Efficiency (>= 0)
        for key in ['global_efficiency', 'local_efficiency']:
            if key in metric:
                try:
                    val = float(metric[key])
                    if not validate_metric_value(val, 0.0, float('inf')):
                        logger.warning(f"Invalid {key} value {val} for subject {metric.get('subject_id', i)}")
                        valid = False
                except (ValueError, TypeError):
                    logger.warning(f"Non-numeric {key} value for subject {metric.get('subject_id', i)}")
                    valid = False
    
    return valid

def run_validation(config: Config):
    """
    Run the metrics validation pipeline.

    Args:
        config (Config): Configuration object.
    """
    logger.info("Starting metrics validation pipeline.")
    
    metrics_path = os.path.join(config.METRICS_DIR, 'network_metrics.csv')
    if not os.path.exists(metrics_path):
        logger.error(f"Metrics file not found: {metrics_path}")
        sys.exit(1)

    metrics = load_metrics_from_csv(metrics_path)
    if not metrics:
        logger.error("No metrics found to validate.")
        sys.exit(1)

    is_valid = validate_metrics(metrics)
    
    if not is_valid:
        logger.critical("Validation failed: Invalid metric values detected.")
        sys.exit(1)
    
    logger.info("Validation passed.")
    log_provenance("validate_metrics", metrics_path, config)

def main():
    """Main entry point for the validate_metrics module."""
    config = Config()
    log_path = config.LOGS_DIR / "validate_metrics.log"
    setup_logging("validate_metrics", log_path=str(log_path))
    run_validation(config)

if __name__ == "__main__":
    main()