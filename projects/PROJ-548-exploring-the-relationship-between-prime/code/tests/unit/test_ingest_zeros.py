"""
Unit tests for src/data/ingest_zeros.py
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import json

# Adjust path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.ingest_zeros import (
    verify_url_reachability,
    verify_sources,
    parse_zeta_zero_line,
    ingest_zeros_sample,
    ZetaZero
)

class TestVerifyUrlReachability:
    def test_reachable_url(self):
        # Mock urllib.request.urlopen to simulate success
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        
        with patch('src.data.ingest_zeros.urllib.request.urlopen', return_value=mock_response):
            with patch('src.data.ingest_zeros.urllib.request.Request'):
                success, msg = verify_url_reachability("http://example.com")
                assert success is True
                assert msg == "Reachable"

    def test_unreachable_url_timeout(self):
        with patch('src.data.ingest_zeros.socket.timeout', side_effect=Exception("Timeout")):
            with patch('src.data.ingest_zeros.urllib.request.urlopen', side_effect=Exception("Timeout")):
                success, msg = verify_url_reachability("http://bad.url")
                assert success is False
                assert "timed out" in msg or "Timeout" in msg

    def test_http_error(self):
        mock_error = MagicMock()
        mock_error.code = 404
        mock_error.reason = "Not Found"
        
        with patch('src.data.ingest_zeros.urllib.request.urlopen', side_effect=mock_error):
            success, msg = verify_url_reachability("http://example.com/missing")
            assert success is False
            assert "HTTP Error" in msg

class TestStateManagement:
    def test_verify_sources_structure(self):
        # Mock verify_url_reachability to return success
        with patch('src.data.ingest_zeros.verify_url_reachability', return_value=(True, "OK")):
            result = verify_sources()
            assert "verification_successful" in result
            assert "sources" in result
            assert result["verification_successful"] is True
            
            # Check that both expected sources are in the result
            assert "LMFDB API" in result["sources"]
            assert "Odlyzko Dataset" in result["sources"]

class TestVerifiedSources:
    def test_parse_zeta_zero_line_valid(self):
        # Odlyzko format: index, imaginary_part
        line = "1 14.134725"
        z = parse_zeta_zero_line(line)
        assert z is not None
        assert z.index == 1
        assert z.real_part == 0.5
        assert abs(z.imaginary_part - 14.134725) < 1e-6

    def test_parse_zeta_zero_line_invalid(self):
        line = "invalid data"
        z = parse_zeta_zero_line(line)
        assert z is None

    def test_parse_zeta_zero_line_empty(self):
        line = ""
        z = parse_zeta_zero_line(line)
        assert z is None

class TestIngestZerosSample:
    @pytest.fixture
    def temp_output_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test_zeros.csv"

    def test_ingest_zeros_fails_if_sources_unreachable(self, temp_output_path):
        # Mock verify_sources to return failure
        mock_result = {"verification_successful": False, "sources": {}}
        
        with patch('src.data.ingest_zeros.verify_sources', return_value=mock_result):
            with pytest.raises(RuntimeError, match="Verified data sources are unreachable"):
                ingest_zeros_sample(temp_output_path)

    def test_ingest_zeros_success(self, temp_output_path):
        # Mock the URL opening and reading
        mock_response = MagicMock()
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = lambda self, *args: None
        mock_response.__iter__ = lambda self: iter([b"1 14.134725\n2 21.022040\n"])
        
        mock_req = MagicMock()
        
        with patch('src.data.ingest_zeros.verify_sources', return_value={"verification_successful": True, "sources": {}}):
            with patch('src.data.ingest_zeros.urllib.request.urlopen', return_value=mock_response):
                with patch('src.data.ingest_zeros.urllib.request.Request', return_value=mock_req):
                    count = ingest_zeros_sample(temp_output_path, limit=10)
                    
                    assert count == 2
                    assert temp_output_path.exists()
                    
                    with open(temp_output_path, 'r') as f:
                        content = f.read()
                        assert "index,real_part,imaginary_part" in content
                        assert "1,0.5,14.134725" in content
                        assert "2,0.5,21.022040" in content