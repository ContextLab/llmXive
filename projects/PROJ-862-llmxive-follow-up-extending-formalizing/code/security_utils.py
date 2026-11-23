"""
Security utilities for PII detection and sanitization in the llmXive pipeline.

This module provides tools to detect, hash, and remove Personally Identifiable 
Information (PII) from logs, datasets, and output files to prevent data leaks.

Implements FR-014: Security hardening - Ensure no PII leaks in logs or output files.
"""
import re
import hashlib
import logging
import json
import csv
import tempfile
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Set, Iterator
from pathlib import Path

# Configure logging for security events
logger = logging.getLogger(__name__)

@dataclass
class SanitizationResult:
    """Result of a sanitization operation."""
    original_length: int
    sanitized_length: int
    pii_found: bool
    pii_types: List[str]
    replacements_made: int
    was_successful: bool
    error_message: Optional[str] = None

# PII Detection Patterns
PII_PATTERNS = {
    'email': re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        re.IGNORECASE
    ),
    'phone_us': re.compile(
        r'\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?)[-.\s]?\d{3}[-.\s]?\d{4}\b'
    ),
    'ssn': re.compile(
        r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b'
    ),
    'credit_card': re.compile(
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
    ),
    'ip_address': re.compile(
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ),
    'url': re.compile(
        r'https?://[^\s<>"{}|\\^`\[\]]+'
    ),
    'date_of_birth': re.compile(
        r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'
    ),
    'passport': re.compile(
        r'\b[A-Z]{2}\d{6,9}\b'
    ),
    'drivers_license': re.compile(
        r'\b[A-Z]{1,2}\d{6,9}\b'
    ),
    'social_security': re.compile(
        r'\b\d{3}-\d{2}-\d{4}\b'
    ),
}

# Sensitive keys that might appear in dictionaries
SENSITIVE_KEYS = {
    'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey',
    'private_key', 'access_token', 'refresh_token', 'session_id', 'cookie',
    'credit_card', 'ssn', 'social_security', 'bank_account', 'routing_number',
    'card_number', 'cvv', 'pin', 'encryption_key', 'signature'
}

