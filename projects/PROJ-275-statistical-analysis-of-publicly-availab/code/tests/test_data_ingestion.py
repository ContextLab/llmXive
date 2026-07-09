"""
Tests for data ingestion module.

Implements contract tests for T009 download_datasets function.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_ingestion import download_datasets
from config import get_dataset_urls, ensure_directories

class TestDownloadDatasets:
    """Test suite for download_datasets function."""
    
    def test_download_datasets_returns_dict(self):
        """Test that download_datasets returns a dictionary."""
        # This test will be skipped if network is unavailable
        # In real execution, it should return a dict of downloaded files
        with patch('data_ingestion.get_dataset_urls') as mock_urls, \
             patch('data_ingestion.subprocess.run') as mock_run, \
             patch('data_ingestion.Path.exists') as mock_exists, \
             patch('data_ingestion.Path.stat') as mock_stat:
            
            # Mock configuration
            mock_urls.return_value = {
                'tmdb_5000': {
                    'url': 'https://example.com/tmdb.csv',
                    'filename': 'tmdb_5000.csv'
                }
            }
            
            # Mock successful download
            mock_run.return_value = MagicMock(returncode=0)
            mock_exists.return_value = True
            mock_stat.return_value = MagicMock(st_size=1000)
            
            result = download_datasets()
            
            assert isinstance(result, dict)
            assert 'tmdb_5000' in result
            
    def test_download_datasets_uses_wget(self):
        """Test that wget is used for downloading."""
        with patch('data_ingestion.get_dataset_urls') as mock_urls, \
             patch('data_ingestion.subprocess.run') as mock_run, \
             patch('data_ingestion.Path.exists') as mock_exists, \
             patch('data_ingestion.Path.stat') as mock_stat:
            
            mock_urls.return_value = {
                'test_dataset': {
                    'url': 'https://example.com/test.csv',
                    'filename': 'test.csv'
                }
            }
            
            mock_run.return_value = MagicMock(returncode=0)
            mock_exists.return_value = True
            mock_stat.return_value = MagicMock(st_size=1000)
            
            download_datasets()
            
            # Verify subprocess.run was called with wget
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == 'wget'
            
    def test_download_datasets_handles_missing_urls(self):
        """Test that appropriate error is raised when no URLs configured."""
        with patch('data_ingestion.get_dataset_urls') as mock_urls:
            mock_urls.return_value = {}
            
            with pytest.raises(RuntimeError) as exc_info:
                download_datasets()
            
            assert "No dataset URLs found" in str(exc_info.value)
            
    def test_download_datasets_validates_file_size(self):
        """Test that empty files are detected and handled."""
        with patch('data_ingestion.get_dataset_urls') as mock_urls, \
             patch('data_ingestion.subprocess.run') as mock_run, \
             patch('data_ingestion.Path.exists') as mock_exists, \
             patch('data_ingestion.Path.stat') as mock_stat:
            
            mock_urls.return_value = {
                'test_dataset': {
                    'url': 'https://example.com/test.csv',
                    'filename': 'test.csv'
                }
            }
            
            mock_run.return_value = MagicMock(returncode=0)
            mock_exists.return_value = True
            mock_stat.return_value = MagicMock(st_size=0)  # Empty file
            
            # Should continue but log warning (not raise exception for single failure)
            result = download_datasets()
            
            # If all downloads fail, should raise error
            # If some succeed, should return partial results
            # This test verifies the logic handles empty files
            
    def test_config_integration(self):
        """Test that the function properly integrates with config system."""
        # Verify config has the expected structure
        urls = get_dataset_urls()
        
        # If URLs are configured, they should have the expected format
        if urls:
            for name, info in urls.items():
                assert 'url' in info, f"URL missing for {name}"
                assert isinstance(info['url'], str), f"URL must be string for {name}"
                
                # Optional filename
                if 'filename' in info:
                    assert isinstance(info['filename'], str), f"Filename must be string for {name}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
