"""
Unit tests for PII Scanner module.

Tests PII pattern detection, file scanning, and output generation.
"""

import csv
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from pii_scanner import (
    PII_PATTERNS,
    should_scan_file,
    scan_file_for_pii,
    run_pii_scan,
    TEXT_EXTENSIONS,
    BINARY_EXTENSIONS,
    SKIP_DIRS
)


class TestPIIPatterns:
    """Test PII pattern definitions."""

    def test_email_pattern_matches_valid_email(self):
        """Test that email pattern matches valid email addresses."""
        pattern, _ = PII_PATTERNS['email']
        assert pattern.search('contact@example.com') is not None
        assert pattern.search('user.name+tag@domain.co.uk') is not None
        assert pattern.search('test123@test.org') is not None

    def test_email_pattern_does_not_match_invalid(self):
        """Test that email pattern does not match invalid emails."""
        pattern, _ = PII_PATTERNS['email']
        assert pattern.search('notanemail') is None
        assert pattern.search('@nodomain.com') is None
        assert pattern.search('noatsign.com') is None

    def test_ssn_pattern_matches(self):
        """Test SSN pattern matches valid format."""
        pattern, _ = PII_PATTERNS['ssn']
        assert pattern.search('123-45-6789') is not None
        assert pattern.search('000-00-0000') is not None

    def test_credit_card_patterns(self):
        """Test credit card patterns for different card types."""
        visa_pattern, _ = PII_PATTERNS['credit_card_visa']
        assert visa_pattern.search('4111111111111111') is not None

        mc_pattern, _ = PII_PATTERNS['credit_card_mastercard']
        assert mc_pattern.search('5500000000000004') is not None

        amex_pattern, _ = PII_PATTERNS['credit_card_amex']
        assert amex_pattern.search('378282246310005') is not None

    def test_phone_us_pattern(self):
        """Test US phone number pattern."""
        pattern, _ = PII_PATTERNS['phone_us']
        assert pattern.search('(555) 123-4567') is not None
        assert pattern.search('555-123-4567') is not None
        assert pattern.search('+1-555-123-4567') is not None

    def test_ip_v4_pattern(self):
        """Test IPv4 address pattern."""
        pattern, _ = PII_PATTERNS['ip_v4']
        assert pattern.search('192.168.1.1') is not None
        assert pattern.search('10.0.0.1') is not None
        assert pattern.search('255.255.255.255') is not None

    def test_aws_access_key_pattern(self):
        """Test AWS access key pattern."""
        pattern, _ = PII_PATTERNS['aws_access_key']
        assert pattern.search('AKIAIOSFODNN7EXAMPLE') is not None

    def test_github_token_pattern(self):
        """Test GitHub token pattern."""
        pattern, _ = PII_PATTERNS['github_token']
        assert pattern.search('ghp_1234567890abcdefghijklmnopqrstuvwxyz') is not None

    def test_url_with_credentials(self):
        """Test URL with embedded credentials pattern."""
        pattern, _ = PII_PATTERNS['url_with_creds']
        assert pattern.search('https://user:pass@example.com/path') is not None


class TestShouldScanFile:
    """Test file filtering logic."""

    def test_text_files_should_be_scanned(self):
        """Test that text files are scanned."""
        assert should_scan_file(Path('test.py')) is True
        assert should_scan_file(Path('test.csv')) is True
        assert should_scan_file(Path('test.json')) is True
        assert should_scan_file(Path('test.txt')) is True

    def test_binary_files_should_not_be_scanned(self):
        """Test that binary files are not scanned."""
        assert should_scan_file(Path('image.png')) is False
        assert should_scan_file(Path('document.pdf')) is False
        assert should_scan_file(Path('archive.zip')) is False

    def test_hidden_files_should_not_be_scanned(self):
        """Test that hidden files are not scanned."""
        assert should_scan_file(Path('.gitignore')) is False
        assert should_scan_file(Path('.env')) is False

    def test_unknown_extension_not_scanned(self):
        """Test that files with unknown extensions are not scanned."""
        assert should_scan_file(Path('test.xyz')) is False


class TestScanFileForPII:
    """Test file scanning functionality."""

    @pytest.fixture
    def temp_file_with_pii(self, tmp_path):
        """Create a temporary file with PII data."""
        file_path = tmp_path / 'test_file.py'
        content = """
        # Test file with PII
        email = "test@example.com"
        ssn = "123-45-6789"
        phone = "555-123-4567"
        aws_key = "AKIAIOSFODNN7EXAMPLE"
        """
        file_path.write_text(content)
        return file_path

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return Mock()

    def test_scan_file_detects_pii(self, temp_file_with_pii, mock_logger):
        """Test that PII is detected in file."""
        findings = scan_file_for_pii(temp_file_with_pii, mock_logger)

        # Should find at least email, ssn, phone, and aws_key
        pattern_types = [f['pattern_type'] for f in findings]
        assert 'email' in pattern_types
        assert 'ssn' in pattern_types
        assert 'phone_us' in pattern_types
        assert 'aws_access_key' in pattern_types

    def test_scan_file_empty(self, tmp_path, mock_logger):
        """Test scanning an empty file."""
        file_path = tmp_path / 'empty.py'
        file_path.write_text('')

        findings = scan_file_for_pii(file_path, mock_logger)
        assert len(findings) == 0

    def test_scan_file_no_pii(self, tmp_path, mock_logger):
        """Test scanning a file with no PII."""
        file_path = tmp_path / 'clean.py'
        file_path.write_text('def hello():\n    print("Hello, World!")')

        findings = scan_file_for_pii(file_path, mock_logger)
        assert len(findings) == 0


