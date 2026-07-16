"""
Unit tests for security sanitization utilities.

These tests verify that PII is correctly detected and masked in log messages
and data structures to prevent data leakage.
"""
import pytest
import re
from code.utils.security import (
    sanitize_string,
    sanitize_dict,
    sanitize_log_message,
    SanitizedLogger,
    ensure_log_safety,
    PII_PATTERNS,
    PII_REPLACEMENTS
)
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging


class TestSanitizeString:
    """Tests for the sanitize_string function."""
    
    def test_email_masking(self):
        """Test that email addresses are masked."""
        message = "Contact us at support@example.com for help"
        sanitized = sanitize_string(message)
        assert '[EMAIL_MASKED]' in sanitized
        assert 'support@example.com' not in sanitized
    
    def test_phone_masking(self):
        """Test that US phone numbers are masked."""
        test_cases = [
            "Call +1-555-123-4567 today",
            "Phone: (555) 123-4567",
            "Number: 5551234567"
        ]
        for message in test_cases:
            sanitized = sanitize_string(message)
            assert '[PHONE_MASKED]' in sanitized
            assert not re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', sanitized)
    
    def test_ssn_masking(self):
        """Test that SSN patterns are masked."""
        message = "SSN: 123-45-6789"
        sanitized = sanitize_string(message)
        assert '[SSN_MASKED]' in sanitized
        assert '123-45-6789' not in sanitized
    
    def test_credit_card_masking(self):
        """Test that credit card numbers are masked."""
        test_cases = [
            "Card: 4111-1111-1111-1111",
            "Number: 4111111111111111"
        ]
        for message in test_cases:
            sanitized = sanitize_string(message)
            assert '[CC_MASKED]' in sanitized
    
    def test_ip_address_masking(self):
        """Test that IP addresses are masked."""
        message = "User connected from 192.168.1.100"
        sanitized = sanitize_string(message)
        assert '[IP_MASKED]' in sanitized
        assert '192.168.1.100' not in sanitized
    
    def test_participant_id_masking(self):
        """Test that participant IDs are masked."""
        message = "Participant PID-123456 completed the session"
        sanitized = sanitize_string(message)
        assert '[PID_MASKED]' in sanitized
        assert 'PID-123456' not in sanitized
    
    def test_no_pii_unchanged(self):
        """Test that messages without PII remain unchanged."""
        message = "Normal log message without any sensitive data"
        sanitized = sanitize_string(message)
        assert sanitized == message
    
    def test_non_string_input(self):
        """Test handling of non-string inputs."""
        assert sanitize_string(123) == "123"
        assert sanitize_string(None) == "None"
    
    def test_mask_sensitive_false(self):
        """Test that PII masking can be disabled."""
        message = "Email: test@example.com"
        sanitized = sanitize_string(message, mask_sensitive=False)
        assert sanitized == message


class TestSanitizeDict:
    """Tests for the sanitize_dict function."""
    
    def test_sensitive_key_masking(self):
        """Test that values of sensitive keys are masked."""
        data = {
            'email': 'test@example.com',
            'phone': '555-123-4567',
            'normal_key': 'normal_value'
        }
        sanitized = sanitize_dict(data)
        assert sanitized['email'] == '[SENSITIVE]'
        assert sanitized['phone'] == '[SENSITIVE]'
        assert sanitized['normal_key'] == 'normal_value'
    
    def test_nested_dict_sanitization(self):
        """Test sanitization of nested dictionaries."""
        data = {
            'user': {
                'email': 'nested@example.com',
                'profile': {
                    'name': 'John Doe',
                    'ssn': '123-45-6789'
                }
            }
        }
        sanitized = sanitize_dict(data)
        assert sanitized['user']['email'] == '[SENSITIVE]'
        assert sanitized['user']['profile']['ssn'] == '[SENSITIVE]'
    
    def test_string_values_sanitized(self):
        """Test that string values are also sanitized for PII patterns."""
        data = {
            'message': 'Contact john@example.com for details'
        }
        sanitized = sanitize_dict(data)
        assert '[EMAIL_MASKED]' in sanitized['message']
    
    def test_non_dict_input(self):
        """Test handling of non-dict inputs."""
        assert sanitize_dict("not a dict") == "not a dict"
        assert sanitize_dict(123) == 123
    
    def test_mask_values_false(self):
        """Test that sensitive key masking can be disabled."""
        data = {'email': 'test@example.com'}
        sanitized = sanitize_dict(data, mask_values=False)
        # Value should still be sanitized for patterns
        assert '[EMAIL_MASKED]' in sanitized['email']


