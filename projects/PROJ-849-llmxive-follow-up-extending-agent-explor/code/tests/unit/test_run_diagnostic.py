"""
Unit tests for the run_diagnostic entry point.
"""

import pytest
import socket
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add code/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.cli.run_diagnostic import (
    DiagnosticError,
    check_url_reachability,
    run_preflight_checks,
    validate_dataset_size_after_load
)

class TestCheckUrlReachability:
    """Tests for the check_url_reachability function."""

    @patch('socket.gethostbyname')
    def test_reachable_url(self, mock_gethostbyname):
        """Test that a reachable URL returns True."""
        mock_gethostbyname.return_value = "192.168.1.1"
        
        result = check_url_reachability("https://example.com")
        
        assert result is True
        mock_gethostbyname.assert_called_once_with("example.com")

    @patch('socket.gethostbyname')
    def test_unreachable_url_dns_failure(self, mock_gethostbyname):
        """Test that a DNS failure raises DiagnosticError."""
        mock_gethostbyname.side_effect = socket.gaierror("DNS failed")
        
        with pytest.raises(DiagnosticError) as excinfo:
            check_url_reachability("https://nonexistent.invalid")
        
        assert "DNS resolution failed" in str(excinfo.value)

    @patch('socket.gethostbyname')
    def test_unreachable_url_timeout(self, mock_gethostbyname):
        """Test that a timeout raises DiagnosticError."""
        mock_gethostbyname.side_effect = socket.timeout("Timeout")
        
        with pytest.raises(DiagnosticError) as excinfo:
            check_url_reachability("https://slow-server.invalid")
        
        assert "connection timeout" in str(excinfo.value).lower()

    def test_local_path_returns_true(self):
        """Test that local paths return True."""
        result = check_url_reachability("/local/path/to/data")
        assert result is True


class TestValidateDatasetSize:
    """Tests for the validate_dataset_size_after_load function."""

    def test_valid_dataset_size(self):
        """Test that a valid dataset size passes validation."""
        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=100)
        
        # Should not raise
        validate_dataset_size_after_load(mock_dataset, min_size=30)

    def test_insufficient_dataset_size(self):
        """Test that an insufficient dataset size raises ValidationError."""
        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=20)
        
        with pytest.raises(Exception) as excinfo:
            validate_dataset_size_after_load(mock_dataset, min_size=30)
        
        assert "Insufficient sample size" in str(excinfo.value)

    def test_exact_minimum_size(self):
        """Test that exactly the minimum size passes validation."""
        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=30)
        
        # Should not raise
        validate_dataset_size_after_load(mock_dataset, min_size=30)

    def test_streaming_dataset_no_length(self):
        """Test that a streaming dataset without length raises DiagnosticError."""
        mock_dataset = MagicMock()
        del mock_dataset.__len__
        mock_dataset.num_rows = None
        
        with pytest.raises(DiagnosticError) as excinfo:
            validate_dataset_size_after_load(mock_dataset, min_size=30)
        
        assert "Unable to determine dataset size" in str(excinfo.value)


class TestRunPreflightChecks:
    """Tests for the run_preflight_checks function."""

    @patch('src.cli.run_diagnostic.check_url_reachability')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    def test_preflight_checks_pass(self, mock_mkdir, mock_exists, mock_check_url):
        """Test that preflight checks pass when all conditions are met."""
        mock_exists.return_value = True
        mock_check_url.return_value = True
        
        # Create a mock args object
        args = MagicMock()
        args.dataset_url = "https://example.com"
        args.output_dir = "/tmp/test_output"
        
        # Should not raise
        run_preflight_checks(args)

    @patch('src.cli.run_diagnostic.check_url_reachability')
    def test_preflight_checks_fail_url(self, mock_check_url):
        """Test that preflight checks fail when URL is unreachable."""
        mock_check_url.side_effect = DiagnosticError("URL unreachable")
        
        args = MagicMock()
        args.dataset_url = "https://unreachable.com"
        args.output_dir = "/tmp/test_output"
        
        with pytest.raises(DiagnosticError) as excinfo:
            run_preflight_checks(args)
        
        assert "URL unreachable" in str(excinfo.value)