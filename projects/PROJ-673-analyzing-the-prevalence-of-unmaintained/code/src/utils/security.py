"""
Security utilities for the NPM dependency analysis pipeline.

This module provides tools for:
- Secret redaction and sanitization
- Environment variable validation
- Hardcoded secret detection
- Secure logging
- API key format validation
"""

import os
import re
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from functools import wraps

# Common patterns for sensitive data
SECRET_PATTERNS = [
    r'api[_-]?key',
    r'password',
    r'secret',
    r'token',
    r'auth',
    r'credential',
    r'private[_-]?key',
    r'access[_-]?key',
    r'client[_-]?secret',
]

# Common API key formats
API_KEY_FORMATS = {
    'npm': r'^npm_[a-zA-Z0-9]{36}$',
    'github': r'^gh[pousr]_[A-Za-z0-9_]{36,}$',
    'generic': r'^[a-zA-Z0-9]{32,}$',
}

class SecretRedactionError(Exception):
    """Raised when a secret is detected in logs or outputs."""
    pass


def sanitize_value(value: Any, pattern: str = None) -> str:
    """
    Sanitize a value by redacting sensitive information.
    
    Args:
        value: The value to sanitize
        pattern: Optional regex pattern for specific redaction
        
    Returns:
        Sanitized string with sensitive data redacted
    """
    if value is None:
        return "None"
        
    str_value = str(value)
    
    # Check if this looks like a secret key
    if pattern:
        if re.search(pattern, str_value, re.IGNORECASE):
            return "***REDACTED***"
    
    # Check against common secret patterns in the value itself
    for secret_pattern in SECRET_PATTERNS:
        if re.search(secret_pattern, str_value, re.IGNORECASE):
            # If the value contains the key name and looks like a value, redact it
            if re.search(r'[=:]\s*[a-zA-Z0-9_\-]{8,}', str_value, re.IGNORECASE):
                return "***REDACTED***"
    
    return str_value


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize a dictionary, redacting sensitive keys and values.
    
    Args:
        data: Dictionary to sanitize
        
    Returns:
        Sanitized dictionary
    """
    sanitized = {}
    for key, value in data.items():
        # Check if key looks like a secret
        is_secret_key = any(
            re.search(pattern, key, re.IGNORECASE)
            for pattern in SECRET_PATTERNS
        )
        
        if is_secret_key:
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict(item) if isinstance(item, dict) else sanitize_value(item)
                for item in value
            ]
        else:
            sanitized[key] = sanitize_value(value)
    
    return sanitized


def validate_env_vars(required_vars: List[str]) -> Dict[str, bool]:
    """
    Validate that required environment variables are set.
    
    Args:
        required_vars: List of required environment variable names
        
    Returns:
        Dictionary mapping variable names to validation status
    """
    results = {}
    for var in required_vars:
        value = os.getenv(var)
        results[var] = value is not None and len(value) > 0
        
        # Additional format validation for known API keys
        if var == 'NPM_API_KEY' and value:
            results[var] = bool(re.match(API_KEY_FORMATS['npm'], value))
        elif var == 'GITHUB_TOKEN' and value:
            results[var] = bool(re.match(API_KEY_FORMATS['github'], value))
    
    return results


def check_for_hardcoded_secrets(code_file: Path) -> List[Dict[str, Any]]:
    """
    Scan a file for potential hardcoded secrets.
    
    Args:
        code_file: Path to the file to scan
        
    Returns:
        List of findings with location and type
    """
    findings = []
    
    try:
        with open(code_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logging.warning(f"Could not read file {code_file}: {e}")
        return findings
    
    for line_num, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith('#'):
            continue
        
        # Skip lines with explicit redaction markers
        if 'REDACTED' in line or '***' in line:
            continue
        
        # Check for potential secrets
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Check if it's an assignment
                if re.search(r'[=:]\s*["\'][^"\']{8,}["\']', line):
                    findings.append({
                        'file': str(code_file),
                        'line': line_num,
                        'pattern': pattern,
                        'context': line.strip()[:100],
                        'severity': 'warning'
                    })
    
    return findings


def validate_api_key_format(api_key: str, provider: str = 'generic') -> bool:
    """
    Validate an API key against known formats.
    
    Args:
        api_key: The API key to validate
        provider: The provider (npm, github, generic)
        
    Returns:
        True if the key matches the expected format
    """
    if not api_key or not isinstance(api_key, str):
        return False
        
    pattern = API_KEY_FORMATS.get(provider, API_KEY_FORMATS['generic'])
    return bool(re.match(pattern, api_key))


def secure_logger(logger: logging.Logger, sensitive_keys: List[str] = None) -> logging.Logger:
    """
    Wrap a logger to automatically redact sensitive information.
    
    Args:
        logger: The logger to wrap
        sensitive_keys: List of keys to consider sensitive
        
    Returns:
        Wrapped logger instance
    """
    if sensitive_keys is None:
        sensitive_keys = SECRET_PATTERNS
    
    original_makeRecord = logger.makeRecord
    
    def safe_makeRecord(name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        record = original_makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)
        
        # Sanitize the message
        if isinstance(record.msg, str):
            record.msg = sanitize_value(record.msg)
        elif isinstance(record.msg, dict):
            record.msg = sanitize_dict(record.msg)
        
        # Sanitize extra fields
        if record.__dict__.get('extra'):
            record.__dict__['extra'] = sanitize_dict(record.__dict__['extra'])
        
        return record
    
    logger.makeRecord = safe_makeRecord
    return logger


def ensure_no_secrets_in_log_record(record: logging.LogRecord) -> bool:
    """
    Check if a log record contains potential secrets.
    
    Args:
        record: The log record to check
        
    Returns:
        True if no secrets detected, False otherwise
    """
    msg_str = str(record.msg)
    
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, msg_str, re.IGNORECASE):
            # Check if it looks like a value assignment
            if re.search(r'[=:]\s*[a-zA-Z0-9_\-]{8,}', msg_str, re.IGNORECASE):
                return False
    
    return True


class SecureHandler(logging.Handler):
    """
    A logging handler that automatically redacts sensitive information.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensitive_patterns = SECRET_PATTERNS
    
    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            
            # Redact sensitive patterns
            for pattern in self.sensitive_patterns:
                msg = re.sub(
                    rf'({pattern}[=:]\s*)["\']?([a-zA-Z0-9_\-]+)["\']?',
                    r'\1***REDACTED***',
                    msg,
                    flags=re.IGNORECASE
                )
            
            self.stream.write(msg + self.terminator)
        except Exception:
            self.handleError(record)


