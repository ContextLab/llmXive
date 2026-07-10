"""
Unit tests for security hardening module.

Tests ensure PII detection, sanitization, and safe logging work correctly.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import tempfile
import os
from pathlib import Path

from security import (
    sanitize_string,
    sanitize_dataframe,
    sanitize_log_message,
    audit_output_file,
    ensure_no_pii_in_output,
    PII_PATTERNS
)

class TestSanitizeString:
    """Tests for sanitize_string function."""
    
    def test_email_masking(self):
        """Test that email addresses are masked."""
        input_str = "Contact: user@example.com for info"
        result = sanitize_string(input_str)
        assert "user@example.com" not in result
        assert "***" in result
        assert "Contact:" in result
    
    def test_phone_masking(self):
        """Test that phone numbers are masked."""
        input_str = "Call me at 555-123-4567"
        result = sanitize_string(input_str)
        assert "555-123-4567" not in result
        assert "***" in result
    
    def test_ssn_masking(self):
        """Test that SSN is masked."""
        input_str = "SSN: 123-45-6789"
        result = sanitize_string(input_str)
        assert "123-45-6789" not in result
        assert "***" in result
    
    def test_ip_address_masking(self):
        """Test that IP addresses are masked."""
        input_str = "IP: 192.168.1.1"
        result = sanitize_string(input_str)
        assert "192.168.1.1" not in result
        assert "***" in result
    
    def test_no_pii_unchanged(self):
        """Test that strings without PII remain unchanged."""
        input_str = "This is a normal sentence without any PII."
        result = sanitize_string(input_str)
        assert result == input_str
    
    def test_nan_handling(self):
        """Test that NaN values are handled correctly."""
        result = sanitize_string(np.nan)
        assert pd.isna(result)
    
    def test_empty_string(self):
        """Test empty string handling."""
        result = sanitize_string("")
        assert result == ""
    
    def test_custom_mask_char(self):
        """Test custom mask character."""
        input_str = "user@example.com"
        result = sanitize_string(input_str, mask_char='X')
        assert "user@example.com" not in result
        assert "XXXX" in result

class TestSanitizeDataFrame:
    """Tests for sanitize_dataframe function."""
    
    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame with PII."""
        return pd.DataFrame({
            'id': [1, 2, 3],
            'email': ['user1@test.com', 'user2@test.com', 'clean'],
            'phone': ['555-123-4567', 'clean', '555-987-6543'],
            'name': ['John', 'Jane', 'Bob']
        })
    
    def test_email_column_sanitized(self, sample_df):
        """Test email column is sanitized."""
        result = sanitize_dataframe(sample_df, columns_to_check=['email'])
        assert 'user1@test.com' not in result['email'].values
        assert '***' in result['email'].values[0]
    
    def test_all_string_columns(self, sample_df):
        """Test all string columns are sanitized when no columns specified."""
        result = sanitize_dataframe(sample_df)
        # Check that PII is masked in all string columns
        assert 'user1@test.com' not in str(result['email'].values)
        assert '555-123-4567' not in str(result['phone'].values)
    
    def test_sensitive_column_detection(self, sample_df):
        """Test that sensitive column names trigger sanitization."""
        df_with_sensitive = pd.DataFrame({
            'user_email': ['test@example.com'],
            'id': [1]
        })
        result = sanitize_dataframe(df_with_sensitive)
        assert 'test@example.com' not in result['user_email'].values
        assert '***' in result['user_email'].values[0]
    
    def test_numeric_columns_unchanged(self, sample_df):
        """Test that numeric columns remain unchanged."""
        result = sanitize_dataframe(sample_df)
        assert list(result['id']) == [1, 2, 3]

class TestSanitizeLogMessage:
    """Tests for sanitize_log_message function."""
    
    def test_log_message_with_email(self):
        """Test log message with email is sanitized."""
        msg = "User logged in: user@example.com"
        result = sanitize_log_message(msg)
        assert "user@example.com" not in result
        assert "***" in result
    
    def test_log_message_without_pii(self):
        """Test log message without PII remains unchanged."""
        msg = "Processing complete for user 123"
        result = sanitize_log_message(msg)
        assert result == msg

