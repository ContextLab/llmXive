"""
Utility functions for the llmXive research pipeline.
Includes error handling frameworks for corrupted files and missing metadata.
"""

import os
import traceback
from typing import Optional, Any

from logging_config import get_logger, log_pipeline_error

logger = get_logger(__name__)


def handle_corrupted_file(
    file_path: str,
    error_type: str = "unknown",
    error_msg: Optional[str] = None,
    return_value: Any = None
) -> Optional[Any]:
    """
    Handles corrupted file errors by logging the incident and returning a safe fallback.

    This function is designed to be used in data processing pipelines where a file
    might be unreadable due to corruption, missing metadata, or format issues.
    Instead of crashing the pipeline, it logs the error and allows execution to
    continue (or skip the specific file) by returning a safe value (default: None).

    Args:
        file_path (str): The path to the corrupted or problematic file.
        error_type (str): Classification of the error. Expected values include:
            - "corrupted_media": File exists but is unreadable/invalid format.
            - "missing_metadata": File exists but lacks required metadata headers.
            - "io_error": General I/O failure (permission, disk full, etc.).
            - "unknown": Default fallback for unspecified errors.
        error_msg (str, optional): Specific error message from the exception.
        return_value (Any, optional): The value to return on failure. Defaults to None.

    Returns:
        Optional[Any]: The configured return_value (usually None) to indicate failure,
                       allowing the caller to handle the skip logic.

    Raises:
        None: This function catches exceptions and logs them; it does not re-raise.
    """
    if not file_path or not os.path.exists(file_path):
        error_type = "missing_file"
        error_msg = error_msg or f"File not found: {file_path}"
    elif error_type == "unknown" and error_msg is None:
        error_msg = f"Unexpected error processing file: {file_path}"

    # Construct a structured error message
    log_message = (
        f"File processing failed | Path: {file_path} | "
        f"Type: {error_type} | Message: {error_msg}"
    )

    # Log to the main logger
    logger.error(log_message)
    
    # Log to the pipeline error stream if available (from logging_config)
    try:
        log_pipeline_error(file_path, error_type, error_msg)
    except Exception as log_exc:
        # Fallback if logging_config setup is incomplete or fails
        logger.warning(f"Failed to log pipeline error event: {log_exc}")

    # Log full traceback if available in the calling context (optional debug)
    # Note: Since we don't have the exception object here, we log the context.
    logger.debug(f"Context for failure: {file_path}, {error_type}")

    return return_value