"""
Error handling utilities for missing or corrupted noise files.

This module provides robust error handling for scenarios where
LIGO O3 noise files are missing, corrupted, or inaccessible.
It ensures the pipeline fails gracefully with clear error messages
rather than crashing with cryptic tracebacks.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Tuple
import hashlib

# Configure logging for this module
logger = logging.getLogger(__name__)

class NoiseFileError(Exception):
    """Custom exception for noise file related errors."""
    pass

class MissingNoiseFileError(NoiseFileError):
    """Raised when a required noise file is missing."""
    pass

class CorruptedNoiseFileError(NoiseFileError):
    """Raised when a noise file is corrupted or invalid."""
    pass

class NoiseFileAccessError(NoiseFileError):
    """Raised when noise file cannot be accessed (permissions, etc.)."""
    pass

def validate_noise_file(
    noise_path: str,
    expected_checksum: Optional[str] = None,
    min_size_bytes: int = 1024
) -> Tuple[bool, str]:
    """
    Validate that a noise file exists, is accessible, and meets basic integrity checks.
    
    Args:
        noise_path: Path to the noise file
        expected_checksum: Optional MD5 checksum to verify against
        min_size_bytes: Minimum acceptable file size in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(noise_path)
    
    # Check if file exists
    if not path.exists():
        return False, f"Noise file not found: {noise_path}"
    
    # Check if it's a file (not directory)
    if not path.is_file():
        return False, f"Path is not a file: {noise_path}"
    
    # Check file size
    try:
        file_size = path.stat().st_size
        if file_size < min_size_bytes:
            return False, f"Noise file too small ({file_size} bytes < {min_size_bytes} bytes): {noise_path}"
    except OSError as e:
        return False, f"Cannot access file size: {noise_path} - {str(e)}"
    
    # Verify checksum if provided
    if expected_checksum:
        try:
            actual_checksum = calculate_file_checksum(path)
            if actual_checksum.lower() != expected_checksum.lower():
                return False, f"Checksum mismatch for {noise_path}: expected {expected_checksum}, got {actual_checksum}"
        except Exception as e:
            return False, f"Checksum verification failed for {noise_path}: {str(e)}"
    
    return True, ""

def calculate_file_checksum(file_path: Path, algorithm: str = 'md5') -> str:
    """
    Calculate the checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: md5)
        
    Returns:
        Hex digest of the file checksum
        
    Raises:
        NoiseFileAccessError: If file cannot be read
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
    except Exception as e:
        raise NoiseFileAccessError(f"Error reading file {file_path}: {str(e)}")

def load_noise_file_with_fallback(
    noise_path: str,
    fallback_path: Optional[str] = None
) -> Tuple[Optional[Path], Optional[str]]:
    """
    Attempt to load a noise file with fallback to an alternative location.
    
    Args:
        noise_path: Primary noise file path
        fallback_path: Optional fallback path if primary is missing/corrupted
        
    Returns:
        Tuple of (valid_path_or_none, error_message_or_none)
    """
    # Try primary path
    valid, error = validate_noise_file(noise_path)
    if valid:
        logger.info(f"Using primary noise file: {noise_path}")
        return Path(noise_path), None
    
    logger.warning(f"Primary noise file invalid: {error}")
    
    # Try fallback if provided
    if fallback_path:
        valid, fallback_error = validate_noise_file(fallback_path)
        if valid:
            logger.info(f"Using fallback noise file: {fallback_path}")
            return Path(fallback_path), None
        logger.warning(f"Fallback noise file also invalid: {fallback_error}")
    
    # No valid file found
    return None, f"Failed to load noise file. Primary: {error}" + (f"; Fallback: {fallback_error}" if fallback_path else "")

def handle_noise_file_error(
    noise_path: str,
    error_context: str = "waveform generation",
    raise_on_failure: bool = True
) -> bool:
    """
    Handle noise file errors gracefully with logging and optional raising.
    
    Args:
        noise_path: Path to the problematic noise file
        error_context: Context where the error occurred (e.g., "waveform generation")
        raise_on_failure: If True, raise an exception; if False, return False
        
    Returns:
        True if noise file is valid, False otherwise
    """
    valid, error_msg = validate_noise_file(noise_path)
    
    if not valid:
        error_msg = f"Noise file error during {error_context}: {error_msg}"
        
        if raise_on_failure:
            # Determine appropriate exception type
            if "not found" in error_msg.lower():
                raise MissingNoiseFileError(error_msg)
            elif "too small" in error_msg.lower() or "checksum" in error_msg.lower():
                raise CorruptedNoiseFileError(error_msg)
            else:
                raise NoiseFileError(error_msg)
        else:
            logger.error(error_msg)
            return False
    
    return True

def get_noise_file_directories() -> dict:
    """
    Return standard directories where noise files are expected.
    
    Returns:
        Dictionary with 'raw', 'processed', and 'fallback' paths
    """
    base_dir = Path(__file__).parent.parent.parent / "data"
    return {
        'raw': base_dir / "raw" / "ligo_noise",
        'processed': base_dir / "processed" / "noise",
        'fallback': base_dir / "raw" / "fallback_noise"
    }

def find_noise_file(
    search_patterns: list,
    directories: Optional[dict] = None
) -> Optional[Path]:
    """
    Search for a noise file matching patterns in standard directories.
    
    Args:
        search_patterns: List of filename patterns to search for
        directories: Optional dict of directories to search (defaults to standard paths)
        
    Returns:
        Path to first valid noise file found, or None
    """
    if directories is None:
        directories = get_noise_file_directories()
    
    for directory_type, dir_path in directories.items():
        if not dir_path.exists():
            continue
            
        for pattern in search_patterns:
            for file_path in dir_path.glob(pattern):
                if file_path.is_file():
                    valid, _ = validate_noise_file(str(file_path))
                    if valid:
                        logger.info(f"Found noise file: {file_path} (in {directory_type})")
                        return file_path
    
    return None

def ensure_noise_file_availability(
    required_patterns: list,
    error_context: str = "analysis"
) -> Path:
    """
    Ensure a noise file is available, raising a clear error if not.
    
    Args:
        required_patterns: List of filename patterns that are acceptable
        error_context: Context for error message
        
    Returns:
        Path to the found noise file
        
    Raises:
        MissingNoiseFileError: If no valid noise file is found
    """
    noise_file = find_noise_file(required_patterns)
    
    if noise_file is None:
        directories = get_noise_file_directories()
        dir_list = ", ".join([f"{k}: {v}" for k, v in directories.items()])
        
        error_msg = (
            f"No valid noise file found for {error_context}. "
            f"Searched patterns: {required_patterns}. "
            f"Expected locations: {dir_list}. "
            f"Please ensure LIGO O3 noise data is downloaded and placed in the appropriate directory."
        )
        
        raise MissingNoiseFileError(error_msg)
    
    return noise_file
