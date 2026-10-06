import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Import from sibling modules as per API surface
from utils.logging_config import get_logger, log_warning
from utils.config import get_project_root, get_results_path, get_log_path

logger = get_logger(__name__)


def load_pipeline_summary() -> Dict[str, Any]:
    """
    Load the pipeline summary log to retrieve initial query counts.

    Reads from logs/pipeline.log to find the initial number of datasets
    queried before filtering and merging.

    Returns:
        Dict containing 'initial_count' and 'log_path'.
    """
    log_path = get_log_path()
    pipeline_log = log_path / "pipeline.log"

    if not pipeline_log.exists():
        raise FileNotFoundError(f"Pipeline log not found at {pipeline_log}. Run the ingestion pipeline first.")

    initial_count = 0
    try:
        with open(pipeline_log, 'r', encoding='utf-8') as f:
            for line in f:
                if "Initial query count:" in line:
                    # Expected format: "Initial query count: 123"
                    parts = line.split(":")
                    if len(parts) >= 2:
                        initial_count = int(parts[1].strip())
                        break
    except ValueError as e:
        log_warning(f"Failed to parse initial count from log: {e}")
        raise

    return {
        "initial_count": initial_count,
        "log_path": str(pipeline_log)
    }


def calculate_completeness(
    initial_count: int,
    retained_count: int
) -> Dict[str, Any]:
    """
    Calculate the Data Completeness percentage.

    Formula: (Retained Datasets / Initial Query Results) × 100

    Args:
        initial_count: Number of datasets initially queried.
        retained_count: Number of datasets successfully retained after processing.

    Returns:
        Dictionary containing completeness metrics.
    """
    if initial_count == 0:
        log_warning("Initial count is zero; cannot calculate completeness percentage.")
        completeness_pct = 0.0
    else:
        completeness_pct = (retained_count / initial_count) * 100

    return {
        "initial_count": initial_count,
        "retained_count": retained_count,
        "completeness_percentage": round(completeness_pct, 2),
        "timestamp": datetime.now().isoformat()
    }


def write_completeness_report(metrics: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Write the completeness metrics to a JSON file.

    Args:
        metrics: Dictionary containing completeness data.
        output_path: Optional specific path to write the report. Defaults to results/data_completeness.json.

    Returns:
        Path to the written file.
    """
    if output_path is None:
        results_dir = get_results_path()
        output_path = results_dir / "data_completeness.json"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4)

    logger.info(f"Data completeness report written to {output_path}")
    return output_path


def run_completeness_check() -> Dict[str, Any]:
    """
    Execute the full completeness check workflow.

    1. Loads the pipeline summary to get initial count.
    2. Determines retained count from the processed data directory.
    3. Calculates the percentage.
    4. Writes the report.

    Returns:
        The calculated metrics dictionary.
    """
    # 1. Load initial count
    summary = load_pipeline_summary()
    initial_count = summary["initial_count"]

    # 2. Determine retained count
    # We check the processed directory for the merged matrix or list of retained files
    results_dir = get_results_path()
    processed_dir = Path(get_project_root()) / "data" / "processed"

    retained_count = 0
    if processed_dir.exists():
        # Count valid CSV/Parquet files as retained datasets
        valid_extensions = {'.csv', '.parquet'}
        for file in processed_dir.iterdir():
            if file.suffix.lower() in valid_extensions:
                retained_count += 1

    if retained_count == 0 and initial_count > 0:
        log_warning("Processed data directory is empty. Retained count is 0.")

    # 3. Calculate metrics
    metrics = calculate_completeness(initial_count, retained_count)

    # 4. Write report
    write_completeness_report(metrics)

    return metrics


def main() -> int:
    """
    Main entry point for the completeness check script.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        logger.info("Starting data completeness check...")
        metrics = run_completeness_check()
        logger.info(f"Computation complete. Completeness: {metrics['completeness_percentage']}%")
        return 0
    except Exception as e:
        logger.error(f"Completeness check failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
