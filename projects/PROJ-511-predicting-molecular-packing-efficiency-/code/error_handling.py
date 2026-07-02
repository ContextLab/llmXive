"""
Error handling utilities for the molecular packing efficiency project.
"""
import logging
import os
from typing import Dict, List, Optional, Tuple, Any, Callable
from functools import wraps
import traceback
from utils import setup_logging

# Setup logging
logger = setup_logging(__name__)

class CIFParseError(Exception):
    """Error raised when CIF parsing fails."""
    pass

class MissingMetadataError(Exception):
    """Error raised when required metadata is missing."""
    pass

class DataValidationError(Exception):
    """Error raised when data validation fails."""
    pass

def handle_corrupt_cif(cif_path: str, error: Exception) -> bool:
    """
    Handle a corrupt CIF file.
    
    Args:
        cif_path: Path to the corrupt CIF file
        error: The exception that occurred
        
    Returns:
        True if the file should be skipped, False otherwise
    """
    logger.error(f"Corrupt CIF file {cif_path}: {error}")
    # Remove the corrupt file
    try:
        if os.path.exists(cif_path):
            os.remove(cif_path)
    except Exception as e:
        logger.warning(f"Failed to remove corrupt file {cif_path}: {e}")
    return True

def validate_required_metadata(metadata: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validate that required metadata fields are present.
    
    Args:
        metadata: Metadata dictionary
        required_fields: List of required field names
        
    Returns:
        True if all required fields are present, False otherwise
    """
    missing_fields = [field for field in required_fields if field not in metadata or metadata[field] is None]
    if missing_fields:
        logger.warning(f"Missing required metadata fields: {missing_fields}")
        return False
    return True

def safe_cif_read(cif_path: str) -> Optional[str]:
    """
    Safely read a CIF file.
    
    Args:
        cif_path: Path to the CIF file
        
    Returns:
        CIF content as string, or None if reading fails
    """
    try:
        with open(cif_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read CIF file {cif_path}: {e}")
        return None

def get_cif_metadata_summary(cif_content: str) -> Dict[str, Any]:
    """
    Extract a summary of metadata from CIF content.
    
    Args:
        cif_content: CIF file content
        
    Returns:
        Dictionary of metadata summary
    """
    metadata = {}
    
    # Extract common metadata fields
    metadata_fields = [
        '_cell_length_a', '_cell_length_b', '_cell_length_c',
        '_cell_angle_alpha', '_cell_angle_beta', '_cell_angle_gamma',
        '_chemical_formula_sum', '_space_group_name_H-M_alt',
        '_exptl_crystal_density_diffrn', '_reflns_number_total'
    ]
    
    for field in metadata_fields:
        for line in cif_content.split('\n'):
            if line.startswith(field):
                value = line.split(None, 1)[1].strip() if len(line.split(None, 1)) > 1 else None
                metadata[field] = value
                break
    
    return metadata

def log_processing_statistics(stats: Dict[str, Any]):
    """
    Log processing statistics.
    
    Args:
        stats: Dictionary of statistics to log
    """
    logger.info("Processing statistics:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

def error_handler(func: Callable) -> Callable:
    """
    Decorator to handle errors in processing functions.
    
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
            logger.error(f"CIF parsing error in {func.__name__}: {e}")
            return None
        except MissingMetadataError as e:
            logger.error(f"Missing metadata error in {func.__name__}: {e}")
            return None
        except DataValidationError as e:
            logger.error(f"Data validation error in {func.__name__}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            logger.debug(traceback.format_exc())
            return None
    return wrapper