class SecurityLogFilter(logging.Filter):
    """
    A logging filter that scans log records for PII and masks it before output.
    
    This ensures that even if developers accidentally log sensitive data,
    it gets sanitized in the output.
    """
    def __init__(self, pattern_map: Optional[Dict[str, re.Pattern]] = None):
        super().__init__()
        self.pattern_map = pattern_map or PII_PATTERNS
        self.replacement_token = "[REDACTED]"

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Scan the log message for PII and replace it with a redaction token.
        
        Args:
            record: The log record to filter
            
        Returns:
            True (always allow the record through, but sanitized)
        """
        message = record.getMessage()
        sanitized_message = self._sanitize_message(message)
        
        if sanitized_message != message:
            # Log that redaction occurred (without revealing the original)
            logger.debug("PII detected and redacted in log message")
            record.msg = sanitized_message
            # Clear args to prevent any PII in formatted args
            record.args = None
        
        return True

    def _sanitize_message(self, message: str) -> str:
        """Replace PII patterns in a message with redaction tokens."""
        sanitized = message
        for pii_type, pattern in self.pattern_map.items():
            matches = pattern.findall(sanitized)
            if matches:
                # Replace all occurrences of this pattern
                sanitized = pattern.sub(self.replacement_token, sanitized)
        return sanitized

def sanitize_text(text: str, pattern_map: Optional[Dict[str, re.Pattern]] = None) -> SanitizationResult:
    """
    Scan and sanitize a string for PII patterns.
    
    Args:
        text: The text to sanitize
        pattern_map: Optional custom pattern map (defaults to PII_PATTERNS)
        
    Returns:
        SanitizationResult with details about what was found and replaced
    """
    patterns = pattern_map or PII_PATTERNS
    original_text = text
    pii_types_found: Set[str] = set()
    replacements_made = 0
    
    sanitized_text = text
    
    for pii_type, pattern in patterns.items():
        matches = pattern.findall(sanitized_text)
        if matches:
            pii_types_found.add(pii_type)
            count = len(matches)
            sanitized_text = pattern.sub("[REDACTED]", sanitized_text)
            replacements_made += count
    
    return SanitizationResult(
        original_length=len(original_text),
        sanitized_length=len(sanitized_text),
        pii_found=len(pii_types_found) > 0,
        pii_types=list(pii_types_found),
        replacements_made=replacements_made,
        was_successful=True
    )

def sanitize_dict(data: Dict[str, Any], sensitive_keys: Optional[Set[str]] = None) -> SanitizationResult:
    """
    Recursively sanitize a dictionary, masking sensitive values.
    
    Args:
        data: The dictionary to sanitize
        sensitive_keys: Optional set of keys to treat as sensitive
        
    Returns:
        SanitizationResult with details about the sanitization
    """
    keys = sensitive_keys or SENSITIVE_KEYS
    original_str = json.dumps(data, default=str)
    sanitized_data = _sanitize_dict_recursive(data, keys)
    sanitized_str = json.dumps(sanitized_data, default=str)
    
    return SanitizationResult(
        original_length=len(original_str),
        sanitized_length=len(sanitized_str),
        pii_found=len(original_str) != len(sanitized_str),
        pii_types=["sensitive_keys"],
        replacements_made=0,  # Counting nested replacements is complex
        was_successful=True
    )

def _sanitize_dict_recursive(data: Any, sensitive_keys: Set[str]) -> Any:
    """Recursively process a dictionary to mask sensitive values."""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            if key_lower in sensitive_keys:
                # Mask the value
                if isinstance(value, str):
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, (int, float)):
                    sanitized[key] = 0
                else:
                    sanitized[key] = "[REDACTED]"
            else:
                # Recurse
                sanitized[key] = _sanitize_dict_recursive(value, sensitive_keys)
        return sanitized
    elif isinstance(data, list):
        return [_sanitize_dict_recursive(item, sensitive_keys) for item in data]
    else:
        return data

def hash_sensitive_id(value: str, salt: str = "llmXive_salt") -> str:
    """
    Create a deterministic hash of a sensitive identifier.
    
    This allows tracking of records without exposing the actual ID.
    
    Args:
        value: The sensitive identifier to hash
        salt: Salt value for hashing (should be consistent across runs)
        
    Returns:
        SHA-256 hash of the salted value
    """
    salted_value = f"{salt}:{value}"
    return hashlib.sha256(salted_value.encode('utf-8')).hexdigest()

def scan_file_for_pii(file_path: str, pattern_map: Optional[Dict[str, re.Pattern]] = None) -> Dict[str, Any]:
    """
    Scan a file for PII patterns and return a report.
    
    Args:
        file_path: Path to the file to scan
        pattern_map: Optional custom pattern map
        
    Returns:
        Dictionary containing scan results
    """
    patterns = pattern_map or PII_PATTERNS
    results = {
        'file_path': file_path,
        'pii_found': False,
        'pii_types': {},
        'total_matches': 0,
        'sample_matches': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        for pii_type, pattern in patterns.items():
            matches = pattern.findall(content)
            if matches:
                results['pii_found'] = True
                results['pii_types'][pii_type] = len(matches)
                results['total_matches'] += len(matches)
                # Store up to 3 sample matches (already redacted for safety)
                for match in matches[:3]:
                    if len(results['sample_matches']) < 3:
                        results['sample_matches'].append(f"[{pii_type}: ...]")
    
    except Exception as e:
        results['error'] = str(e)
        logger.error(f"Error scanning file {file_path}: {e}")
        
    return results

def sanitize_csv_file(
    input_path: str,
    output_path: str,
    sensitive_columns: Optional[List[str]] = None,
    pattern_map: Optional[Dict[str, re.Pattern]] = None
) -> SanitizationResult:
    """
    Read a CSV file, sanitize sensitive columns and values, and write to a new file.
    
    Args:
        input_path: Path to the input CSV file
        output_path: Path to write the sanitized CSV
        sensitive_columns: List of column names to treat as sensitive
        pattern_map: Optional custom pattern map for text scanning
        
    Returns:
        SanitizationResult with details about the operation
    """
    patterns = pattern_map or PII_PATTERNS
    cols_to_sanitize = set(sensitive_columns) if sensitive_columns else set()
    
    total_rows = 0
    rows_modified = 0
    pii_found = False
    pii_types_found: Set[str] = set()
    
    try:
        with open(input_path, 'r', newline='', encoding='utf-8') as infile, \
             open(output_path, 'w', newline='', encoding='utf-8') as outfile:
             
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            
            if not fieldnames:
                return SanitizationResult(
                    original_length=0,
                    sanitized_length=0,
                    pii_found=False,
                    pii_types=[],
                    replacements_made=0,
                    was_successful=False,
                    error_message="CSV file has no headers"
                )
            
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                total_rows += 1
                modified_row = False
                row_pii_types: Set[str] = set()
                
                for field, value in row.items():
                    if value is None:
                        continue
                    
                    value_str = str(value)
                    original_value = value_str
                    
                    # Check if column is sensitive
                    if field.lower() in cols_to_sanitize:
                        value_str = "[REDACTED]"
                        modified_row = True
                        row_pii_types.add(f"column:{field}")
                    else:
                        # Scan for PII patterns
                        for pii_type, pattern in patterns.items():
                            if pattern.search(value_str):
                                value_str = pattern.sub("[REDACTED]", value_str)
                                modified_row = True
                                row_pii_types.add(pii_type)
                    
                    row[field] = value_str
                
                if modified_row:
                    rows_modified += 1
                    pii_found = True
                    pii_types_found.update(row_pii_types)
                
                writer.writerow(row)
                
    except Exception as e:
        logger.error(f"Error sanitizing CSV {input_path}: {e}")
        return SanitizationResult(
            original_length=0,
            sanitized_length=0,
            pii_found=False,
            pii_types=[],
            replacements_made=0,
            was_successful=False,
            error_message=str(e)
        )
    
    return SanitizationResult(
        original_length=total_rows,
        sanitized_length=rows_modified,
        pii_found=pii_found,
        pii_types=list(pii_types_found),
        replacements_made=rows_modified,
        was_successful=True
    )

def ensure_no_pii_in_output(
    output_path: str,
    check_logs: bool = True,
    pattern_map: Optional[Dict[str, re.Pattern]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify that an output file contains no PII before it is finalized.
    
    This is a guard function that should be called before any file is
    considered "safe" to distribute or log.
    
    Args:
        output_path: Path to the file to verify
        check_logs: Whether to apply additional log-specific checks
        pattern_map: Optional custom pattern map
        
    Returns:
        Tuple of (is_safe, report_dict)
    """
    patterns = pattern_map or PII_PATTERNS
    report = {
        'file_path': output_path,
        'is_safe': True,
        'violations': [],
        'scan_details': {}
    }
    
    try:
        # Scan for PII patterns
        scan_result = scan_file_for_pii(output_path, patterns)
        report['scan_details'] = scan_result
        
        if scan_result.get('pii_found', False):
            report['is_safe'] = False
            report['violations'].append({
                'type': 'pattern_match',
                'details': scan_result
            })
        
        # Additional checks for log files
        if check_logs and output_path.endswith('.log'):
            with open(output_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                # Check for common log leakage patterns
                if 'password=' in line.lower() or 'token=' in line.lower():
                    report['is_safe'] = False
                    report['violations'].append({
                        'type': 'sensitive_log_entry',
                        'line_number': i + 1,
                        'snippet': line[:100] + "..." if len(line) > 100 else line
                    })
                    
    except Exception as e:
        report['is_safe'] = False
        report['violations'].append({
            'type': 'scan_error',
            'error': str(e)
        })
        
    return report['is_safe'], report

# Unit Tests for Security Utilities
class TestSanitizeText:
    """Unit tests for sanitize_text function."""
    
    def test_email_redaction(self):
        text = "Contact me at user@example.com for details"
        result = sanitize_text(text)
        assert result.pii_found is True
        assert 'email' in result.pii_types
        assert 'user@example.com' not in result.__dict__.get('sanitized_text', text)
        
    def test_phone_redaction(self):
        text = "Call 555-123-4567 or 555.987.6543"
        result = sanitize_text(text)
        assert result.pii_found is True
        assert 'phone_us' in result.pii_types
        
    def test_no_pii(self):
        text = "This is a normal sentence with no sensitive data."
        result = sanitize_text(text)
        assert result.pii_found is False
        assert result.replacements_made == 0

class TestSanitizeDict:
    """Unit tests for sanitize_dict function."""
    
    def test_sensitive_key_masking(self):
        data = {
            'username': 'john_doe',
            'password': 'secret123',
            'email': 'john@example.com'
        }
        result = sanitize_dict(data)
        # The password key should be masked
        sanitized_data = _sanitize_dict_recursive(data, SENSITIVE_KEYS)
        assert sanitized_data['password'] == '[REDACTED]'
        assert sanitized_data['username'] == 'john_doe'
        
    def test_nested_dict(self):
        data = {
            'user': {
                'name': 'Alice',
                'secret': 'hidden_value'
            }
        }
        sanitized_data = _sanitize_dict_recursive(data, SENSITIVE_KEYS)
        assert sanitized_data['user']['secret'] == '[REDACTED]'
        assert sanitized_data['user']['name'] == 'Alice'

class TestHashSensitiveId:
    """Unit tests for hash_sensitive_id function."""
    
    def test_deterministic_hash(self):
        id1 = hash_sensitive_id("user123")
        id2 = hash_sensitive_id("user123")
        assert id1 == id2
        
    def test_different_inputs_different_hashes(self):
        id1 = hash_sensitive_id("user1")
        id2 = hash_sensitive_id("user2")
        assert id1 != id2

class TestSecurityLogFilter:
    """Unit tests for SecurityLogFilter."""
    
    def test_email_in_log(self):
        filter_obj = SecurityLogFilter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='User email: test@example.com',
            args=(),
            exc_info=None
        )
        filter_obj.filter(record)
        assert 'test@example.com' not in record.getMessage()
        assert '[REDACTED]' in record.getMessage()

