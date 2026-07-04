"""
Security hardening utilities for llmXive pipeline.

This module provides functions to:
1. Validate that no secrets are present in logs
2. Ensure API keys are handled exclusively via environment variables
3. Sanitize data structures before logging or serialization
"""
import os
import re
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from functools import wraps

# Common patterns for secrets that should not be logged
SECRET_PATTERNS = [
    re.compile(r'api[_-]?key', re.IGNORECASE),
    re.compile(r'api[_-]?secret', re.IGNORECASE),
    re.compile(r'auth[_-]?token', re.IGNORECASE),
    re.compile(r'access[_-]?token', re.IGNORECASE),
    re.compile(r'private[_-]?key', re.IGNORECASE),
    re.compile(r'password', re.IGNORECASE),
    re.compile(r'secret', re.IGNORECASE),
    # Specific patterns for known services
    re.compile(r'ghp_[a-zA-Z0-9]{36}'),  # GitHub Personal Access Token
    re.compile(r'gho_[a-zA-Z0-9]{36}'),  # GitHub OAuth Token
    re.compile(r'ghu_[a-zA-Z0-9]{36}'),  # GitHub User Token
    re.compile(r'ghs_[a-zA-Z0-9]{36}'),  # GitHub Server Token
    re.compile(r'npm_[a-zA-Z0-9]{36}'),  # NPM Token
    re.compile(r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'),  # JWT
]

# Keys that are expected to be environment variables and should never be hardcoded
EXPECTED_ENV_KEYS = {
    'NPM_API_KEY',
    'GITHUB_TOKEN',
    'GITHUB_TOKEN_READ',
    'GITHUB_TOKEN_WRITE',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'DATABASE_URL',
}

class SecretRedactionError(Exception):
    """Raised when a potential secret is detected in log output."""
    pass

def sanitize_value(value: Any) -> str:
    """
    Sanitize a value by redacting potential secrets.
    
    Args:
        value: The value to sanitize (string, dict, list, etc.)
        
    Returns:
        A sanitized string representation with secrets redacted.
    """
    if value is None:
        return "None"
    
    if isinstance(value, (dict, list)):
        # For complex structures, convert to string and sanitize
        import json
        try:
            str_value = json.dumps(value)
        except (TypeError, ValueError):
            str_value = str(value)
    else:
        str_value = str(value)
    
    # Check against secret patterns
    for pattern in SECRET_PATTERNS:
        if pattern.search(str_value):
            # If it looks like a secret key name, redact the value
            # If it looks like a token, redact the whole match
            if pattern.match(str_value):
                return "[REDACTED]"
            else:
                # Replace the matched pattern with [REDACTED]
                str_value = pattern.sub("[REDACTED]", str_value)
    
    return str_value

def sanitize_dict(data: Dict[str, Any], keys_to_redact: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Recursively sanitize a dictionary, redacting sensitive values.
    
    Args:
        data: Dictionary to sanitize
        keys_to_redact: Optional list of specific keys to always redact
        
    Returns:
        Sanitized dictionary
    """
    if keys_to_redact is None:
        keys_to_redact = []
    
    sanitized = {}
    for key, value in data.items():
        # Always redact if key name suggests sensitivity
        is_sensitive_key = any(
            pattern.search(key) for pattern in SECRET_PATTERNS
        ) or key.lower() in [k.lower() for k in keys_to_redact]
        
        if is_sensitive_key:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, keys_to_redact)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict(item, keys_to_redact) if isinstance(item, dict) else sanitize_value(item)
                for item in value
            ]
        else:
            sanitized[key] = sanitize_value(value)
    
    return sanitized

def validate_env_vars(required_keys: Optional[List[str]] = None) -> Dict[str, bool]:
    """
    Validate that required environment variables are set and not empty.
    
    Args:
        required_keys: List of environment variable names to check
        
    Returns:
        Dictionary mapping variable names to boolean (True if set and non-empty)
    """
    if required_keys is None:
        required_keys = list(EXPECTED_ENV_KEYS)
    
    results = {}
    for key in required_keys:
        value = os.getenv(key)
        results[key] = value is not None and len(value.strip()) > 0
    
    return results

def check_for_hardcoded_secrets(file_path: Union[str, Path]) -> List[str]:
    """
    Scan a file for potential hardcoded secrets.
    
    Args:
        file_path: Path to the file to scan
        
    Returns:
        List of lines containing potential secrets
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return []
    
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Skip comments and empty lines
                stripped = line.strip()
                if stripped.startswith('#') or not stripped:
                    continue
                
                for pattern in SECRET_PATTERNS:
                    if pattern.search(line):
                        # Check if it's actually a hardcoded value (not an env var reference)
                        # Look for patterns like: key = "actual_secret" or key = 'actual_secret'
                        if re.search(r'[=:]?\s*["\'][^"\']{8,}["\']', line):
                            issues.append(f"Line {line_num}: Potential hardcoded secret detected")
                            break
    except Exception as e:
        logging.error(f"Error scanning file {file_path}: {e}")
    
    return issues

def secure_logger(name: str, redact_keys: Optional[List[str]] = None) -> logging.Logger:
    """
    Create a logger that automatically redacts sensitive information.
    
    Args:
        name: Logger name
        redact_keys: Additional keys to always redact
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Custom formatter that sanitizes messages
    class SecureFormatter(logging.Formatter):
        def format(self, record):
            message = super().format(record)
            sanitized = sanitize_dict({'message': message}, redact_keys)
            return sanitized['message']
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Add console handler with secure formatter
    handler = logging.StreamHandler()
    handler.setFormatter(SecureFormatter())
    logger.addHandler(handler)
    
    return logger

def secure_config_loader(config_dict: Dict[str, Any], env_prefix: str = '') -> Dict[str, Any]:
    """
    Load configuration ensuring API keys come from environment variables.
    
    Args:
        config_dict: Raw configuration dictionary
        env_prefix: Prefix for environment variable names
        
    Returns:
        Configuration dictionary with sensitive values from environment
    """
    secure_config = {}
    
    for key, value in config_dict.items():
        env_var_name = f"{env_prefix}{key.upper()}" if env_prefix else key.upper()
        
        # Check if this is a sensitive key
        is_sensitive = any(pattern.search(key) for pattern in SECRET_PATTERNS)
        
        if is_sensitive:
            # Always prefer environment variable
            env_value = os.getenv(env_var_name)
            if env_value:
                secure_config[key] = env_value
            else:
                # If not in env, use default but log warning
                if value is not None:
                    logging.warning(f"Sensitive config '{key}' not found in environment variables. Using default or None.")
                secure_config[key] = value
        else:
            secure_config[key] = value
    
    return secure_config

def ensure_no_secrets_in_log_record(record: logging.LogRecord) -> logging.LogRecord:
    """
    Filter log records to remove any potential secrets.
    
    Args:
        record: Log record to filter
        
    Returns:
        Filtered log record
    """
    # Sanitize the message
    record.msg = sanitize_value(record.msg)
    
    # Sanitize args if present
    if record.args:
        if isinstance(record.args, dict):
            record.args = sanitize_dict(record.args)
        elif isinstance(record.args, (list, tuple)):
            record.args = tuple(sanitize_value(arg) for arg in record.args)
        else:
            record.args = sanitize_value(record.args)
    
    return record

class SecureHandler(logging.Handler):
    """Logging handler that automatically redacts secrets from log messages."""
    
    def __init__(self, redact_keys: Optional[List[str]] = None):
        super().__init__()
        self.redact_keys = redact_keys or []
    
    def emit(self, record: logging.LogRecord):
        try:
            sanitized_record = ensure_no_secrets_in_log_record(record)
            self.format(sanitized_record)
            # Write to original destination
            stream = self.stream if hasattr(self, 'stream') else None
            if stream:
                msg = self.format(sanitized_record)
                stream.write(msg + self.terminator)
                self.flush()
        except Exception:
            self.handleError(record)

def validate_api_key_format(key: str, key_type: str) -> bool:
    """
    Validate the format of an API key based on its type.
    
    Args:
        key: The API key to validate
        key_type: Type of key ('npm', 'github', 'generic')
        
    Returns:
        True if the key format is valid, False otherwise
    """
    if not key or not isinstance(key, str):
        return False
    
    key = key.strip()
    
    if key_type == 'github':
        # GitHub tokens: ghp_, gho_, ghu_, ghs_, or GitHub App tokens starting with github_pat_
        return bool(re.match(r'^(gh[pous]_|github_pat_)[a-zA-Z0-9]{36,}$', key))
    
    elif key_type == 'npm':
        # NPM tokens: npm_ followed by 36 alphanumeric characters
        return bool(re.match(r'^npm_[a-zA-Z0-9]{36}$', key))
    
    else:  # generic
        # Generic check: not empty, reasonable length, no obvious patterns of being a placeholder
        if len(key) < 8:
            return False
        # Check if it's a common placeholder
        placeholders = ['your_', 'xxx', 'changeme', 'replace', 'placeholder', 'test']
        if any(p in key.lower() for p in placeholders):
            return False
        return True

def audit_security_config() -> Dict[str, Any]:
    """
    Perform a security audit of the current configuration.
    
    Returns:
        Dictionary with audit results
    """
    audit_results = {
        'env_vars_checked': {},
        'hardcoded_secrets_found': [],
        'security_warnings': []
    }
    
    # Check environment variables
    audit_results['env_vars_checked'] = validate_env_vars()
    
    # Check for missing critical env vars
    missing_critical = [k for k, v in audit_results['env_vars_checked'].items() if not v]
    if missing_critical:
        audit_results['security_warnings'].append(
            f"Critical environment variables not set: {', '.join(missing_critical)}"
        )
    
    # Check common config files for hardcoded secrets
    config_files = [
        'src/config/settings.py',
        'config.py',
        '.env',
        'settings.json',
        'config.yaml',
        'config.yml'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            issues = check_for_hardcoded_secrets(config_file)
            if issues:
                audit_results['hardcoded_secrets_found'].extend(
                    [f"{config_file}: {issue}" for issue in issues]
                )
    
    return audit_results

# Decorator to ensure function arguments are sanitized in logs
def secure_function_logger(func):
    """Decorator to log function calls securely."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(f"secure.{func.__name__}")
        
        # Log entry with sanitized args
        try:
            sanitized_args = [sanitize_value(arg) for arg in args]
            sanitized_kwargs = sanitize_dict(kwargs)
            logger.debug(f"Calling {func.__name__} with args={sanitized_args}, kwargs={sanitized_kwargs}")
        except Exception as e:
            logger.debug(f"Calling {func.__name__} (failed to sanitize args: {e})")
        
        result = func(*args, **kwargs)
        
        # Log exit with sanitized result
        try:
            sanitized_result = sanitize_value(result)
            logger.debug(f"{func.__name__} returned: {sanitized_result}")
        except Exception as e:
            logger.debug(f"{func.__name__} returned (failed to sanitize: {e})")
        
        return result
    
    return wrapper

def main():
    """
    Main function to run security audit and demonstrate security utilities.
    """
    print("Running Security Audit for llmXive Pipeline")
    print("=" * 50)
    
    # Run audit
    audit_results = audit_security_config()
    
    print("\nEnvironment Variable Status:")
    for key, status in audit_results['env_vars_checked'].items():
        status_str = "✓ SET" if status else "✗ MISSING"
        print(f"  {key}: {status_str}")
    
    if audit_results['hardcoded_secrets_found']:
        print("\n⚠️  Potential Hardcoded Secrets Found:")
        for issue in audit_results['hardcoded_secrets_found']:
            print(f"  - {issue}")
    else:
        print("\n✓ No hardcoded secrets detected in configuration files.")
    
    if audit_results['security_warnings']:
        print("\n⚠️  Security Warnings:")
        for warning in audit_results['security_warnings']:
            print(f"  - {warning}")
    else:
        print("\n✓ No security warnings.")
    
    # Demonstrate secure logging
    print("\nDemonstrating Secure Logging:")
    secure_logger_instance = secure_logger("test_secure_logger")
    test_data = {
        'package_name': 'express',
        'api_key': 'ghp_1234567890abcdefghijklmnopqrstuvwxyz',
        'npm_token': 'npm_abcdefghijklmnopqrstuvwx1234567890',
        'version': '4.18.2'
    }
    secure_logger_instance.info(f"Processing package: {test_data}")
    
    # Validate API key formats
    print("\nAPI Key Format Validation:")
    test_keys = [
        ('ghp_1234567890abcdefghijklmnopqrstuvwxyz', 'github', True),
        ('npm_abcdefghijklmnopqrstuvwx1234567890', 'npm', True),
        ('your_api_key_here', 'generic', False),
        ('valid_generic_key_12345', 'generic', True),
    ]
    
    for key, key_type, expected in test_keys:
        result = validate_api_key_format(key, key_type)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {key_type} key: {result} (expected {expected})")
    
    print("\nSecurity audit complete.")
    return audit_results

if __name__ == "__main__":
    main()
