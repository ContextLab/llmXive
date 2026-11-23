"""
Error handling utilities for the molecular packing efficiency pipeline.
"""
import logging
import os
import traceback
from typing import Dict, List, Optional, Tuple, Any, Callable
from functools import wraps
import numpy as np

logger = logging.getLogger(__name__)

class CIFParseError(Exception):
    """Raised when a CIF file cannot be parsed."""
    pass

class MissingMetadataError(Exception):
    """Raised when required metadata is missing from a CIF file."""
    pass

class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass

def handle_corrupt_cif(file_path: str, error: Exception) -> None:
    """Log and handle a corrupt CIF file."""
    logger.error(f"Corrupt CIF file: {file_path}")
    logger.error(f"Error details: {str(error)}")
    raise CIFParseError(f"Failed to parse CIF file: {file_path}") from error

def validate_required_metadata(metadata: Dict[str, Any], required_keys: List[str]) -> None:
    """Validate that required metadata keys are present."""
    missing_keys = [key for key in required_keys if key not in metadata]
    if missing_keys:
        raise MissingMetadataError(f"Missing required metadata keys: {missing_keys}")

def safe_cif_read(func: Callable) -> Callable:
    """Decorator to safely read CIF files with error handling."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if len(args) > 0:
                file_path = str(args[0])
            else:
                file_path = "unknown"
            handle_corrupt_cif(file_path, e)
    return wrapper

def get_cif_metadata_summary(metadata: Dict[str, Any]) -> str:
    """Generate a summary string of CIF metadata."""
    summary_lines = []
    for key, value in metadata.items():
        if isinstance(value, (list, np.ndarray)):
            summary_lines.append(f"{key}: [{len(value)} items]")
        else:
            summary_lines.append(f"{key}: {value}")
    return "\n".join(summary_lines)

def log_processing_statistics(success: int, failure: int, total: Optional[int] = None, 
                              start_time: Optional[float] = None, end_time: Optional[float] = None) -> None:
    """
    Log processing statistics in a flexible format.
    
    Handles multiple call signatures:
    - log_processing_statistics(success, failure)
    - log_processing_statistics(success, failure, total)
    - log_processing_statistics(success, failure, total, start_time, end_time)
    """
    if total is None:
        total = success + failure
    
    rate = (success / total * 100) if total > 0 else 0.0
    
    logger.info(f"Processing Statistics:")
    logger.info(f"  Total: {total}")
    logger.info(f"  Success: {success}")
    logger.info(f"  Failure: {failure}")
    logger.info(f"  Success Rate: {rate:.2f}%")
    
    if start_time is not None and end_time is not None:
        duration = end_time - start_time
        logger.info(f"  Duration: {duration:.2f} seconds")
        if total > 0:
            per_second = total / duration
            logger.info(f"  Throughput: {per_second:.2f} items/second")