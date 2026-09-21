"""
Unit tests for zeta zero ingestion module.

Tests verify_url_reachability, parse_zeta_zero_line, and basic ingestion logic.
Note: Actual URL fetching is mocked to avoid network dependencies in unit tests.
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import csv
import io

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.ingest_zeros import (
    verify_url_reachability,
    parse_zeta_zero_line,
    ingest_zeros_sample,
    fetch_zeta_zeros,
    ZetaZero
)
from src.utils.models import ZetaZero as ZetaZeroModel

class TestVerifyUrlReachability:
    @patch('socket.socket')
    @patch('urllib.request.urlopen')
    def test_url_reachable(self, mock_urlopen, mock_socket):
        """Test that a reachable URL returns True."""
        mock_socket.return_value.connect.return_value = None
        mock_urlopen.return_value = MagicMock()
        
        result = verify_url_reachability("https://example.com", timeout=5)
        assert result is True
        
    @patch('socket.socket')
    def test_url_unreachable_timeout(self, mock_socket):
        """Test that a timeout returns False."""
        mock_socket.return_value.connect.side_effect = Exception("Timeout")
        
        result = verify_url_reachability("https://example.com", timeout=5)
        assert result is False
        
    @patch('socket.socket')
    @patch('urllib.request.urlopen')
    def test_url_unreachable_http_error(self, mock_urlopen, mock_socket):
        """Test that an HTTP error returns False."""
        mock_socket.return_value.connect.return_value = None
        mock_urlopen.side_effect = Exception("HTTP Error")
        
        result = verify_url_reachability("https://example.com", timeout=5)
        assert result is False

class TestParseZetaZeroLine:
    def test_valid_float_line(self):
        """Test parsing a valid float line."""
        result = parse_zeta_zero_line("14.134725")
        assert result is not None
        assert result.t == 14.134725
        
    def test_comment_line(self):
        """Test that comment lines return None."""
        result = parse_zeta_zero_line("# This is a comment")
        assert result is None
        
    def test_empty_line(self):
        """Test that empty lines return None."""
        result = parse_zeta_zero_line("")
        assert result is None
        
    def test_whitespace_line(self):
        """Test that whitespace-only lines return None."""
        result = parse_zeta_zero_line("   ")
        assert result is None
        
    def test_invalid_float_line(self):
        """Test that invalid float lines return None."""
        result = parse_zeta_zero_line("not_a_number")
        assert result is None

class TestIngestZerosSample:
    @patch('src.data.ingest_zeros.verify_sources')
    @patch('src.data.ingest_zeros.fetch_zeta_zeros')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.data.ingest_zeros.load_state')
    @patch('src.data.ingest_zeros.update_state_checksums')
    @patch('src.data.ingest_zeros.commit_state')
    def test_successful_ingestion(
        self, mock_commit, mock_update, mock_load, mock_open_file, mock_fetch, mock_verify
    ):
        """Test successful ingestion of zeros."""
        # Setup mocks
        mock_verify.return_value = ["https://example.com/zeros"]
        mock_fetch.return_value = [
            ZetaZero(t=14.134725, source="LMFDB"),
            ZetaZero(t=21.022040, source="LMFDB")
        ]
        mock_load.return_value = {"checkpoints": {}}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_zeros.csv")
            count = ingest_zeros_sample(output_path, max_zeros=10)
            
            # Verify results
            assert count == 2
            
            # Verify file was written correctly
            mock_open_file.assert_called_once()
            handle = mock_open_file()
            calls = handle.write.call_args_list
            
            # Check header
            assert "t" in str(calls[0])
            assert "source" in str(calls[0])
            
            # Check data rows
            data_written = "".join(str(call) for call in calls)
            assert "14.134725" in data_written
            assert "21.022040" in data_written
            
    @patch('src.data.ingest_zeros.verify_sources')
    def test_no_zeros_fetched(self, mock_verify):
        """Test that ingestion fails when no zeros are fetched."""
        mock_verify.return_value = ["https://example.com/zeros"]
        
        with patch('src.data.ingest_zeros.fetch_zeta_zeros') as mock_fetch:
            mock_fetch.return_value = []
            
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "test_zeros.csv")
                
                with pytest.raises(RuntimeError) as exc_info:
                    ingest_zeros_sample(output_path, max_zeros=10)
                
                assert "No zeta zeros were successfully ingested" in str(exc_info.value)

class TestFetchZetaZeros:
    @patch('urllib.request.urlopen')
    def test_fetch_parsing(self, mock_urlopen):
        """Test that fetch correctly parses response."""
        # Mock response with sample data
        mock_response = MagicMock()
        mock_response.read.return_value = b"14.134725\n21.022040\n25.010858\n"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        zeros = fetch_zeta_zeros("https://example.com/zeros", max_zeros=10)
        
        assert len(zeros) == 3
        assert abs(zeros[0].t - 14.134725) < 0.0001
        assert abs(zeros[1].t - 21.022040) < 0.0001
        assert abs(zeros[2].t - 25.010858) < 0.0001

    @patch('urllib.request.urlopen')
    def test_max_zeros_limit(self, mock_urlopen):
        """Test that max_zeros limit is respected."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"14.134725\n21.022040\n25.010858\n30.424876\n"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        zeros = fetch_zeta_zeros("https://example.com/zeros", max_zeros=2)
        
        assert len(zeros) == 2
        assert abs(zeros[0].t - 14.134725) < 0.0001
        assert abs(zeros[1].t - 21.022040) < 0.0001