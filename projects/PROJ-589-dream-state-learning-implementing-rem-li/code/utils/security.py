"""
Security hardening utilities for the Dream-State Learning pipeline.

Implements input validation, path sanitization, and resource constraint checks
to prevent common vulnerabilities (path traversal, injection, resource exhaustion).
"""
import os
import re
import hashlib
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from utils.exceptions import DataIntegrityError

# Security constants
MAX_PATH_LENGTH = 255
ALLOWED_FILE_EXTENSIONS = {'.py', '.json', '.yaml', '.yml', '.txt', '.csv', '.pt', '.bin'}
MAX_FILE_SIZE_MB = 100  # Prevent massive file uploads/reads
INPUT_SANITIZATION_PATTERN = re.compile(r'[^a-zA-Z0-9_.\-/]')

class SecurityError(Exception):
    """Base exception for security-related errors."""
    pass

class PathTraversalError(SecurityError):
    """Raised when path traversal attempt is detected."""
    pass

class InvalidInputError(SecurityError):
    """Raised when input validation fails."""
    pass

def sanitize_path(input_path: str, base_dir: Optional[Union[str, Path]] = None) -> str:
    """
    Sanitize and validate file paths to prevent traversal attacks.

    Args:
        input_path: User-provided path string
        base_dir: Optional base directory to resolve relative paths against

    Returns:
        Sanitized absolute path as string

    Raises:
        PathTraversalError: If path traversal attempt detected
        InvalidInputError: If path is invalid or empty
    """
    if not input_path or not isinstance(input_path, str):
        raise InvalidInputError("Path must be a non-empty string")

    # Check for null bytes
    if '\x00' in input_path:
        raise InvalidInputError("Path contains null bytes")

    # Check length
    if len(input_path) > MAX_PATH_LENGTH:
        raise InvalidInputError(f"Path exceeds maximum length of {MAX_PATH_LENGTH}")

    # Remove null bytes and normalize
    sanitized = input_path.replace('\x00', '')

    # Resolve to absolute path if base_dir provided
    if base_dir:
        base = Path(base_dir).resolve()
        try:
            resolved = (base / sanitized).resolve()
        except (ValueError, OSError) as e:
            raise InvalidInputError(f"Invalid path resolution: {e}")

        # Ensure resolved path is within base directory
        try:
            resolved.relative_to(base)
        except ValueError:
            raise PathTraversalError(f"Path traversal attempt detected: {input_path}")
    else:
        resolved = Path(sanitized).resolve()

    return str(resolved)

def validate_file_extension(filepath: Union[str, Path]) -> bool:
    """
    Validate that file has an allowed extension.

    Args:
        filepath: Path to validate

    Returns:
        True if extension is allowed, False otherwise
    """
    path = Path(filepath)
    return path.suffix.lower() in ALLOWED_FILE_EXTENSIONS

def validate_file_size(filepath: Union[str, Path], max_size_mb: Optional[int] = None) -> bool:
    """
    Validate that file size is within limits.

    Args:
        filepath: Path to file
        max_size_mb: Maximum file size in MB (defaults to MAX_FILE_SIZE_MB)

    Returns:
        True if file size is acceptable, False otherwise
    """
    if max_size_mb is None:
        max_size_mb = MAX_FILE_SIZE_MB

    max_bytes = max_size_mb * 1024 * 1024
    try:
        size = os.path.getsize(filepath)
        return size <= max_bytes
    except OSError:
        return False

