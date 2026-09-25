"""
Main orchestration and logging infrastructure for the llmXive pipeline.

This module provides functions to manage the pipeline lifecycle, log start/end
events, and persist data versioning information to data_version.json.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from src.config import get_project_root, get_data_processed_path
from src.data.schema import (
    DataVersionFile,
    create_empty_data_version,
    save_data_version_to_file,
    load_data_version_from_file,
)
import logging

# Configure module logger
logger = logging.getLogger(__name__)


def ensure_data_directory() -> Path:
    """
    Ensure the data directory exists.
    
    Returns:
        Path: The path to the data directory.
    """
    data_dir = get_project_root() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_data_version_path() -> Path:
    """
    Get the path to the data_version.json file.
    
    Returns:
        Path: The full path to data_version.json.
    """
    return ensure_data_directory() / "data_version.json"


def load_data_version() -> Dict[str, Any]:
    """
    Load the existing data_version.json or return an empty structure if it doesn't exist.
    
    Returns:
        Dict[str, Any]: The loaded data version dictionary.
    """
    version_path = get_data_version_path()
    if version_path.exists():
        with open(version_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return create_empty_data_version()


def save_data_version(version_data: Dict[str, Any]) -> None:
    """
    Save the data version dictionary to data_version.json.
    
    Args:
        version_data: The dictionary containing version information.
    """
    version_path = get_data_version_path()
    save_data_version_to_file(version_data, version_path)
    logger.info(f"Data version saved to {version_path}")


def log_data_version(source_url: str, checksum_sha256: str, timestamp: Optional[str] = None) -> None:
    """
    Log data version information to data_version.json.
    
    This function appends a new entry to the 'files' list in data_version.json
    with the provided source URL, checksum, and timestamp.
    
    Args:
        source_url: The URL from which the data was fetched.
        checksum_sha256: The SHA256 checksum of the downloaded file.
        timestamp: Optional timestamp string. If None, current UTC time is used.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    
    version_data = load_data_version()
    
    new_entry = {
        "source_url": source_url,
        "checksum_sha256": checksum_sha256,
        "timestamp": timestamp,
    }
    
    version_data["files"].append(new_entry)
    
    # Update the overall timestamp of the version file
    version_data["timestamp"] = timestamp
    
    save_data_version(version_data)
    logger.info(f"Logged data version for {source_url}")


def log_pipeline_start(pipeline_name: str) -> Dict[str, Any]:
    """
    Log the start of a pipeline run.
    
    Args:
        pipeline_name: The name of the pipeline being started.
        
    Returns:
        Dict[str, Any]: Metadata about the start event.
    """
    start_time = time.time()
    timestamp = datetime.now(timezone.utc).isoformat()
    
    logger.info(f"Pipeline '{pipeline_name}' started at {timestamp}")
    
    return {
        "pipeline_name": pipeline_name,
        "start_time": start_time,
        "timestamp": timestamp,
    }


def log_pipeline_end(pipeline_name: str, start_info: Dict[str, Any], success: bool = True) -> None:
    """
    Log the end of a pipeline run.
    
    Args:
        pipeline_name: The name of the pipeline that ended.
        start_info: The metadata returned by log_pipeline_start.
        success: Whether the pipeline completed successfully.
    """
    end_time = time.time()
    duration = end_time - start_info["start_time"]
    timestamp = datetime.now(timezone.utc).isoformat()
    
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"Pipeline '{pipeline_name}' {status} at {timestamp} (duration: {duration:.2f}s)")


def main() -> None:
    """
    Main entry point for the pipeline orchestration script.
    
    This function demonstrates the logging infrastructure by:
    1. Starting a pipeline run
    2. Logging a mock data version entry
    3. Ending the pipeline run
    """
    pipeline_name = "T007b_logging_demo"
    
    # Ensure data directory exists
    ensure_data_directory()
    
    # Log pipeline start
    start_info = log_pipeline_start(pipeline_name)
    
    try:
        # Demonstrate logging a data version entry
        # In a real scenario, this would be called after downloading data
        log_data_version(
            source_url="https://example.com/mock-data.csv",
            checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        logger.info("Logging infrastructure test completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during logging infrastructure test: {e}", exc_info=True)
        log_pipeline_end(pipeline_name, start_info, success=False)
        sys.exit(1)
    
    # Log pipeline end
    log_pipeline_end(pipeline_name, start_info, success=True)


if __name__ == "__main__":
    main()