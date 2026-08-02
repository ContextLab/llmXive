"""
Unit tests for the export_descriptors module.

Tests Task T021: Output descriptors to `data/processed/descriptors.csv` linked to original sample IDs.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from features.export_descriptors import load_processed_data, calculate_and_export_descriptors
from data.models import EbsdSample

class TestLoadProcessedData:
    """Tests for the load_processed_data function."""
    
    @patch('features.export_descriptors.get_data_path')
    @patch('features.export_descriptors.pd.read_parquet')
    def test_load_processed_data_success(self, mock_read_parquet, mock_get_data_path):
        """Test successful loading of processed data."""
        # Setup mocks
        mock_path = Path("/fake/data/path")
        mock_get_data_path.return_value = mock_path
        
        # Create mock DataFrame
        mock_df = pd.DataFrame({
            'sample_id': ['sample1', 'sample2'],
            'material': ['Al', 'Cu'],
            'reduction': [10, 20],
            'phi1': [0.0, 10.0],
            'Phi': [45.0, 50.0],
            'phi2': [0.0, 10.0]
        })
        mock_read_parquet.return_value = mock_df
        
        # Call function
        result = load_processed_data()
        
        # Assertions
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'sample_id' in result.columns
        mock_read_parquet.assert_called_once_with(mock_path / "processed" / "cleaned_ebsd.parquet")
    
    @patch('features.export_descriptors.get_data_path')
    def test_load_processed_data_file_not_found(self, mock_get_data_path):
        """Test FileNotFoundError when file does not exist."""
        mock_path = Path("/fake/data/path")
        mock_get_data_path.return_value = mock_path
        
        with patch('features.export_descriptors.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                load_processed_data()
    
    @patch('features.export_descriptors.get_data_path')
    @patch('features.export_descriptors.pd.read_parquet')
    def test_load_processed_data_empty(self, mock_read_parquet, mock_get_data_path):
        """Test ValueError when data file is empty."""
        mock_path = Path("/fake/data/path")
        mock_get_data_path.return_value = mock_path
        
        mock_df = pd.DataFrame()
        mock_read_parquet.return_value = mock_df
        
        with pytest.raises(ValueError):
            load_processed_data()

class TestCalculateAndExportDescriptors:
    """Tests for the calculate_and_export_descriptors function."""
    
    @patch('features.export_descriptors.calculate_descriptors')
    @patch('features.export_descriptors.get_data_path')
    @patch('features.export_descriptors.pd.DataFrame.to_csv')
    @patch('features.export_descriptors.pd.read_parquet')
    def test_calculate_and_export_descriptors_success(
        self, mock_read_parquet, mock_to_csv, mock_get_data_path, mock_calc_desc
    ):
        """Test successful calculation and export of descriptors."""
        # Setup mocks
        mock_path = Path("/fake/data/path")
        mock_get_data_path.return_value = mock_path
        
        # Create mock input data
        mock_df = pd.DataFrame({
            'sample_id': ['sample1', 'sample1', 'sample2', 'sample2'],
            'material': ['Al', 'Al', 'Cu', 'Cu'],
            'reduction': [10, 10, 20, 20],
            'phi1': [0.0, 10.0, 0.0, 10.0],
            'Phi': [45.0, 50.0, 45.0, 50.0],
            'phi2': [0.0, 10.0, 0.0, 10.0]
        })
        mock_read_parquet.return_value = mock_df
        
        # Mock descriptor calculation
        mock_calc_desc.side_effect = [
            {'texture_index': 1.2, 'brass_fraction': 0.3, 'copper_fraction': 0.2, 
             's_fraction': 0.1, 'goss_fraction': 0.05, 'random_fraction': 0.35},
            {'texture_index': 1.5, 'brass_fraction': 0.4, 'copper_fraction': 0.25, 
             's_fraction': 0.15, 'goss_fraction': 0.05, 'random_fraction': 0.15}
        ]
        
        # Call function
        result = calculate_and_export_descriptors()
        
        # Assertions
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'sample_id' in result.columns
        assert 'texture_index' in result.columns
        assert 'brass_fraction' in result.columns
        
        # Verify CSV was called
        mock_to_csv.assert_called_once()
        call_args = mock_to_csv.call_args
        assert call_args[1]['index'] == False
        
        # Verify output path
        expected_path = mock_path / "processed" / "descriptors.csv"
        assert str(call_args[0][0]) == str(expected_path)
    
    @patch('features.export_descriptors.calculate_descriptors')
    @patch('features.export_descriptors.get_data_path')
    @patch('features.export_descriptors.pd.DataFrame.to_csv')
    @patch('features.export_descriptors.pd.read_parquet')
    def test_calculate_and_export_descriptors_with_errors(
        self, mock_read_parquet, mock_to_csv, mock_get_data_path, mock_calc_desc
    ):
        """Test handling of errors during descriptor calculation."""
        # Setup mocks
        mock_path = Path("/fake/data/path")
        mock_get_data_path.return_value = mock_path
        
        mock_df = pd.DataFrame({
            'sample_id': ['sample1', 'sample2'],
            'material': ['Al', 'Cu'],
            'reduction': [10, 20],
            'phi1': [0.0, 10.0],
            'Phi': [45.0, 50.0],
            'phi2': [0.0, 10.0]
        })
        mock_read_parquet.return_value = mock_df
        
        # First sample succeeds, second fails
        mock_calc_desc.side_effect = [
            {'texture_index': 1.2, 'brass_fraction': 0.3, 'copper_fraction': 0.2, 
             's_fraction': 0.1, 'goss_fraction': 0.05, 'random_fraction': 0.35},
            Exception("Calculation failed")
        ]
        
        # Call function
        result = calculate_and_export_descriptors()
        
        # Assertions
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        
        # First sample should have values
        assert result.iloc[0]['texture_index'] is not None
        
        # Second sample should have None values
        assert result.iloc[1]['texture_index'] is None
        
        # CSV should still be written
        mock_to_csv.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
