"""
Error handling utilities for the LLMXive automated science pipeline.

This module provides specialized error handlers for resource constraints,
specifically memory errors encountered during quantization and large model operations.
"""

import logging
from typing import Tuple

# Configure logger for this module
logger = logging.getLogger(__name__)

def handle_memory_error(e: MemoryError) -> Tuple[bool, str]:
    """
    Handle a MemoryError encountered during quantization or generation.
    
    This function logs the error with the specific message "Quantization Failure"
    as required by FR-008 and returns a skip flag to allow the pipeline to
    gracefully continue with other quantization levels or prompts.
    
    Args:
        e: The MemoryError exception instance.
        
    Returns:
        A tuple containing:
        - skip_flag (bool): True indicating the current operation should be skipped.
        - message (str): A descriptive log message "Quantization Failure".
        
    Example:
        try:
            perform_quantization()
        except MemoryError as err:
            should_skip, msg = handle_memory_error(err)
            if should_skip:
                logger.warning(msg)
                return None
    """
    message = "Quantization Failure"
    logger.error(f"{message}: {str(e)}")
    return True, message