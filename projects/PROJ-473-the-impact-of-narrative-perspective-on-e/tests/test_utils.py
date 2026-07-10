"""
Unit tests for code/utils.py
"""

import pytest
import tempfile
import os
from code.utils import scan_for_pii, compute_artifact_hash


class TestScanForPii:
    """Tests for the scan_for_pii function."""

    def test_detects_email(self):
        text = "Contact me at user@example.com for details."
        results = scan_for_pii(text)
        assert "user@example.com" in results

    def test_detects_phone_formats(self):
        text = "Call me at (123) 456-7890 or 123-456-7890."
        results = scan_for_pii(text)
        # Should detect both formats
        assert len(results) >= 2

    def test_detects_ssn(self):
        text = "My SSN is 123-45-6789."
        results = scan_for_pii(text)
        assert "123-45-6789" in results

    def test_detects_ip_address(self):
        text = "Server running at 192.168.1.1."
        results = scan_for_pii(text)
        assert "192.168.1.1" in results

    def test_no_pii(self):
        text = "This is a normal sentence with no sensitive data."
        results = scan_for_pii(text)
        assert results == []

    def test_empty_string(self):
        results = scan_for_pii("")
        assert results == []

    def test_mixed_content(self):
        text = "Email: test@test.com, Phone: 555-123-4567, IP: 10.0.0.1"
        results = scan_for_pii(text)
        assert len(results) == 3


class TestComputeArtifactHash:
    """Tests for the compute_artifact_hash function."""

    def test_hash_consistency(self):
        """Verify that the same file produces the same hash."""
        content = "This is a test file content."
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(content)
            temp_path = f.name

        try:
            hash1 = compute_artifact_hash(temp_path)
            hash2 = compute_artifact_hash(temp_path)
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA-256 hex length
        finally:
            os.unlink(temp_path)

    def test_different_content_different_hash(self):
        """Verify that different content produces different hashes."""
        content1 = "Content A"
        content2 = "Content B"

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(content1)
            path1 = f.name

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(content2)
            path2 = f.name

        try:
            hash1 = compute_artifact_hash(path1)
            hash2 = compute_artifact_hash(path2)
            assert hash1 != hash2
        finally:
            os.unlink(path1)
            os.unlink(path2)

    def test_file_not_found(self):
        """Verify that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            compute_artifact_hash("/nonexistent/path/file.txt")

    def test_binary_content(self):
        """Verify hash works on binary content."""
        content = b"\x00\x01\x02\xff\xfe"
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
            f.write(content)
            temp_path = f.name

        try:
            hash_val = compute_artifact_hash(temp_path)
            assert len(hash_val) == 64
        finally:
            os.unlink(temp_path)