class TestAuditOutputFile:
    """Tests for audit_output_file function."""
    
    @pytest.fixture
    def temp_csv_with_pii(self, tmp_path):
        """Create a temporary CSV file with PII."""
        file_path = tmp_path / "test_pii.csv"
        df = pd.DataFrame({
            'id': [1, 2],
            'email': ['user@test.com', 'clean'],
            'value': [100, 200]
        })
        df.to_csv(file_path, index=False)
        return str(file_path)
    
    @pytest.fixture
    def temp_csv_no_pii(self, tmp_path):
        """Create a temporary CSV file without PII."""
        file_path = tmp_path / "test_no_pii.csv"
        df = pd.DataFrame({
            'id': [1, 2],
            'name': ['Alice', 'Bob'],
            'value': [100, 200]
        })
        df.to_csv(file_path, index=False)
        return str(file_path)
    
    def test_detect_pii_in_csv(self, temp_csv_with_pii):
        """Test that PII is detected in CSV file."""
        result = audit_output_file(temp_csv_with_pii)
        assert result['has_pii'] is True
        assert len(result['pii_locations']) > 0
    
    def test_no_pii_in_clean_csv(self, temp_csv_no_pii):
        """Test that no PII is detected in clean CSV file."""
        result = audit_output_file(temp_csv_no_pii)
        assert result['has_pii'] is False
        assert len(result['pii_locations']) == 0
    
    def test_file_not_found(self, tmp_path):
        """Test handling of non-existent file."""
        result = audit_output_file(str(tmp_path / "nonexistent.csv"))
        assert len(result['warnings']) > 0
        assert "not found" in result['warnings'][0].lower()

class TestEnsureNoPiiInOutput:
    """Tests for ensure_no_pii_in_output function."""
    
    @pytest.fixture
    def temp_csv_with_pii(self, tmp_path):
        """Create a temporary CSV file with PII."""
        file_path = tmp_path / "test_pii.csv"
        df = pd.DataFrame({
            'id': [1],
            'email': ['user@test.com']
        })
        df.to_csv(file_path, index=False)
        return str(file_path)
    
    @pytest.fixture
    def temp_csv_no_pii(self, tmp_path):
        """Create a temporary CSV file without PII."""
        file_path = tmp_path / "test_no_pii.csv"
        df = pd.DataFrame({
            'id': [1],
            'name': ['Alice']
        })
        df.to_csv(file_path, index=False)
        return str(file_path)
    
    def test_raises_on_pii(self, temp_csv_with_pii):
        """Test that ValueError is raised when PII is detected."""
        with pytest.raises(ValueError):
            ensure_no_pii_in_output(temp_csv_with_pii, critical=True)
    
    def test_returns_false_on_pii_not_critical(self, temp_csv_with_pii):
        """Test that function returns False when PII is detected (non-critical)."""
        result = ensure_no_pii_in_output(temp_csv_with_pii, critical=False)
        assert result is False
    
    def test_returns_true_no_pii(self, temp_csv_no_pii):
        """Test that function returns True when no PII is detected."""
        result = ensure_no_pii_in_output(temp_csv_no_pii, critical=True)
        assert result is True

class TestPIIPatterns:
    """Tests for PII pattern definitions."""
    
    def test_email_pattern(self):
        """Test email pattern matches valid emails."""
        import re
        pattern = PII_PATTERNS['email']
        assert re.search(pattern, "user@example.com")
        assert re.search(pattern, "user.name+tag@domain.co.uk")
        assert not re.search(pattern, "not-an-email")
    
    def test_phone_pattern(self):
        """Test phone pattern matches valid phone numbers."""
        import re
        pattern = PII_PATTERNS['phone']
        assert re.search(pattern, "555-123-4567")
        assert re.search(pattern, "(555) 123-4567")
        assert re.search(pattern, "+1-555-123-4567")
    
    def test_ssn_pattern(self):
        """Test SSN pattern matches valid SSNs."""
        import re
        pattern = PII_PATTERNS['ssn']
        assert re.search(pattern, "123-45-6789")
        assert re.search(pattern, "123.45.6789")
        assert not re.search(pattern, "12345678")  # No separators

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
