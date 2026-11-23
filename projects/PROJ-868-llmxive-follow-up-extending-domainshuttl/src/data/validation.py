"""
Validation logic for User Story 1 data processing.

Ensures a sufficient number of unique IDs are processed and saved.
Logs any failures to data/processed/failed_subjects.log.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Set

from src.config.settings import get_config
from src.utils.io import ensure_dir, load_json, save_json

logger = logging.getLogger(__name__)

# Minimum unique subjects required to consider the dataset valid
MIN_UNIQUE_SUBJECTS = 95  # Allow 5% failure rate tolerance


def validate_unique_ids(
    embeddings_dir: Path,
    complexity_csv_path: Path,
    output_log_path: Path
) -> Dict[str, Any]:
    """
    Validate that a sufficient number of unique subject IDs were processed.

    Args:
        embeddings_dir: Path to directory containing embedding tensors.
        complexity_csv_path: Path to the CSV file with complexity scores.
        output_log_path: Path to the log file for recording failures.

    Returns:
        Dictionary with validation results:
        - 'success': bool
        - 'total_processed': int
        - 'unique_subjects': int
        - 'min_required': int
        - 'failures': List[Dict]
    """
    ensure_dir(output_log_path.parent)

    # Collect unique IDs from embeddings directory
    embedding_ids: Set[str] = set()
    embedding_failures: List[Dict[str, Any]] = []

    if embeddings_dir.exists():
        for file in embeddings_dir.glob("*.pt"):
            try:
                subject_id = file.stem
                # Validate ID format (should be numeric or alphanumeric)
                if not subject_id:
                    raise ValueError("Empty filename")
                embedding_ids.add(subject_id)
            except Exception as e:
                embedding_failures.append({
                    "file": str(file),
                    "error": str(e),
                    "type": "embedding_file"
                })

    # Cross-reference with CSV
    csv_ids: Set[str] = set()
    csv_failures: List[Dict[str, Any]] = []

    if complexity_csv_path.exists():
        import pandas as pd
        try:
            df = pd.read_csv(complexity_csv_path)
            if "subject_id" in df.columns:
                csv_ids = set(df["subject_id"].dropna().astype(str).unique())
            else:
                csv_failures.append({
                    "file": str(complexity_csv_path),
                    "error": "Missing 'subject_id' column",
                    "type": "csv_structure"
                })
        except Exception as e:
            csv_failures.append({
                "file": str(complexity_csv_path),
                "error": str(e),
                "type": "csv_read"
            })
    else:
        csv_failures.append({
            "file": str(complexity_csv_path),
            "error": "File not found",
            "type": "file_missing"
        })

    # Combine results
    all_ids = embedding_ids & csv_ids
    total_unique = len(all_ids)

    # Determine success
    success = total_unique >= MIN_UNIQUE_SUBJECTS

    # Collect all failures
    all_failures = embedding_failures + csv_failures

    # Log failures to file
    log_entries = []
    for failure in all_failures:
        log_entry = {
            "timestamp": None,  # Will be set by caller if needed
            "subject_id": failure.get("file", "unknown"),
            "error": failure["error"],
            "type": failure["type"]
        }
        log_entries.append(log_entry)

    if all_failures:
        with open(output_log_path, "w", encoding="utf-8") as f:
            for entry in log_entries:
                f.write(json.dumps(entry) + "\n")
        logger.warning(f"Logged {len(log_entries)} failures to {output_log_path}")
    else:
        # Clear the log file if no failures
        with open(output_log_path, "w", encoding="utf-8") as f:
            f.write("")
        logger.info("No failures detected; cleared failed_subjects.log")

    # Return validation summary
    result = {
        "success": success,
        "total_processed": total_unique,
        "unique_subjects": total_unique,
        "min_required": MIN_UNIQUE_SUBJECTS,
        "failures_count": len(all_failures),
        "failures": all_failures
    }

    logger.info(f"Validation complete: {total_unique} unique subjects "
                f"(required: {MIN_UNIQUE_SUBJECTS}) - {'PASS' if success else 'FAIL'}")

    return result


def run_validation() -> None:
    """
    Entry point for running validation after pipeline execution.
    Reads configuration and executes validation, exiting with error if failed.
    """
    config = get_config()
    
    # Paths from config
    embeddings_dir = Path(config["paths"]["processed_embeddings"])
    complexity_csv = Path(config["paths"]["complexity_scores"])
    failed_log = Path(config["paths"]["processed_failed_subjects_log"])

    logger.info(f"Starting validation for {embeddings_dir} and {complexity_csv}")

    result = validate_unique_ids(
        embeddings_dir=embeddings_dir,
        complexity_csv_path=complexity_csv,
        output_log_path=failed_log
    )

    if not result["success"]:
        logger.error(f"Validation FAILED: {result['unique_subjects']} unique subjects "
                     f"found, but {MIN_UNIQUE_SUBJECTS} required.")
        # Exit with error code to fail the pipeline
        import sys
        sys.exit(1)
    else:
        logger.info("Validation PASSED")


if __name__ == "__main__":
    # Configure basic logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run_validation()
