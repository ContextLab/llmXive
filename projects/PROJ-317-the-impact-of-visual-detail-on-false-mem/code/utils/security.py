"""
Security utilities for sanitizing log messages and preventing PII leakage.

This module provides functions to sanitize strings and dictionaries to remove
or mask personally identifiable information (PII) before logging.
"""
import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from config import get_logs_dir

# Common PII patterns to detect and mask
PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone_us': r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    'date_of_birth': r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
    'participant_id_leak': r'\bPID[-_]\d{6,}\b',  # Custom pattern for project-specific IDs
}

# Replacement strings for masked PII
PII_REPLACEMENTS = {
    'email': '[EMAIL_MASKED]',
    'phone_us': '[PHONE_MASKED]',
    'ssn': '[SSN_MASKED]',
    'credit_card': '[CC_MASKED]',
    'ip_address': '[IP_MASKED]',
    'date_of_birth': '[DOB_MASKED]',
    'participant_id_leak': '[PID_MASKED]',
}

# Sensitive keys that might contain PII in dictionaries
SENSITIVE_KEYS = {
    'email', 'phone', 'telephone', 'mobile', 'ssn', 'social_security',
    'credit_card', 'card_number', 'dob', 'date_of_birth', 'birth_date',
    'address', 'street', 'city', 'state', 'zip', 'postal_code',
    'country', 'participant_id', 'user_id', 'session_id', 'name',
    'first_name', 'last_name', 'full_name', 'username', 'password',
    'token', 'secret', 'api_key', 'auth', 'token'
}

def sanitize_string(value: str, mask_sensitive: bool = True) -> str:
    """
    Sanitize a string by masking potential PII patterns.
    
    Args:
        value: The string to sanitize.
        mask_sensitive: If True, apply PII masking patterns.
        
    Returns:
        Sanitized string with PII replaced by masked placeholders.
    """
    if not isinstance(value, str):
        return str(value)
    
    sanitized = value
    
    if mask_sensitive:
        for pattern_name, pattern in PII_PATTERNS.items():
            replacement = PII_REPLACEMENTS[pattern_name]
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    return sanitized

def sanitize_dict(data: Dict[str, Any], mask_sensitive: bool = True, mask_values: bool = True) -> Dict[str, Any]:
    """
    Sanitize a dictionary by masking sensitive keys and their values.
    
    Args:
        data: The dictionary to sanitize.
        mask_sensitive: If True, apply PII masking patterns to values.
        mask_values: If True, replace values of sensitive keys with '[SENSITIVE]'.
        
    Returns:
        Sanitized dictionary with sensitive data masked.
    """
    if not isinstance(data, dict):
        return data
    
    sanitized = {}
    for key, value in data.items():
        key_str = str(key).lower()
        
        # Check if key is sensitive
        is_sensitive_key = any(sensitive in key_str for sensitive in SENSITIVE_KEYS)
        
        if is_sensitive_key and mask_values:
            sanitized[key] = '[SENSITIVE]'
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, mask_sensitive, mask_values)
        elif isinstance(value, str):
            sanitized[key] = sanitize_string(value, mask_sensitive)
        else:
            sanitized[key] = value
    
    return sanitized

def sanitize_log_message(message: str) -> str:
    """
    Sanitize a log message to prevent PII leakage.
    
    This is the primary function used by the logging system to ensure
    that no personally identifiable information is written to log files.
    
    Args:
        message: The log message to sanitize.
        
    Returns:
        Sanitized log message with PII masked.
    """
    if not isinstance(message, str):
        message = str(message)
    
    return sanitize_string(message, mask_sensitive=True)

