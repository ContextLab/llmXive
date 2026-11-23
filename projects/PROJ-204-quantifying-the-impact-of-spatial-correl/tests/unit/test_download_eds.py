"""
Unit tests for T011 conditional download functionality.

Tests verify:
1. Correct behavior when T010 fails (skip download)
2. Correct behavior when T010 succeeds (attempt download)
3. Proper error handling for network failures
4. Correct status file generation
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.download_eds import (
    load_feasibility_status,
    download_file,
    download_from_zenodo,
    main
)

class TestLoadFeasibilityStatus:
    """Tests for load_feasibility_status function."""
    
    def test_missing_status_file(self, tmp_path):
        """Test behavior when status file is missing."""
        # Create a temporary directory structure
        state_dir = tmp_path / 'state'
        state_dir.mkdir()
        
        with patch('data.download_eds.project_root', tmp_path):
            result = load_feasibility_status()
        
        assert result['success'] is False
        assert 'missing' in result['reason'].lower()
    
    def test_valid_status_file(self, tmp_path):
        """Test loading a valid status file."""
        state_dir = tmp_path / 'state'
        state_dir.mkdir()
        
        status_file = state_dir / 'data_feasibility_status.yaml'
        status_data = {
            'success': True,
            'verified_url': 'https://example.com/data.zip',
            'zenodo_record': '1234567'
        }
        
        with open(status_file, 'w') as f:
            yaml.dump(status_data, f)
        
        with patch('data.download_eds.project_root', tmp_path):
            result = load_feasibility_status()
        
        assert result['success'] is True
        assert result['verified_url'] == 'https://example.com/data.zip'
        assert result['zenodo_record'] == '1234567'
    
    def test_invalid_yaml(self, tmp_path):
        """Test behavior with invalid YAML content."""
        state_dir = tmp_path / 'state'
        state_dir.mkdir()
        
        status_file = state_dir / 'data_feasibility_status.yaml'
        with open(status_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        with patch('data.download_eds.project_root', tmp_path):
            result = load_feasibility_status()
        
        assert result['success'] is False
        assert 'error' in result['reason'].lower() or 'failed' in result['reason'].lower()

class TestDownloadFile:
    """Tests for download_file function."""
    
    def test_successful_download(self, tmp_path):
        """Test successful file download."""
        test_url = 'https://httpbin.org/bytes/1024'
        output_path = tmp_path / 'test_file.bin'
        
        # Mock the requests.get to avoid actual network call
        with patch('data.download_eds.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [b'x' * 1024]
            mock_response.headers.get.return_value = '1024'
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = download_file(test_url, output_path)
        
        assert result is True
        assert output_path.exists()
        assert output_path.stat().st_size == 1024
    
    def test_download_failure(self, tmp_path):
        """Test handling of download failure."""
        test_url = 'https://invalid-url-that-does-not-exist.example/file'
        output_path = tmp_path / 'test_file.bin'
        
        result = download_file(test_url, output_path)
        
        assert result is False
        assert not output_path.exists()

class TestDownloadFromZenodo:
    """Tests for download_from_zenodo function."""
    
    def test_successful_zenodo_download(self, tmp_path):
        """Test successful Zenodo record processing."""
        record_id = '1234567'
        output_dir = tmp_path / 'zenodo_output'
        output_dir.mkdir()
        
        # Mock the Zenodo API response
        mock_record_data = {
            'files': [
                {
                    'key': 'eds_map_1.zip',
                    'links': {'self': 'https://zenodo.org/record/1234567/files/eds_map_1.zip'}
                },
                {
                    'key': 'eds_map_2.zip',
                    'links': {'self': 'https://zenodo.org/record/1234567/files/eds_map_2.zip'}
                }
            ]
        }
        
        with patch('data.download_eds.requests.get') as mock_get:
            # First call: metadata fetch
            mock_metadata_response = MagicMock()
            mock_metadata_response.json.return_value = mock_record_data
            mock_metadata_response.raise_for_status = MagicMock()
            
            # Second call: file download
            mock_file_response = MagicMock()
            mock_file_response.iter_content.return_value = [b'x' * 1024]
            mock_file_response.headers.get.return_value = '1024'
            mock_file_response.raise_for_status = MagicMock()
            
            mock_get.side_effect = [mock_metadata_response, mock_file_response, mock_file_response]
            
            result = download_from_zenodo(record_id, output_dir)
        
        assert result == 2
        assert (output_dir / 'eds_map_1.zip').exists()
        assert (output_dir / 'eds_map_2.zip').exists()
    
    def test_empty_zenodo_record(self, tmp_path):
        """Test handling of Zenodo record with no files."""
        record_id = '9999999'
        output_dir = tmp_path / 'zenodo_output'
        output_dir.mkdir()
        
        mock_record_data = {'files': []}
        
        with patch('data.download_eds.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_record_data
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = download_from_zenodo(record_id, output_dir)
        
        assert result == 0

class TestMain:
    """Tests for main function."""
    
    def test_skip_when_t010_fails(self, tmp_path):
        """Test that download is skipped when T010 fails."""
        state_dir = tmp_path / 'state'
        state_dir.mkdir()
        
        status_file = state_dir / 'data_feasibility_status.yaml'
        status_data = {
            'success': False,
            'reason': 'No verified data source found'
        }
        
        with open(status_file, 'w') as f:
            yaml.dump(status_data, f)
        
        with patch('data.download_eds.project_root', tmp_path):
            with patch('data.download_eds.get_config') as mock_config:
                mock_config.return_value = {}
                
                exit_code = main()
        
        # Should return 0 (success) even though download was skipped
        assert exit_code == 0
        
        # Check that T011 status file was created
        t011_status_file = tmp_path / 'state' / 't011_download_status.yaml'
        assert t011_status_file.exists()
        
        with open(t011_status_file, 'r') as f:
            t011_status = yaml.safe_load(f)
        
        assert t011_status['status'] == 'skipped'
    
    def test_download_when_t010_succeeds(self, tmp_path):
        """Test that download proceeds when T010 succeeds."""
        state_dir = tmp_path / 'state'
        state_dir.mkdir()
        
        status_file = state_dir / 'data_feasibility_status.yaml'
        status_data = {
            'success': True,
            'verified_url': 'https://httpbin.org/bytes/512',
            'zenodo_record': None
        }
        
        with open(status_file, 'w') as f:
            yaml.dump(status_data, f)
        
        data_dir = tmp_path / 'data' / 'raw'
        data_dir.mkdir(parents=True)
        
        with patch('data.download_eds.project_root', tmp_path):
            with patch('data.download_eds.get_config') as mock_config:
                mock_config.return_value = {}
                
                # Mock the download to succeed
                with patch('data.download_eds.download_file') as mock_download:
                    mock_download.return_value = True
                    
                    exit_code = main()
        
        # Should return 0 (success)
        assert exit_code == 0
        
        # Check that T011 status file was created
        t011_status_file = tmp_path / 'state' / 't011_download_status.yaml'
        assert t011_status_file.exists()
        
        with open(t011_status_file, 'r') as f:
            t011_status = yaml.safe_load(f)
        
        assert t011_status['status'] == 'completed'
        assert t011_status['total_downloaded'] == 1
    
    def test_partial_download_on_failure(self, tmp_path):
        """Test handling of partial download failures."""
        state_dir = tmp_path / 'state'
        state_dir.mkdir()
        
        status_file = state_dir / 'data_feasibility_status.yaml'
        status_data = {
            'success': True,
            'verified_url': 'https://invalid-url.example/file',
            'zenodo_record': '1234567'
        }
        
        with open(status_file, 'w') as f:
            yaml.dump(status_data, f)
        
        data_dir = tmp_path / 'data' / 'raw'
        data_dir.mkdir(parents=True)
        
        with patch('data.download_eds.project_root', tmp_path):
            with patch('data.download_eds.get_config') as mock_config:
                mock_config.return_value = {}
                
                # Mock downloads to fail
                with patch('data.download_eds.download_file') as mock_download:
                    mock_download.return_value = False
                    
                    with patch('data.download_eds.download_from_zenodo') as mock_zenodo:
                        mock_zenodo.return_value = 0
                        
                        exit_code = main()
        
        # Should return 1 (partial failure)
        assert exit_code == 1
        
        # Check that T011 status file reflects partial success
        t011_status_file = tmp_path / 'state' / 't011_download_status.yaml'
        assert t011_status_file.exists()
        
        with open(t011_status_file, 'r') as f:
            t011_status = yaml.safe_load(f)
        
        assert t011_status['status'] == 'partial'
        assert t011_status['total_failed'] > 0
