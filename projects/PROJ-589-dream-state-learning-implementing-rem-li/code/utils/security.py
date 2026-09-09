"""
Security utilities for the Dream-State Learning pipeline.

This module provides hardened functions for path validation, input sanitization,
secure token generation, and safe file operations to prevent common vulnerabilities
such as path traversal, injection attacks, and unauthorized file access.
"""
import os
import re
import hashlib
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import yaml
import json
import logging
from datetime import datetime

# Configure logger for security events
logger = logging.getLogger(__name__)

class SecurityError(Exception):
    """Base exception for security-related errors."""
    pass

class PathTraversalError(SecurityError):
    """Raised when a path traversal attempt is detected."""
    pass

class InvalidInputError(SecurityError):
    """Raised when input validation fails."""
    pass

class ConfigLoadError(SecurityError):
    """Raised when safe config loading fails."""
    pass

# Security constants
ALLOWED_EXTENSIONS = {'.py', '.txt', '.json', '.yaml', '.yml', '.csv', '.log', '.md', '.sh'}
MAX_FILE_SIZE_MB = 100  # 100 MB limit
MAX_INPUT_LENGTH = 10000  # Maximum characters for input strings
SECURE_TOKEN_LENGTH = 32
PATH_TRAVERSAL_PATTERNS = [
    r'\.\.',  # Parent directory
    r'~/',    # Home directory
    r'/etc/', r'/proc/', r'/sys/',  # System directories
    r'\\',    # Windows path separator
    r'%00',   # Null byte injection
]

def sanitize_path(input_path: Union[str, Path], base_dir: Optional[Path] = None) -> Path:
    """
    Sanitize a file path to prevent path traversal attacks.
    
    Args:
        input_path: The input path to sanitize
        base_dir: Optional base directory to constrain the path to
        
    Returns:
        A sanitized Path object
        
    Raises:
        PathTraversalError: If path traversal is detected
        InvalidInputError: If the path is invalid
    """
    if not input_path:
        raise InvalidInputError("Input path cannot be empty")
    
    # Convert to string for pattern checking
    path_str = str(input_path)
    
    # Check for path traversal patterns
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, path_str, re.IGNORECASE):
            logger.warning(f"Path traversal attempt detected: {path_str}")
            raise PathTraversalError(f"Path traversal detected: {path_str}")
    
    # Resolve the path
    try:
        resolved_path = Path(path_str).resolve()
    except Exception as e:
        raise InvalidInputError(f"Invalid path: {path_str} - {str(e)}")
    
    # Constrain to base directory if provided
    if base_dir:
        base_resolved = base_dir.resolve()
        try:
            resolved_path.relative_to(base_resolved)
        except ValueError:
            logger.warning(f"Path escapes base directory: {path_str} (base: {base_resolved})")
            raise PathTraversalError(f"Path escapes base directory: {path_str}")
    
    return resolved_path

def validate_file_extension(file_path: Union[str, Path], allowed_extensions: Optional[set] = None) -> bool:
    """
    Validate that a file has an allowed extension.
    
    Args:
        file_path: Path to the file
        allowed_extensions: Set of allowed extensions (defaults to ALLOWED_EXTENSIONS)
        
    Returns:
        True if extension is allowed
        
    Raises:
        InvalidInputError: If extension is not allowed
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS
    
    ext = Path(file_path).suffix.lower()
    if ext not in allowed_extensions:
        logger.warning(f"File extension not allowed: {ext} in {file_path}")
        raise InvalidInputError(f"File extension '{ext}' not allowed. Allowed: {allowed_extensions}")
    
    return True

def validate_file_size(file_path: Union[str, Path], max_size_mb: Optional[int] = None) -> bool:
    """
    Validate that a file does not exceed the maximum size.
    
    Args:
        file_path: Path to the file
        max_size_mb: Maximum size in MB (defaults to MAX_FILE_SIZE_MB)
        
    Returns:
        True if file size is within limits
        
    Raises:
        InvalidInputError: If file exceeds size limit
    """
    if max_size_mb is None:
        max_size_mb = MAX_FILE_SIZE_MB
    
    try:
        file_size = Path(file_path).stat().st_size
        max_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_bytes:
            logger.warning(f"File exceeds size limit: {file_size} bytes (max: {max_bytes})")
            raise InvalidInputError(f"File size {file_size} bytes exceeds limit {max_bytes} bytes")
        
        return True
    except FileNotFoundError:
        raise InvalidInputError(f"File not found: {file_path}")
    except Exception as e:
        raise InvalidInputError(f"Error checking file size: {str(e)}")

def generate_secure_token(length: Optional[int] = None) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token (defaults to SECURE_TOKEN_LENGTH)
        
    Returns:
        A secure random token string
    """
    if length is None:
        length = SECURE_TOKEN_LENGTH
    
    return secrets.token_hex(length)