def secure_config_loader(config_path: Path) -> Dict[str, Any]:
    """
    Load a configuration file securely, redacting sensitive values.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary with sanitized configuration
    """
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse as JSON
        try:
            import json
            config = json.loads(content)
            return sanitize_dict(config)
        except json.JSONDecodeError:
            pass
        
        # Try to parse as YAML
        try:
            import yaml
            config = yaml.safe_load(content)
            if isinstance(config, dict):
                return sanitize_dict(config)
        except ImportError:
            pass
        
        return {'raw': sanitize_value(content)}
        
    except Exception as e:
        logging.error(f"Failed to load config securely: {e}")
        return {}


def audit_security_config() -> Dict[str, Any]:
    """
    Audit the current security configuration.
    
    Returns:
        Dictionary with security audit results
    """
    required_vars = ['NPM_API_KEY', 'GITHUB_TOKEN']
    validation_results = validate_env_vars(required_vars)
    
    # Check for hardcoded secrets in key files
    key_files = [
        Path('src/utils/security.py'),
        Path('src/config/settings.py'),
        Path('src/cli/collect_data.py'),
    ]
    
    hardcoded_findings = []
    for file_path in key_files:
        if file_path.exists():
            findings = check_for_hardcoded_secrets(file_path)
            hardcoded_findings.extend(findings)
    
    return {
        'environment_variables': validation_results,
        'hardcoded_secrets': hardcoded_findings,
        'all_secrets_valid': all(validation_results.values()) and len(hardcoded_findings) == 0,
        'recommendation': (
            "All secrets are properly configured via environment variables"
            if all(validation_results.values()) and len(hardcoded_findings) == 0
            else "Review security configuration and ensure secrets are not hardcoded"
        )
    }

def secure_function_logger(func):
    """
    Decorator to ensure function arguments are sanitized in logs.
    
    Args:
        func: The function to wrap
        
    Returns:
        Wrapped function with secure logging
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Log entry with sanitized args
        logging.info(
            f"Executing {func.__name__} with args: {sanitize_value(args)}, "
            f"kwargs: {sanitize_dict(kwargs)}"
        )
        
        try:
            result = func(*args, **kwargs)
            logging.info(f"Completed {func.__name__} successfully")
            return result
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {sanitize_value(str(e))}")
            raise
    
    return wrapper


def main():
    """
    Main function to demonstrate security utilities.
    """
    # Validate environment variables
    print("Validating environment variables...")
    results = validate_env_vars(['NPM_API_KEY', 'GITHUB_TOKEN'])
    for var, valid in results.items():
        print(f"  {var}: {'✓' if valid else '✗'}")
    
    # Audit security configuration
    print("\nAuditing security configuration...")
    audit = audit_security_config()
    print(f"  All secrets valid: {audit['all_secrets_valid']}")
    print(f"  Recommendation: {audit['recommendation']}")
    
    if audit['hardcoded_secrets']:
        print("\n  Found potential hardcoded secrets:")
        for finding in audit['hardcoded_secrets']:
            print(f"    - {finding['file']}:{finding['line']} - {finding['context']}")

if __name__ == '__main__':
    main()