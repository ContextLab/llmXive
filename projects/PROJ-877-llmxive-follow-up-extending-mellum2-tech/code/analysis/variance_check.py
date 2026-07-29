"""
T011b: Variance Detection & Graceful Degradation.

Loads preprocessed annotated data (JSONL) and checks for zero variance in
key complexity metrics (cyclomatic_complexity, nesting_depth).

If zero variance is detected for any metric:
  1. Logs a warning.
  2. Writes a report to `data/results/variance_null_report.json`.
  3. Does NOT exit (allows T020 to handle graceful degradation).

If variance > 0 for all metrics, no report is written (implicit pass),
and the pipeline proceeds to T018/T019.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import config for paths
from config import get_config
# Import logging utilities
from utils.logging import get_logger, PipelineError

logger = get_logger(__name__)

def load_annotated_data(file_path: Path) -> List[Dict[str, Any]]:
    """
    Loads a JSONL file containing annotated code chunks.
    
    Args:
        file_path: Path to the JSONL file.
        
    Returns:
        List of dictionaries representing the chunks.
        
    Raises:
        PipelineError: If file not found or invalid JSON.
    """
    if not file_path.exists():
        raise PipelineError(f"Annotated data file not found: {file_path}")
    
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON at line {line_num} in {file_path}: {e}")
                    continue
    except Exception as e:
        raise PipelineError(f"Failed to read {file_path}: {e}")
    
    if not data:
        raise PipelineError(f"No valid data found in {file_path}")
        
    return data

def compute_variance(values: List[float]) -> float:
    """
    Computes the population variance of a list of numbers.
    
    Args:
        values: List of numeric values.
        
    Returns:
        The variance (float).
    """
    n = len(values)
    if n == 0:
        return 0.0
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    return variance

def check_metric_variance(data: List[Dict[str, Any]], metric_name: str) -> Tuple[float, bool]:
    """
    Extracts a specific metric from data and checks if its variance is zero.
    
    Args:
        data: List of chunk dictionaries.
        metric_name: The key in the dictionary to check (e.g., 'cyclomatic_complexity').
        
    Returns:
        Tuple of (variance, is_null).
    """
    values = []
    for chunk in data:
        # Handle nested structures if metrics are stored under 'metrics' key
        if isinstance(chunk, dict):
            if metric_name in chunk:
                val = chunk[metric_name]
            elif 'metrics' in chunk and isinstance(chunk['metrics'], dict) and metric_name in chunk['metrics']:
                val = chunk['metrics'][metric_name]
            else:
                # Try to find case-insensitive or similar key if exact match fails
                val = None
                for k in chunk:
                    if k.lower() == metric_name.lower():
                        val = chunk[k]
                        break
            
            if val is not None and isinstance(val, (int, float)):
                values.append(float(val))
    
    if not values:
        logger.warning(f"No valid values found for metric '{metric_name}' in data.")
        return 0.0, True
        
    variance = compute_variance(values)
    is_null = (variance == 0.0)
    return variance, is_null

def write_null_variance_report(
    output_path: Path,
    metrics: List[Dict[str, Any]],
    total_chunks: int
) -> None:
    """
    Writes the variance null report to disk.
    
    Args:
        output_path: Path to the output JSON file.
        metrics: List of dicts with metric name, variance, and is_null status.
        total_chunks: Total number of chunks processed.
    """
    report = {
        "status": "null_variance",
        "total_chunks_processed": total_chunks,
        "metrics_with_null_variance": [m for m in metrics if m["is_null"]],
        "metrics_with_variance": [m for m in metrics if not m["is_null"]],
        "message": "No variance detected in one or more metrics; skipping correlation analysis for those metrics.",
        "timestamp": str(Path(output_path).parent.parent.parent) # Just a placeholder for now, real timestamp logic if needed
    }
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Null variance report written to {output_path}")

def main() -> int:
    """
    Main entry point for the variance check task.
    
    Returns:
        0 on success (even if null variance found, as per graceful degradation requirement).
        1 on fatal error.
    """
    config = get_config()
    data_dir = Path(config.get("data_dir", "data"))
    results_dir = data_dir / "results"
    
    # Define input paths based on T016 output
    annotated_python = data_dir / "processed" / "annotated_python.jsonl"
    annotated_java = data_dir / "processed" / "annotated_java.jsonl"
    
    # Define output path
    variance_report_path = results_dir / "variance_null_report.json"
    
    # Metrics to check
    metrics_to_check = ["cyclomatic_complexity", "nesting_depth"]
    
    all_data = []
    all_chunks_count = 0
    
    # Load Python data
    if annotated_python.exists():
        try:
            python_data = load_annotated_data(annotated_python)
            all_data.extend(python_data)
            all_chunks_count += len(python_data)
            logger.info(f"Loaded {len(python_data)} chunks from {annotated_python}")
        except PipelineError as e:
            logger.error(f"Failed to load Python data: {e}")
            # Continue to check Java if available, or fail if both missing
    else:
        logger.warning(f"Python data file not found: {annotated_python}")
        
    # Load Java data
    if annotated_java.exists():
        try:
            java_data = load_annotated_data(annotated_java)
            all_data.extend(java_data)
            all_chunks_count += len(java_data)
            logger.info(f"Loaded {len(java_data)} chunks from {annotated_java}")
        except PipelineError as e:
            logger.error(f"Failed to load Java data: {e}")
    else:
        logger.warning(f"Java data file not found: {annotated_java}")
    
    if all_chunks_count == 0:
        logger.error("No data loaded from any source. Cannot perform variance check.")
        # Write a report indicating no data found
        try:
            write_null_variance_report(
                variance_report_path,
                [{"name": "N/A", "variance": 0.0, "is_null": True}],
                0
            )
        except Exception:
            pass
        return 1

    null_metrics = []
    
    logger.info(f"Checking variance for {all_chunks_count} chunks across {len(metrics_to_check)} metrics.")
    
    for metric in metrics_to_check:
        variance, is_null = check_metric_variance(all_data, metric)
        logger.info(f"Metric '{metric}': Variance = {variance:.6f}, Null = {is_null}")
        
        if is_null:
            null_metrics.append({
                "name": metric,
                "variance": variance,
                "is_null": True
            })
            logger.warning(f"WARNING: No variance detected for metric '{metric}'.")
        else:
            null_metrics.append({
                "name": metric,
                "variance": variance,
                "is_null": False
            })
    
    # If any metric has null variance, write the report
    if any(m["is_null"] for m in null_metrics):
        write_null_variance_report(variance_report_path, null_metrics, all_chunks_count)
        logger.warning("Variance check completed with null variance detected. Proceeding to next stage gracefully.")
    else:
        logger.info("Variance check completed. All metrics have non-zero variance. No report written.")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
