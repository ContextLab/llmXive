"""
Error handling utilities for gravitational wave data processing.

This module provides custom exceptions and utility functions for handling
missing or corrupted noise files gracefully, ensuring the pipeline fails
with clear, actionable error messages rather than silent failures or
cryptic tracebacks.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import hashlib
import json

# Configure logging for this module
logger = logging.getLogger(__name__)


# --- Custom Exception Classes ---

class NoiseFileError(Exception):
    """Base exception for noise file related errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}
        self.message = message

class MissingNoiseFileError(NoiseFileError):
    """Raised when a required noise file cannot be found in any configured location."""
    def __init__(self, message: str, search_paths: Optional[list] = None):
        super().__init__(message)
        self.search_paths = search_paths or []
        self.details['search_paths'] = self.search_paths

class CorruptedNoiseFileError(NoiseFileError):
    """Raised when a noise file exists but fails integrity validation."""
    def __init__(self, message: str, file_path: str, expected_checksum: Optional[str] = None, actual_checksum: Optional[str] = None):
        super().__init__(message)
        self.file_path = file_path
        self.details['expected_checksum'] = expected_checksum
        self.details['actual_checksum'] = actual_checksum
        self.details['file_path'] = file_path

class NoiseFileAccessError(NoiseFileError):
    """Raised when a noise file cannot be read due to permissions or I/O errors."""
    def __init__(self, message: str, file_path: str, error_type: str):
        super().__init__(message)
        self.file_path = file_path
        self.error_type = error_type
        self.details['file_path'] = file_path
        self.details['error_type'] = error_type


# --- Utility Functions ---

def get_noise_file_directories() -> list:
    """
    Returns a list of directories where noise files are expected to be found.
    
    This checks environment variables first, then falls back to project defaults.
    
    Returns:
        list: Ordered list of Path objects to search.
    """
    # Check for environment variable override
    env_var = os.environ.get('GW_NOISE_DATA_DIR')
    if env_var:
        paths = [Path(p) for p in env_var.split(os.pathsep)]
        logger.info(f"Using noise directories from environment: {paths}")
        return paths
    
    # Default project structure paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    default_paths = [
        base_dir / 'data' / 'raw' / 'noise',
        base_dir / 'data' / 'processed' / 'noise',
        Path('/data/gw_noise')  # Common external mount point
    ]
    return default_paths

def find_noise_file(basename: str, required: bool = True) -> Optional[Path]:
    """
    Searches for a noise file in configured directories.
    
    Args:
        basename: Name of the file to find (e.g., 'O3_noise.h5')
        required: If True, raises MissingNoiseFileError if not found.
                 If False, returns None.
    
    Returns:
        Path: Absolute path to the file if found.
    
    Raises:
        MissingNoiseFileError: If file is not found and required=True.
    """
    search_dirs = get_noise_file_directories()
    
    for directory in search_dirs:
        if not directory.exists():
            logger.debug(f"Search directory does not exist: {directory}")
            continue
        
        file_path = directory / basename
        if file_path.exists() and file_path.is_file():
            logger.info(f"Found noise file at: {file_path}")
            return file_path
    
    # File not found
    msg = f"Noise file '{basename}' not found in any configured directory."
    if required:
        raise MissingNoiseFileError(msg, search_paths=[str(p) for p in search_dirs])
    
    logger.warning(msg)
    return None

