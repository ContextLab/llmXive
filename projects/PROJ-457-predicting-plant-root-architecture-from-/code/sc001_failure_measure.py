"""
Measure Original SC-001 Failure.

Calculates the original SC-001 metric (proportion of datasets merged with ISRIC)
which is deferred due to exclusion (FR-002).

Writes result to artifacts/reports/metrics.json.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any
from config import get_config, setup_logging

def measure_original_sc001_failure() -> Dict[str, Any]:
    """
    Measure the original SC-001 failure rate.
    
    Since ISRIC source is unavailable and FR-002 excludes this merge,
    the original merge rate is 0.0.
    
    Returns:
        Dict containing the metric and reason.
    """
    return {
        "sc001_original_merge_rate": 0.0,
        "reason": "ISRIC source unavailable; FR-002 excluded"
    }

def write_metrics_report(metrics: Dict[str, Any], config: Dict[str, Any]) -> None:
    """
    Write the metrics report to artifacts/reports/metrics.json.
    
    If the file already exists, this function updates it with the new metrics
    rather than overwriting the entire file, preserving other metrics.
    
    Args:
        metrics: Dictionary of metrics to write.
        config: Configuration dictionary with paths.
    """
    output_path = Path(config["paths"]["artifacts"]) / "reports" / "metrics.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing metrics if file exists
    existing_metrics = {}
    if output_path.exists():
        try:
            with open(output_path, "r") as f:
                existing_metrics = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Could not read existing metrics.json: {e}. Starting fresh.")
    
    # Update with new metrics
    existing_metrics.update(metrics)
    
    # Write back
    with open(output_path, "w") as f:
        json.dump(existing_metrics, f, indent=2)
    
    logging.info(f"Metrics report written to {output_path}")

def main():
    """Main entry point for SC-001 failure measurement."""
    config = get_config()
    logger = setup_logging()
    
    logger.info("Starting SC-001 failure measurement...")
    
    # Measure the failure
    metrics = measure_original_sc001_failure()
    
    # Write the report
    write_metrics_report(metrics, config)
    
    logger.info("SC-001 failure measurement completed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
