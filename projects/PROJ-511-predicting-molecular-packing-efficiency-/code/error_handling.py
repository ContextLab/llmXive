"""
Error handling utilities for the molecular packing efficiency pipeline.

This module provides robust error handling for:
- Corrupt CIF files (parsing failures, structural inconsistencies)
- Missing metadata (unit cell parameters, symmetry info, chemical composition)
- Data validation failures against expected schemas

Designed to work with the existing utils.py logging infrastructure.
"""
import logging
import os
from typing import Dict, List, Optional, Tuple, Any, Callable
from functools import wraps
import traceback

from utils import setup_logging

# Initialize logger for this module
logger = setup_logging(__name__)


class CIFParseError(Exception):
    """Raised when a CIF file cannot be parsed or is structurally corrupt."""
    def __init__(self, message: str, filepath: str, details: Optional[Dict] = None):
        super().__init__(message)
        self.filepath = filepath
        self.details = details or {}
        self.message = message

class MissingMetadataError(Exception):
    """Raised when required metadata is missing from a CIF file."""
    def __init__(self, message: str, filepath: str, missing_fields: List[str]):
        super().__init__(message)
        self.filepath = filepath
        self.missing_fields = missing_fields
        self.message = message

class DataValidationError(Exception):
    """Raised when data fails schema validation."""
    def __init__(self, message: str, filepath: str, validation_errors: List[str]):
        super().__init__(message)
        self.filepath = filepath
        self.validation_errors = validation_errors
        self.message = message


def handle_corrupt_cif(func: Callable) -> Callable:
    """
    Decorator to handle corrupt CIF file parsing with graceful degradation.

    Catches parsing exceptions and logs them with file context, allowing
    the pipeline to continue processing other files.

    Args:
        func: Function that parses CIF files

    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(filepath: str, *args, **kwargs) -> Tuple[Optional[Any], bool]:
        try:
            result = func(filepath, *args, **kwargs)
            return result, True
        except CIFParseError as e:
            logger.warning(f"Corrupt CIF detected: {e.filepath} - {e.message}")
            logger.debug(f"CIF parse details: {e.details}")
            return None, False
        except Exception as e:
            logger.error(f"Unexpected error parsing CIF {filepath}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None, False
    return wrapper


def validate_required_metadata(
    filepath: str,
    required_fields: List[str],
    cif_data: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate that all required metadata fields are present in CIF data.

    Args:
        filepath: Path to the CIF file (for error reporting)
        required_fields: List of field names that must be present
        cif_data: Dictionary containing parsed CIF data

    Returns:
        Tuple of (is_valid, list_of_missing_fields)
    """
    missing_fields = []
    for field in required_fields:
        # Handle nested field access (e.g., "_cell.length_a")
        if '.' in field:
            parts = field.split('.')
            current = cif_data
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    current = None
                    break
            if current is None:
                missing_fields.append(field)
        else:
            if field not in cif_data or cif_data[field] is None:
                missing_fields.append(field)

    is_valid = len(missing_fields) == 0
    if not is_valid:
        logger.error(f"Missing metadata in {filepath}: {missing_fields}")
        raise MissingMetadataError(
            f"Required metadata missing",
            filepath,
            missing_fields
        )

    return is_valid, missing_fields


