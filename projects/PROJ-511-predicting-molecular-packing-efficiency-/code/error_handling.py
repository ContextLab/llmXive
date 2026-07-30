"""
Error handling utilities for CIF parsing and metadata validation.

This module provides robust error handling for corrupt CIF files and missing
metadata, ensuring the pipeline fails loudly with informative logs rather than
silently skipping or producing garbage data.
"""
import logging
import os
import traceback
from typing import Dict, List, Optional, Tuple, Any, Callable
from functools import wraps

from utils import setup_logging

# Configure logger
logger = logging.getLogger(__name__)


class CIFParseError(Exception):
    """Raised when a CIF file cannot be parsed due to corruption or format errors."""
    def __init__(self, message: str, cif_id: Optional[str] = None):
        self.cif_id = cif_id
        super().__init__(message)


class MissingMetadataError(Exception):
    """Raised when required metadata fields are missing from a CIF file."""
    def __init__(self, message: str, missing_fields: List[str], cif_id: Optional[str] = None):
        self.missing_fields = missing_fields
        self.cif_id = cif_id
        super().__init__(message)


class DataValidationError(Exception):
    """Raised when data fails validation against expected schema or constraints."""
    def __init__(self, message: str, details: Dict[str, Any], cif_id: Optional[str] = None):
        self.details = details
        self.cif_id = cif_id
        super().__init__(message)


def handle_corrupt_cif(cif_path: str, cif_id: str, error: Exception) -> Dict[str, Any]:
    """
    Handle a corrupt CIF file by logging the error and returning a failure record.

    Args:
        cif_path: Path to the corrupt CIF file
        cif_id: Crystallographic Open Database identifier
        error: The exception that occurred during parsing

    Returns:
        A dictionary with error details for downstream processing
    """
    error_msg = f"Corrupt CIF detected: {cif_id} at {cif_path}"
    logger.error(f"{error_msg}: {str(error)}")
    logger.debug(traceback.format_exc())

    return {
        "cif_id": cif_id,
        "status": "failed",
        "error_type": "corrupt_cif",
        "error_message": str(error),
        "skipped": True
    }


def validate_required_metadata(metadata: Dict[str, Any], required_fields: List[str], cif_id: str) -> Tuple[bool, List[str]]:
    """
    Validate that all required metadata fields are present and non-empty.

    Args:
        metadata: Dictionary of parsed CIF metadata
        required_fields: List of field names that must be present
        cif_id: Crystallographic Open Database identifier for logging

    Returns:
        Tuple of (is_valid, list_of_missing_fields)
    """
    missing = []
    for field in required_fields:
        value = metadata.get(field)
        if value is None or value == "" or (isinstance(value, str) and value.strip() == ""):
            missing.append(field)

    if missing:
        error = MissingMetadataError(
            f"Missing required metadata for {cif_id}",
            missing_fields=missing,
            cif_id=cif_id
        )
        logger.error(f"Missing metadata for {cif_id}: {missing}")
        return False, missing

    return True, []


def safe_cif_read(cif_path: str, cif_id: str, parser_func: Callable) -> Optional[Dict[str, Any]]:
    """
    Safely read and parse a CIF file, catching and logging all errors.

    Args:
        cif_path: Path to the CIF file
        cif_id: Crystallographic Open Database identifier
        parser_func: Function to call to parse the CIF (e.g., parse_cif_file)

    Returns:
        Parsed data dictionary if successful, None if failed
    """
    try:
        if not os.path.exists(cif_path):
            raise FileNotFoundError(f"CIF file not found: {cif_path}")

        if not os.path.isfile(cif_path):
            raise ValueError(f"Path is not a file: {cif_path}")

        result = parser_func(cif_path)

        if result is None:
            raise CIFParseError("Parser returned None", cif_id=cif_id)

        logger.debug(f"Successfully parsed {cif_id}")
        return result

    except CIFParseError:
        handle_corrupt_cif(cif_path, cif_id, CIFParseError("Parsing failed"))
        return None
    except MissingMetadataError as e:
        logger.error(f"Metadata validation failed for {cif_id}: {e.missing_fields}")
        return None
    except Exception as e:
        error_record = handle_corrupt_cif(cif_path, cif_id, e)
        logger.error(f"Unhandled exception for {cif_id}: {type(e).__name__}: {str(e)}")
        return None


def get_cif_metadata_summary(metadata: Dict[str, Any], cif_id: str) -> Dict[str, Any]:
    """
    Generate a summary of metadata for logging and validation purposes.

    Args:
        metadata: Parsed CIF metadata dictionary
        cif_id: Crystallographic Open Database identifier

    Returns:
        Summary dictionary with key fields and validation status
    """
    summary = {
        "cif_id": cif_id,
        "has_formula": "formula" in metadata and bool(metadata["formula"]),
        "has_cell_params": all(
            k in metadata and metadata[k] is not None
            for k in ["_cell_length_a", "_cell_length_b", "_cell_length_c",
                      "_cell_angle_alpha", "_cell_angle_beta", "_cell_angle_gamma"]
        ),
        "has_atoms": "_atom_site_label" in metadata and len(metadata["_atom_site_label"]) > 0,
        "atom_count": len(metadata.get("_atom_site_label", [])),
        "source": metadata.get("_database_codb_id", cif_id),
        "temperature": metadata.get("_exptl_crystal_growth_temperature", "N/A")
    }
    return summary


def log_processing_statistics(stats: Dict[str, Any]) -> None:
    """
    Log summary statistics of CIF processing.

    Args:
        stats: Dictionary with keys: total, successful, failed, skipped
    """
    total = stats.get("total", 0)
    successful = stats.get("successful", 0)
    failed = stats.get("failed", 0)
    skipped = stats.get("skipped", 0)

    logger.info(f"Processing Statistics: Total={total}, Success={successful}, "
                f"Failed={failed}, Skipped={skipped}")

    if total > 0:
        success_rate = (successful / total) * 100
        logger.info(f"Success rate: {success_rate:.2f}%")

    if failed > 0:
        logger.warning(f"{failed} CIFs failed to parse. Check logs for details.")


class error_handler:
    """
    Context manager for handling errors in a block of code.

    Usage:
        with error_handler(cif_id="12345"):
            process_data()
    """
    def __init__(self, cif_id: str, context: str = "processing"):
        self.cif_id = cif_id
        self.context = context
        self.errors: List[Dict[str, Any]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            error_record = {
                "cif_id": self.cif_id,
                "context": self.context,
                "error_type": exc_type.__name__,
                "error_message": str(exc_val),
                "traceback": traceback.format_exc()
            }
            self.errors.append(error_record)
            logger.error(f"Error in {self.context} for {self.cif_id}: {error_record['error_message']}")
            # Do not suppress the exception - let it propagate
            return False
        return True