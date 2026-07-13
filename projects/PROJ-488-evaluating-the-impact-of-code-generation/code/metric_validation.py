"""
Metric Validation Module for T022.

Validates extracted scores from metric_extraction.py.
Detects NaN or out-of-range values.
Aborts with error 102 if >= 5% of snippets fail validation.
Generates a diagnostic report upon failure.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

# Local imports matching API surface
from logging_config import get_logger, setup_logger
from data_model import MetricResult

# Constants
ERROR_102_CODE = 102
FAILURE_THRESHOLD_PERCENT = 5.0
VALID_RANGE_METRICS = {
    "cyclomatic_complexity": (0, 1000),  # Reasonable upper bound
    "loc": (1, 100000),
    "maintainability_index": (0, 1000),
    "pylint_bug_count": (0, 10000),
    "pylint_style_count": (0, 10000),
    "pylint_convention_count": (0, 10000),
    "pylint_refactor_count": (0, 10000)
}

def setup_validation_logger():
    """Setup logger specific to this validation task."""
    logger = get_logger("metric_validation")
    if not logger.handlers:
        logger = setup_logger("metric_validation", level=logging.INFO)
    return logger

def load_metrics_data(metrics_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Load all metric CSVs from the specified directory.
    
    Args:
        metrics_dir: Path to data/metrics/
        
    Returns:
        Dictionary mapping metric_type to DataFrame
    """
    data = {}
    if not metrics_dir.exists():
        raise FileNotFoundError(f"Metrics directory not found: {metrics_dir}")
    
    for file_path in metrics_dir.glob("*.csv"):
        metric_type = file_path.stem
        try:
            df = pd.read_csv(file_path)
            data[metric_type] = df
        except Exception as e:
            logging.warning(f"Could not read {file_path}: {e}")
    
    return data

def validate_single_metric(df: pd.DataFrame, metric_type: str) -> Tuple[int, int, List[Dict]]:
    """
    Validate a single metric DataFrame for NaNs and out-of-range values.
    
    Args:
        df: DataFrame containing the metric scores
        metric_type: Name of the metric (for logging)
        
    Returns:
        Tuple of (total_rows, failed_rows, list of failure details)
    """
    total_rows = len(df)
    if total_rows == 0:
        return 0, 0, []
    
    failures = []
    failed_count = 0
    
    # Identify score columns (exclude 'snippet_id', 'timestamp', etc.)
    # Assuming the schema from data_model.py has 'score' or specific metric columns
    # We look for columns that are numeric and likely scores
    score_columns = []
    for col in df.columns:
        if col in ['snippet_id', 'timestamp', 'metric_type']:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            score_columns.append(col)
    
    # If no obvious score columns, try to find 'score' column specifically
    if not score_columns:
        if 'score' in df.columns:
            score_columns = ['score']
        else:
            # Fallback: check all numeric columns except ID
            score_columns = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in ['snippet_id', 'timestamp', 'metric_type']]
    
    for idx, row in df.iterrows():
        row_failed = False
        row_details = {"row_index": idx, "snippet_id": row.get('snippet_id', 'N/A'), "issues": []}
        
        for col in score_columns:
            val = row[col]
            
            # Check for NaN
            if pd.isna(val):
                row_failed = True
                row_details["issues"].append(f"{col}: NaN")
                continue
            
            # Check range if defined
            if col in VALID_RANGE_METRICS:
                min_val, max_val = VALID_RANGE_METRICS[col]
                if val < min_val or val > max_val:
                    row_failed = True
                    row_details["issues"].append(f"{col}: {val} (out of range [{min_val}, {max_val}])")
        
        if row_failed:
            failed_count += 1
            failures.append(row_details)
    
    return total_rows, failed_count, failures

def generate_diagnostic_report(
    total_snippets: int, 
    total_failures: int, 
    failure_details: Dict[str, List[Dict]], 
    output_path: Path
):
    """
    Generate a diagnostic report JSON file.
    
    Args:
        total_snippets: Total number of snippets processed
        total_failures: Total number of failed snippets
        failure_details: Dict mapping metric_type to list of failure dicts
        output_path: Path to write the report
    """
    failure_rate = (total_failures / total_snippets * 100) if total_snippets > 0 else 0.0
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "validation_status": "FAILED",
        "summary": {
            "total_snippets_processed": total_snippets,
            "total_failed_snippets": total_failures,
            "failure_rate_percent": round(failure_rate, 2),
            "threshold_percent": FAILURE_THRESHOLD_PERCENT
        },
        "details_by_metric": {
            metric: {
                "failed_count": len(details),
                "sample_failures": details[:10]  # Limit to first 10 for brevity
            }
            for metric, details in failure_details.items()
        }
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logging.error(f"Diagnostic report written to {output_path}")

def run_metric_validation(metrics_dir: Optional[Path] = None) -> bool:
    """
    Main entry point for metric validation.
    
    Args:
        metrics_dir: Optional override for metrics directory path.
        
    Returns:
        True if validation passes, False otherwise (raises error 102).
    """
    logger = setup_validation_logger()
    logger.info("Starting metric validation (T022)...")
    
    if metrics_dir is None:
        metrics_dir = Path("data/metrics")
    
    if not metrics_dir.exists():
        logger.error(f"Metrics directory does not exist: {metrics_dir}")
        return False
    
    data = load_metrics_data(metrics_dir)
    
    if not data:
        logger.warning("No metric files found to validate.")
        return True
    
    total_snippets = 0
    total_failures = 0
    all_failures: Dict[str, List[Dict]] = {}
    
    for metric_type, df in data.items():
        logger.info(f"Validating metric: {metric_type} ({len(df)} rows)")
        rows, fails, details = validate_single_metric(df, metric_type)
        
        total_snippets += rows
        total_failures += fails
        all_failures[metric_type] = details
        
        if fails > 0:
            logger.warning(f"Found {fails} failures in {metric_type}")
    
    failure_rate = (total_failures / total_snippets * 100) if total_snippets > 0 else 0.0
    logger.info(f"Overall failure rate: {failure_rate:.2f}% ({total_failures}/{total_snippets})")
    
    if failure_rate >= FAILURE_THRESHOLD_PERCENT:
        logger.error(f"Failure rate {failure_rate:.2f}% exceeds threshold {FAILURE_THRESHOLD_PERCENT}%.")
        report_path = Path("results/validation/diagnostic_report_T022.json")
        generate_diagnostic_report(total_snippets, total_failures, all_failures, report_path)
        
        # Abort with Error 102
        raise SystemExit(f"Error {ERROR_102_CODE}: Metric validation failed. Failure rate {failure_rate:.2f}% >= {FAILURE_THRESHOLD_PERCENT}%. See {report_path} for details.")
    
    logger.info("Metric validation passed.")
    return True

def main():
    """CLI entry point."""
    try:
        success = run_metric_validation()
        if success:
            print("Validation successful.")
        else:
            print("Validation failed or no data found.")
            return 1
    except SystemExit as e:
        print(str(e))
        return ERROR_102_CODE
    except Exception as e:
        logging.exception("Unexpected error during validation")
        return 1

if __name__ == "__main__":
    exit(main())
