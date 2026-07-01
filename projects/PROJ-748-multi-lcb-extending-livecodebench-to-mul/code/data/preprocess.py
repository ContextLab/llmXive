"""
Preprocessing and contamination filter for Multi-LCB dataset.

This module implements:
1. Conversion of STDIN/STDOUT test cases to a unified format.
2. Application of release-date cutoffs to filter contaminated tasks.
3. Logging of exclusion rates (SC-005) and missing metadata warnings.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import config utilities from the sibling module
from config import get_data_path, get_results_path, get_logs_path


def setup_logging() -> logging.Logger:
    """Configure logging to file and console."""
    log_dir = get_logs_path()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "preprocess.log"

    logger = logging.getLogger("preprocess")
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def convert_test_case_to_unified_format(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a raw test case from STDIN/STDOUT format to the unified format.

    The unified format standardizes inputs and expected outputs for consistent
    evaluation across languages.

    Args:
        test_case: Raw test case dictionary containing 'input', 'output', etc.

    Returns:
        Dictionary in unified format with keys:
            - 'input': Standardized input string
            - 'expected_output': Standardized expected output string
            - 'type': 'STDIN' or 'STDOUT' (normalized)
            - 'timeout': Default timeout if missing
    """
    # Extract raw data with defaults
    raw_input = test_case.get("input", test_case.get("stdin", ""))
    raw_output = test_case.get("output", test_case.get("stdout", ""))
    case_type = test_case.get("type", "STDIN").upper()

    # Normalize type
    if case_type not in ("STDIN", "STDOUT", "FILE"):
        case_type = "STDIN"

    # Ensure strings (handle potential None or non-string types)
    if not isinstance(raw_input, str):
        raw_input = str(raw_input) if raw_input is not None else ""
    if not isinstance(raw_output, str):
        raw_output = str(raw_output) if raw_output is not None else ""

    # Construct unified format
    unified = {
        "input": raw_input,
        "expected_output": raw_output,
        "type": case_type,
        "timeout": test_case.get("timeout", 10.0),  # Default 10s timeout
    }

    return unified


def apply_release_date_cutoff(
    task: Dict[str, Any],
    cutoff_date: datetime,
    logger: logging.Logger
) -> Tuple[bool, Optional[str]]:
    """
    Check if a task should be excluded based on its release date.

    A task is considered contaminated (excluded) if its release date is
    on or after the model's training cutoff date.

    Args:
        task: The task dictionary containing metadata.
        cutoff_date: The model training cutoff datetime.
        logger: Logger instance for warnings and info.

    Returns:
        Tuple of (is_excluded, reason).
        is_excluded is True if the task should be filtered out.
    """
    # Extract release date from various possible keys
    release_date_str = task.get("release_date") or task.get("date") or task.get("created_at")

    if not release_date_str:
        # Missing metadata - log warning, do not exclude (conservative approach)
        task_id = task.get("task_id", "UNKNOWN")
        logger.warning(
            f"[SC-005] Missing release_date metadata for task {task_id}. "
            "Task retained for safety, but metadata should be verified."
        )
        return False, None

    try:
        # Parse date string (handles ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        if "T" in release_date_str:
            release_date = datetime.fromisoformat(release_date_str.replace("Z", "+00:00"))
        else:
            release_date = datetime.strptime(release_date_str, "%Y-%m-%d")

        # Normalize to naive datetime for comparison if both are naive
        if release_date.tzinfo is not None and cutoff_date.tzinfo is None:
            release_date = release_date.replace(tzinfo=None)

        # Contamination check: Task released >= cutoff means contaminated
        if release_date >= cutoff_date:
            task_id = task.get("task_id", "UNKNOWN")
            logger.info(
                f"[SC-005] Excluding task {task_id} due to release date "
                f"({release_date.date()}) >= cutoff ({cutoff_date.date()})."
            )
            return True, f"Release date {release_date.date()} >= cutoff {cutoff_date.date()}"
        else:
            return False, None

    except (ValueError, TypeError) as e:
        task_id = task.get("task_id", "UNKNOWN")
        logger.warning(
            f"[SC-005] Could not parse release_date '{release_date_str}' for task {task_id}. "
            f"Error: {e}. Task retained."
        )
        return False, None


