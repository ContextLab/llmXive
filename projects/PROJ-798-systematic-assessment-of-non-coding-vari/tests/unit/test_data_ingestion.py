import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import hashlib

# Mock the config module to avoid directory creation issues in tests
import sys
from types import ModuleType

mock_config = ModuleType('config')
mock_config.DATA_RAW_DIR = Path(tempfile.mkdtemp())
mock_config.DATA_DERIVED_DIR = Path(tempfile.mkdtemp())
mock_config.ensure_data_dirs = lambda: None
sys.modules['config'] = mock_config

from data_ingestion import download_jaspar_pwms, log_source_lineage

def test_download_jaspar_pwms_creates_file():
    """Test that download_jaspar_pwms creates the output file."""
    # We mock the actual download to avoid network calls
    with patch('data_ingestion.download_file_http') as mock_download:
        # Create a temporary file to simulate the download
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
            tmp.write(b">Test PWM\n")
            tmp_path = tmp.name
        
        mock_download.return_value = "dummy_checksum"
        
        try:
            # Override the output path for testing
            with patch('data_ingestion.JASPAR_OUTPUT', Path(tmp_path)):
                result_path = download_jaspar_pwms()
                
                assert os.path.exists(result_path)
                assert Path(result_path).read_text() == ">Test PWM\n"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

def test_log_source_lineage_appends_to_log():
    """Test that log_source_lineage appends to source_log.txt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "source_log.txt"
        
        # Patch DATA_RAW_DIR to use our temp directory
        with patch('data_ingestion.DATA_RAW_DIR', Path(tmpdir)):
            log_source_lineage(
                source_name="TEST_SOURCE",
                file_path="test.txt",
                checksum="abc123",
                notes="Test note"
            )
            
            assert log_path.exists()
            content = log_path.read_text()
            assert "TEST_SOURCE" in content
            assert "abc123" in content
            assert "Test note" in content

def test_download_jaspar_pwms_skips_existing():
    """Test that download_jaspar_pwms skips download if file exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "jaspar_pwm.txt"
        output_path.write_text("Existing content")
        
        with patch('data_ingestion.JASPAR_OUTPUT', output_path):
            with patch('data_ingestion.download_file_http') as mock_download:
                download_jaspar_pwms()
                # Should not call download if file exists
                mock_download.assert_not_called()
