import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import io

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.ingest_zeros import (
    verify_url_reachability,
    verify_sources,
    parse_zeta_zero_line,
    fetch_zeta_zeros,
    ingest_zeros_sample,
    run_pipeline
)

class TestVerifyUrlReachability:
    def test_reachable_url(self):
        """Test that a reachable URL returns True."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            result = verify_url_reachability("http://example.com")
            assert result is True

    def test_unreachable_url(self):
        """Test that an unreachable URL returns False."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = Exception("Network error")
            
            result = verify_url_reachability("http://unreachable.com")
            assert result is False

    def test_timeout(self):
        """Test that a timeout returns False."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            import socket
            mock_urlopen.side_effect = socket.timeout("Timeout")
            
            result = verify_url_reachability("http://slow.com")
            assert result is False

class TestParseZetaZeroLine:
    def test_valid_line_two_parts(self):
        """Test parsing a valid line with two parts (index, imag)."""
        line = "1 14.134725"
        idx, real, imag = parse_zeta_zero_line(line)
        assert idx == 1
        assert real == 0.5
        assert abs(imag - 14.134725) < 1e-6

    def test_valid_line_three_parts(self):
        """Test parsing a valid line with three parts (index, real, imag)."""
        line = "1 0.5 14.134725"
        idx, real, imag = parse_zeta_zero_line(line)
        assert idx == 1
        assert abs(real - 0.5) < 1e-6
        assert abs(imag - 14.134725) < 1e-6

    def test_invalid_line_too_short(self):
        """Test that a line with too few parts raises ValueError."""
        line = "1"
        with pytest.raises(ValueError):
            parse_zeta_zero_line(line)

    def test_invalid_line_non_numeric(self):
        """Test that a line with non-numeric values raises ValueError."""
        line = "1 abc 14.134725"
        with pytest.raises(ValueError):
            parse_zeta_zero_line(line)

class TestIngestZerosSample:
    def test_sample_generation(self):
        """Test that sample generation produces expected structure."""
        zeros = ingest_zeros_sample()
        assert len(zeros) == 100
        assert all(len(z) == 3 for z in zeros)
        assert all(z[1] == 0.5 for z in zeros) # Real part is 0.5

class TestFetchZeros:
    def test_fetch_success(self):
        """Test successful fetching of zeros."""
        mock_data = b"1 14.134725\n2 21.022040\n3 25.010858\n"
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.__iter__.return_value = [line.encode() for line in mock_data.decode().split('\n') if line]
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            zeros = fetch_zeta_zeros("http://example.com", 10)
            assert len(zeros) == 3
            assert zeros[0][0] == 1
            assert abs(zeros[0][2] - 14.134725) < 1e-6

    def test_fetch_max_count(self):
        """Test that fetching stops at max_count."""
        mock_data = "\n".join([f"{i} {14.134725 + i*1.5}" for i in range(1, 201)])
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.__iter__.return_value = [line.encode() for line in mock_data.split('\n')]
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            zeros = fetch_zeta_zeros("http://example.com", 100)
            assert len(zeros) == 100

    def test_fetch_malformed_lines(self):
        """Test that malformed lines are skipped."""
        mock_data = b"1 14.134725\nbad line\n2 21.022040\n"
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.__iter__.return_value = [line.encode() for line in mock_data.decode().split('\n') if line]
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            zeros = fetch_zeta_zeros("http://example.com", 10)
            assert len(zeros) == 2

class TestVerifySources:
    @patch('src.data.ingest_zeros.verify_url_reachability')
    def test_source_available(self, mock_verify):
        """Test that verification passes if at least one source is available."""
        mock_verify.side_effect = [False, True, False] # First fails, second succeeds
        
        result = verify_sources()
        assert result is True
        assert mock_verify.call_count == 2

    @patch('src.data.ingest_zeros.verify_url_reachability')
    def test_no_source_available(self, mock_verify):
        """Test that verification fails if no sources are available."""
        mock_verify.side_effect = [False, False, False]
        
        result = verify_sources()
        assert result is False
        assert mock_verify.call_count == 3

class TestRunPipeline:
    @patch('src.data.ingest_zeros.verify_sources')
    @patch('src.data.ingest_zeros.fetch_zeta_zeros')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.data.ingest_zeros.csv.writer')
    def test_pipeline_success(self, mock_writer, mock_open, mock_fetch, mock_verify):
        """Test successful pipeline execution."""
        mock_verify.return_value = True
        mock_fetch.return_value = [(1, 0.5, 14.134725), (2, 0.5, 21.022040)]
        
        # Mock csv writer to avoid actual file operations
        mock_writer_instance = MagicMock()
        mock_writer.return_value = mock_writer_instance
        
        result = run_pipeline()
        assert result == 2
        mock_open.assert_called_once()
        mock_writer_instance.writerow.assert_any_call(['index', 'real_part', 'imaginary_part'])
        assert mock_writer_instance.writerow.call_count >= 3 # Header + 2 data rows

    @patch('src.data.ingest_zeros.verify_sources')
    def test_pipeline_no_sources(self, mock_verify):
        """Test pipeline fails if no sources are available."""
        mock_verify.return_value = False
        
        with pytest.raises(RuntimeError) as excinfo:
            run_pipeline()
        assert "Data Unavailable" in str(excinfo.value)

    @patch('src.data.ingest_zeros.verify_sources')
    @patch('src.data.ingest_zeros.fetch_zeta_zeros')
    def test_pipeline_fetch_failure(self, mock_fetch, mock_verify):
        """Test pipeline fails if fetch fails."""
        mock_verify.return_value = True
        mock_fetch.side_effect = Exception("Fetch failed")
        
        with pytest.raises(RuntimeError) as excinfo:
            run_pipeline()
        assert "Data Unavailable" in str(excinfo.value)