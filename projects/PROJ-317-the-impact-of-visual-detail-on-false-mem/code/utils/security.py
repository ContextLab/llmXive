"""
Security utilities for the llmXive research pipeline.

This module provides functions to sanitize log messages and data artifacts
to prevent Personally Identifiable Information (PII) leakage.
"""
import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

# Patterns for common PII
PII_PATTERNS = {
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'phone_us': re.compile(r'\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?)[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    'ssn': re.compile(r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b'),
    # Credit card pattern (basic Luhn check not included for performance, just regex)
    'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
    # IP address (IPv4)
    'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    # UUID
    'uuid': re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I),
}

REDACTION_MARKER = "[REDACTED]"

def sanitize_string(text: str, pattern_type: Optional[str] = None) -> str:
    """
    Sanitize a string by replacing PII with redaction markers.
    
    Args:
        text: The input string to sanitize.
        pattern_type: Optional specific pattern type to target (e.g., 'email').
                     If None, all known PII patterns are scanned.
                     
    Returns:
        The sanitized string with PII replaced by [REDACTED].
    """
    if not text:
        return text
    
    patterns_to_use = [PII_PATTERNS[pattern_type]] if pattern_type else PII_PATTERNS.values()
    
    sanitized = text
    for pattern in patterns_to_use:
        sanitized = pattern.sub(REDACTION_MARKER, sanitized)
        
    return sanitized

def sanitize_dict(data: Dict[str, Any], sensitive_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Recursively sanitize a dictionary, redacting values for sensitive keys
    and scanning all string values for PII patterns.
    
    Args:
        data: The dictionary to sanitize.
        sensitive_keys: A list of keys that should always be redacted regardless of content.
                     
    Returns:
        A new dictionary with sanitized values.
    """
    if sensitive_keys is None:
        sensitive_keys = []
        
    sanitized_data = {}
    
    for key, value in data.items():
        if key in sensitive_keys:
            # Force redaction for known sensitive keys
            if isinstance(value, str):
                sanitized_data[key] = REDACTION_MARKER
            else:
                sanitized_data[key] = "[REDACTED_VALUE]"
        elif isinstance(value, dict):
            sanitized_data[key] = sanitize_dict(value, sensitive_keys)
        elif isinstance(value, list):
            sanitized_data[key] = [
                sanitize_string(item) if isinstance(item, str) else item 
                for item in value
            ]
        elif isinstance(value, str):
            sanitized_data[key] = sanitize_string(value)
        else:
            sanitized_data[key] = value
            
    return sanitized_data

def sanitize_log_message(message: str) -> str:
    """
    Sanitize a log message before it is written to disk or console.
    
    This ensures that accidental logging of participant emails, IDs, or
    other PII does not occur in log files.
    
    Args:
        message: The log message string.
        
    Returns:
        The sanitized message.
    """
    return sanitize_string(message)

class SanitizedLogger(logging.LoggerAdapter):
    """
    A LoggerAdapter that automatically sanitizes log messages to prevent PII leakage.
    
    Usage:
        logger = SanitizedLogger(logging.getLogger(__name__), {})
        logger.info(f"Participant {email} completed session") 
        # Will output: Participant [REDACTED] completed session
    """
    def process(self, msg, kwargs):
        # Sanitize the message string
        safe_msg = sanitize_log_message(str(msg))
        return safe_msg, kwargs

def ensure_log_safety(file_path: Union[str, Path], sensitive_keys: Optional[List[str]] = None) -> bool:
    """
    Scan an existing log file for potential PII leakage and return a report.
    
    This is a defensive check to run on existing logs to ensure no PII was
    accidentally written during previous runs.
    
    Args:
        file_path: Path to the log file to scan.
        sensitive_keys: Keys to treat as sensitive if scanning structured logs (JSON).
        
    Returns:
        True if no PII was found, False if PII was detected.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return True
        
    found_pii = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                for p_name, pattern in PII_PATTERNS.items():
                    matches = pattern.findall(line)
                    if matches:
                        found_pii.append({
                            'line': line_num,
                            'type': p_name,
                            'snippet': line.strip()[:100] # Truncate for safety in report
                        })
    except Exception as e:
        # If we can't read it, we can't verify safety
        return False
        
    if found_pii:
        # In a real system, we might alert or fail the build
        return False
        
    return True

def main():
    """CLI entry point for security checks."""
    import argparse
    import sys
    from config import get_logs_dir, get_project_root
    
    parser = argparse.ArgumentParser(description="Security hardening and PII scan")
    parser.add_argument('--scan-dir', type=str, help="Directory to scan for PII")
    parser.add_argument('--check-logs', action='store_true', help="Scan log directory for PII")
    
    args = parser.parse_args()
    
    if args.check_logs:
        log_dir = get_logs_dir()
        print(f"Scanning log directory: {log_dir}")
        all_safe = True
        for log_file in Path(log_dir).glob("*.log"):
            if not ensure_log_safety(log_file):
                print(f"⚠️ PII DETECTED in {log_file}")
                all_safe = False
        
        if all_safe:
            print("✅ All log files are safe (no PII detected).")
            sys.exit(0)
        else:
            print("❌ PII detected in logs. Please review and sanitize.")
            sys.exit(1)
            
    if args.scan_dir:
        scan_path = Path(args.scan_dir)
        if not scan_path.exists():
            print(f"Error: Directory {scan_path} does not exist.")
            sys.exit(1)
            
        # Simple recursive scan for text files
        found_any = False
        for file_path in scan_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.log', '.txt', '.json', '.csv']:
                if not ensure_log_safety(file_path):
                    print(f"⚠️ PII detected in {file_path}")
                    found_any = True
                    
        if not found_any:
            print("✅ Scan complete. No PII detected.")
        else:
            print("❌ PII detected in scanned files.")
            sys.exit(1)

if __name__ == "__main__":
    main()
