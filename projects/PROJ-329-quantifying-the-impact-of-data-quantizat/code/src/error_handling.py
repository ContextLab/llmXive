"""
Error handling module for noise file management.

Provides robust error handling for missing or corrupted noise files,
ensuring the pipeline fails gracefully with clear error messages.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import hashlib
import json
import struct

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NoiseFileError(Exception):
    """Base exception for noise file errors."""
    pass


class MissingNoiseFileError(NoiseFileError):
    """Raised when a required noise file is not found."""
    pass


class CorruptedNoiseFileError(NoiseFileError):
    """Raised when a noise file is corrupted or invalid."""
    pass


class NoiseFileAccessError(NoiseFileError):
    """Raised when there is an issue accessing a noise file."""
    pass


def get_noise_file_directories() -> list:
    """
    Get the list of directories where noise files are expected.
    
    Returns:
        List of Path objects pointing to noise file directories.
    """
    base_dir = Path(__file__).parent.parent.parent
    return [
        base_dir / "data" / "raw" / "noise",
        base_dir / "data" / "processed" / "noise"
    ]


def find_noise_file(file_name: str, search_dirs: Optional[list] = None) -> Optional[Path]:
    """
    Search for a noise file in the specified directories.
    
    Args:
        file_name: Name of the noise file to find.
        search_dirs: List of directories to search. If None, uses default directories.
        
    Returns:
        Path to the noise file if found, None otherwise.
    """
    if search_dirs is None:
        search_dirs = get_noise_file_directories()
    
    for directory in search_dirs:
        if not directory.exists():
            logger.debug(f"Directory does not exist: {directory}")
            continue
        
        file_path = directory / file_name
        if file_path.exists() and file_path.is_file():
            logger.info(f"Found noise file: {file_path}")
            return file_path
    
    logger.warning(f"Noise file not found: {file_name} in {search_dirs}")
    return None


def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file for integrity verification.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal checksum string.
        
    Raises:
        NoiseFileAccessError: If the file cannot be read.
    """
    try:
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except PermissionError:
        raise NoiseFileAccessError(f"Permission denied reading file: {file_path}")
    except IOError as e:
        raise NoiseFileAccessError(f"IO error reading file {file_path}: {e}")


def validate_noise_file(file_path: Path, expected_checksum: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validate a noise file for integrity and format.
    
    Args:
        file_path: Path to the noise file.
        expected_checksum: Optional expected checksum for verification.
        
    Returns:
        Tuple of (is_valid, message)
        
    Raises:
        MissingNoiseFileError: If the file does not exist.
        CorruptedNoiseFileError: If the file is corrupted or invalid.
    """
    if not file_path.exists():
        raise MissingNoiseFileError(f"Noise file does not exist: {file_path}")
    
    if not file_path.is_file():
        raise CorruptedNoiseFileError(f"Path is not a file: {file_path}")
    
    try:
        # Check file size (should be non-zero)
        file_size = file_path.stat().st_size
        if file_size == 0:
            raise CorruptedNoiseFileError(f"Noise file is empty: {file_path}")
        
        # Attempt to read the file header to verify format
        # Assuming HDF5 format (common for GW data)
        with open(file_path, 'rb') as f:
            header = f.read(8)
            
            # HDF5 files start with specific magic bytes
            if header[:4] == b'\x89HDF':
                logger.debug(f"Valid HDF5 file detected: {file_path}")
                # Additional HDF5 validation could be done here
            elif file_path.suffix == '.txt' or file_path.suffix == '.csv':
                # Text-based format, try to read first line
                f.seek(0)
                first_line = f.readline()
                if not first_line:
                    raise CorruptedNoiseFileError(f"Noise file appears empty or unreadable: {file_path}")
            else:
                # Unknown format, but file exists and has content
                logger.warning(f"Unknown file format for noise file: {file_path}")
        
        # Checksum verification if provided
        if expected_checksum:
            actual_checksum = calculate_file_checksum(file_path)
            if actual_checksum != expected_checksum:
                raise CorruptedNoiseFileError(
                    f"Checksum mismatch for {file_path}. "
                    f"Expected: {expected_checksum}, Got: {actual_checksum}"
                )
        
        return True, f"Noise file validated successfully: {file_path}"
        
    except Exception as e:
        if isinstance(e, (MissingNoiseFileError, CorruptedNoiseFileError, NoiseFileAccessError)):
            raise
        raise CorruptedNoiseFileError(f"Error validating noise file {file_path}: {e}")


def load_noise_file_with_fallback(file_name: str, expected_checksum: Optional[str] = None) -> Path:
    """
    Load a noise file with comprehensive error handling.
    
    This function attempts to find and validate a noise file, raising
    appropriate exceptions if it is missing or corrupted.
    
    Args:
        file_name: Name of the noise file.
        expected_checksum: Optional expected checksum for verification.
        
    Returns:
        Path to the validated noise file.
        
    Raises:
        MissingNoiseFileError: If the file is not found.
        CorruptedNoiseFileError: If the file is corrupted.
        NoiseFileAccessError: If there is an access issue.
    """
    file_path = find_noise_file(file_name)
    
    if file_path is None:
        raise MissingNoiseFileError(
            f"Noise file '{file_name}' not found in any of the configured directories. "
            f"Please ensure the file exists in data/raw/noise/ or data/processed/noise/"
        )
    
    # Validate the file
    is_valid, message = validate_noise_file(file_path, expected_checksum)
    if not is_valid:
        raise CorruptedNoiseFileError(f"Noise file validation failed: {message}")
    
    logger.info(f"Noise file ready for use: {file_path}")
    return file_path


def handle_noise_file_error(error: NoiseFileError) -> None:
    """
    Handle noise file errors with appropriate logging and user feedback.
    
    Args:
        error: The noise file error to handle.
    """
    if isinstance(error, MissingNoiseFileError):
        logger.error(f"MISSING NOISE FILE: {error}")
        logger.error("Action required: Download or generate the missing noise file.")
    elif isinstance(error, CorruptedNoiseFileError):
        logger.error(f"CORRUPTED NOISE FILE: {error}")
        logger.error("Action required: Re-download or regenerate the noise file.")
    elif isinstance(error, NoiseFileAccessError):
        logger.error(f"ACCESS ERROR: {error}")
        logger.error("Action required: Check file permissions and disk space.")
    else:
        logger.error(f"UNKNOWN NOISE FILE ERROR: {error}")
    
    # Re-raise the error to halt execution
    raise error


def ensure_noise_file_availability(file_name: str, expected_checksum: Optional[str] = None) -> Path:
    """
    Ensure a noise file is available and valid before proceeding.
    
    This is a convenience wrapper that combines finding, validating, and
    error handling for noise files.
    
    Args:
        file_name: Name of the noise file.
        expected_checksum: Optional expected checksum.
        
    Returns:
        Path to the validated noise file.
        
    Raises:
        NoiseFileError: If the file is missing, corrupted, or inaccessible.
    """
    try:
        return load_noise_file_with_fallback(file_name, expected_checksum)
    except NoiseFileError as e:
        handle_noise_file_error(e)
        # handle_noise_file_error re-raises, but for type safety:
        raise
    except Exception as e:
        logger.error(f"Unexpected error handling noise file: {e}")
        raise NoiseFileError(f"Unexpected error: {e}")