class TestRunPIIScan:
    """Test the main scan function."""

    def test_run_scan_on_empty_directory(self, tmp_path, mock_logger):
        """Test scanning an empty directory."""
        # Create required subdirectories
        (tmp_path / 'raw').mkdir()
        (tmp_path / 'processed').mkdir()
        (tmp_path / 'analysis').mkdir()

        output_file = tmp_path / 'results.csv'

        findings = run_pii_scan(
            data_dir=tmp_path,
            output_file=output_file,
            logger=mock_logger
        )

        assert len(findings) == 0
        assert output_file.exists()

    def test_run_scan_creates_output_file(self, tmp_path, mock_logger):
        """Test that output file is created."""
        # Create directory structure
        (tmp_path / 'raw').mkdir()
        (tmp_path / 'processed').mkdir()
        (tmp_path / 'analysis').mkdir()

        output_file = tmp_path / 'results.csv'

        run_pii_scan(
            data_dir=tmp_path,
            output_file=output_file,
            logger=mock_logger
        )

        assert output_file.exists()

    def test_run_scan_writes_csv_headers(self, tmp_path, mock_logger):
        """Test that CSV file has correct headers."""
        (tmp_path / 'raw').mkdir()
        (tmp_path / 'processed').mkdir()
        (tmp_path / 'analysis').mkdir()

        output_file = tmp_path / 'results.csv'

        run_pii_scan(
            data_dir=tmp_path,
            output_file=output_file,
            logger=mock_logger
        )

        with open(output_file, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)

        expected_headers = [
            'file_path', 'pattern_type', 'description', 'matched_value',
            'position', 'line_number', 'timestamp'
        ]
        assert headers == expected_headers


class TestConstants:
    """Test module constants."""

    def test_text_extensions_defined(self):
        """Test that text extensions are defined."""
        assert '.py' in TEXT_EXTENSIONS
        assert '.csv' in TEXT_EXTENSIONS
        assert '.json' in TEXT_EXTENSIONS
        assert '.txt' in TEXT_EXTENSIONS

    def test_binary_extensions_defined(self):
        """Test that binary extensions are defined."""
        assert '.png' in BINARY_EXTENSIONS
        assert '.pdf' in BINARY_EXTENSIONS
        assert '.zip' in BINARY_EXTENSIONS

    def test_skip_dirs_defined(self):
        """Test that skip directories are defined."""
        assert '__pycache__' in SKIP_DIRS
        assert '.git' in SKIP_DIRS
        assert 'node_modules' in SKIP_DIRS

    def test_pii_patterns_defined(self):
        """Test that PII patterns are defined."""
        assert 'email' in PII_PATTERNS
        assert 'ssn' in PII_PATTERNS
        assert 'phone_us' in PII_PATTERNS
        assert 'ip_v4' in PII_PATTERNS
        assert 'aws_access_key' in PII_PATTERNS


class TestPIIIntegration:
    """Integration tests for PII scanning."""

    def test_full_scan_with_mixed_content(self, tmp_path, mock_logger):
        """Test scanning a directory with mixed PII and clean files."""
        # Create directory structure
        raw_dir = tmp_path / 'raw'
        raw_dir.mkdir()

        # Create file with PII
        pii_file = raw_dir / 'with_pii.py'
        pii_file.write_text('email = "test@example.com"\nssn = "123-45-6789"')

        # Create clean file
        clean_file = raw_dir / 'clean.py'
        clean_file.write_text('def clean():\n    return True')

        (tmp_path / 'processed').mkdir()
        (tmp_path / 'analysis').mkdir()

        output_file = tmp_path / 'results.csv'

        findings = run_pii_scan(
            data_dir=tmp_path,
            output_file=output_file,
            logger=mock_logger
        )

        # Should find email and ssn
        assert len(findings) >= 2
        pattern_types = [f['pattern_type'] for f in findings]
        assert 'email' in pattern_types
        assert 'ssn' in pattern_types

    def test_skips_binary_files(self, tmp_path, mock_logger):
        """Test that binary files are skipped."""
        raw_dir = tmp_path / 'raw'
        raw_dir.mkdir()

        # Create a binary file (simulated)
        binary_file = raw_dir / 'image.png'
        binary_file.write_bytes(b'\x89PNG\r\n\x1a\n')

        # Create text file with PII
        text_file = raw_dir / 'test.py'
        text_file.write_text('email = "test@example.com"')

        (tmp_path / 'processed').mkdir()
        (tmp_path / 'analysis').mkdir()

        output_file = tmp_path / 'results.csv'

        findings = run_pii_scan(
            data_dir=tmp_path,
            output_file=output_file,
            logger=mock_logger
        )

        # Should only find PII in text file, not binary
        assert len(findings) == 1
        assert findings[0]['file_path'].endswith('test.py')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])