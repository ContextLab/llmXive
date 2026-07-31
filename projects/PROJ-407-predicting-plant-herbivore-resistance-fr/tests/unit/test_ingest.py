import pytest
import pandas as pd
import json
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from ingest import (
    extract_resistance_column,
    convert_categorical_to_ordinal,
    check_herbivore_density_normalization,
    harmonize_dataset
)
from config import DATA_ROOT

class TestExtractResistanceColumn:
    def test_missing_column(self):
        """Test error when resistance column is missing."""
        data = {'sample_id': [1, 2], 'metabolite_A': [10, 20]}
        df = pd.DataFrame(data)
        # Mock dataset object
        class MockDataset:
            column_names = list(data.keys())
            def __getitem__(self, key):
                return data[key]
        
        ds = MockDataset()
        
        with pytest.raises(ValueError, match="No quantifiable resistance metric found"):
            extract_resistance_column(ds)

    def test_non_numeric_resistance(self):
        """Test error when resistance is non-numeric and not categorical."""
        data = {'sample_id': [1, 2], 'resistance': ['A', 'B'], 'metabolite_A': [10, 20]}
        df = pd.DataFrame(data)
        class MockDataset:
            column_names = list(data.keys())
            def __getitem__(self, key):
                return data[key]
        
        ds = MockDataset()
        with pytest.raises(ValueError, match="No quantifiable resistance metric found"):
            extract_resistance_column(ds)

    def test_numeric_resistance(self):
        """Test successful extraction of numeric resistance."""
        data = {'sample_id': [1, 2], 'resistance': [1.5, 2.5], 'metabolite_A': [10, 20]}
        class MockDataset:
            column_names = list(data.keys())
            def __getitem__(self, key):
                return data[key]
        
        ds = MockDataset()
        result = extract_resistance_column(ds)
        assert result is not None
        assert len(result) == 2

class TestConvertCategoricalToOrdinal:
    def test_conversion(self):
        """Test categorical to ordinal conversion."""
        data = {'resistance': ['Low', 'Medium', 'High', 'Low']}
        df = pd.DataFrame(data)
        
        result_df = convert_categorical_to_ordinal(df)
        
        expected = [1, 2, 3, 1]
        assert list(result_df['resistance']) == expected

    def test_log_file_created(self):
        """Test that the mapping log file is created."""
        # Create a temporary directory for testing to avoid polluting DATA_ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            interim_path = os.path.join(tmpdir, 'interim')
            os.makedirs(interim_path, exist_ok=True)
            
            # Patch the DATA_ROOT usage in ingest module by patching os.path.join logic
            # Since DATA_ROOT is imported from config, we patch the specific file path generation
            mock_log_path = os.path.join(interim_path, 'ordinal_mapping.log')
            
            data = {'resistance': ['Low', 'High']}
            df = pd.DataFrame(data)
            
            # We need to mock the file writing path to point to our temp dir
            # Since the function uses a hardcoded path relative to DATA_ROOT,
            # we patch the open function or the path construction
            original_open = open
            
            def mock_open_func(*args, **kwargs):
                if 'ordinal_mapping.log' in args[0]:
                    # Redirect to temp file
                    return original_open(mock_log_path, *args[1:], **kwargs)
                return original_open(*args, **kwargs)
            
            with patch('builtins.open', mock_open_func):
                convert_categorical_to_ordinal(df)
                
            # Verify the log file was created
            assert os.path.exists(mock_log_path), f"Log file not created at {mock_log_path}"
            
            # Verify content
            with open(mock_log_path, 'r') as f:
                content = f.read()
                assert 'Low' in content
                assert 'High' in content

