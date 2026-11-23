"""
Variance Detection & Graceful Degradation (T011b).

Loads preprocessed annotated code chunks, computes variance for key
complexity metrics (cyclomatic_complexity, nesting_depth), and writes
a failure report if zero variance is detected for any metric.

Dependencies:
  - data.preprocess (for file paths)
  - config (for project root)
  - utils.logging (for logging)

Artifacts:
  - data/results/variance_null_report.json (ONLY if zero variance detected)
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import statistics

# Import from project API surface
from config import get_config, get_project_root
from utils.logging import get_logger, PipelineError

# Configure logger
logger = get_logger(__name__)

# Constants
METRICS_TO_CHECK = ["cyclomatic_complexity", "nesting_depth"]
VARIANCE_THRESHOLD = 0.0  # Strict zero check

def load_annotated_data(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Load annotated JSONL files from the specified data directory.
    
    Args:
        data_dir: Path to the directory containing annotated JSONL files.
        
    Returns:
        List of dictionaries containing chunk data.
        
    Raises:
        PipelineError: If no data files are found or if parsing fails.
    """
    if not data_dir.exists():
        raise PipelineError(f"Data directory does not exist: {data_dir}")

    data_files = list(data_dir.glob("*.jsonl"))
    if not data_files:
        raise PipelineError(f"No .jsonl files found in {data_dir}")

    all_records = []
    for file_path in data_files:
        logger.info(f"Loading data from {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        all_records.append(record)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON at line {line_num} in {file_path}: {e}")
        except IOError as e:
            raise PipelineError(f"Failed to read {file_path}: {e}")

    if not all_records:
        raise PipelineError(f"No valid records loaded from {data_dir}")

    logger.info(f"Loaded {len(all_records)} records from {len(data_files)} files")
    return all_records

def compute_variance(values: List[float]) -> float:
    """
    Compute the variance of a list of numeric values.
    
    Args:
        values: List of numeric values.
        
    Returns:
        The variance of the values. Returns 0.0 if list is empty or has < 2 items.
    """
    if len(values) < 2:
        return 0.0
    try:
        return statistics.variance(values)
    except statistics.StatisticsError as e:
        logger.warning(f"Could not compute variance: {e}")
        return 0.0

def check_metric_variance(
    records: List[Dict[str, Any]], 
    metric_name: str
) -> Tuple[float, bool, Optional[str]]:
    """
    Check variance for a specific metric across all records.
    
    Args:
        records: List of chunk records.
        metric_name: Name of the metric to check.
        
    Returns:
        Tuple of (variance, is_null, error_message).
    """
    values = []
    missing_count = 0
    
    for record in records:
        if metric_name in record:
            val = record[metric_name]
            if isinstance(val, (int, float)):
                values.append(float(val))
            else:
                logger.warning(f"Non-numeric value for {metric_name}: {val}")
                missing_count += 1
        else:
            missing_count += 1

    if not values:
        return 0.0, True, f"No valid numeric values found for {metric_name} (missing in {missing_count} records)"

    variance = compute_variance(values)
    is_null = variance <= VARIANCE_THRESHOLD
    
    if is_null:
        msg = f"Zero variance detected for {metric_name} (variance={variance:.6f}, N={len(values)})"
        logger.warning(msg)
        return variance, True, msg
    
    logger.info(f"Metric {metric_name} has variance {variance:.6f} (N={len(values)})")
    return variance, False, None

def write_null_variance_report(
    output_path: Path,
    results: Dict[str, Any]
) -> None:
    """
    Write the variance null report to JSON.
    
    Args:
        output_path: Path to the output JSON file.
        results: Dictionary containing variance analysis results.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "status": "null_variance",
        "timestamp": results.get("timestamp"),
        "metrics_analyzed": results.get("metrics_analyzed", []),
        "null_metrics": results.get("null_metrics", []),
        "message": "Zero variance detected in one or more metrics. Correlation analysis cannot proceed.",
        "recommendation": "Review data collection or preprocessing pipeline. The dataset lacks necessary complexity variation."
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Wrote null variance report to {output_path}")

def main() -> int:
    """
    Main entry point for the variance check task.
    
    Returns:
        0 if variance is sufficient (no artifact written),
        1 if zero variance detected (artifact written and error raised),
        2 on fatal error.
    """
    config = get_config()
    project_root = get_project_root()
    
    # Determine input paths based on language availability
    # We check both Python and Java processed directories if they exist
    processed_dir = project_root / "data" / "processed"
    python_dir = processed_dir / "train_python"
    java_dir = processed_dir / "val_java"
    
    all_records = []
    languages_processed = []
    
    if python_dir.exists():
        try:
            records = load_annotated_data(python_dir)
            all_records.extend(records)
            languages_processed.append("python")
        except PipelineError as e:
            logger.warning(f"Could not load Python data: {e}")
    
    if java_dir.exists():
        try:
            records = load_annotated_data(java_dir)
            all_records.extend(records)
            languages_processed.append("java")
        except PipelineError as e:
            logger.warning(f"Could not load Java data: {e}")
    
    if not all_records:
        logger.error("No annotated data found in any processed directory.")
        print("ERROR: No annotated data found to analyze variance.", file=sys.stderr)
        return 2
    
    logger.info(f"Analyzing variance across {len(all_records)} records from: {languages_processed}")
    
    results = {
        "timestamp": str(__import__('datetime').datetime.now()),
        "languages_processed": languages_processed,
        "total_records": len(all_records),
        "metrics_analyzed": [],
        "null_metrics": []
    }
    
    has_null_variance = False
    
    for metric in METRICS_TO_CHECK:
        variance, is_null, message = check_metric_variance(all_records, metric)
        
        metric_result = {
            "metric": metric,
            "variance": variance,
            "is_null": is_null
        }
        
        if is_null:
            metric_result["message"] = message
            results["null_metrics"].append(metric_result)
            has_null_variance = True
        else:
            results["metrics_analyzed"].append(metric_result)
    
    output_path = project_root / "data" / "results" / "variance_null_report.json"
    
    if has_null_variance:
        write_null_variance_report(output_path, results)
        logger.error("Zero variance detected. Pipeline cannot proceed with correlation analysis.")
        print("ERROR: Zero variance detected in complexity metrics. See data/results/variance_null_report.json", file=sys.stderr)
        return 1
    
    logger.info("Variance check passed. All metrics have non-zero variance.")
    # No artifact written on success, as per requirements
    return 0

if __name__ == "__main__":
    sys.exit(main())