def preprocess_dataset(
    input_path: Path,
    output_path: Path,
    cutoff_date_str: str,
    logger: logging.Logger
) -> Dict[str, int]:
    """
    Main preprocessing function.

    Performs:
    1. Loads the raw dataset.
    2. Converts test cases to unified format.
    3. Applies release date cutoff to filter contaminated tasks.
    4. Logs exclusion statistics (SC-005).
    5. Saves the cleaned dataset.

    Args:
        input_path: Path to the raw dataset JSON file.
        output_path: Path where the preprocessed dataset will be saved.
        cutoff_date_str: Model training cutoff date (ISO format string).
        logger: Logger instance.

    Returns:
        Dictionary with statistics:
            - 'total_tasks': Total number of tasks processed
            - 'kept_tasks': Number of tasks kept after filtering
            - 'excluded_tasks': Number of tasks excluded
            - 'exclusion_rate': Rate of exclusion
    """
    logger.info(f"Starting preprocessing: {input_path}")

    # Parse cutoff date
    try:
        cutoff_date = datetime.fromisoformat(cutoff_date_str)
        logger.info(f"Using release date cutoff: {cutoff_date.date()}")
    except ValueError as e:
        logger.error(f"Invalid cutoff date format: {cutoff_date_str}. Error: {e}")
        raise

    # Load raw data
    if not input_path.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Handle both list and dict with 'tasks' key
    if isinstance(raw_data, dict) and "tasks" in raw_data:
        tasks = raw_data["tasks"]
    elif isinstance(raw_data, list):
        tasks = raw_data
    else:
        raise ValueError(f"Unexpected dataset format at {input_path}")

    total_tasks = len(tasks)
    kept_tasks = 0
    excluded_tasks = 0
    excluded_reasons: List[str] = []

    preprocessed_tasks = []

    for idx, task in enumerate(tasks):
        task_id = task.get("task_id", f"task_{idx}")

        # 1. Convert test cases to unified format
        if "test_cases" in task:
            unified_test_cases = []
            for tc in task["test_cases"]:
                try:
                    unified_tc = convert_test_case_to_unified_format(tc)
                    unified_test_cases.append(unified_tc)
                except Exception as e:
                    logger.warning(
                        f"Failed to convert test case for {task_id}: {e}. Skipping test case."
                    )
            task["test_cases"] = unified_test_cases

        # 2. Apply release date cutoff
        is_excluded, reason = apply_release_date_cutoff(task, cutoff_date, logger)

        if is_excluded:
            excluded_tasks += 1
            if reason:
                excluded_reasons.append(reason)
        else:
            kept_tasks += 1
            preprocessed_tasks.append(task)

        # Progress logging
        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{total_tasks} tasks...")

    # Calculate and log statistics
    exclusion_rate = (excluded_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

    logger.info("=" * 60)
    logger.info("PREPROCESSING SUMMARY (SC-005)")
    logger.info("=" * 60)
    logger.info(f"Total tasks processed: {total_tasks}")
    logger.info(f"Tasks kept: {kept_tasks}")
    logger.info(f"Tasks excluded (contaminated): {excluded_tasks}")
    logger.info(f"Exclusion rate: {exclusion_rate:.2f}%")
    if excluded_reasons:
        logger.info(f"Sample exclusion reasons: {excluded_reasons[:3]}")
    logger.info("=" * 60)

    # Save preprocessed data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(preprocessed_tasks, f, indent=2, ensure_ascii=False)

    logger.info(f"Preprocessed dataset saved to: {output_path}")

    return {
        "total_tasks": total_tasks,
        "kept_tasks": kept_tasks,
        "excluded_tasks": excluded_tasks,
        "exclusion_rate": round(exclusion_rate, 4)
    }


def main() -> None:
    """Entry point for the preprocessing script."""
    logger = setup_logging()

    # Get paths from config
    data_dir = get_data_path()
    results_dir = get_results_path()

    # Expected input/output paths
    # Assuming the download script produced 'raw_dataset.json' in data_dir
    input_file = data_dir / "raw_dataset.json"
    output_file = results_dir / "preprocessed_dataset.json"

    # Cutoff date configuration (defaulting to a common LLM cutoff if not specified)
    # In a real scenario, this might come from config.py or command line args
    cutoff_date = "2024-01-01"  # Example cutoff

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run data/download.py first to fetch the dataset.")
        sys.exit(1)

    try:
        stats = preprocess_dataset(input_file, output_file, cutoff_date, logger)
        logger.info(f"Preprocessing completed successfully. Stats: {stats}")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()