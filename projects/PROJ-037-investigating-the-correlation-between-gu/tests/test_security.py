"""
Tests for security hardening module.
"""

import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path

from code.security import (
    SecurityConfig,
    SecurityManager,
    secure_load_csv,
    secure_save_csv,
    PII_PATTERNS
)


class TestSecurityManager:
    """Tests for SecurityManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.security_manager = SecurityManager()

    def test_detect_pii_email(self):
        """Test detection of email addresses."""
        text = "Contact us at support@example.com"
        pii = self.security_manager.detect_pii(text)
        assert len(pii) == 1
        assert pii[0][0] == 'email'
        assert pii[0][1] == 'support@example.com'

    def test_detect_pii_phone(self):
        """Test detection of phone numbers."""
        text = "Call us at 555-123-4567"
        pii = self.security_manager.detect_pii(text)
        assert len(pii) == 1
        assert pii[0][0] == 'phone'

    def test_detect_pii_ssn(self):
        """Test detection of SSN."""
        text = "SSN: 123-45-6789"
        pii = self.security_manager.detect_pii(text)
        assert len(pii) == 1
        assert pii[0][0] == 'ssn'

    def test_redact_pii(self):
        """Test PII redaction."""
        text = "Email: john@example.com, Phone: 555-123-4567"
        redacted = self.security_manager.redact_pii(text)
        assert 'EMAIL_REDACTED' in redacted
        assert 'PHONE_REDACTED' in redacted
        assert 'john@example.com' not in redacted
        assert '555-123-4567' not in redacted

    def test_validate_file_path_traversal(self):
        """Test validation of directory traversal attempts."""
        assert not self.security_manager.validate_file_path('../../../etc/passwd')
        assert not self.security_manager.validate_file_path('/etc/passwd')
        assert self.security_manager.validate_file_path('safe_file.csv')

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        dangerous = 'file<>:"/\\|?*.txt'
        sanitized = self.security_manager.sanitize_filename(dangerous)
        assert '<' not in sanitized
        assert '>' not in sanitized
        assert ':' not in sanitized
        assert '/' not in sanitized
        assert '\\' not in sanitized
        assert '|' not in sanitized
        assert '?' not in sanitized
        assert '*' not in sanitized

    def test_set_secure_permissions(self):
        """Test setting secure file permissions."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            success = self.security_manager.set_secure_permissions(temp_path)
            assert success

            # Check permissions
            mode = os.stat(temp_path).st_mode & 0o777
            assert mode == 0o600
        finally:
            os.remove(temp_path)

    def test_hash_file(self):
        """Test file hashing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            hash1 = self.security_manager.hash_file(temp_path)
            hash2 = self.security_manager.hash_file(temp_path)
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA256 hex length
        finally:
            os.remove(temp_path)

    def test_validate_dataframe_schema(self):
        """Test DataFrame schema validation."""
        df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        assert self.security_manager.validate_dataframe_schema(df, ['col1', 'col2'])
        assert not self.security_manager.validate_dataframe_schema(df, ['col1', 'col3'])

    def test_redact_dataframe_pii(self):
        """Test PII redaction in DataFrame."""
        df = pd.DataFrame({
            'name': ['John', 'Jane'],
            'email': ['john@example.com', 'jane@test.org'],
            'value': [1, 2]
        })

        redacted_df = self.security_manager.redact_dataframe_pii(df)
        assert 'EMAIL_REDACTED' in redacted_df['email'].iloc[0]
        assert 'john@example.com' not in redacted_df['email'].iloc[0]


class TestSecureLoadSave:
    """Tests for secure load and save functions."""

    def test_secure_save_and_load_csv(self):
        """Test secure save and load of CSV files."""
        df = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'sleep_duration': [7.5, 8.0],
            'email': ['test@example.com', 'test2@test.org']
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, 'test_data.csv')

            # Save securely
            secure_save_csv(df, file_path)

            # Check file exists
            assert os.path.exists(file_path)

            # Check permissions
            mode = os.stat(file_path).st_mode & 0o777
            assert mode == 0o600

            # Load securely (should redact PII)
            loaded_df = secure_load_csv(file_path)

            # Verify PII was redacted
            assert 'EMAIL_REDACTED' in loaded_df['email'].iloc[0]

    def test_secure_save_sanitize_filename(self):
        """Test that dangerous characters in filenames are sanitized."""
        df = pd.DataFrame({'col': [1, 2]})

        with tempfile.TemporaryDirectory() as tmpdir:
            dangerous_name = 'test<>:"/\\|?*.csv'
            file_path = os.path.join(tmpdir, dangerous_name)

            secure_save_csv(df, file_path)

            # Check that file was saved with sanitized name
            files = os.listdir(tmpdir)
            assert len(files) == 1
            assert '<' not in files[0]
            assert '>' not in files[0]


class TestSecurityConfig:
    """Tests for SecurityConfig class."""

    def test_default_config(self):
        """Test default security configuration."""
        config = SecurityConfig()
        assert config.pii_redaction_enabled is True
        assert config.strict_file_permissions is True
        assert config.input_validation_enabled is True
        assert config.secure_temp_files is True
        assert config.min_file_permissions == 0o600

    def test_disabled_security(self):
        """Test configuration with security disabled."""
        config = SecurityConfig(
            pii_redaction_enabled=False,
            strict_file_permissions=False,
            input_validation_enabled=False,
            secure_temp_files=False
        )
        assert config.pii_redaction_enabled is False
        assert config.strict_file_permissions is False
        assert config.input_validation_enabled is False
        assert config.secure_temp_files is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