def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: Length of token in bytes

    Returns:
        Hex-encoded token string
    """
    return secrets.token_hex(length)

def validate_input_string(input_str: str, allowed_chars: Optional[re.Pattern] = None) -> str:
    """
    Validate and sanitize input string.

    Args:
        input_str: Input string to validate
        allowed_chars: Optional regex pattern of allowed characters

    Returns:
        Sanitized string

    Raises:
        InvalidInputError: If input contains invalid characters
    """
    if not input_str or not isinstance(input_str, str):
        raise InvalidInputError("Input must be a non-empty string")

    if len(input_str) > MAX_PATH_LENGTH:
        raise InvalidInputError(f"Input exceeds maximum length of {MAX_PATH_LENGTH}")

    if allowed_chars:
        if not allowed_chars.fullmatch(input_str):
            raise InvalidInputError("Input contains invalid characters")
    else:
        # Default: allow alphanumeric, underscores, hyphens, dots, slashes
        if not re.match(r'^[a-zA-Z0-9_.\-/\s]+$', input_str):
            raise InvalidInputError("Input contains invalid characters")

    return input_str.strip()

def verify_checksum_integrity(filepath: Union[str, Path], expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Verify file checksum integrity.

    Args:
        filepath: Path to file
        expected_checksum: Expected checksum string
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        True if checksum matches, False otherwise

    Raises:
        DataIntegrityError: If checksum verification fails
    """
    try:
        hasher = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)

        actual_checksum = hasher.hexdigest()

        if not secrets.compare_digest(actual_checksum, expected_checksum):
            raise DataIntegrityError(
                f"Checksum mismatch for {filepath}: expected {expected_checksum}, got {actual_checksum}"
            )

        return True

    except FileNotFoundError:
        raise DataIntegrityError(f"File not found: {filepath}")
    except Exception as e:
        raise DataIntegrityError(f"Checksum verification failed: {e}")

def safe_load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Safely load configuration file with validation.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        SecurityError: If config file is invalid or unsafe
    """
    # Validate path
    safe_path = sanitize_path(str(config_path))

    # Validate extension
    if not validate_file_extension(safe_path):
        raise InvalidInputError(f"Config file must have allowed extension: {ALLOWED_FILE_EXTENSIONS}")

    # Validate size
    if not validate_file_size(safe_path):
        raise InvalidInputError(f"Config file exceeds maximum size")

    # Load and validate content
    try:
        import json
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Limit content size in memory
        if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise InvalidInputError("Config file too large")

        config = json.loads(content)

        # Basic structure validation
        if not isinstance(config, dict):
            raise InvalidInputError("Config must be a JSON object")

        return config

    except json.JSONDecodeError as e:
        raise InvalidInputError(f"Invalid JSON in config file: {e}")
    except Exception as e:
        raise SecurityError(f"Failed to load config: {e}")

class SecurityContext:
    """
    Context manager for secure operations with automatic cleanup.
    """

    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or "/tmp"
        self.created_files: List[str] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup created files
        for filepath in self.created_files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except OSError:
                pass
        return False

    def create_secure_temp_file(self, prefix: str = "dream_", suffix: str = ".tmp") -> str:
        """
        Create a secure temporary file.

        Args:
            prefix: File prefix
            suffix: File suffix

        Returns:
            Path to created temporary file
        """
        import tempfile

        # Generate secure filename
        filename = f"{prefix}{generate_secure_token(16)}{suffix}"
        filepath = os.path.join(self.temp_dir, filename)

        # Create file securely
        try:
            with open(filepath, 'w') as f:
                pass  # Create empty file
            self.created_files.append(filepath)
            return filepath
        except Exception as e:
            raise SecurityError(f"Failed to create secure temp file: {e}")

def validate_environment() -> Dict[str, bool]:
    """
    Validate security-relevant environment settings.

    Returns:
        Dictionary of validation results
    """
    results = {
        'temp_dir_writable': False,
        'safe_home': False,
        'no_debug_mode': False,
    }

    # Check temp directory
    try:
        test_file = os.path.join(tempfile.gettempdir(), f".security_test_{generate_secure_token(8)}")
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        results['temp_dir_writable'] = True
    except (OSError, IOError):
        pass

    # Check home directory
    home = os.path.expanduser('~')
    if home and home != '/' and not home.startswith('/root'):
        results['safe_home'] = True

    # Check debug mode
    debug_mode = os.environ.get('DEBUG', 'false').lower()
    results['no_debug_mode'] = debug_mode not in ('true', '1', 'yes')

    return results

def secure_delete(filepath: Union[str, Path]) -> bool:
    """
    Securely delete a file by overwriting before removal.

    Args:
        filepath: Path to file to delete

    Returns:
        True if deletion successful, False otherwise
    """
    filepath = Path(filepath)

    if not filepath.exists():
        return True

    try:
        # Get file size
        size = filepath.stat().st_size

        # Overwrite with random data
        with open(filepath, 'wb') as f:
            f.write(secrets.token_bytes(size))
            f.flush()
            os.fsync(f.fileno())

        # Remove file
        filepath.unlink()
        return True

    except Exception:
        # Fallback to regular delete if secure delete fails
        try:
            filepath.unlink()
            return True
        except Exception:
            return False