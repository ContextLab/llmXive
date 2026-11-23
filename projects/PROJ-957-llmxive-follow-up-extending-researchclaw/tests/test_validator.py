"""
Tests for the Reference-Validator module (T009a).
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from src.scaffolding.validator import (
    verify_url_existence,
    write_verified_url,
    main,
    TEMPLATE_URL,
    VERIFIED_URL_PATH,
    GATE_DONE_PATH
)


class TestVerifyUrlExistence:
    """Tests for verify_url_existence function."""

    @patch('src.scaffolding.validator.urlopen')
    def test_valid_url_returns_true(self, mock_urlopen):
        """Test that a valid URL returns True."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = verify_url_existence("https://example.com")
        
        assert result is True
        mock_urlopen.assert_called_once_with("https://example.com", timeout=10)

    @patch('src.scaffolding.validator.urlopen')
    def test_invalid_status_returns_false(self, mock_urlopen):
        """Test that a non-200 status returns False."""
        mock_response = MagicMock()
        mock_response.status = 404
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = verify_url_existence("https://example.com")
        
        assert result is False

    @patch('src.scaffolding.validator.urlopen')
    def test_url_error_raises_exception(self, mock_urlopen):
        """Test that URLError is raised when URL is unreachable."""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Network error")
        
        with pytest.raises(URLError, match="Failed to verify URL"):
            verify_url_existence("https://invalid.example.com")


class TestWriteVerifiedUrl:
    """Tests for write_verified_url function."""

    def test_write_url_creates_file(self, tmp_path):
        """Test that write_verified_url creates the file with correct content."""
        test_url = "https://example.com/template.md"
        output_file = tmp_path / "verified_url.txt"
        
        write_verified_url(test_url, output_file)
        
        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == test_url

    def test_write_url_creates_parent_directories(self, tmp_path):
        """Test that write_verified_url creates parent directories."""
        test_url = "https://example.com/template.md"
        output_file = tmp_path / "subdir" / "nested" / "verified_url.txt"
        
        write_verified_url(test_url, output_file)
        
        assert output_file.exists()
        assert output_file.parent.exists()


class TestMain:
    """Tests for the main function."""

    @patch('src.scaffolding.validator.verify_url_existence')
    @patch('src.scaffolding.validator.write_verified_url')
    @patch('src.scaffolding.validator.VERIFIED_URL_PATH', new_callable=lambda: Path("/tmp/test_verified.txt"))
    def test_main_success(self, mock_path, mock_write, mock_verify):
        """Test that main returns 0 on successful verification."""
        mock_verify.return_value = True
        
        result = main()
        
        assert result == 0
        mock_verify.assert_called_once_with(TEMPLATE_URL)
        mock_write.assert_called_once()

    @patch('src.scaffolding.validator.verify_url_existence')
    def test_main_failure(self, mock_verify):
        """Test that main returns 1 when verification fails."""
        mock_verify.return_value = False
        
        result = main()
        
        assert result == 1
        mock_verify.assert_called_once_with(TEMPLATE_URL)

    @patch('src.scaffolding.validator.verify_url_existence')
    def test_main_exception_handling(self, mock_verify):
        """Test that main returns 1 when an exception occurs."""
        mock_verify.side_effect = Exception("Unexpected error")
        
        result = main()
        
        assert result == 1
        mock_verify.assert_called_once_with(TEMPLATE_URL)