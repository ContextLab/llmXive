"""
Error handling module for gravitational wave data processing.

Provides custom exceptions and utility functions for handling
missing or corrupted noise files in a graceful manner.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import hashlib
import json

# Configure logging
logger = logging.getLogger(__name__)

class NoiseFileError(Exception):
    """Base exception for noise file related errors."""
    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(message)
        self.file_path = file_path

class MissingNoiseFileError(NoiseFileError):
    """Exception raised when a noise file is not found."""
    def __init__(self, file_path: str, search_paths: Optional[list] = None):
        self.search_paths = search_paths or []
        msg = f"Noise file not found: {file_path}"
        if self.search_paths:
            msg += f"\nSearched in: {self.search_paths}"
        super().__init__(msg, file_path)

class CorruptedNoiseFileError(NoiseFileError):
    """Exception raised when a noise file is corrupted or invalid."""
    def __init__(self, file_path: str, reason: str, expected_checksum: Optional[str] = None, actual_checksum: Optional[str] = None):
        self.reason = reason
        self.expected_checksum = expected_checksum
        self.actual_checksum = actual_checksum
        msg = f"Corrupted noise file: {file_path}\nReason: {reason}"
        if expected_checksum and actual_checksum:
            msg += f"\nExpected checksum: {expected_checksum}\nActual checksum: {actual_checksum}"
        super().__init__(msg, file_path)

class NoiseFileAccessError(NoiseFileError):
    """Exception raised when there are permission or access issues."""
    def __init__(self, file_path: str, reason: str):
        msg = f"Cannot access noise file: {file_path}\nReason: {reason}"
        super().__init__(msg, file_path)

def get_noise_file_directories() -> list:
    """
    Returns a list of directories where noise files are expected.
    
    Returns:
        list: List of Path objects representing search directories.
    """
    base_dir = Path(os.getenv('PROJECT_ROOT', '.'))
    # Standard locations based on project structure
    search_dirs = [
        base_dir / 'data' / 'raw' / 'noise',
        base_dir / 'data' / 'processed' / 'noise',
        base_dir / 'data' / 'raw',
        base_dir / 'data' / 'processed',
    ]
    # Filter to existing directories
    return [d for d in search_dirs if d.exists()]

def find_noise_file(filename: str) -> Optional[Path]:
    """
    Search for a noise file in standard directories.
    
    Args:
        filename: Name of the noise file to find.
        
    Returns:
        Path to the file if found, None otherwise.
    """
    search_dirs = get_noise_file_directories()
    for directory in search_dirs:
        candidate = directory / filename
        if candidate.exists() and candidate.is_file():
            logger.info(f"Found noise file at: {candidate}")
            return candidate
    
    logger.warning(f"Noise file '{filename}' not found in any standard location.")
    return None

def calculate_file_checksum(file_path: str) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal checksum string.
        
    Raises:
        NoiseFileAccessError: If file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise MissingNoiseFileError(str(path))
    
    try:
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except PermissionError as e:
        raise NoiseFileAccessError(str(path), f"Permission denied: {e}")
    except Exception as e:
        raise NoiseFileAccessError(str(path), f"Error reading file: {e}")

def validate_noise_file(file_path: str, expected_checksum: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validate a noise file for integrity and format.
    
    Args:
        file_path: Path to the noise file.
        expected_checksum: Optional expected SHA-256 checksum.
        
    Returns:
        Tuple of (is_valid, message)
        
    Raises:
        MissingNoiseFileError: If file does not exist.
        CorruptedNoiseFileError: If file is invalid.
    """
    path = Path(file_path)
    
    # Check existence
    if not path.exists():
        raise MissingNoiseFileError(str(path))
    
    # Check readability
    try:
        if not os.access(path, os.R_OK):
            raise NoiseFileAccessError(str(path), "File is not readable")
    except Exception as e:
        raise NoiseFileAccessError(str(path), str(e))
    
    # Check file size (should be non-zero)
    size = path.stat().st_size
    if size == 0:
        raise CorruptedNoiseFileError(str(path), "File is empty")
    
    # Validate format based on extension
    suffix = path.suffix.lower()
    if suffix in ['.h5', '.hdf5']:
        try:
            import h5py
            with h5py.File(path, 'r') as f:
                # Check for expected datasets
                if 'data' not in f and 'timeseries' not in f and 'strain' not in f:
                    raise CorruptedNoiseFileError(
                        str(path), 
                        "HDF5 file missing expected data dataset (data, timeseries, or strain)"
                    )
        except ImportError:
            # h5py not available, skip HDF5 specific checks
            logger.warning("h5py not available, skipping HDF5 validation")
        except Exception as e:
            raise CorruptedNoiseFileError(str(path), f"HDF5 validation failed: {e}")
    elif suffix == '.txt' or suffix == '.csv':
        # Basic text file check
        try:
            with open(path, 'r') as f:
                first_line = f.readline()
                if not first_line.strip():
                    raise CorruptedNoiseFileError(str(path), "Text file is empty or invalid")
        except Exception as e:
            raise CorruptedNoiseFileError(str(path), f"Text file validation failed: {e}")
    else:
        logger.warning(f"Unknown file format: {suffix}, skipping format validation")
    
    # Checksum validation if provided
    if expected_checksum:
        actual_checksum = calculate_file_checksum(str(path))
        if actual_checksum != expected_checksum:
            raise CorruptedNoiseFileError(
                str(path), 
                "Checksum mismatch",
                expected_checksum=expected_checksum,
                actual_checksum=actual_checksum
            )
    
    return True, "File validation successful"

