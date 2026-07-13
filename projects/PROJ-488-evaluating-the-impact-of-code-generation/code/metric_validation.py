import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import existing logging utilities
from logging_config import setup_logger, get_logger

# Constants
VALIDATION_THRESHOLD = 0.05  # 5% failure rate threshold
ERROR_CODE_102 = 102
DIAGNOSTIC_REPORT_FILENAME = "metric_validation_report.json"
METRICS_DIR = "data/metrics"

def setup_validation_logger(name: str = "metric_validation") -> logging.Logger:
    """
    Setup a dedicated logger for metric validation tasks.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return setup_logger(name, level=logging.INFO)

def load_metrics_data(metrics_dir: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
    """
    Load all metric CSV files from the metrics directory.
    
    Args:
        metrics_dir: Path to metrics directory (defaults to data/metrics)
        
    Returns:
        Dictionary mapping metric type to DataFrame
    """
    if metrics_dir is None:
        metrics_dir = Path("data/metrics")
    
    if not metrics_dir.exists():
        raise FileNotFoundError(f"Metrics directory not found: {metrics_dir}")
    
    metrics_data = {}
    for csv_file in metrics_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            metric_type = csv_file.stem  # filename without extension
            metrics_data[metric_type] = df
            logging.info(f"Loaded {len(df)} rows from {csv_file}")
        except Exception as e:
            logging.error(f"Failed to load {csv_file}: {e}")
            raise
    
    return metrics_data

def validate_single_metric(df: pd.DataFrame, metric_name: str) -> Tuple[int, int, List[Dict[str, Any]]]:
    """
    Validate a single metric DataFrame for NaN values and out-of-range scores.
    
    Args:
        df: DataFrame containing metric scores
        metric_name: Name of the metric for logging
        
    Returns:
        Tuple of (total_snippets, failed_count, list of failure details)
    """
    total_snippets = len(df)
    failed_count = 0
    failures = []
    
    if total_snippets == 0:
        logging.warning(f"No snippets found in {metric_name}")
        return 0, 0, []
    
    # Identify score columns (typically contain 'score' in the name)
    score_columns = [col for col in df.columns if 'score' in col.lower() or col.lower() in ['score', 'value']]
    
    if not score_columns:
        # If no obvious score column, assume the first numeric column or 'score' if it exists
        score_columns = [col for col in df.columns if df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
        if not score_columns:
            logging.warning(f"No numeric columns found in {metric_name}")
            return total_snippets, 0, []
    
    for col in score_columns:
        # Check for NaN values
        nan_mask = df[col].isna()
        nan_count = nan_mask.sum()
        
        if nan_count > 0:
            failed_count += nan_count
            nan_indices = df.index[nan_mask].tolist()
            failures.append({
                "metric": metric_name,
                "column": col,
                "issue": "nan_value",
                "count": int(nan_count),
                "sample_indices": nan_indices[:10]  # Store first 10 for diagnostics
            })
            logging.warning(f"Found {nan_count} NaN values in {metric_name}.{col}")
        
        # Check for out-of-range values (assuming scores should be non-negative for most metrics)
        # For radon complexity: should be >= 0
        # For pylint: typically counts (>= 0) or ratings (0-10)
        # We'll implement a generic check: values < 0 are invalid for count-based metrics
        negative_mask = df[col] < 0
        negative_count = negative_mask.sum()
        
        if negative_count > 0:
            failed_count += negative_count
            negative_indices = df.index[negative_mask].tolist()
            failures.append({
                "metric": metric_name,
                "column": col,
                "issue": "negative_value",
                "count": int(negative_count),
                "sample_indices": negative_indices[:10],
                "min_value": float(df[col].min())
            })
            logging.warning(f"Found {negative_count} negative values in {metric_name}.{col}")
        
        # Check for infinite values
        inf_mask = df[col].apply(lambda x: x in [float('inf'), float('-inf')]) if df[col].dtype in ['float64', 'float32'] else pd.Series([False] * len(df))
        inf_count = inf_mask.sum()
        
        if inf_count > 0:
            failed_count += inf_count
            inf_indices = df.index[inf_mask].tolist()
            failures.append({
                "metric": metric_name,
                "column": col,
                "issue": "infinite_value",
                "count": int(inf_count),
                "sample_indices": inf_indices[:10]
            })
            logging.warning(f"Found {inf_count} infinite values in {metric_name}.{col}")
    
    return total_snippets, failed_count, failures

def generate_diagnostic_report(
    total_snippets: int,
    total_failed: int,
    all_failures: List[Dict[str, Any]],
    metrics_data: Dict[str, pd.DataFrame],
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a diagnostic report for metric validation failures.
    
    Args:
        total_snippets: Total number of snippets processed
        total_failed: Total number of failed validations
        all_failures: List of all failure details
        metrics_data: Original metrics data for context
        output_path: Path to save the report (defaults to data/metrics/)
        
    Returns:
        Path to the generated report
    """
    if output_path is None:
        output_path = Path("data/metrics")
    output_path.mkdir(parents=True, exist_ok=True)
    
    report_path = output_path / DIAGNOSTIC_REPORT_FILENAME
    
    failure_rate = total_failed / total_snippets if total_snippets > 0 else 0.0
    
    report = {
        "summary": {
            "total_snippets": total_snippets,
            "total_failed": total_failed,
            "failure_rate": failure_rate,
            "threshold": VALIDATION_THRESHOLD,
            "validation_passed": failure_rate < VALIDATION_THRESHOLD,
            "timestamp": pd.Timestamp.now().isoformat()
        },
        "failures_by_metric": {},
        "detailed_failures": all_failures,
        "metrics_summary": {}
    }
    
    # Group failures by metric
    for failure in all_failures:
        metric = failure["metric"]
        if metric not in report["failures_by_metric"]:
            report["failures_by_metric"][metric] = {
                "total_failures": 0,
                "issues": []
            }
        report["failures_by_metric"][metric]["total_failures"] += failure["count"]
        report["failures_by_metric"][metric]["issues"].append({
            "issue_type": failure["issue"],
            "count": failure["count"],
            "column": failure.get("column", "N/A")
        })
    
    # Add metrics summary
    for metric_name, df in metrics_data.items():
        report["metrics_summary"][metric_name] = {
            "total_rows": len(df),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logging.info(f"Diagnostic report written to {report_path}")
    return report_path

def run_metric_validation(
    metrics_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    abort_on_failure: bool = True
) -> bool:
    """
    Run the complete metric validation workflow.
    
    Args:
        metrics_dir: Path to metrics directory (defaults to data/metrics)
        output_dir: Path for diagnostic report output (defaults to data/metrics)
        abort_on_failure: If True, raise SystemExit with code 102 if failure rate >= 5%
        
    Returns:
        True if validation passed, False otherwise (if abort_on_failure is False)
    """
    logger = setup_validation_logger()
    logger.info("Starting metric validation workflow")
    
    # Load all metrics data
    try:
        metrics_data = load_metrics_data(metrics_dir)
    except FileNotFoundError as e:
        logger.error(f"Metrics directory not found: {e}")
        if abort_on_failure:
            sys.exit(ERROR_CODE_102)
        return False
    
    if not metrics_data:
        logger.error("No metric files found in the specified directory")
        if abort_on_failure:
            sys.exit(ERROR_CODE_102)
        return False
    
    total_snippets = 0
    total_failed = 0
    all_failures = []
    
    # Validate each metric
    for metric_name, df in metrics_data.items():
        logger.info(f"Validating metric: {metric_name}")
        total, failed, failures = validate_single_metric(df, metric_name)
        total_snippets += total
        total_failed += failed
        all_failures.extend(failures)
    
    # Calculate failure rate
    failure_rate = total_failed / total_snippets if total_snippets > 0 else 0.0
    
    logger.info(f"Validation complete: {total_failed}/{total_snippets} snippets failed ({failure_rate:.2%})")
    
    # Generate diagnostic report
    if output_dir is None:
        output_dir = Path("data/metrics")
    report_path = generate_diagnostic_report(
        total_snippets, total_failed, all_failures, metrics_data, output_dir
    )
    
    # Check against threshold
    if failure_rate >= VALIDATION_THRESHOLD:
        logger.error(f"Validation FAILED: {failure_rate:.2%} failure rate exceeds threshold of {VALIDATION_THRESHOLD:.2%}")
        logger.error(f"Diagnostic report saved to: {report_path}")
        if abort_on_failure:
            logger.error(f"Exiting with error code {ERROR_CODE_102}")
            sys.exit(ERROR_CODE_102)
        return False
    
    logger.info(f"Validation PASSED: {failure_rate:.2%} failure rate is within acceptable threshold")
    return True

def main():
    """Main entry point for metric validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate extracted metric scores")
    parser.add_argument(
        "--metrics-dir", 
        type=str, 
        default="data/metrics",
        help="Path to metrics directory"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="data/metrics",
        help="Path for diagnostic report output"
    )
    parser.add_argument(
        "--no-abort", 
        action="store_true",
        help="Do not abort on failure (just return False)"
    )
    
    args = parser.parse_args()
    
    metrics_dir = Path(args.metrics_dir)
    output_dir = Path(args.output_dir)
    abort_on_failure = not args.no_abort
    
    success = run_metric_validation(metrics_dir, output_dir, abort_on_failure)
    
    if not success and abort_on_failure:
        # This point should not be reached if abort_on_failure is True
        sys.exit(ERROR_CODE_102)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()