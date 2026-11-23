import os
import traceback
from typing import Optional, Any
from logging_config import get_logger, log_pipeline_error

logger = get_logger()

def handle_corrupted_file(file_path: str, error_reason: str) -> Optional[Any]:
    """
    Handles corrupted or problematic files by logging the error and returning None.
    
    Args:
        file_path: Path to the problematic file.
        error_reason: Description of why the file is corrupted/problematic.
        
    Returns:
        None (always returns None to indicate failure for the caller to handle).
    """
    logger.error(f"File corrupted/problematic: {file_path}")
    logger.error(f"Reason: {error_reason}")
    log_pipeline_error(f"Corrupted file: {file_path} - {error_reason}")
    return None
