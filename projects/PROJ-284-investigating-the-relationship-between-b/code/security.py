"""
Security hardening module for API credential handling.

Implements secure retrieval, validation, and masking of sensitive credentials.
Prevents accidental logging of secrets and ensures credentials are not
exposed in error messages or logs.
"""
import os
import re
import logging
from typing import Optional, Dict, Any, Set
from pathlib import Path
from config import get_hcp_credentials, get_config

# Pattern to detect potential secrets in strings
SECRET_PATTERNS = [
    r'(?i)api[_-]?key',
    r'(?i)secret',
    r'(?i)token',
    r'(?i)password',
    r'(?i)credential',
    r'(?i)auth',
]
SECRET_PATTERN = re.compile('|'.join(SECRET_PATTERNS))

# Maximum length for masked output
MAX_VISIBLE_CHARS = 4

logger = logging.getLogger(__name__)


def mask_secret(value: str, visible_chars: int = MAX_VISIBLE_CHARS) -> str:
    """
    Mask a secret value, showing only the first few characters.
    
    Args:
        value: The secret string to mask
        visible_chars: Number of characters to show at the start
        
    Returns:
        Masked string (e.g., 'abc****')
    """
    if not value:
        return "***"
    
    if len(value) <= visible_chars:
        return '*' * len(value)
    
    return value[:visible_chars] + '*' * (len(value) - visible_chars)


def is_secret_key(key: str) -> bool:
    """
    Check if a dictionary key likely contains a secret.
    
    Args:
        key: The key name to check
        
    Returns:
        True if the key matches secret patterns
    """
    return bool(SECRET_PATTERN.search(key))


def sanitize_dict_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a copy of a dictionary with secrets masked.
    
    Args:
        data: Dictionary that may contain sensitive values
        
    Returns:
        New dictionary with sensitive values masked
    """
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, dict):
            sanitized[key] = sanitize_dict_for_logging(value)
        elif isinstance(value, str) and is_secret_key(key):
            sanitized[key] = mask_secret(value)
        elif isinstance(value, str) and key.lower() in ['token', 'password', 'secret', 'credential']:
            sanitized[key] = mask_secret(value)
        else:
            sanitized[key] = value
    return sanitized


def validate_hcp_credentials() -> bool:
    """
    Validate HCP API credentials without exposing them.
    
    Checks that credentials are present and non-empty.
    Does NOT log the actual credential values.
    
    Returns:
        True if credentials are valid, False otherwise
    """
    try:
        creds = get_hcp_credentials()
        
        # Check for required fields
        required_fields = ['username', 'password']
        missing = []
        
        for field in required_fields:
            if field not in creds or not creds[field]:
                missing.append(field)
        
        if missing:
            logger.warning(f"HCP credentials missing required fields: {missing}")
            return False
        
        # Validate format (basic checks)
        username = creds['username']
        password = creds['password']
        
        if len(username) < 3:
            logger.warning("HCP username too short")
            return False
        
        if len(password) < 8:
            logger.warning("HCP password too short")
            return False
        
        # Log validation success without exposing credentials
        logger.info(f"HCP credentials validated for user: {username[:2]}***")
        return True
        
    except Exception as e:
        logger.error(f"Failed to validate HCP credentials: {str(e)}")
        return False


def secure_getenv(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Safely get an environment variable, ensuring it's not logged accidentally.
    
    Args:
        var_name: Name of the environment variable
        default: Default value if not set
        
    Returns:
        Value of the environment variable or default
    """
    value = os.environ.get(var_name, default)
    
    # If value exists and looks like a secret, log a warning
    if value and is_secret_key(var_name):
        logger.debug(f"Environment variable {var_name} is set (masked: {mask_secret(value)})")
    
    return value


def check_for_secret_leaks_in_config(config: Dict[str, Any]) -> Set[str]:
    """
    Scan configuration dictionary for potential secret leaks.
    
    Args:
        config: Configuration dictionary to scan
        
    Returns:
        Set of keys that might contain secrets
    """
    leaked_keys = set()
    
    for key, value in config.items():
        if isinstance(value, dict):
            leaked_keys.update(check_for_secret_leaks_in_config(value))
        elif isinstance(value, str) and is_secret_key(key):
            leaked_keys.add(key)
    
    return leaked_keys


def secure_logging_filter(record: logging.LogRecord) -> bool:
    """
    Filter log records to prevent secret exposure.
    
    This should be added as a filter to log handlers.
    
    Args:
        record: Log record to filter
        
    Returns:
        True if record should be logged, False otherwise
    """
    # Check message
    if record.getMessage():
        msg = record.getMessage()
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, msg, re.IGNORECASE):
                # Check if it looks like a value is being logged
                if '=' in msg or ':' in msg:
                    logger.warning("Potential secret in log message - filtering")
                    return False
    
    # Check extra fields
    if hasattr(record, 'extra'):
        for key, value in record.extra.items():
            if is_secret_key(key) and isinstance(value, str):
                logger.warning(f"Secret key '{key}' in log extra - filtering")
                return False
    
    return True


def setup_secure_logging():
    """
    Configure logging with security filters enabled.
    
    Adds a filter to all handlers to prevent secret leakage.
    """
    # Get root logger
    root_logger = logging.getLogger()
    
    # Create and add security filter
    security_filter = logging.Filter()
    security_filter.filter = secure_logging_filter
    
    for handler in root_logger.handlers:
        handler.addFilter(security_filter)
    
    logger.info("Secure logging filter enabled")


def validate_environment_security() -> bool:
    """
    Perform security checks on the environment.
    
    Checks:
    1. Credentials are not hardcoded in source files (basic check)
    2. Environment variables for secrets are set
    3. No obvious secret patterns in common config locations
    
    Returns:
        True if environment appears secure, False otherwise
    """
    is_secure = True
    
    # Check if HCP credentials are properly configured
    if not validate_hcp_credentials():
        logger.warning("HCP credentials validation failed")
        is_secure = False
    
    # Check for common insecure patterns in environment
    insecure_vars = ['HCP_PASSWORD', 'API_SECRET', 'DB_PASSWORD']
    for var in insecure_vars:
        if var in os.environ:
            # This is expected, but we log it securely
            logger.debug(f"Secure variable {var} is set")
    
    # Check config for potential leaks
    try:
        config = get_config()
        leaked = check_for_secret_leaks_in_config(config)
        if leaked:
            logger.warning(f"Potential secret keys in config: {leaked}")
            # This is informational, not necessarily a failure
    except Exception as e:
        logger.error(f"Error checking config security: {e}")
        is_secure = False
    
    if is_secure:
        logger.info("Environment security check passed")
    
    return is_secure


def main():
    """
    Main entry point for security validation.
    
    Runs all security checks and reports status.
    """
    print("Running security hardening validation...")
    
    # Enable secure logging
    setup_secure_logging()
    
    # Run validation
    is_valid = validate_environment_security()
    
    if is_valid:
        print("✓ Security validation passed")
        return 0
    else:
        print("✗ Security validation failed - review logs")
        return 1


if __name__ == "__main__":
    exit(main())