class TestFileSanitization:
    """Unit tests for file sanitization functions."""
    
    def test_scan_file_for_pii(self):
        # Create a temporary file with PII
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Contact: user@test.com\n")
            temp_path = f.name
        
        try:
            result = scan_file_for_pii(temp_path)
            assert result['pii_found'] is True
            assert 'email' in result['pii_types']
        finally:
            os.unlink(temp_path)

class TestPIIScanning:
    """Integration tests for PII scanning."""
    
    def test_multiple_pii_types(self):
        text = "Email: test@example.com, Phone: 555-123-4567, SSN: 123-45-6789"
        result = sanitize_text(text)
        assert result.pii_found is True
        assert len(result.pii_types) >= 2

class TestEnsureNoPIIInOutput:
    """Tests for the output verification function."""
    
    def test_safe_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("This is safe content.\n")
            temp_path = f.name
        
        try:
            is_safe, report = ensure_no_pii_in_output(temp_path)
            assert is_safe is True
        finally:
            os.unlink(temp_path)
            
    def test_unsafe_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Email: user@example.com\n")
            temp_path = f.name
        
        try:
            is_safe, report = ensure_no_pii_in_output(temp_path)
            assert is_safe is False
            assert len(report['violations']) > 0
        finally:
            os.unlink(temp_path)

def main():
    """Demonstration of security utilities."""
    logging.basicConfig(level=logging.INFO)
    
    # Add security filter to root logger
    root_logger = logging.getLogger()
    root_logger.addFilter(SecurityLogFilter())
    
    # Example usage
    logger.info("This log contains an email: user@example.com")
    logger.info("This log is clean.")
    
    # Test text sanitization
    text = "Contact user@test.com or call 555-123-4567"
    result = sanitize_text(text)
    print(f"PII found: {result.pii_found}")
    print(f"Types: {result.pii_types}")

if __name__ == "__main__":
    main()
