import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from utils.config import get_config_summary

# Configure logging to write to a specific file in the results directory
# This ensures logging happens regardless of stdout/stderr capture in CI
def setup_processing_logger(log_path: Optional[str] = None) -> logging.Logger:
    """
    Sets up a logger that writes to a file in results/ and also logs to console.
    Returns the logger instance.
    """
    if log_path is None:
        log_path = "results/processing_log.json"
    
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create a custom formatter that includes timestamp and level
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File handler
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Get or create logger
    logger = logging.getLogger('pipeline_processor')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def log_excluded_subjects(
    logger: logging.Logger,
    excluded_reasons: List[Dict[str, Any]],
    total_processed: int,
    total_valid: int
) -> None:
    """
    Logs excluded subjects and processing counts to the file and console.
    
    Args:
        logger: The configured logger instance.
        excluded_reasons: List of dicts with keys 'subject_id' and 'reason'.
        total_processed: Total number of subjects attempted.
        total_valid: Number of subjects that passed all filters.
    """
    logger.info("=== PROCESSING SUMMARY ===")
    logger.info(f"Total subjects processed: {total_processed}")
    logger.info(f"Total valid subjects: {total_valid}")
    logger.info(f"Total excluded subjects: {len(excluded_reasons)}")
    
    if excluded_reasons:
        logger.info("=== EXCLUDED SUBJECTS DETAILS ===")
        for entry in excluded_reasons:
            subject_id = entry.get('subject_id', 'unknown')
            reason = entry.get('reason', 'unknown')
            logger.warning(f"Excluded: {subject_id} - Reason: {reason}")
    else:
        logger.info("No subjects were excluded.")
    
    logger.info("=== END SUMMARY ===")

def save_exclusion_report(
    output_path: str,
    excluded_reasons: List[Dict[str, Any]],
    total_processed: int,
    total_valid: int
) -> None:
    """
    Saves a structured JSON report of excluded subjects and counts.
    
    Args:
        output_path: Path to the output JSON file.
        excluded_reasons: List of dicts with 'subject_id' and 'reason'.
        total_processed: Total number of subjects attempted.
        total_valid: Number of subjects that passed all filters.
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_processed": total_processed,
            "total_valid": total_valid,
            "total_excluded": len(excluded_reasons)
        },
        "excluded_subjects": excluded_reasons
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

def main():
    """
    Main entry point for the logging module.
    This is primarily used to demonstrate the logging setup or run as a standalone
    utility if needed. In the pipeline, the functions are called directly.
    """
    logger = setup_processing_logger()
    logger.info("Logging module initialized.")
    
    # Example usage (not executed in production unless called explicitly)
    if __name__ == "__main__":
        # This block is for testing the logging setup independently
        logger.info("Test log message")
        logger.warning("Test warning message")
        logger.error("Test error message")

if __name__ == "__main__":
    main()
