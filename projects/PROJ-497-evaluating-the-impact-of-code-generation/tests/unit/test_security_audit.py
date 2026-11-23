"""
Unit tests for the security audit module (T039).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module to test
# We assume the test runs from the project root, so we import from code
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from security_audit import scan_file, PII_PATTERNS, is_binary_file, run_security_audit

class TestSecurityAudit:
    
    def test_email_detection(self):
        """Test that email addresses are detected."""
        content = "Contact us at support@example.com for help."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = Path(f.name)

        try:
            findings = scan_file(temp_path, PII_PATTERNS)
            assert len(findings) > 0
            assert any(f['category'] == 'email' for f in findings)
        finally:
            os.unlink(temp_path)

    def test_phone_detection(self):
        """Test that US phone numbers are detected."""
        content = "Call me at 555-123-4567."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = Path(f.name)

        try:
            findings = scan_file(temp_path, PII_PATTERNS)
            assert len(findings) > 0
            assert any(f['category'] == 'phone_us' for f in findings)
        finally:
            os.unlink(temp_path)

    def test_ssn_detection(self):
        """Test that SSN patterns are detected."""
        content = "SSN: 123-45-6789."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = Path(f.name)

        try:
            findings = scan_file(temp_path, PII_PATTERNS)
            assert len(findings) > 0
            assert any(f['category'] == 'ssn' for f in findings)
        finally:
            os.unlink(temp_path)

    def test_api_key_detection(self):
        """Test that API keys are detected."""
        content = "api_key = 'sk_live_1234567890abcdef'"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = Path(f.name)

        try:
            findings = scan_file(temp_path, PII_PATTERNS)
            assert len(findings) > 0
            assert any(f['category'] == 'api_key_generic' for f in findings)
        finally:
            os.unlink(temp_path)

    def test_clean_file(self):
        """Test that a clean file returns no findings."""
        content = "This is a safe log line. No PII here. Just numbers like 12345."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()
            temp_path = Path(f.name)

        try:
            findings = scan_file(temp_path, PII_PATTERNS)
            assert len(findings) == 0
        finally:
            os.unlink(temp_path)

    def test_binary_file_skip(self):
        """Test that binary files are skipped."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.bin', delete=False) as f:
            f.write(b'\x00\x01\x02\x03')
            temp_path = Path(f.name)

        try:
            result = is_binary_file(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_report_structure(self):
        """Test that the full audit returns a valid report structure."""
        # Create a temporary directory structure to simulate the project
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a safe file
            safe_file = Path(tmpdir) / "safe.txt"
            safe_file.write_text("Hello world")
            
            # Create a file with PII
            pii_file = Path(tmpdir) / "leak.txt"
            pii_file.write_text("Email: user@test.com")

            # Mock the SCAN_DIRECTORIES to point to our temp dir
            with patch('security_audit.SCAN_DIRECTORIES', [tmpdir]):
                report = run_security_audit()
                
                assert "timestamp" in report
                assert "summary" in report
                assert "findings" in report
                assert report["summary"]["total_findings"] >= 1
                assert report["summary"]["severity"] in ["WARNING", "CRITICAL"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
