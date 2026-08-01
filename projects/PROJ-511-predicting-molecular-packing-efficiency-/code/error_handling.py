import logging
import os
import traceback
from typing import Dict, List, Optional, Tuple, Any, Callable
from functools import wraps
import numpy as np

logger = logging.getLogger(__name__)

class CIFParseError(Exception):
    """Exception raised for errors in CIF file parsing."""
    pass

class MissingMetadataError(Exception):
    """Exception raised when required metadata is missing."""
    pass

class DataValidationError(Exception):
    """Exception raised when data validation fails."""
    pass

def handle_corrupt_cif(file_path: str, error: Exception) -> Dict[str, Any]:
    """
    Handle a corrupt CIF file by logging the error and returning a failure record.
    
    Args:
        file_path: Path to the corrupt file
        error: The exception that occurred
        
    Returns:
        Dictionary indicating failure
    """
    logger.error(f"Corrupt CIF file detected: {file_path}")
    logger.error(f"Error details: {str(error)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return {
        'file_path': file_path,
        'status': 'failed',
        'error': str(error),
        'smiles': None,
        'metadata': None
    }

def validate_required_metadata(cif_data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validate that required metadata fields are present in CIF data.
    
    Args:
        cif_data: Parsed CIF data
        required_fields: List of required field names
        
    Returns:
        True if all required fields are present, False otherwise
    """
    missing_fields = []
    for field in required_fields:
        if field not in cif_data or cif_data[field] is None or cif_data[field] == '':
            missing_fields.append(field)
    
    if missing_fields:
        logger.warning(f"Missing required metadata fields: {missing_fields}")
        return False
    
    return True

def safe_cif_read(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Safely read a CIF file, handling errors gracefully.
    
    Args:
        file_path: Path to the CIF file
        
    Returns:
        Parsed CIF data or None if reading fails
    """
    try:
        from cif_loader import parse_cif_file
        return parse_cif_file(file_path)
    except Exception as e:
        logger.error(f"Failed to read CIF file {file_path}: {e}")
        return None

def get_cif_metadata_summary(cif_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a summary of key metadata from CIF data.
    
    Args:
        cif_data: Parsed CIF data
        
    Returns:
        Dictionary with metadata summary
    """
    summary = {}
    
    # Extract key metadata
    if '_chemical_formula_sum' in cif_data:
        summary['formula'] = cif_data['_chemical_formula_sum']
    if '_cell_length_a' in cif_data:
        summary['a'] = cif_data['_cell_length_a']
    if '_cell_length_b' in cif_data:
        summary['b'] = cif_data['_cell_length_b']
    if '_cell_length_c' in cif_data:
        summary['c'] = cif_data['_cell_length_c']
    if '_symmetry_space_group_name_H-M' in cif_data:
        summary['space_group'] = cif_data['_symmetry_space_group_name_H-M']
    if '_exptl_temperature' in cif_data:
        summary['temperature_K'] = cif_data['_exptl_temperature']
    
    return summary

def log_processing_statistics(processed_count: int, failed_count: int, 
                              total_count: int, start_time: float, 
                              end_time: float) -> None:
    """
    Log processing statistics.
    
    Args:
        processed_count: Number of successfully processed files
        failed_count: Number of failed files
        total_count: Total number of files attempted
        start_time: Start timestamp
        end_time: End timestamp
    """
    duration = end_time - start_time
    success_rate = (processed_count / total_count * 100) if total_count > 0 else 0
    
    logger.info(f"Processing Statistics:")
    logger.info(f"  Total files: {total_count}")
    logger.info(f"  Processed: {processed_count}")
    logger.info(f"  Failed: {failed_count}")
    logger.info(f"  Success rate: {success_rate:.2f}%")
    logger.info(f"  Duration: {duration:.2f} seconds")
    logger.info(f"  Average time per file: {duration/total_count:.2f} seconds" if total_count > 0 else "")

def error_handler(func: Callable) -> Callable:
    """
    Decorator to handle errors in CIF processing functions.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CIFParseError as e:
            logger.error(f"CIF Parse Error in {func.__name__}: {e}")
            return None
        except MissingMetadataError as e:
            logger.error(f"Missing Metadata Error in {func.__name__}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            logger.error(traceback.format_exc())
            return None
    return wrapper
