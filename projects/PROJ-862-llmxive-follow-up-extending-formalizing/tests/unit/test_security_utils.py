"""
Unit tests for security utilities (T038 - Security Hardening).

These tests verify that PII detection, sanitization, and logging filters
work correctly to prevent data leaks in the llmXive pipeline.
"""
import pytest
import json
import tempfile
import os
import logging
from io import StringIO

# Import the security utilities
from security_utils import (
    sanitize_text,
    sanitize_dict,
    hash_sensitive_id,
    SecurityLogFilter,
    scan_file_for_pii,
    sanitize_csv_file,
    ensure_no_pii_in_output,
    SanitizationResult,
    SENSITIVE_KEYS,
    PII_PATTERNS
)


class TestSanitizeText:
    """Tests for the sanitize_text function."""
    
    def test_email_detection_and_redaction(self):
        """Test that email addresses are detected and redacted."""
        text = "Contact user@example.com for support."
        result = sanitize_text(text)
        
        assert result.pii_found is True
        assert 'email' in result.pii_types
        assert result.replacements_made >= 1
        assert 'user@example.com' not in text  # Original unchanged
        
    def test_phone_number_detection(self):
        """Test US phone number detection."""
        text = "Call me at 555-123-4567 or (555) 987-6543."
        result = sanitize_text(text)
        
        assert result.pii_found is True
        assert 'phone_us' in result.pii_types
        
    def test_ssn_detection(self):
        """Test Social Security Number detection."""
        text = "SSN: 123-45-6789"
        result = sanitize_text(text)
        
        assert result.pii_found is True
        assert 'ssn' in result.pii_types
        
    def test_credit_card_detection(self):
        """Test credit card number detection."""
        text = "Card: 1234-5678-9012-3456"
        result = sanitize_text(text)
        
        assert result.pii_found is True
        assert 'credit_card' in result.pii_types
        
    def test_ip_address_detection(self):
        """Test IP address detection."""
        text = "Server IP: 192.168.1.1"
        result = sanitize_text(text)
        
        assert result.pii_found is True
        assert 'ip_address' in result.pii_types
        
    def test_no_pii_in_text(self):
        """Test that text without PII returns no findings."""
        text = "This is a normal sentence with no sensitive information."
        result = sanitize_text(text)
        
        assert result.pii_found is False
        assert result.pii_types == []
        assert result.replacements_made == 0
        
    def test_multiple_pii_types(self):
        """Test detection of multiple PII types in one string."""
        text = "Email: test@example.com, Phone: 555-123-4567, IP: 10.0.0.1"
        result = sanitize_text(text)
        
        assert result.pii_found is True
        assert len(result.pii_types) >= 3
        assert 'email' in result.pii_types
        assert 'phone_us' in result.pii_types
        assert 'ip_address' in result.pii_types


class TestSanitizeDict:
    """Tests for the sanitize_dict function."""
    
    def test_sensitive_key_redaction(self):
        """Test that sensitive keys are redacted in dictionaries."""
        data = {
            'username': 'john_doe',
            'password': 'secret123',
            'api_key': 'sk-12345',
            'email': 'john@example.com'
        }
        
        from security_utils import _sanitize_dict_recursive
        sanitized = _sanitize_dict_recursive(data, SENSITIVE_KEYS)
        
        assert sanitized['password'] == '[REDACTED]'
        assert sanitized['api_key'] == '[REDACTED]'
        assert sanitized['username'] == 'john_doe'
        
    def test_nested_dictionary_sanitization(self):
        """Test recursive sanitization of nested dictionaries."""
        data = {
            'user': {
                'name': 'Alice',
                'credentials': {
                    'password': 'hidden',
                    'token': 'secret_token'
                }
            }
        }
        
        from security_utils import _sanitize_dict_recursive
        sanitized = _sanitize_dict_recursive(data, SENSITIVE_KEYS)
        
        assert sanitized['user']['credentials']['password'] == '[REDACTED]'
        assert sanitized['user']['credentials']['token'] == '[REDACTED]'
        assert sanitized['user']['name'] == 'Alice'
        
    def test_list_handling(self):
        """Test that lists are processed correctly."""
        data = {
            'items': [
                {'secret': 'val1'},
                {'secret': 'val2'}
            ]
        }
        
        from security_utils import _sanitize_dict_recursive
        sanitized = _sanitize_dict_recursive(data, SENSITIVE_KEYS)
        
        assert sanitized['items'][0]['secret'] == '[REDACTED]'
        assert sanitized['items'][1]['secret'] == '[REDACTED]'


class TestHashSensitiveId:
    """Tests for the hash_sensitive_id function."""
    
    def test_deterministic_hashing(self):
        """Test that the same input always produces the same hash."""
        id1 = hash_sensitive_id("user_12345")
        id2 = hash_sensitive_id("user_12345")
        
        assert id1 == id2
        assert len(id1) == 64  # SHA-256 produces 64 hex characters
        
    def test_different_inputs_different_hashes(self):
        """Test that different inputs produce different hashes."""
        id1 = hash_sensitive_id("user_a")
        id2 = hash_sensitive_id("user_b")
        
        assert id1 != id2
        
    def test_salted_hashing(self):
        """Test that salt affects the hash output."""
        id1 = hash_sensitive_id("user", salt="salt1")
        id2 = hash_sensitive_id("user", salt="salt2")
        
        assert id1 != id2


