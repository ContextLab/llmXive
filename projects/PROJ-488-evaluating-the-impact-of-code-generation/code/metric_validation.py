"""
Metric Validation Module.
Validates extracted metrics for NaNs, out-of-range values, and schema compliance.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

from data_model import MetricResult, validate_metric_result
from logging_config import setup_logger, get_logger
from data_model import validate_metric_result, MetricResult

logger = get_logger("metric_validation")

def setup_validation_logger(log_file: Optional[str] = None):
    """Setup the validation logger."""
    return setup_logger("metric_validation", log_file)

def load_metrics_data(metrics_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all metric CSV files from the metrics directory.
    Returns a list of dictionaries representing the rows.
    """
    all_data = []
    if not metrics_dir.exists():
        logger.error(f"Metrics directory not found: {metrics_dir}")
        return all_data

    for csv_file in metrics_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            rows = df.to_dict(orient='records')
            all_data.extend(rows)
            logger.info(f"Loaded {len(rows)} rows from {csv_file.name}")
        except Exception as e:
            logger.error(f"Error reading {csv_file.name}: {e}")
    return all_data

def validate_single_metric(row: Dict[str, Any]) -> bool:
    """
    Validates a single metric row against the MetricResult schema.
    """
    try:
        # Convert dict to MetricResult
        # Ensure timestamp has a default if missing
        if 'timestamp' not in row:
            row['timestamp'] = "2024-01-01T00:00:00"
        
        result = MetricResult(**row)
        if validate_metric_result(result):
            return True
        else:
            logger.warning(f"Row failed validation: {row.get('metric_type', 'N/A')} - {row.get('group_label', 'N/A')}")
            return False
    except TypeError as e:
        logger.error(f"Row failed schema conversion: {e} - {row}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating row: {e}")
        return False

def generate_diagnostic_report(failed_rows: List[Dict[str, Any]], output_path: Path):
    """
    Generates a diagnostic report for failed metric validations.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("# Metric Validation Diagnostic Report\n\n")
        f.write(f"Total failed rows: {len(failed_rows)}\n\n")
        if failed_rows:
            f.write("Failed Rows Details:\n")
            for i, row in enumerate(failed_rows):
                f.write(f"### Row {i+1}\n")
                for k, v in row.items():
                    f.write(f"- {k}: {v}\n")
                f.write("\n")
    logger.info(f"Diagnostic report written to {output_path}")

def run_metric_validation(metrics_dir: Path, output_dir: Path):
    """
    Main workflow to validate all metric outputs against the MetricResult schema.
    """
    logger.info(f"Starting metric validation for directory: {metrics_dir}")
    
    data = load_metrics_data(metrics_dir)
    if not data:
        logger.warning("No metric data found to validate.")
        return True

    failed_rows = []
    for row in data:
        if not validate_single_metric(row):
            failed_rows.append(row)

    if failed_rows:
        logger.error(f"Validation failed for {len(failed_rows)} rows.")
        report_path = output_dir / "validation_errors.json"
        generate_diagnostic_report(failed_rows, report_path)
        # Also save as CSV for easier inspection
        report_csv = output_dir / "validation_errors.csv"
        pd.DataFrame(failed_rows).to_csv(report_csv, index=False)
        logger.error(f"Error report saved to {report_csv}")
        return False
    else:
        logger.info("All metric rows passed validation.")
        return True

def main():
    """Entry point for CLI execution."""
    logger.info("Running metric validation pipeline...")
    metrics_dir = Path("data/metrics")
    output_dir = Path("data/metrics") # Output reports to same dir or a subfolder
    
    success = run_metric_validation(metrics_dir, output_dir)
    if not success:
        logger.error("Metric validation failed. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("Metric validation completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
