import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_ingestion import (
    parse_jaspar_pfm,
    convert_jaspar_to_text_format,
    download_jaspar_pwms,
    log_source_lineage
)
from config import ensure_data_dirs

class TestJASPARParsing:
    """Test JASPAR PFM parsing and conversion logic."""
    
    def test_parse_jaspar_pfm_empty_file(self, tmp_path):
        """Test parsing an empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        
        result = parse_jaspar_pfm(str(empty_file))
        assert result == []
    
    def test_parse_jaspar_pfm_single_pwm(self, tmp_path):
        """Test parsing a single PWM."""
        jaspar_content = """>MA0001.1 Test TF
        A 10 5 2 1
        C 2 8 5 3
        G 1 2 9 4
        T 1 1 2 10
        // ID MA0001.1
        // DE Test TF description
        
        """
        test_file = tmp_path / "test.jaspar"
        test_file.write_text(jaspar_content)
        
        result = parse_jaspar_pfm(str(test_file))
        
        assert len(result) == 1
        assert result[0]['metadata']['id'] == 'MA0001.1'
        assert 'Test TF' in result[0]['metadata']['name']
        assert 'matrix' in result[0]
        assert len(result[0]['matrix']['A']) == 4
        assert result[0]['matrix']['A'] == [10, 5, 2, 1]
    
    def test_convert_to_text_format(self, tmp_path):
        """Test conversion to standardized text format."""
        jaspar_content = """>MA0001.1 Test TF
        A 10 5 2 1
        C 2 8 5 3
        G 1 2 9 4
        T 1 1 2 10
        // ID MA0001.1
        
        """
        input_file = tmp_path / "input.jaspar"
        input_file.write_text(jaspar_content)
        
        output_file = tmp_path / "output.txt"
        
        pwm_data = parse_jaspar_pfm(str(input_file))
        convert_jaspar_to_text_format(pwm_data, str(output_file))
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "MA0001.1" in content
        assert "Test TF" in content
        assert "A 10 5 2 1" in content
        assert "C 2 8 5 3" in content

class TestJASPARDownload:
    """Test JASPAR download functionality."""
    
    def test_log_source_lineage_creates_file(self, tmp_path, monkeypatch):
        """Test that log_source_lineage creates the log file."""
        # Monkeypatch SOURCE_LOG_PATH
        import data_ingestion
        original_path = data_ingestion.SOURCE_LOG_PATH
        test_log_path = str(tmp_path / "source_log.txt")
        data_ingestion.SOURCE_LOG_PATH = test_log_path
        
        try:
            log_source_lineage(
                source_name="TEST_SOURCE",
                url="http://example.com",
                output_path="data/raw/test.txt",
                status="SUCCESS",
                message="Test message"
            )
            
            assert os.path.exists(test_log_path)
            with open(test_log_path, 'r') as f:
                content = f.read()
                assert "TEST_SOURCE" in content
                assert "http://example.com" in content
                assert "SUCCESS" in content
        finally:
            data_ingestion.SOURCE_LOG_PATH = original_path
    
    def test_download_jaspar_pwms_real_data(self):
        """Test downloading real JASPAR data (if network available)."""
        # This test will fail in offline environments, which is expected
        # The important thing is that the function attempts to download real data
        ensure_data_dirs()
        
        # Try to download - this will succeed or fail based on network
        success = download_jaspar_pwms()
        
        if success:
            # Verify the file was created and is not empty
            output_path = Path("data/raw/jaspar_pwm.txt")
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            
            # Verify it contains valid PWM data
            from data_ingestion import parse_jaspar_pfm
            pwm_data = parse_jaspar_pfm(str(output_path))
            assert len(pwm_data) > 0
        else:
            # If download failed, verify the log was written
            log_path = Path("data/raw/source_log.txt")
            assert log_path.exists()
            with open(log_path, 'r') as f:
                content = f.read()
                assert "JASPAR_CORE" in content
                assert "FAILURE" in content

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
