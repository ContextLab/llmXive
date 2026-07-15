"""
Unit tests for src/data/ingest_zeros.py
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust path to include src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.ingest_zeros import parse_zeta_zero_line, verify_url_reachability, ZetaZero

class TestParseZetaZeroLine:
    def test_valid_line_comma_delimited(self):
        line = "0.5, 14.134725"
        result = parse_zeta_zero_line(line, 1)
        assert result is not None
        assert result.t == 0.5
        assert abs(result.gamma - 14.134725) < 1e-6

    def test_valid_line_space_delimited(self):
        line = "0.5 21.022039"
        result = parse_zeta_zero_line(line, 2)
        assert result is not None
        assert result.t == 0.5
        assert abs(result.gamma - 21.022039) < 1e-6

    def test_valid_line_tab_delimited(self):
        line = "0.5\t30.424876"
        result = parse_zeta_zero_line(line, 3)
        assert result is not None
        assert result.t == 0.5
        assert abs(result.gamma - 30.424876) < 1e-6

    def test_malformed_insufficient_columns(self, caplog):
        line = "0.5"
        with caplog.at_level("WARNING"):
            result = parse_zeta_zero_line(line, 4)
        assert result is None
        assert "insufficient columns" in caplog.text

    def test_malformed_non_numeric(self, caplog):
        line = "abc, def"
        with caplog.at_level("WARNING"):
            result = parse_zeta_zero_line(line, 5)
        assert result is None
        assert "malformed" in caplog.text

    def test_empty_line(self):
        line = ""
        result = parse_zeta_zero_line(line, 6)
        assert result is None

    def test_comment_line(self):
        line = "# This is a comment"
        result = parse_zeta_zero_line(line, 7)
        assert result is None

class TestVerifyUrlReachability:
    @patch('urllib.request.urlopen')
    def test_reachable_url(self, mock_urlopen):
        mock_urlopen.return_value = MagicMock()
        assert verify_url_reachability("http://example.com") is True

    @patch('urllib.request.urlopen')
    def test_unreachable_url_socket_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Socket Error")
        assert verify_url_reachability("http://invalid.invalid") is False

    @patch('urllib.request.urlopen')
    def test_timeout(self, mock_urlopen):
        import socket
        mock_urlopen.side_effect = socket.timeout()
        assert verify_url_reachability("http://slow.server") is False