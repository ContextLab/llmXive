"""
Unit tests for the data loader module.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

from utils.exceptions import DataIntegrityError
from data.loader import (
    load_glue_subset,
    load_superglue_subset,
    load_dataset_subset,
    get_available_subsets,
    verify_dataset_integrity,
    compute_file_checksum
)

def test_compute_file_checksum():
    """Test checksum computation for a simple file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = compute_file_checksum(temp_path)
        assert len(checksum) == 64  # SHA-256 hex string length
        assert all(c in '0123456789abcdef' for c in checksum)
    finally:
        os.unlink(temp_path)

def test_compute_file_checksum_consistency():
    """Test that checksum is consistent for the same file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum1 = compute_file_checksum(temp_path)
        checksum2 = compute_file_checksum(temp_path)
        assert checksum1 == checksum2
    finally:
        os.unlink(temp_path)

def test_load_glue_subset_invalid_subset():
    """Test that loading an invalid GLUE subset raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported GLUE subset"):
        load_glue_subset("invalid_subset")

def test_load_superglue_subset_invalid_subset():
    """Test that loading an invalid SuperGLUE subset raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported SuperGLUE subset"):
        load_superglue_subset("invalid_subset")

def test_get_available_subsets_glue():
    """Test getting available GLUE subsets."""
    subsets = get_available_subsets("glue")
    assert isinstance(subsets, list)
    assert "sst2" in subsets
    assert "mnli" in subsets

def test_get_available_subsets_superglue():
    """Test getting available SuperGLUE subsets."""
    subsets = get_available_subsets("superglue")
    assert isinstance(subsets, list)
    assert "boolq" in subsets
    assert "cb" in subsets

def test_get_available_subsets_invalid_type():
    """Test that getting subsets for invalid type raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported dataset type"):
        get_available_subsets("invalid_type")

@patch('data.loader.load_dataset')
@patch('data.loader.verify_dataset_integrity')
def test_load_glue_subset_mocked(mock_verify, mock_load):
    """Test loading GLUE subset with mocked dataset loading."""
    mock_dataset = MagicMock()
    mock_dataset.__getitem__ = MagicMock(return_value=MagicMock(__len__=MagicMock(return_value=100)))
    mock_load.return_value = mock_dataset
    mock_verify.return_value = True

    dataset = load_glue_subset("sst2", verify_checksum=True)
    
    mock_load.assert_called_once_with("glue", "sst2", cache_dir=None, trust_remote_code=True)
    mock_verify.assert_called_once_with("glue", "sst2", None)

@patch('data.loader.load_dataset')
@patch('data.loader.verify_dataset_integrity')
def test_load_superglue_subset_mocked(mock_verify, mock_load):
    """Test loading SuperGLUE subset with mocked dataset loading."""
    mock_dataset = MagicMock()
    mock_dataset.__getitem__ = MagicMock(return_value=MagicMock(__len__=MagicMock(return_value=100)))
    mock_load.return_value = mock_dataset
    mock_verify.return_value = True

    dataset = load_superglue_subset("boolq", verify_checksum=True)
    
    mock_load.assert_called_once_with("super_glue", "boolq", cache_dir=None, trust_remote_code=True)
    mock_verify.assert_called_once_with("super_glue", "boolq", None)

@patch('data.loader.load_glue_subset')
def test_load_dataset_subset_glue(mock_glue):
    """Test loading dataset subset with GLUE type."""
    mock_glue.return_value = MagicMock()
    
    dataset = load_dataset_subset("glue", "sst2")
    
    mock_glue.assert_called_once_with("sst2", None, True)

@patch('data.loader.load_superglue_subset')
def test_load_dataset_subset_superglue(mock_superglue):
    """Test loading dataset subset with SuperGLUE type."""
    mock_superglue.return_value = MagicMock()
    
    dataset = load_dataset_subset("superglue", "boolq")
    
    mock_superglue.assert_called_once_with("boolq", None, True)

def test_load_dataset_subset_invalid_type():
    """Test that loading dataset subset with invalid type raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported dataset type"):
        load_dataset_subset("invalid_type", "sst2")

@patch('data.loader.load_dataset')
def test_verify_dataset_integrity_empty_dataset(mock_load):
    """Test that empty dataset raises DataIntegrityError."""
    mock_dataset = MagicMock()
    mock_dataset.__getitem__ = MagicMock(return_value=MagicMock(__len__=MagicMock(return_value=0)))
    mock_load.return_value = mock_dataset

    with pytest.raises(DataIntegrityError, match="is empty"):
        verify_dataset_integrity("glue", "sst2")

@patch('data.loader.load_dataset')
def test_verify_dataset_integrity_success(mock_load):
    """Test successful dataset integrity verification."""
    mock_dataset = MagicMock()
    mock_dataset.__getitem__ = MagicMock(return_value=MagicMock(__len__=MagicMock(return_value=100)))
    mock_load.return_value = mock_dataset

    result = verify_dataset_integrity("glue", "sst2")
    assert result is True

@patch('data.loader.load_dataset')
def test_verify_dataset_integrity_exception(mock_load):
    """Test that exception during verification raises DataIntegrityError."""
    mock_load.side_effect = Exception("Dataset load failed")

    with pytest.raises(DataIntegrityError, match="Failed to verify dataset integrity"):
        verify_dataset_integrity("glue", "sst2")