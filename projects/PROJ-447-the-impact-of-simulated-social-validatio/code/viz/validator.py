"""
Visualization validation module.

This module counts generated visualization files and updates the pipeline log
if files are missing.
"""

import os
import json
import logging
from typing import List, Tuple, Dict, Any
from pathlib import Path

from utils.constants import get_seed

logger = logging.getLogger(__name__)


def count_generated_visualizations(
    directory: str,
    expected_files: List[str] = None
) -> Tuple[int, List[str]]:
    """
    Count existing visualization files in a directory.

    Args:
        directory: Directory to check.
        expected_files: List of expected filenames.

    Returns:
        Tuple of (count of found files, list of missing files).
    """
    if expected_files is None:
        expected_files = ["scatter_plot.png", "residuals.png"]

    found_count = 0
    missing_files = []

    for fname in expected_files:
        fpath = os.path.join(directory, fname)
        if os.path.exists(fpath):
            found_count += 1
        else:
            missing_files.append(fname)

    return found_count, missing_files


def validate_visualization_count(
    count: int,
    expected: int = 2
) -> bool:
    """
    Validate that the expected number of visualizations were generated.

    Args:
        count: Actual count of files.
        expected: Expected count.

    Returns:
        True if count >= expected.
    """
    return count >= expected


def update_pipeline_log(
    log_path: str,
    missing_files: List[str]
) -> None:
    """
    Update the pipeline run log with missing visualization information.

    Args:
        log_path: Path to the pipeline log JSON file.
        missing_files: List of missing filenames.
    """
    if not os.path.exists(log_path):
        logger.warning(f"Pipeline log not found at {log_path}")
        return

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

        log_data["visualization_status"] = {
            "missing_files": missing_files,
            "count": len(missing_files),
            "status": "incomplete" if missing_files else "complete"
        }

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)

        logger.info(f"Pipeline log updated with visualization status")

    except Exception as e:
        logger.error(f"Failed to update pipeline log: {e}")


def main() -> None:
    """
    Main entry point for visualization validation.
    """
    from pathlib import Path
    base_dir = Path(__file__).resolve().parents[2]
    viz_dir = str(base_dir / "data" / "processed")
    log_path = str(base_dir / "data" / "processed" / "pipeline_run_log.json")

    logger.info("Executing main() for viz validation")

    count, missing = count_generated_visualizations(viz_dir)
    logger.info(f"Found {count} visualizations. Missing: {missing}")

    if missing:
        update_pipeline_log(log_path, missing)


if __name__ == "__main__":
    main()
