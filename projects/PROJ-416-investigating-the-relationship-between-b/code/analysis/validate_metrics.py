"""
Metric Validation Module for Brain Network Dynamics.

This module enforces mathematical bounds on network metrics (Modularity Q,
Global Efficiency, Local Efficiency) derived from functional connectivity
matrices. It halts execution if systematic failures (invalid values) are detected,
ensuring data integrity before statistical analysis.

Boundaries enforced:
- Modularity Q >= 0
- Global Efficiency >= 0
- Local Efficiency >= 0
- No NaN or Infinity values allowed.
"""
import csv
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from code.config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Constants for bounds
MIN_MODULARITY = 0.0
MIN_EFFICIENCY = 0.0

def load_metrics_from_csv(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load network metrics from a CSV file.

    Args:
        filepath: Path to the CSV file containing network metrics.

    Returns:
        List of dictionaries, each representing a subject's metrics.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the CSV is empty or missing required columns.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Metrics file not found: {filepath}")

    metrics_list = []
    required_columns = {'subject_id', 'modularity_q', 'global_efficiency', 'local_efficiency'}

    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or has no header.")
            
            # Check for required columns
            missing_cols = required_columns - set(reader.fieldnames)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            for row in reader:
                metrics_list.append(row)
    except csv.Error as e:
        logger.error(f"Error reading CSV {filepath}: {e}")
        raise

    if not metrics_list:
        raise ValueError(f"No data rows found in {filepath}")

    return metrics_list

def validate_metric_value(value_str: str, metric_name: str, min_val: float) -> Optional[float]:
    """
    Validate a single metric value against bounds.

    Args:
        value_str: String representation of the value.
        metric_name: Name of the metric for error reporting.
        min_val: Minimum allowed value.

    Returns:
        The float value if valid.

    Raises:
        ValueError: If the value is NaN, Infinity, or below the minimum bound.
    """
    try:
        val = float(value_str)
    except ValueError:
        raise ValueError(f"Invalid number format for {metric_name}: '{value_str}'")

    import math

    if math.isnan(val):
        raise ValueError(f"{metric_name} is NaN for this subject.")
    
    if math.isinf(val):
        raise ValueError(f"{metric_name} is Infinity for this subject.")

    if val < min_val:
        raise ValueError(f"{metric_name} is {val}, which is below the minimum bound of {min_val}.")

    return val

def validate_metrics(metrics_list: List[Dict[str, Any]]) -> bool:
    """
    Validate all metrics in the list against mathematical bounds.

    Args:
        metrics_list: List of metric dictionaries.

    Returns:
        True if all metrics are valid.

    Raises:
        SystemExit: If any metric fails validation (halt on systematic failure).
    """
    logger.info(f"Validating {len(metrics_list)} subjects' network metrics...")
    failures = []

    for row in metrics_list:
        subject_id = row.get('subject_id', 'Unknown')
        try:
            # Validate Modularity Q
            validate_metric_value(row['modularity_q'], 'Modularity Q', MIN_MODULARITY)
            
            # Validate Global Efficiency
            validate_metric_value(row['global_efficiency'], 'Global Efficiency', MIN_EFFICIENCY)
            
            # Validate Local Efficiency
            validate_metric_value(row['local_efficiency'], 'Local Efficiency', MIN_EFFICIENCY)

        except ValueError as e:
            failures.append(f"Subject {subject_id}: {e}")

    if failures:
        error_msg = "Systematic validation failures detected:\n" + "\n".join(failures)
        logger.error(error_msg)
        logger.critical("Halting pipeline due to invalid network metrics.")
        raise SystemExit(1)

    logger.info("All network metrics passed validation.")
    return True

def run_validation(config: Optional[Config] = None) -> None:
    """
    Entry point for running metric validation.

    Args:
        config: Configuration object. If None, attempts to load default config.
    """
    if config is None:
        config = Config()

    metrics_path = config.METRICS_PATH / "network_metrics.csv"
    
    if not metrics_path.exists():
        logger.warning(f"Metrics file not found at {metrics_path}. Skipping validation.")
        return

    try:
        metrics = load_metrics_from_csv(metrics_path)
        validate_metrics(metrics)
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        raise SystemExit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise SystemExit(1)
    except SystemExit:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        raise SystemExit(1)

def main() -> None:
    """Main entry point for CLI execution."""
    from code.utils.logging import setup_logging
    import argparse

    parser = argparse.ArgumentParser(description="Validate network metrics bounds.")
    parser.add_argument("--config", type=str, default=None, help="Path to config file (optional)")
    args = parser.parse_args()

    setup_logging(log_level=logging.INFO)
    
    config = Config()
    run_validation(config)

if __name__ == "__main__":
    main()
