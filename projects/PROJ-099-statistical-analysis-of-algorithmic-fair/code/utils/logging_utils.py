"""
Logging utilities for the statistical analysis of algorithmic fairness pipeline.

This module provides functions for managing exclusion logs and other project logging
requirements. All logging follows the FR-008 disclaimer requirement where applicable.

Exclusion Log Format (logs/exclusion.log):
CSV with columns: timestamp, dataset_id, missing_variable_name, reason

This logging infrastructure supports traceability as required by FR-004.
"""
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

# Constants
EXCLUSION_LOG_PATH = Path("logs/exclusion.log")
CSV_HEADER = ["timestamp", "dataset_id", "missing_variable_name", "reason"]

# FR-008 Disclaimer
FR008_DISCLAIMER = (
    "Findings are associational only; no causal claims are made."
)

def init_exclusion_log() -> None:
    """
    Initialize the exclusion log file with CSV header.
    
    Creates the logs directory if it doesn't exist and writes the CSV header
    to the exclusion log file. This function is idempotent - calling it multiple
    times will not duplicate the header.
    
    Returns:
        None
    
    Side Effects:
        Creates logs/exclusion.log if it doesn't exist with CSV header.
    """
    # Ensure logs directory exists
    EXCLUSION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Only write header if file doesn't exist
    if not EXCLUSION_LOG_PATH.exists():
        with open(EXCLUSION_LOG_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)
    
    # Configure logging for the exclusion log
    logging.basicConfig(
        filename=str(EXCLUSION_LOG_PATH),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def log_exclusion(
    dataset_id: str,
    missing_variable_name: str,
    reason: str
) -> None:
    """
    Log an exclusion entry to the exclusion log file.
    
    Records when a dataset is excluded from analysis due to missing required
    variables. This supports traceability requirements (FR-004) and enables
    reproducibility of the analysis pipeline.
    
    Args:
        dataset_id: Unique identifier for the dataset being excluded.
        missing_variable_name: Name of the missing variable that caused exclusion.
        reason: Detailed explanation of why the variable is missing or why
               the dataset is being excluded.
    
    Returns:
        None
    
    Side Effects:
        Appends a row to logs/exclusion.log with timestamp and exclusion details.
    
    Note:
        All exclusion logs are associational in nature per FR-008:
        {FR008_DISCLAIMER}
    """
    # Ensure log file is initialized
    init_exclusion_log()
    
    # Generate timestamp
    timestamp = datetime.now().isoformat()
    
    # Append to CSV
    with open(EXCLUSION_LOG_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, dataset_id, missing_variable_name, reason])

def log_warning(
    message: str,
    dataset_id: Optional[str] = None,
    variable_name: Optional[str] = None
) -> None:
    """
    Log a warning message to the exclusion log.
    
    Provides a flexible logging interface for warnings that may not result
    in dataset exclusion but should be recorded for audit purposes.
    
    Args:
        message: Warning message to log.
        dataset_id: Optional dataset identifier for context.
        variable_name: Optional variable name for context.
    
    Returns:
        None
    
    Side Effects:
        Appends a warning entry to logs/exclusion.log.
    """
    init_exclusion_log()
    
    timestamp = datetime.now().isoformat()
    dataset_id = dataset_id or "N/A"
    variable_name = variable_name or "N/A"
    
    with open(EXCLUSION_LOG_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, dataset_id, variable_name, f"WARNING: {message}"])

def read_exclusion_log() -> list:
    """
    Read all entries from the exclusion log file.
    
    Returns:
        List of dictionaries, where each dictionary represents a row in the
        exclusion log with keys matching the CSV header columns.
    
    Raises:
        FileNotFoundError: If the exclusion log file doesn't exist.
    """
    if not EXCLUSION_LOG_PATH.exists():
        return []
    
    entries = []
    with open(EXCLUSION_LOG_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)
    
    return entries

def get_exclusion_count() -> int:
    """
    Get the total number of exclusion entries in the log.
    
    Returns:
        Integer count of exclusion entries (excluding header row).
    """
    return len(read_exclusion_log())

def clear_exclusion_log() -> None:
    """
    Clear all entries from the exclusion log (keeps header).
    
    Useful for testing or resetting the log between pipeline runs.
    
    Returns:
        None
    
    Side Effects:
        Truncates logs/exclusion.log to contain only the CSV header.
    """
    with open(EXCLUSION_LOG_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
