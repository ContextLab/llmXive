"""
Unit tests for download_genomes functionality.

Tests include:
- Genome size filter logic
- Retry logic behavior
- Timeout handling
- File validation
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import os
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.download import (
    _calculate_file_size_mb,
    _download_file_with_retry,
    _validate_genome_file,
    _extract_species_name_from_url,
    MAX_GENOME_SIZE_MB,
    DownloadError
)

class TestCalculateFileSize:
    """Tests for _calculate_file_size_mb function."""
    
    @patch('data.download.requests.head')
    def test_successful_size_retrieval(self, mock_head):
        """Test successful retrieval of file size from Content-Length header."""
        mock_response = MagicMock()
        mock_response.headers = {'Content-Length': '104857600'}  # 100 MB
        mock_response.raise_for_status = MagicMock()
        mock_head.return_value = mock_response
        
        size_mb = _calculate_file_size_mb('http://example.com/file.fasta')
        
        assert size_mb == 100.0
        mock_head.assert_called_once()
    
    @patch('data.download.requests.head')
    def test_no_content_length_header(self, mock_head):
        """Test behavior when Content-Length header is missing."""
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()
        mock_head.return_value = mock_response
        
        size_mb = _calculate_file_size_mb('http://example.com/file.fasta')
        
        assert size_mb is None
    
    @patch('data.download.requests.head')
    def test_request_exception_handling(self, mock_head):
        """Test graceful handling of request exceptions."""
        mock_head.side_effect = Exception("Network error")
        
        size_mb = _calculate_file_size_mb('http://example.com/file.fasta')
        
        assert size_mb is None


class TestDownloadFileWithRetry:
    """Tests for _download_file_with_retry function."""
    
    def test_successful_download(self, tmp_path):
        """Test successful file download."""
        test_content = b"Test genome data"
        output_path = tmp_path / "test.fasta"
        
        with patch('data.download.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.headers = {'content-length': str(len(test_content))}
            mock_response.iter_content = MagicMock(return_value=[test_content])
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = _download_file_with_retry(
                'http://example.com/test.fasta',
                output_path,
                'test file'
            )
            
            assert result is True
            assert output_path.exists()
            assert output_path.read_bytes() == test_content
    
    @patch('data.download.time.sleep')
    def test_retry_on_timeout(self, mock_sleep, tmp_path):
        """Test retry logic on timeout errors."""
        output_path = tmp_path / "test.fasta"
        test_content = b"Test data"
        
        with patch('data.download.requests.get') as mock_get:
            # First two attempts fail with timeout, third succeeds
            mock_get.side_effect = [
                Exception("Timeout"),
                Exception("Timeout"),
                MagicMock(
                    headers={'content-length': str(len(test_content))},
                    iter_content=MagicMock(return_value=[test_content]),
                    raise_for_status=MagicMock()
                )
            ]
            
            result = _download_file_with_retry(
                'http://example.com/test.fasta',
                output_path,
                'test file'
            )
            
            assert result is True
            assert mock_get.call_count == 3
            assert mock_sleep.call_count == 2  # Sleep between retries
    
    @patch('data.download.time.sleep')
    def test_failure_after_max_retries(self, mock_sleep, tmp_path):
        """Test failure after exhausting all retry attempts."""
        output_path = tmp_path / "test.fasta"
        
        with patch('data.download.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = _download_file_with_retry(
                'http://example.com/test.fasta',
                output_path,
                'test file'
            )
            
            assert result is False
            assert mock_get.call_count == 3  # MAX_RETRIES


class TestValidateGenomeFile:
    """Tests for _validate_genome_file function."""
    
    def test_valid_file(self, tmp_path):
        """Test validation of a valid non-empty file."""
        test_file = tmp_path / "genome.fasta"
        test_file.write_text("ATCGATCG")
        
        assert _validate_genome_file(test_file) is True
    
    def test_empty_file(self, tmp_path):
        """Test validation of an empty file."""
        test_file = tmp_path / "genome.fasta"
        test_file.write_text("")
        
        assert _validate_genome_file(test_file) is False
    
    def test_nonexistent_file(self, tmp_path):
        """Test validation of a non-existent file."""
        test_file = tmp_path / "nonexistent.fasta"
        
        assert _validate_genome_file(test_file) is False


class TestExtractSpeciesName:
    """Tests for _extract_species_name_from_url function."""
    
    def test_extract_from_fasta_url(self):
        """Test extraction from URL with .fasta extension."""
        url = "https://example.com/species_name.fasta"
        name = _extract_species_name_from_url(url)
        assert name == "Species Name"
    
    def test_extract_from_gff_url(self):
        """Test extraction from URL with .gff3 extension."""
        url = "https://example.com/Arabidopsis_thaliana.gff3"
        name = _extract_species_name_from_url(url)
        assert name == "Arabidopsis Thaliana"
    
    def test_fallback_to_path_segment(self):
        """Test fallback when no pattern matches."""
        url = "https://example.com/path/to/file"
        name = _extract_species_name_from_url(url)
        assert name == "File"
    
    def test_underscore_replacement(self):
        """Test that underscores are replaced with spaces."""
        url = "https://example.com/Zea_mays.fasta"
        name = _extract_species_name_from_url(url)
        assert name == "Zea Mays"


class TestGenomeSizeFilter:
    """Integration tests for genome size filtering logic."""
    
    def test_size_limit_constant(self):
        """Test that the size limit constant is set correctly."""
        assert MAX_GENOME_SIZE_MB == 500
    
    def test_size_calculation_accuracy(self):
        """Test accuracy of size calculation."""
        # 1 MB = 1048576 bytes
        test_bytes = 524288000  # 500 MB
        expected_mb = 500.0
        
        with patch('data.download.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.headers = {'Content-Length': str(test_bytes)}
            mock_response.raise_for_status = MagicMock()
            mock_head.return_value = mock_response
            
            size_mb = _calculate_file_size_mb('http://example.com/file.fasta')
            
            assert size_mb == expected_mb

if __name__ == "__main__":
    pytest.main([__file__, "-v"])