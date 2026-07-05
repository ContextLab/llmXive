"""
Unit tests for data hygiene validation logic in download.py.
Ensures that only official SPARC sources are accepted and fake/synthetic sources are rejected.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

# Import the functions to test
from download import is_valid_sparc_source, verify_file_integrity

class TestIsValidSparcSource:
    """Tests for the URL source validation logic."""

    def test_valid_official_url_raw_github(self):
        """Test that the official raw GitHub URL is accepted."""
        url = "https://github.com/giacomellil/SPARC/raw/master/Data.tar.gz"
        assert is_valid_sparc_source(url) is True

    def test_valid_official_url_githubusercontent(self):
        """Test that the raw.githubusercontent.com URL is accepted."""
        url = "https://raw.githubusercontent.com/giacomellil/SPARC/master/Data.tar.gz"
        assert is_valid_sparc_source(url) is True

    def test_invalid_malicious_url(self):
        """Test that a malicious or fake URL is rejected."""
        url = "https://fake-sparc-data.com/data.tar.gz"
        assert is_valid_sparc_source(url) is False

    def test_invalid_wrong_repo(self):
        """Test that a URL from a different repository is rejected."""
        url = "https://github.com/other-user/SPARC/raw/master/Data.tar.gz"
        assert is_valid_sparc_source(url) is False

    def test_invalid_wrong_file(self):
        """Test that a URL pointing to the wrong file in the repo is rejected."""
        # Even if the repo is correct, we should be strict about the file type
        url = "https://github.com/giacomellil/SPARC/raw/master/README.md"
        assert is_valid_sparc_source(url) is False

    def test_case_insensitivity(self):
        """Test that URL validation is case-insensitive."""
        url = "https://GITHUB.COM/GIACOMELLIL/SPARC/RAW/MASTER/DATA.TAR.GZ"
        assert is_valid_sparc_source(url) is True

class TestVerifyFileIntegrity:
    """Tests for the downloaded file integrity verification."""

    def test_empty_file_rejected(self):
        """Test that an empty file is rejected."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            result = verify_file_integrity(tmp_path)
            assert result is False
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_non_gzip_file_rejected(self):
        """Test that a non-gzip file is rejected."""
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
            tmp.write("This is not a gzip file")
            tmp_path = Path(tmp.name)
        
        try:
            result = verify_file_integrity(tmp_path)
            assert result is False
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_valid_gzip_file_accepted(self):
        """Test that a valid gzip file is accepted."""
        import gzip
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gz') as tmp:
            with gzip.open(tmp.name, 'wb') as gz:
                gz.write(b"Test data for SPARC integrity check")
            tmp_path = Path(tmp.name)
        
        try:
            result = verify_file_integrity(tmp_path)
            assert result is True
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_missing_file_rejected(self):
        """Test that a missing file is rejected."""
        fake_path = Path("/tmp/does_not_exist_12345.tar.gz")
        result = verify_file_integrity(fake_path)
        assert result is False