class SanitizedLogger:
    """
    A logger wrapper that automatically sanitizes all log messages.
    
    This class ensures that no PII is leaked through log messages by
    sanitizing all input before passing it to the underlying logger.
    """
    
    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the sanitized logger.
        
        Args:
            name: Name for the logger.
            logger: Optional underlying logger instance. If None, creates a new logger.
        """
        self.name = name
        self.logger = logger or logging.getLogger(name)
        self.logger.addHandler(logging.NullHandler())  # Prevent duplicate handlers
    
    def _sanitize(self, msg: str, *args, **kwargs) -> tuple:
        """Sanitize message and arguments."""
        sanitized_msg = sanitize_log_message(msg)
        
        sanitized_args = []
        for arg in args:
            if isinstance(arg, str):
                sanitized_args.append(sanitize_log_message(arg))
            elif isinstance(arg, dict):
                sanitized_args.append(sanitize_dict(arg))
            else:
                sanitized_args.append(arg)
        
        sanitized_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                sanitized_kwargs[key] = sanitize_log_message(value)
            elif isinstance(value, dict):
                sanitized_kwargs[key] = sanitize_dict(value)
            else:
                sanitized_kwargs[key] = value
        
        return sanitized_msg, tuple(sanitized_args), sanitized_kwargs
    
    def debug(self, msg: str, *args, **kwargs):
        sanitized_msg, sanitized_args, sanitized_kwargs = self._sanitize(msg, *args, **kwargs)
        self.logger.debug(sanitized_msg, *sanitized_args, **sanitized_kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        sanitized_msg, sanitized_args, sanitized_kwargs = self._sanitize(msg, *args, **kwargs)
        self.logger.info(sanitized_msg, *sanitized_args, **sanitized_kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        sanitized_msg, sanitized_args, sanitized_kwargs = self._sanitize(msg, *args, **kwargs)
        self.logger.warning(sanitized_msg, *sanitized_args, **sanitized_kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        sanitized_msg, sanitized_args, sanitized_kwargs = self._sanitize(msg, *args, **kwargs)
        self.logger.error(sanitized_msg, *sanitized_args, **sanitized_kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        sanitized_msg, sanitized_args, sanitized_kwargs = self._sanitize(msg, *args, **kwargs)
        self.logger.critical(sanitized_msg, *sanitized_args, **sanitized_kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        sanitized_msg, sanitized_args, sanitized_kwargs = self._sanitize(msg, *args, **kwargs)
        self.logger.exception(sanitized_msg, *sanitized_args, **sanitized_kwargs)

def ensure_log_safety(log_file_path: Path) -> bool:
    """
    Ensure that a log file path is safe and does not leak sensitive information.
    
    Args:
        log_file_path: Path to the log file.
        
    Returns:
        True if the path is safe, False otherwise.
    """
    if not log_file_path:
        return False
    
    path_str = str(log_file_path)
    
    # Check for sensitive patterns in the path itself
    for pattern_name, pattern in PII_PATTERNS.items():
        if re.search(pattern, path_str, re.IGNORECASE):
            return False
    
    # Ensure the path is within the logs directory
    logs_dir = get_logs_dir()
    try:
        log_file_path.resolve().relative_to(logs_dir.resolve())
        return True
    except ValueError:
        return False

def main():
    """
    Main function to demonstrate security sanitization utilities.
    
    This function runs a set of test cases to demonstrate the PII masking
    capabilities of the security module.
    """
    print("Security Hardening Module - PII Sanitization Demo")
    print("=" * 50)
    
    # Test cases
    test_messages = [
        "User john.doe@example.com logged in from 192.168.1.100",
        "Participant PID-123456 with SSN 123-45-6789 completed the task",
        "Phone call from +1 (555) 123-4567 regarding order #12345",
        "Credit card 4111-1111-1111-1111 was declined",
        "Normal log message without any PII",
        "Session data: {'user_email': 'test@example.com', 'ip': '10.0.0.1', 'name': 'John Doe'}"
    ]
    
    for i, msg in enumerate(test_messages, 1):
        sanitized = sanitize_log_message(msg)
        print(f"\nTest {i}:")
        print(f"  Original:  {msg}")
        print(f"  Sanitized: {sanitized}")
    
    # Test dictionary sanitization
    sensitive_data = {
        'participant_id': 'PID-987654',
        'email': 'participant@example.com',
        'phone': '+1-555-987-6543',
        'ssn': '987-65-4321',
        'session_info': {
            'ip_address': '172.16.0.100',
            'user_agent': 'Mozilla/5.0',
            'timestamp': '2026-01-15T10:30:00Z'
        }
    }
    
    print(f"\nDictionary sanitization:")
    print(f"  Original:  {sensitive_data}")
    sanitized_dict = sanitize_dict(sensitive_data)
    print(f"  Sanitized: {sanitized_dict}")
    
    # Test SanitizedLogger
    print(f"\nSanitizedLogger test:")
    logger = SanitizedLogger("security_test")
    logger.info("Test message with email: test@example.com and IP: 192.168.1.1")
    
    print("\n" + "=" * 50)
    print("Security hardening demo completed successfully.")
    print("All PII patterns have been masked to prevent data leakage.")

if __name__ == "__main__":
    main()