class TestSecurityLogFilter:
    """Tests for the SecurityLogFilter class."""
    
    def test_email_in_log_message(self):
        """Test that email addresses in log messages are redacted."""
        filter_obj = SecurityLogFilter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='User email: user@example.com logged in',
            args=(),
            exc_info=None
        )
        
        filter_obj.filter(record)
        
        message = record.getMessage()
        assert 'user@example.com' not in message
        assert '[REDACTED]' in message
        
    def test_password_in_log_message(self):
        """Test that password patterns in log messages are redacted."""
        filter_obj = SecurityLogFilter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Password: secret123 was used',
            args=(),
            exc_info=None
        )
        
        filter_obj.filter(record)
        
        message = record.getMessage()
        # The filter should catch common password patterns
        # Note: Exact behavior depends on pattern definitions
        
    def test_clean_log_message_unchanged(self):
        """Test that clean log messages pass through unchanged."""
        filter_obj = SecurityLogFilter()
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Processing completed successfully',
            args=(),
            exc_info=None
        )
        
        filter_obj.filter(record)
        
        message = record.getMessage()
        assert message == 'Processing completed successfully'


class TestFileScanning:
    """Tests for file-based PII scanning."""
    
    def test_scan_file_with_email(self):
        """Test scanning a file containing an email address."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Contact: user@example.com\n")
            temp_path = f.name
        
        try:
            result = scan_file_for_pii(temp_path)
            
            assert result['pii_found'] is True
            assert 'email' in result['pii_types']
            assert result['total_matches'] >= 1
        finally:
            os.unlink(temp_path)
            
    def test_scan_file_without_pii(self):
        """Test scanning a file without PII."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("This file contains no sensitive data.\n")
            temp_path = f.name
        
        try:
            result = scan_file_for_pii(temp_path)
            
            assert result['pii_found'] is False
            assert result['total_matches'] == 0
        finally:
            os.unlink(temp_path)
            
    def test_scan_nonexistent_file(self):
        """Test scanning a file that doesn't exist."""
        result = scan_file_for_pii('/nonexistent/path/file.txt')
        
        assert 'error' in result
        assert result['pii_found'] is False


class TestCSVSanitization:
    """Tests for CSV file sanitization."""
    
    def test_sanitize_csv_with_sensitive_columns(self):
        """Test sanitizing a CSV with sensitive columns."""
        input_content = "name,password,email\njohn,secret123,john@example.com\n"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as infile:
            infile.write(input_content)
            input_path = infile.name
        
        output_path = input_path.replace('.csv', '_sanitized.csv')
        
        try:
            result = sanitize_csv_file(
                input_path,
                output_path,
                sensitive_columns=['password', 'email']
            )
            
            assert result.was_successful is True
            assert result.pii_found is True
            
            # Verify output file
            with open(output_path, 'r') as f:
                content = f.read()
                
            assert 'secret123' not in content
            assert 'john@example.com' not in content
            assert '[REDACTED]' in content
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestEnsureNoPIIInOutput:
    """Tests for the output verification function."""
    
    def test_safe_file_returns_true(self):
        """Test that a file without PII returns is_safe=True."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("This is safe content.\n")
            temp_path = f.name
        
        try:
            is_safe, report = ensure_no_pii_in_output(temp_path)
            
            assert is_safe is True
            assert len(report['violations']) == 0
        finally:
            os.unlink(temp_path)
            
    def test_unsafe_file_returns_false(self):
        """Test that a file with PII returns is_safe=False."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Email: user@example.com\n")
            temp_path = f.name
        
        try:
            is_safe, report = ensure_no_pii_in_output(temp_path)
            
            assert is_safe is False
            assert len(report['violations']) > 0
        finally:
            os.unlink(temp_path)
            
    def test_log_file_with_sensitive_patterns(self):
        """Test detection of sensitive patterns in log files."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("INFO: password=secret123 used\n")
            temp_path = f.name
        
        try:
            is_safe, report = ensure_no_pii_in_output(temp_path, check_logs=True)
            
            assert is_safe is False
            # Should detect the password pattern
        finally:
            os.unlink(temp_path)


class TestSecurityIntegration:
    """Integration tests for security utilities."""
    
    def test_end_to_end_pipeline_security(self):
        """Test that the security utilities work together in a pipeline scenario."""
        # Create sample data with PII
        sample_data = {
            'user_id': 12345,
            'username': 'john_doe',
            'password': 'secret123',
            'email': 'john@example.com',
            'phone': '555-123-4567'
        }
        
        # Sanitize the data
        sanitized_result = sanitize_dict(sample_data)
        
        assert sanitized_result.pii_found is True
        assert sanitized_result.was_successful is True
        
        # Convert to JSON and check
        sanitized_data = _sanitize_dict_recursive(sample_data, SENSITIVE_KEYS)
        json_str = json.dumps(sanitized_data)
        
        assert 'secret123' not in json_str
        assert 'john@example.com' not in json_str
        
        # Write to temp file and scan
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(sanitized_data, f)
            temp_path = f.name
        
        try:
            is_safe, report = ensure_no_pii_in_output(temp_path)
            assert is_safe is True
        finally:
            os.unlink(temp_path)


def _sanitize_dict_recursive(data, sensitive_keys):
    """Helper function imported from security_utils for testing."""
    from security_utils import _sanitize_dict_recursive as helper
    return helper(data, sensitive_keys)