def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculates the cryptographic checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
    
    Returns:
        str: Hexadecimal checksum string.
    
    Raises:
        NoiseFileAccessError: If the file cannot be read.
    """
    try:
        hasher = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except PermissionError as e:
        raise NoiseFileAccessError(
            f"Permission denied reading file: {file_path}",
            str(file_path),
            "PermissionError"
        ) from e
    except IOError as e:
        raise NoiseFileAccessError(
            f"IO error reading file: {file_path}",
            str(file_path),
            type(e).__name__
        ) from e

def validate_noise_file(file_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """
    Validates a noise file for basic integrity and optional checksum.
    
    Args:
        file_path: Path to the noise file.
        expected_checksum: Optional expected checksum to verify against.
    
    Returns:
        bool: True if valid.
    
    Raises:
        CorruptedNoiseFileError: If validation fails.
        NoiseFileAccessError: If file cannot be accessed.
    """
    if not file_path.exists():
        raise MissingNoiseFileError(f"File does not exist: {file_path}")
    
    if not file_path.is_file():
        raise CorruptedNoiseFileError(f"Path is not a file: {file_path}", str(file_path))
    
    try:
        # Check file size > 0
        if file_path.stat().st_size == 0:
            raise CorruptedNoiseFileError(
                f"File is empty: {file_path}",
                str(file_path)
            )
        
        # Validate header/magic bytes if it's a known format
        # For HDF5 (.h5) or similar, check magic bytes
        suffix = file_path.suffix.lower()
        if suffix in ['.h5', '.hdf5']:
            with open(file_path, 'rb') as f:
                magic = f.read(8)
                if magic[:4] != b'\x89HDF':
                    raise CorruptedNoiseFileError(
                        f"Invalid HDF5 header in file: {file_path}",
                        str(file_path)
                    )
        
        # Checksum validation if provided
        if expected_checksum:
            actual_checksum = calculate_file_checksum(file_path)
            if actual_checksum.lower() != expected_checksum.lower():
                raise CorruptedNoiseFileError(
                    f"Checksum mismatch for {file_path}",
                    str(file_path),
                    expected_checksum,
                    actual_checksum
                )
        
        logger.info(f"Noise file validation passed: {file_path}")
        return True
    
    except (CorruptedNoiseFileError, NoiseFileAccessError):
        raise
    except Exception as e:
        # Catch-all for unexpected read errors
        raise CorruptedNoiseFileError(
            f"Unexpected error validating file: {file_path}",
            str(file_path)
        ) from e

def load_noise_file_with_fallback(
    basename: str, 
    expected_checksum: Optional[str] = None,
    strict: bool = True
) -> Optional[Path]:
    """
    Attempts to locate and validate a noise file.
    
    This is the primary entry point for data loading scripts.
    
    Args:
        basename: Name of the noise file.
        expected_checksum: Optional checksum for validation.
        strict: If True, raises exceptions on failure. If False, returns None.
    
    Returns:
        Path: Validated file path, or None if not found and strict=False.
    
    Raises:
        MissingNoiseFileError: If file not found (strict=True).
        CorruptedNoiseFileError: If file is corrupted (strict=True).
    """
    try:
        file_path = find_noise_file(basename, required=True)
        validate_noise_file(file_path, expected_checksum)
        return file_path
    except NoiseFileError as e:
        if strict:
            logger.error(f"Critical noise file error: {e}")
            raise
        logger.warning(f"Non-critical noise file error (strict=False): {e}")
        return None

def handle_noise_file_error(e: NoiseFileError) -> None:
    """
    Centralized error handler for noise file exceptions.
    
    Logs the error with appropriate severity and context, then re-raises.
    
    Args:
        e: The exception instance.
    
    Raises:
        The original exception after logging.
    """
    if isinstance(e, MissingNoiseFileError):
        logger.error(f"MISSING NOISE FILE: {e.message}", extra=e.details)
    elif isinstance(e, CorruptedNoiseFileError):
        logger.error(f"CORRUPTED NOISE FILE: {e.message}", extra=e.details)
    elif isinstance(e, NoiseFileAccessError):
        logger.error(f"ACCESS ERROR: {e.message}", extra=e.details)
    else:
        logger.error(f"NOISE FILE ERROR: {e.message}", extra=e.details)
    
    raise e

def ensure_noise_file_availability(
    basename: str,
    description: str = "Required noise file"
) -> Path:
    """
    Ensures a noise file is available and valid before proceeding.
    
    This function blocks execution if the file is missing or corrupted,
    providing a clear error message to the user.
    
    Args:
        basename: Name of the file.
        description: Human-readable description for error messages.
    
    Returns:
        Path: Validated file path.
    
    Raises:
        NoiseFileError: If the file is unavailable.
    """
    try:
        file_path = load_noise_file_with_fallback(basename, strict=True)
        logger.info(f"{description} is available: {file_path}")
        return file_path
    except NoiseFileError as e:
        handle_noise_file_error(e)
        # handle_noise_file_error re-raises, so this is unreachable
        # but kept for type safety
        raise

# --- Entry Point for Standalone Execution ---

def main():
    """
    Standalone CLI for testing noise file error handling.
    
    Usage:
        python -m src.error_handling --file O3_noise.h5 --checksum <sha256>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test noise file error handling")
    parser.add_argument('--file', required=True, help="Name of the noise file to check")
    parser.add_argument('--checksum', required=False, help="Expected SHA256 checksum")
    args = parser.parse_args()
    
    try:
        path = ensure_noise_file_availability(args.file, description="Testing noise file")
        print(f"SUCCESS: {args.file} is valid at {path}")
    except NoiseFileError as e:
        print(f"FAILURE: {e.message}")
        if 'search_paths' in e.details:
            print(f"  Searched: {e.details['search_paths']}")
        if 'expected_checksum' in e.details:
            print(f"  Expected: {e.details['expected_checksum']}")
        if 'actual_checksum' in e.details:
            print(f"  Actual:   {e.details['actual_checksum']}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
