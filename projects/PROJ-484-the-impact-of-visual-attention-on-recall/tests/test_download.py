import os
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, mock_open
import sys
import logging

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from download_data import download_dataset, load_verified_sources, check_disk_space

def test_verified_source_check():
    """
    Test that the script halts with the correct error message when a dataset 
    is not in the verified list and not hypothetical.
    """
    dataset_id = "openneuro/ds001435"
    error_message = f"ERROR: No verified source found for {dataset_id}"
    
    # Create a temporary directory to simulate the project structure
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create a fake verified_sources.json that does NOT contain the dataset
        verified_path = tmp_path / "code" / "verified_sources.json"
        verified_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(verified_path, 'w') as f:
            json.dump({"other_dataset": {"url": "http://example.com"}}, f)
        
        # Mock Path.exists to return True for our fake file and False for hypothetical
        original_exists = Path.exists
        
        def mock_exists(self):
            if str(self) == str(verified_path):
                return True
            if "verified_sources_hypothetical.json" in str(self):
                return False
            return original_exists(self)
        
        # Mock open to return our fake verified_sources.json content
        original_open = open
        
        def mock_file_open(file, *args, **kwargs):
            if str(file) == str(verified_path):
                return original_open(verified_path, *args, **kwargs)
            return original_open(file, *args, **kwargs)
        
        # Patch the functions inside download_data module
        with patch('download_data.Path.exists', mock_exists), \
             patch('download_data.open', mock_file_open), \
             patch('download_data.logging.getLogger') as mock_get_logger:
            
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Call the function - it should raise RuntimeError
            with pytest.raises(RuntimeError) as excinfo:
                download_dataset(dataset_id, tmp_path)
            
            # Verify the error message matches
            assert error_message in str(excinfo.value)
            
            # Verify the error was logged
            mock_logger.error.assert_called_with(error_message)

def test_verified_source_check_hypothetical_mode():
    """
    Test that the script proceeds with a warning when dataset is marked as hypothetical.
    """
    dataset_id = "openneuro/ds001435"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create verified_sources.json without the dataset
        verified_path = tmp_path / "code" / "verified_sources.json"
        verified_path.parent.mkdir(parents=True, exist_ok=True)
        with open(verified_path, 'w') as f:
            json.dump({"other_dataset": {"url": "http://example.com"}}, f)
        
        # Create verified_sources_hypothetical.json WITH the dataset
        hypothetical_path = tmp_path / "code" / "verified_sources_hypothetical.json"
        with open(hypothetical_path, 'w') as f:
            json.dump({
                dataset_id: {
                    "status": "hypothetical",
                    "mock_path": "/fake/path"
                }
            }, f)
        
        original_exists = Path.exists
        
        def mock_exists(self):
            if str(self) == str(verified_path) or str(self) == str(hypothetical_path):
                return True
            return original_exists(self)
        
        original_open = open
        
        def mock_file_open(file, *args, **kwargs):
            if str(file) == str(verified_path):
                return original_open(verified_path, *args, **kwargs)
            if str(file) == str(hypothetical_path):
                return original_open(hypothetical_path, *args, **kwargs)
            return original_open(file, *args, **kwargs)
        
        with patch('download_data.Path.exists', mock_exists), \
             patch('download_data.open', mock_file_open), \
             patch('download_data.logging.getLogger') as mock_get_logger:
            
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Mock check_disk_space and download_dataset internals to avoid actual download
            with patch('download_data.check_disk_space', return_value=True), \
                 patch('download_data.os.makedirs'), \
                 patch('download_data.hf_hub_download') as mock_download:
                
                    mock_download.return_value = "/fake/downloaded/file"
                    
                    # This should NOT raise, but should log a warning
                    try:
                        download_dataset(dataset_id, tmp_path)
                    except Exception:
                        # We expect it might fail later in the download process due to fake paths,
                        # but the key is that it passed the verified source check
                        pass
                    
                    # Verify the warning was logged
                    warning_call = any(
                        "Hypothetical mode enabled" in str(call) 
                        for call in mock_logger.warning.call_args_list
                    )
                    assert warning_call, "Expected 'Hypothetical mode enabled' warning to be logged"

def test_verified_source_check_success():
    """
    Test that the script proceeds when dataset is in verified list.
    """
    dataset_id = "openneuro/ds001435"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create verified_sources.json WITH the dataset
        verified_path = tmp_path / "code" / "verified_sources.json"
        verified_path.parent.mkdir(parents=True, exist_ok=True)
        with open(verified_path, 'w') as f:
            json.dump({
                dataset_id: {
                    "url": "http://example.com/ds001435",
                    "status": "verified"
                }
            }, f)
        
        original_exists = Path.exists
        
        def mock_exists(self):
            if str(self) == str(verified_path):
                return True
            if "verified_sources_hypothetical.json" in str(self):
                return False
            return original_exists(self)
        
        original_open = open
        
        def mock_file_open(file, *args, **kwargs):
            if str(file) == str(verified_path):
                return original_open(verified_path, *args, **kwargs)
            return original_open(file, *args, **kwargs)
        
        with patch('download_data.Path.exists', mock_exists), \
             patch('download_data.open', mock_file_open), \
             patch('download_data.logging.getLogger') as mock_get_logger:
            
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Mock the actual download logic to avoid network calls
            with patch('download_data.check_disk_space', return_value=True), \
                 patch('download_data.os.makedirs'), \
                 patch('download_data.hf_hub_download') as mock_download:
                
                mock_download.return_value = "/fake/downloaded/file"
                
                # This should NOT raise
                try:
                    download_dataset(dataset_id, tmp_path)
                except Exception:
                    # Might fail later due to fake paths, but passed verified check
                    pass
                
                # Verify no error was logged for missing source
                error_calls = [
                    call for call in mock_logger.error.call_args_list 
                    if "No verified source found" in str(call)
                ]
                assert len(error_calls) == 0, "Did not expect 'No verified source found' error"