class TestCheckHerbivoreDensityNormalization:
    def test_missing_column(self):
        """Test metadata update when herbivore_density is missing."""
        data = {'sample_id': [1], 'resistance': [1.0]}
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            interim_path = os.path.join(tmpdir, 'interim')
            os.makedirs(interim_path, exist_ok=True)
            
            mock_metadata_path = os.path.join(interim_path, 'metadata.json')
            
            # Patch the file path to use our temp directory
            def mock_open_func(*args, **kwargs):
                if 'metadata.json' in args[0]:
                    return open(mock_metadata_path, *args[1:], **kwargs)
                return open(*args, **kwargs)
            
            with patch('builtins.open', mock_open_func):
                # Also need to ensure the directory exists if the function creates it
                with patch('os.makedirs', side_effect=lambda x, **kw: os.makedirs(x, exist_ok=True)):
                    check_herbivore_density_normalization(df)
            
            # Verify the metadata file was created/updated
            assert os.path.exists(mock_metadata_path)
            
            with open(mock_metadata_path, 'r') as f:
                meta = json.load(f)
                assert meta.get('herbivore_density_missing') is True

    def test_column_exists(self):
        """Test that no update happens when column exists."""
        data = {'sample_id': [1], 'resistance': [1.0], 'herbivore_density': [5.0]}
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            interim_path = os.path.join(tmpdir, 'interim')
            os.makedirs(interim_path, exist_ok=True)
            
            mock_metadata_path = os.path.join(interim_path, 'metadata.json')
            
            def mock_open_func(*args, **kwargs):
                if 'metadata.json' in args[0]:
                    return open(mock_metadata_path, *args[1:], **kwargs)
                return open(*args, **kwargs)
            
            # Create an initial empty metadata file
            with open(mock_metadata_path, 'w') as f:
                json.dump({}, f)
            
            with patch('builtins.open', mock_open_func):
                with patch('os.makedirs', side_effect=lambda x, **kw: os.makedirs(x, exist_ok=True)):
                    check_herbivore_density_normalization(df)
            
            with open(mock_metadata_path, 'r') as f:
                meta = json.load(f)
                # The key should NOT be present or be false
                assert meta.get('herbivore_density_missing') is None

class TestHarmonizeDataset:
    def test_harmonization_flow(self):
        """Test full harmonization flow."""
        data = {
            'sample_id': [1, 2, 3],
            'resistance': ['Low', 'High', 'Medium'],
            'metabolite_A': [10.0, None, 20.0],
            'metabolite_B': [15.0, 25.0, 30.0]
        }
        df = pd.DataFrame(data)
        
        result_df = harmonize_dataset(df)
        
        # Check resistance conversion
        assert list(result_df['resistance']) == [1, 3, 2]
        
        # Check imputation flag
        # Row 0: no NaN -> 0
        # Row 1: metabolite_A is NaN -> 1
        # Row 2: no NaN -> 0
        expected_flags = [0, 1, 0]
        assert list(result_df['imputation_flag']) == expected_flags

        # Check that output is a DataFrame
        assert isinstance(result_df, pd.DataFrame)
        assert 'imputation_flag' in result_df.columns

    def test_numeric_resistance_no_conversion(self):
        """Test that numeric resistance is not converted."""
        data = {
            'sample_id': [1, 2, 3],
            'resistance': [1.5, 2.5, 3.5],
            'metabolite_A': [10.0, 20.0, 30.0]
        }
        df = pd.DataFrame(data)
        
        result_df = harmonize_dataset(df)
        
        # Resistance should remain numeric
        assert list(result_df['resistance']) == [1.5, 2.5, 3.5]
        
        # Imputation flag should be all 0
        assert list(result_df['imputation_flag']) == [0, 0, 0]

    def test_multiple_missing_values(self):
        """Test imputation flag with multiple missing values."""
        data = {
            'sample_id': [1, 2],
            'resistance': ['Low', 'High'],
            'metabolite_A': [None, None],
            'metabolite_B': [15.0, 25.0]
        }
        df = pd.DataFrame(data)
        
        result_df = harmonize_dataset(df)
        
        # Both rows have missing metabolite_A, so both flags should be 1
        assert list(result_df['imputation_flag']) == [1, 1]