def load_noise_file_with_fallback(file_path: str, expected_checksum: Optional[str] = None) -> Tuple[Optional[Path], Optional[Exception]]:
    """
    Attempt to load a noise file with validation.
    
    This function attempts to load the file at the specified path.
    If the file is missing or corrupted, it returns None and the
    exception that occurred, allowing the caller to handle it gracefully.
    
    Args:
        file_path: Path to the noise file.
        expected_checksum: Optional expected checksum for validation.
        
    Returns:
        Tuple of (Path if valid, Exception if error)
    """
    try:
        # Try to find the file if exact path not provided
        path = Path(file_path)
        if not path.exists():
            found_path = find_noise_file(path.name)
            if found_path:
                path = found_path
            else:
                raise MissingNoiseFileError(file_path, get_noise_file_directories())
        
        # Validate the file
        is_valid, msg = validate_noise_file(str(path), expected_checksum)
        if is_valid:
            logger.info(f"Noise file validated successfully: {path}")
            return path, None
        else:
            return None, CorruptedNoiseFileError(str(path), msg)
            
    except NoiseFileError as e:
        logger.error(f"Noise file error: {e}")
        return None, e
    except Exception as e:
        logger.error(f"Unexpected error loading noise file: {e}")
        return None, e

def handle_noise_file_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Handle noise file errors gracefully and return structured error information.
    
    Args:
        error: The exception that occurred.
        context: Optional context dictionary with additional information.
        
    Returns:
        Dictionary with error details suitable for logging or reporting.
    """
    error_info = {
        "success": False,
        "error_type": type(error).__name__,
        "message": str(error),
        "file_path": getattr(error, 'file_path', None),
        "context": context or {}
    }
    
    if isinstance(error, MissingNoiseFileError):
        error_info["error_category"] = "missing"
        error_info["search_paths"] = getattr(error, 'search_paths', [])
        logger.critical(f"Missing noise file: {error_info['message']}")
        
    elif isinstance(error, CorruptedNoiseFileError):
        error_info["error_category"] = "corrupted"
        error_info["reason"] = getattr(error, 'reason', 'Unknown')
        logger.critical(f"Corrupted noise file: {error_info['message']}")
        
    elif isinstance(error, NoiseFileAccessError):
        error_info["error_category"] = "access"
        logger.critical(f"Access error for noise file: {error_info['message']}")
        
    else:
        error_info["error_category"] = "unknown"
        logger.error(f"Unexpected noise file error: {error_info['message']}")
    
    return error_info

def ensure_noise_file_availability(file_path: str, expected_checksum: Optional[str] = None) -> Path:
    """
    Ensure a noise file is available and valid. Raises on failure.
    
    This is the primary entry point for ensuring noise file availability.
    It will attempt to find the file if not at the exact path, validate it,
    and raise a specific exception if validation fails.
    
    Args:
        file_path: Path to the noise file.
        expected_checksum: Optional expected checksum.
        
    Returns:
        Path to the validated noise file.
        
    Raises:
        MissingNoiseFileError: If file cannot be found.
        CorruptedNoiseFileError: If file is invalid.
        NoiseFileAccessError: If file cannot be accessed.
    """
    path = Path(file_path)
    
    # If path doesn't exist, try to find it
    if not path.exists():
        found_path = find_noise_file(path.name)
        if found_path:
            path = found_path
        else:
            raise MissingNoiseFileError(file_path, get_noise_file_directories())
    
    # Validate and return
    is_valid, msg = validate_noise_file(str(path), expected_checksum)
    if not is_valid:
        # This will raise an exception if validation fails
        validate_noise_file(str(path), expected_checksum)
    
    logger.info(f"Noise file confirmed available: {path}")
    return path