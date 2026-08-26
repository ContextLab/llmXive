import logging
import os
import traceback
from typing import Dict, List, Optional, Tuple, Any, Callable
from functools import wraps
import numpy as np
import time

class CIFParseError(Exception):
    """Custom exception for CIF parsing failures."""
    pass

class MissingMetadataError(Exception):
    """Custom exception for missing metadata in CIF files."""
    pass

class DataValidationError(Exception):
    """Custom exception for data validation failures."""
    pass

def handle_corrupt_cif(cif_path: str, error: Exception) -> None:
    """Handle a corrupt CIF file by logging the error and raising a CIFParseError."""
    logging.error(f"Corrupt CIF file detected: {cif_path}. Error: {str(error)}")
    raise CIFParseError(f"Failed to parse CIF file {cif_path}: {str(error)}") from error

def validate_required_metadata(metadata: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate that all required metadata fields are present."""
    missing_fields = [field for field in required_fields if field not in metadata or metadata[field] is None]
    if missing_fields:
        raise MissingMetadataError(f"Missing required metadata fields: {missing_fields}")

def safe_cif_read(cif_path: str, parser_func: Callable, *args, **kwargs) -> Optional[Dict[str, Any]]:
    """Safely read a CIF file, handling errors gracefully."""
    try:
        return parser_func(cif_path, *args, **kwargs)
    except Exception as e:
        handle_corrupt_cif(cif_path, e)
        return None

def get_cif_metadata_summary(cif_path: str) -> Dict[str, Any]:
    """Extract a summary of metadata from a CIF file."""
    # Placeholder implementation - would use pymatgen or similar to parse CIF
    # This is a simplified version for demonstration
    summary = {
        'file_path': cif_path,
        'exists': os.path.exists(cif_path),
        'size_bytes': os.path.getsize(cif_path) if os.path.exists(cif_path) else 0
    }
    return summary

def log_processing_statistics(success_count: int, failure_count: int, total_count: Optional[int] = None, start_time: Optional[float] = None, end_time: Optional[float] = None) -> None:
    """
    Log processing statistics with flexible argument handling.
    
    Accepts various call signatures to maintain compatibility with different callers:
    - log_processing_statistics(success, failure)
    - log_processing_statistics(success, failure, total)
    - log_processing_statistics(success, failure, total, start_time, end_time)
    """
    # Handle different call signatures
    if total_count is None:
        # If only 2 args were passed, the third arg (total_count) might be None or not passed
        # In this case, calculate total from success + failure
        total_count = success_count + failure_count
        
    if start_time is None:
        start_time = time.time() - 3600  # Default to 1 hour ago if not provided
        
    if end_time is None:
        end_time = time.time()  # Default to current time if not provided
    
    duration = end_time - start_time
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    logging.info(f"Processing Statistics:")
    logging.info(f"  Total files processed: {total_count}")
    logging.info(f"  Successful: {success_count} ({success_rate:.2f}%)")
    logging.info(f"  Failed: {failure_count}")
    logging.info(f"  Duration: {duration:.2f} seconds")
    
    if success_count > 0:
        avg_time_per_file = duration / success_count
        logging.info(f"  Average time per successful file: {avg_time_per_file:.4f} seconds")

def error_handler(func: Callable) -> Callable:
    """Decorator to handle errors in CIF processing functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {str(e)}")
            traceback.print_exc()
            raise
    return wrapper
