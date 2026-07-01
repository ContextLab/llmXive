"""
Tests for code/data/dataset_loader.py
"""
import pytest
import hashlib
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.data.dataset_loader import (
    compute_sha256, 
    update_state_checksum, 
    load_dataset_wrapper,
    STATE_FILE
)

def test_compute_sha256():
    """Test SHA-256 computation is deterministic."""
    text = "Hello World"
    hash1 = compute_sha256(text)
    hash2 = compute_sha256(text)
    assert hash1 == hash2
    assert len(hash1) == 64  # Hex length

def test_compute_sha256_different():
    """Test different texts produce different hashes."""
    assert compute_sha256("A") != compute_sha256("B")

@patch('code.data.dataset_loader.STATE_DIR')
@patch('code.data.dataset_loader.yaml')
def test_update_state_checksum(mock_yaml, mock_state_dir):
    """Test state file update logic."""
    mock_state_dir.exists.return_value = True
    mock_state_dir.mkdir.return_value = None
    
    # Mock file operations
    with patch('builtins.open', create=True) as mock_open:
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        update_state_checksum("abc123", "test_source", 1024)
        
        # Verify write was called
        assert mock_file.write.called

@patch('code.data.dataset_loader.load_dataset')
@patch('code.data.dataset_loader.update_state_checksum')
def test_load_from_huggingface_success(mock_update, mock_load_ds):
    """Test successful HF load."""
    # Mock dataset structure
    mock_train = MagicMock()
    mock_train.__iter__.return_value = [{'text': 'test text'}]
    mock_train.keys.return_value = ['text']
    
    mock_ds = MagicMock()
    mock_ds.keys.return_value = ['train']
    mock_ds.__getitem__.return_value = mock_train
    
    mock_load_ds.return_value = mock_ds

    ds, source = load_dataset_wrapper()
    
    assert "hf:" in source
    mock_update.assert_called_once()

@patch('code.data.dataset_loader.load_dataset', side_effect=Exception("HF Fail"))
@patch('code.data.dataset_loader.requests.get')
@patch('code.data.dataset_loader.update_state_checksum')
def test_load_fallback_success(mock_update, mock_get, mock_hf_fail):
    """Test fallback download when HF fails."""
    # Mock response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.content = b"PK\x03\x04" # Fake zip header
    
    mock_get.return_value = mock_response
    
    # Mock zipfile to avoid actual unzip
    with patch('code.data.dataset_loader.zipfile.ZipFile') as mock_zip:
        mock_zip_inst = MagicMock()
        mock_zip_inst.namelist.return_value = ['wikitext-2-raw-v1.txt']
        mock_zip_inst.open.return_value.__enter__.return_value.read.return_value = b"Test content"
        mock_zip.return_value = mock_zip_inst
        
        # Mock Path.exists
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.mkdir'):
                with patch('builtins.open', create=True) as mock_open:
                    mock_file = MagicMock()
                    mock_open.return_value.__enter__.return_value = mock_file
                    
                    ds, source = load_dataset_wrapper()
                    
                    assert "s3:" in source
                    mock_update.assert_called()

@patch('code.data.dataset_loader.load_dataset', side_effect=Exception("HF Fail"))
@patch('code.data.dataset_loader.requests.get', side_effect=Exception("Network Fail"))
def test_load_both_fail(mock_get, mock_hf_fail):
    """Test error when both sources fail."""
    with pytest.raises(RuntimeError, match="Both HF and Fallback failed"):
        load_dataset_wrapper()
