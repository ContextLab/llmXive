"""
Unit tests for T051a: Verify Dataset Existence.

These tests verify that the verify_dataset.py script correctly raises
a RuntimeError when the dataset is not found, and handles the verification logic.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add code root to path for imports
code_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(code_root))

from src.data.verify_dataset import verify_dataset_existence

def test_verify_dataset_success():
    """Test that verify_dataset_existence returns True when dataset is found."""
    with patch('src.data.verify_dataset.load_dataset') as mock_load:
        # Mock the dataset object
        mock_ds = MagicMock()
        mock_load.return_value = mock_ds
        
        result = verify_dataset_existence()
        
        assert result is True
        mock_load.assert_called_once()
        
        # Verify arguments match the task requirements
        call_kwargs = mock_load.call_args.kwargs
        assert call_kwargs['streaming'] is True
        assert call_kwargs['trust_remote_code'] is True

def test_verify_dataset_not_found_raises_runtime_error():
    """Test that a 404 or 'not found' error raises RuntimeError."""
    error_message = "Dataset not found: vvud/eb-data"
    
    with patch('src.data.verify_dataset.load_dataset') as mock_load:
        mock_load.side_effect = Exception(error_message)
        
        with pytest.raises(RuntimeError) as excinfo:
            verify_dataset_existence()
        
        assert "CRITICAL FAILURE" in str(excinfo.value)
        assert "does not exist" in str(excinfo.value)

def test_verify_dataset_network_error_raises_runtime_error():
    """Test that network errors also raise RuntimeError (fail loudly)."""
    error_message = "Connection timeout"
    
    with patch('src.data.verify_dataset.load_dataset') as mock_load:
        mock_load.side_effect = Exception(error_message)
        
        with pytest.raises(RuntimeError) as excinfo:
            verify_dataset_existence()
        
        assert "CRITICAL FAILURE" in str(excinfo.value)
        assert "Unable to access" in str(excinfo.value)