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

from logging_config import setup_logger, get_logger
from data_model import validate_metric_result, MetricResult

def setup_validation_logger():
    return setup_logger("metric_validation", log_file="results/metric_validation.log")

def load_metrics_data(metrics_dir: Path = None) -> Dict[str, pd.DataFrame]:
    """Load all metric CSV files."""
    if metrics_dir is None:
        metrics_dir = Path("data/metrics")
        
    if not metrics_dir.exists():
        return {}
        
    data = {}
    for file in metrics_dir.glob("*.csv"):
        try:
            df = pd.read_csv(file)
            data[file.stem] = df
        except Exception as e:
            logging.warning(f"Failed to load {file}: {e}")
    return data

def validate_single_metric(df: pd.DataFrame, metric_name: str) -> Dict[str, Any]:
    """Validate a single metric dataframe."""
    issues = []
    total_rows = len(df)
    
    if total_rows == 0:
        return {"valid": False, "issues": ["Empty dataframe"], "failed_count": 0}
        
    # Check for NaNs
    nan_counts = df.isna().sum()
    nan_total = nan_counts.sum()
    if nan_total > 0:
        issues.append(f"Found {nan_total} NaN values")
        
    # Check for out-of-range values (example: complexity > 1000)
    for col in df.columns:
        if col in ["max_cc", "avg_cc", "loc", "lloc", "error_count", "warning_count"]:
            if col in df.columns:
                max_val = df[col].max()
                if max_val > 10000: # Arbitrary high threshold
                    issues.append(f"Column {col} has suspiciously high max value: {max_val}")
                    
    # Check schema compliance if MetricResult is applicable
    # We check if required columns exist
    required_cols = ["snippet_id", "source"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        issues.append(f"Missing required columns: {missing}")
        
    failed_count = len(issues)
    valid = len(issues) == 0
    
    return {
        "valid": valid,
        "issues": issues,
        "failed_count": failed_count,
        "total_rows": total_rows,
        "nan_count": nan_total
    }

def generate_diagnostic_report(validation_results: Dict[str, Dict[str, Any]], output_path: Path):
    """Generate a diagnostic report for validation failures."""
    with open(output_path, 'w') as f:
        f.write("# Metric Validation Diagnostic Report\n\n")
        for metric, result in validation_results.items():
            f.write(f"## Metric: {metric}\n")
            f.write(f"- Valid: {result['valid']}\n")
            f.write(f"- Total Rows: {result.get('total_rows', 0)}\n")
            f.write(f"- Issues: {result.get('issues', [])}\n\n")
    logging.info(f"Diagnostic report written to {output_path}")

def run_metric_validation(metrics_dir: Path = None):
    """Main validation workflow."""
    logger = setup_validation_logger()
    logger.info("Starting Metric Validation...")
    
    metrics_data = load_metrics_data(metrics_dir)
    if not metrics_data:
        logger.error("No metric data found to validate.")
        sys.exit(1)
        
    all_results = {}
    total_failures = 0
    
    for metric_name, df in metrics_data.items():
        result = validate_single_metric(df, metric_name)
        all_results[metric_name] = result
        if not result['valid']:
            total_failures += 1
            logger.warning(f"Validation failed for {metric_name}: {result['issues']}")
        else:
            logger.info(f"Validation passed for {metric_name}")
            
    failure_rate = total_failures / len(metrics_data) if metrics_data else 0
    
    if failure_rate >= 0.05:
        logger.error(f"Validation failure rate {failure_rate:.2%} >= 5%. Aborting.")
        # Generate diagnostic report
        report_path = Path("results/metric_validation_report.md")
        generate_diagnostic_report(all_results, report_path)
        sys.exit(102) # Error code 102 as per spec
        
    logger.info("Metric validation passed.")
    return all_results

def main():
    """Entry point."""
    run_metric_validation()

if __name__ == "__main__":
    main()