def validate_input_string(input_str: str, max_length: Optional[int] = None, 
                          pattern: Optional[str] = None) -> str:
    """
    Validate and sanitize an input string.
    
    Args:
        input_str: The input string to validate
        max_length: Maximum allowed length (defaults to MAX_INPUT_LENGTH)
        pattern: Optional regex pattern the string must match
        
    Returns:
        The validated string
        
    Raises:
        InvalidInputError: If validation fails
    """
    if not input_str:
        raise InvalidInputError("Input string cannot be empty")
    
    if max_length is None:
        max_length = MAX_INPUT_LENGTH
    
    if len(input_str) > max_length:
        logger.warning(f"Input string exceeds max length: {len(input_str)} > {max_length}")
        raise InvalidInputError(f"Input string too long: {len(input_str)} > {max_length}")
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r'<script',  # XSS
        r'javascript:',  # XSS
        r'on\w+\s*=',  # Event handlers
        r'union\s+select',  # SQL injection
        r';\s*drop\s+table',  # SQL injection
        r'\|\s*cat\s',  # Command injection
        r'\$\{',  # Template injection
    ]
    
    for pattern_str in dangerous_patterns:
        if re.search(pattern_str, input_str, re.IGNORECASE):
            logger.warning(f"Dangerous pattern detected in input: {pattern_str}")
            raise InvalidInputError(f"Dangerous pattern detected in input")
    
    if pattern:
        if not re.match(pattern, input_str):
            raise InvalidInputError(f"Input does not match required pattern")
    
    return input_str

def verify_checksum_integrity(file_path: Union[str, Path], expected_checksum: str, 
                              algorithm: str = 'sha256') -> bool:
    """
    Verify file integrity using checksum comparison.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        True if checksum matches
        
    Raises:
        InvalidInputError: If checksum doesn't match
    """
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.new(algorithm)
            while chunk := f.read(8192):
                file_hash.update(chunk)
            
            actual_checksum = file_hash.hexdigest()
            
            if actual_checksum.lower() != expected_checksum.lower():
                logger.error(f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {actual_checksum}")
                raise InvalidInputError(f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}")
            
            return True
    except FileNotFoundError:
        raise InvalidInputError(f"File not found: {file_path}")
    except Exception as e:
        raise InvalidInputError(f"Error verifying checksum: {str(e)}")

def safe_load_config(config_path: Union[str, Path], config_type: str = 'yaml') -> Dict[str, Any]:
    """
    Safely load a configuration file with security checks.
    
    Args:
        config_path: Path to the config file
        config_type: Type of config ('yaml' or 'json')
        
    Returns:
        Parsed configuration dictionary
        
    Raises:
        ConfigLoadError: If loading fails or security checks fail
    """
    try:
        # Security checks
        config_path = sanitize_path(config_path)
        validate_file_extension(config_path)
        validate_file_size(config_path, MAX_FILE_SIZE_MB)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_type.lower() == 'yaml':
                # Use safe_load to prevent arbitrary code execution
                config = yaml.safe_load(f)
            elif config_type.lower() == 'json':
                config = json.load(f)
            else:
                raise ConfigLoadError(f"Unsupported config type: {config_type}")
        
        if config is None:
            config = {}
        
        logger.info(f"Successfully loaded config from {config_path}")
        return config
        
    except yaml.YAMLError as e:
        raise ConfigLoadError(f"YAML parsing error: {str(e)}")
    except json.JSONDecodeError as e:
        raise ConfigLoadError(f"JSON parsing error: {str(e)}")
    except (PathTraversalError, InvalidInputError) as e:
        raise ConfigLoadError(f"Security validation failed: {str(e)}")
    except Exception as e:
        raise ConfigLoadError(f"Failed to load config: {str(e)}")

class SecurityContext:
    """
    Context manager for security operations.
    
    Provides a scoped environment for security-sensitive operations with
    automatic logging and error handling.
    """
    
    def __init__(self, operation_name: str, base_dir: Optional[Path] = None):
        self.operation_name = operation_name
        self.base_dir = base_dir
        self.start_time = datetime.now()
        self.logger = logging.getLogger(f'security.{operation_name}')
    
    def __enter__(self):
        self.logger.info(f"Starting security operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type:
            self.logger.error(f"Security operation failed: {self.operation_name} - {str(exc_val)}")
        else:
            self.logger.info(f"Security operation completed: {self.operation_name} in {duration:.3f}s")
        return False

def validate_environment(required_env_vars: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Validate that required environment variables are set securely.
    
    Args:
        required_env_vars: List of required environment variable names
        
    Returns:
        Dictionary of validated environment variables
        
    Raises:
        InvalidInputError: If required variables are missing
    """
    if required_env_vars is None:
        required_env_vars = []
    
    validated = {}
    missing = []
    
    for var_name in required_env_vars:
        value = os.environ.get(var_name)
        if value is None:
            missing.append(var_name)
        else:
            # Validate the value
            try:
                validate_input_string(value, max_length=1000)
                validated[var_name] = value
            except InvalidInputError:
                logger.warning(f"Invalid value for env var: {var_name}")
                missing.append(var_name)
    
    if missing:
        raise InvalidInputError(f"Missing or invalid environment variables: {missing}")
    
    logger.info(f"Environment validated successfully: {list(validated.keys())}")
    return validated

def secure_delete(file_path: Union[str, Path], overwrite_passes: int = 3) -> bool:
    """
    Securely delete a file by overwriting before removal.
    
    Args:
        file_path: Path to the file to delete
        overwrite_passes: Number of overwrite passes (default: 3)
        
    Returns:
        True if deletion was successful
        
    Raises:
        InvalidInputError: If deletion fails
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return True
        
        # Get file size
        file_size = path.stat().st_size
        
        # Overwrite with random data multiple times
        for i in range(overwrite_passes):
            with open(path, 'wb') as f:
                f.write(secrets.token_bytes(file_size))
                f.flush()
                os.fsync(f.fileno())
        
        # Remove the file
        path.unlink()
        
        logger.info(f"Securely deleted file: {file_path} ({overwrite_passes} passes)")
        return True
        
    except Exception as e:
        logger.error(f"Failed to securely delete file {file_path}: {str(e)}")
        raise InvalidInputError(f"Failed to securely delete file: {str(e)}")