class TestSanitizeLogMessage:
    """Tests for the sanitize_log_message function."""
    
    def test_email_in_log(self):
        """Test email masking in log messages."""
        message = "User logged in: user@example.com"
        sanitized = sanitize_log_message(message)
        assert '[EMAIL_MASKED]' in sanitized
    
    def test_multiple_pii_types(self):
        """Test masking of multiple PII types in one message."""
        message = "User test@example.com (555) 123-4567 from 192.168.1.1"
        sanitized = sanitize_log_message(message)
        assert '[EMAIL_MASKED]' in sanitized
        assert '[PHONE_MASKED]' in sanitized
        assert '[IP_MASKED]' in sanitized
    
    def test_non_string_message(self):
        """Test handling of non-string log messages."""
        assert sanitize_log_message(123) == "123"
        assert sanitize_log_message(None) == "None"


class TestSanitizedLogger:
    """Tests for the SanitizedLogger class."""
    
    def test_sanitize_on_debug(self):
        """Test that debug messages are sanitized."""
        logger = SanitizedLogger("test_debug")
        with patch.object(logger.logger, 'debug') as mock_debug:
            logger.debug("Email: test@example.com")
            mock_debug.assert_called_once()
            call_args = mock_debug.call_args[0][0]
            assert '[EMAIL_MASKED]' in call_args
            assert 'test@example.com' not in call_args
    
    def test_sanitize_on_info(self):
        """Test that info messages are sanitized."""
        logger = SanitizedLogger("test_info")
        with patch.object(logger.logger, 'info') as mock_info:
            logger.info("IP: 192.168.1.1")
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert '[IP_MASKED]' in call_args
    
    def test_sanitize_on_error(self):
        """Test that error messages are sanitized."""
        logger = SanitizedLogger("test_error")
        with patch.object(logger.logger, 'error') as mock_error:
            logger.error("SSN: 123-45-6789")
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]
            assert '[SSN_MASKED]' in call_args
    
    def test_sanitize_with_dict_arg(self):
        """Test sanitization of dictionary arguments."""
        logger = SanitizedLogger("test_dict")
        sensitive_data = {'email': 'test@example.com', 'normal': 'value'}
        with patch.object(logger.logger, 'info') as mock_info:
            logger.info("User data: %s", sensitive_data)
            mock_info.assert_called_once()
            # The dict should be sanitized
            call_args = mock_info.call_args[0][1][0]
            assert call_args['email'] == '[SENSITIVE]'


class TestEnsureLogSafety:
    """Tests for the ensure_log_safety function."""
    
    def test_safe_log_path(self):
        """Test that safe log paths are accepted."""
        with patch('code.utils.security.get_logs_dir') as mock_get_dir:
            mock_get_dir.return_value = Path('/project/data/logs')
            safe_path = Path('/project/data/logs/test.log')
            assert ensure_log_safety(safe_path) is True
    
    def test_unsafe_log_path_outside_logs_dir(self):
        """Test that paths outside logs directory are rejected."""
        with patch('code.utils.security.get_logs_dir') as mock_get_dir:
            mock_get_dir.return_value = Path('/project/data/logs')
            unsafe_path = Path('/etc/passwd')
            assert ensure_log_safety(unsafe_path) is False
    
    def test_empty_path(self):
        """Test that empty paths are rejected."""
        assert ensure_log_safety(None) is False
        assert ensure_log_safety(Path('')) is False
    
    def test_pii_in_path(self):
        """Test that paths containing PII are rejected."""
        with patch('code.utils.security.get_logs_dir') as mock_get_dir:
            mock_get_dir.return_value = Path('/project/data/logs')
            # Path with email-like pattern
            unsafe_path = Path('/project/data/logs/user@example.com.log')
            assert ensure_log_safety(unsafe_path) is False


class TestPIIPatterns:
    """Tests for PII pattern definitions."""
    
    def test_email_pattern_valid(self):
        """Test that email pattern matches valid emails."""
        pattern = PII_PATTERNS['email']
        assert re.search(pattern, 'test@example.com')
        assert re.search(pattern, 'user.name+tag@domain.co.uk')
    
    def test_phone_pattern_valid(self):
        """Test that phone pattern matches valid US numbers."""
        pattern = PII_PATTERNS['phone_us']
        assert re.search(pattern, '555-123-4567')
        assert re.search(pattern, '(555) 123-4567')
        assert re.search(pattern, '+1-555-123-4567')
    
    def test_ssn_pattern_valid(self):
        """Test that SSN pattern matches valid SSN format."""
        pattern = PII_PATTERNS['ssn']
        assert re.search(pattern, '123-45-6789')
    
    def test_credit_card_pattern_valid(self):
        """Test that credit card pattern matches valid card numbers."""
        pattern = PII_PATTERNS['credit_card']
        assert re.search(pattern, '4111-1111-1111-1111')
        assert re.search(pattern, '4111111111111111')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