def safe_cif_read(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Safely read a CIF file with comprehensive error handling.

    Args:
        filepath: Path to the CIF file

    Returns:
        Parsed CIF data as dictionary, or None if file is corrupt/invalid
    """
    if not os.path.exists(filepath):
        logger.error(f"CIF file not found: {filepath}")
        return None

    try:
        # Attempt to read the file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            logger.warning(f"Empty CIF file: {filepath}")
            return None

        # Try to parse using ciflib or manual parsing
        try:
            import ciflib
            from io import StringIO
            cif_file = ciflib.CifFile.read(StringIO(content))
            # Extract data blocks
            data_blocks = {}
            for block_name, block_data in cif_file.items():
                data_blocks[block_name] = dict(block_data)
            return data_blocks
        except ImportError:
            # Fallback to manual parsing if ciflib not available
            logger.debug(f"ciflib not available, attempting manual parse for {filepath}")
            return _manual_cif_parse(filepath)
        except Exception as e:
            raise CIFParseError(
                f"Failed to parse CIF structure: {str(e)}",
                filepath,
                {"error_type": type(e).__name__}
            )

    except UnicodeDecodeError as e:
        logger.error(f"Encoding error in CIF {filepath}: {str(e)}")
        return None
    except IOError as e:
        logger.error(f"IO error reading CIF {filepath}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading CIF {filepath}: {str(e)}")
        return None


def _manual_cif_parse(filepath: str) -> Dict[str, Any]:
    """
    Manual CIF parser as fallback when ciflib is unavailable.

    Handles basic CIF format with key-value pairs and data blocks.
    """
    parsed_data = {}
    current_block = None

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Data block header
            if line.startswith('data_'):
                current_block = line[5:].strip()
                parsed_data[current_block] = {}
                continue

            # Loop structure (simplified handling)
            if line.startswith('loop_'):
                # Skip loop for now, focus on key-value pairs
                continue

            # Key-value pair
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip("'\"")
                if current_block:
                    parsed_data[current_block][key] = value
                else:
                    parsed_data[key] = value
            elif line.startswith('_'):
                # Simple key-value without equals sign
                parts = line.split(None, 1)
                if len(parts) == 2:
                    key, value = parts
                    value = value.strip().strip("'\"")
                    if current_block:
                        parsed_data[current_block][key] = value
                    else:
                        parsed_data[key] = value

    return parsed_data


def get_cif_metadata_summary(cif_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract a summary of available metadata from parsed CIF data.

    Args:
        cif_data: Parsed CIF data dictionary

    Returns:
        Dictionary with metadata summary
    """
    summary = {
        'data_blocks': list(cif_data.keys()) if isinstance(cif_data, dict) else [],
        'total_fields': 0,
        'has_unit_cell': False,
        'has_symmetry': False,
        'has_chemical_formula': False,
        'missing_critical_fields': []
    }

    if not isinstance(cif_data, dict):
        return summary

    # Check first data block (usually the main one)
    main_block = None
    for block_name, block_data in cif_data.items():
        if isinstance(block_data, dict):
            main_block = block_data
            break

    if main_block:
        summary['total_fields'] = len(main_block)

        # Check for critical fields
        unit_cell_fields = [
            '_cell.length_a', '_cell.length_b', '_cell.length_c',
            '_cell.angle_alpha', '_cell.angle_beta', '_cell.angle_gamma'
        ]
        symmetry_fields = ['_symmetry.space_group_name_H-M', '_symmetry.Int_Tables_number']
        chemical_fields = ['_chemical_formula_sum', '_chemical_formula_structural']

        summary['has_unit_cell'] = any(field in main_block for field in unit_cell_fields)
        summary['has_symmetry'] = any(field in main_block for field in symmetry_fields)
        summary['has_chemical_formula'] = any(field in main_block for field in chemical_fields)

        # Identify missing critical fields
        all_critical = unit_cell_fields + symmetry_fields + chemical_fields
        summary['missing_critical_fields'] = [
            field for field in all_critical if field not in main_block
        ]

    return summary


def log_processing_statistics(
    total_files: int,
    successful_parses: int,
    corrupt_files: List[str],
    missing_metadata_files: List[str]
) -> None:
    """
    Log comprehensive processing statistics.

    Args:
        total_files: Total number of files attempted
        successful_parses: Number of successfully parsed files
        corrupt_files: List of corrupt file paths
        missing_metadata_files: List of files with missing metadata
    """
    success_rate = (successful_parses / total_files * 100) if total_files > 0 else 0

    logger.info("=" * 60)
    logger.info("CIF PROCESSING STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Total files processed: {total_files}")
    logger.info(f"Successful parses: {successful_parses} ({success_rate:.1f}%)")
    logger.info(f"Corrupt files: {len(corrupt_files)}")
    logger.info(f"Missing metadata: {len(missing_metadata_files)}")

    if corrupt_files:
        logger.warning("Corrupt files encountered:")
        for f in corrupt_files[:10]:  # Log first 10
            logger.warning(f"  - {f}")
        if len(corrupt_files) > 10:
            logger.warning(f"  ... and {len(corrupt_files) - 10} more")

    if missing_metadata_files:
        logger.warning("Files with missing metadata:")
        for f in missing_metadata_files[:10]:
            logger.warning(f"  - {f}")
        if len(missing_metadata_files) > 10:
            logger.warning(f"  ... and {len(missing_metadata_files) - 10} more")

    logger.info("=" * 60)