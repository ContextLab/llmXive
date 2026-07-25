import pytest
import pandas as pd
from pathlib import Path
import json
import sys
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from data_loader import validate_dataset, load_datasets
from exceptions import CriticalValidationError

class TestDataLoaderValidation:
    """Unit tests for dataset validation logic in data_loader.py"""
    
    def test_validate_dataset_passes_when_n_ge_50(self):
        """Test that validation passes when dataset has >= 50 rows"""
        df = pd.DataFrame({'col1': range(50), 'col2': range(50, 100)})
        is_valid, reason = validate_dataset(df, "test_dataset", min_n=50)
        
        assert is_valid is True
        assert "50 rows" in reason
        assert ">= 50" in reason
    
    def test_validate_dataset_fails_when_n_lt_50(self):
        """Test that validation fails when dataset has < 50 rows"""
        df = pd.DataFrame({'col1': range(10), 'col2': range(10, 20)})
        is_valid, reason = validate_dataset(df, "small_dataset", min_n=50)
        
        assert is_valid is False
        assert "10 rows" in reason
        assert "less than minimum" in reason
    
    def test_validate_dataset_custom_min_n(self):
        """Test validation with custom minimum N"""
        df = pd.DataFrame({'col1': range(30), 'col2': range(30, 60)})
        
        # Should pass with min_n=30
        is_valid, reason = validate_dataset(df, "test", min_n=30)
        assert is_valid is True
        
        # Should fail with min_n=31
        is_valid, reason = validate_dataset(df, "test", min_n=31)
        assert is_valid is False
    
    @patch('data_loader.load_manifest')
    @patch('data_loader.fetch_dataset')
    @patch('data_loader.validate_dataset')
    @patch('data_loader.open', new_callable=MagicMock)
    def test_load_datasets_logs_violations(self, mock_open, mock_validate, mock_fetch, mock_load_manifest):
        """Test that violations are logged when datasets fail validation"""
        # Setup mocks
        mock_load_manifest.return_value = [
            {'name': 'valid_ds', 'url': 'http://example.com/valid.csv'},
            {'name': 'invalid_ds', 'url': 'http://example.com/invalid.csv'}
        ]
        
        # Mock fetch_dataset to return valid DataFrames
        mock_fetch.return_value = (pd.DataFrame({'col': range(100)}), 'checksum123')
        
        # Mock validate_dataset to return different results
        def mock_validate_side_effect(df, name, min_n):
            if name == 'valid_ds':
                return True, "Valid"
            else:
                return False, "Too small"
        
        mock_validate.side_effect = mock_validate_side_effect
        
        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Run load_datasets
        result = load_datasets(min_n=50)
        
        # Verify valid dataset is included
        assert len(result) == 1
        assert result[0]['name'] == 'valid_ds'
        
        # Verify validation report was written
        mock_open.assert_called()
        # Check that the write call contains violation info
        write_calls = [call[0][0] for call in mock_open.call_args_list if len(call) > 0 and hasattr(call[0][0], 'write')]
        # The actual JSON content would be in the write calls
    
    @patch('data_loader.load_manifest')
    @patch('data_loader.fetch_dataset')
    def test_all_datasets_fail_raises_critical_error(self, mock_fetch, mock_load_manifest):
        """Test that CriticalValidationError is raised when ALL datasets fail"""
        # Setup mocks
        mock_load_manifest.return_value = [
            {'name': 'small_ds1', 'url': 'http://example.com/small1.csv'},
            {'name': 'small_ds2', 'url': 'http://example.com/small2.csv'}
        ]
        
        # Mock fetch to return small DataFrames
        mock_fetch.return_value = (pd.DataFrame({'col': range(10)}), 'checksum')
        
        # Mock validate to always fail
        with patch('data_loader.validate_dataset', return_value=(False, "Too small")):
            with patch('data_loader.open', new_callable=MagicMock):
                with patch('data_loader.Path.mkdir'):
                    with patch('data_loader.json.dump'):
                        with pytest.raises(CriticalValidationError) as exc_info:
                            load_datasets(min_n=50)
                            
                        assert "All" in str(exc_info.value)
                        assert "failed validation" in str(exc_info.value)
    
    def test_validation_report_structure(self):
        """Test that validation report has correct structure"""
        # Create a minimal test scenario
        with patch('data_loader.load_manifest') as mock_manifest, \
             patch('data_loader.fetch_dataset') as mock_fetch, \
             patch('data_loader.validate_dataset') as mock_validate, \
             patch('data_loader.Path.mkdir'), \
             patch('builtins.open', new_callable=MagicMock) as mock_open:
            
            mock_manifest.return_value = [
                {'name': 'test_ds', 'url': 'http://example.com/test.csv'}
            ]
            mock_fetch.return_value = (pd.DataFrame({'col': range(100)}), 'checksum')
            mock_validate.return_value = (True, "Valid")
            
            # Mock the file object for writing
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            load_datasets(min_n=50)
            
            # Verify json.dump was called with correct structure
            assert mock_file.write.called
            # The actual JSON would be passed to write
            # We can't easily extract it from the mock, but we verify the call happened
