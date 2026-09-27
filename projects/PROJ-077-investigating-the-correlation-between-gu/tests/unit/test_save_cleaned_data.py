"""
Unit tests for save_cleaned_data module.

Tests Task T015: Save cleaned dataset functionality.
"""
import os
import sys
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.save_cleaned_data import save_cleaned_dataset, main
from code.logging_config import get_logger

logger = get_logger(__name__)

class TestSaveCleanedDataset:
    """Test suite for save_cleaned_dataset function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_output_path = os.path.join(self.test_dir, "test_cleaned_data.csv")
        
        # Create a sample DataFrame
        self.sample_df = pd.DataFrame({
            'participant_id': ['P001', 'P002', 'P003'],
            'shannon_index': [3.2, 3.5, 2.9],
            'fluid_intelligence': [45, 52, 38],
            'age': [45, 50, 42],
            'sex': ['M', 'F', 'M'],
            'bmi': [24.5, 26.1, 22.8],
            'dqs': [65, 70, 58]
        })
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_save_cleaned_dataset_creates_file(self):
        """Test that save_cleaned_dataset creates the output file."""
        result_path = save_cleaned_dataset(self.sample_df, self.test_output_path)
        
        assert os.path.exists(result_path), "Output file should exist"
        assert result_path == self.test_output_path, "Returned path should match input path"
    
    def test_save_cleaned_dataset_contains_data(self):
        """Test that the saved file contains the expected data."""
        save_cleaned_dataset(self.sample_df, self.test_output_path)
        
        # Read the file back
        with open(self.test_output_path, 'r') as f:
            lines = f.readlines()
        
        # Check for column definitions in header
        header_lines = [l for l in lines if l.startswith('#')]
        assert len(header_lines) > 0, "File should contain column definition comments"
        
        # Check that actual data exists
        data_lines = [l for l in lines if not l.startswith('#')]
        assert len(data_lines) == 4, "Should have 1 header + 3 data rows"  # header + 3 rows
    
    def test_save_cleaned_dataset_empty_dataframe_raises_error(self):
        """Test that saving an empty DataFrame raises ValueError."""
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError, match="Cannot save empty or None DataFrame"):
            save_cleaned_dataset(empty_df, self.test_output_path)
    
    def test_save_cleaned_dataset_none_dataframe_raises_error(self):
        """Test that saving None raises ValueError."""
        with pytest.raises(ValueError, match="Cannot save empty or None DataFrame"):
            save_cleaned_dataset(None, self.test_output_path)
    
    def test_save_cleaned_dataset_column_definitions(self):
        """Test that column definitions are correctly formatted."""
        save_cleaned_dataset(self.sample_df, self.test_output_path)
        
        with open(self.test_output_path, 'r') as f:
            content = f.read()
        
        # Check for expected column definitions
        assert "participant_id" in content, "Should contain participant_id definition"
        assert "shannon_index" in content, "Should contain shannon_index definition"
        assert "fluid_intelligence" in content, "Should contain fluid_intelligence definition"
        assert "dtype=" in content, "Should contain dtype information"
        assert "nulls=" in content, "Should contain null count information"
    
    def test_save_cleaned_dataset_creates_directories(self):
        """Test that save_cleaned_dataset creates missing directories."""
        nested_path = os.path.join(self.test_dir, "nested", "path", "output.csv")
        result_path = save_cleaned_dataset(self.sample_df, nested_path)
        
        assert os.path.exists(result_path), "File should exist in nested directory"
        assert os.path.isdir(os.path.dirname(result_path)), "Directory should be created"

class TestMainFunction:
    """Test suite for main function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('code.save_cleaned_data.run_ingestion_pipeline')
    @patch('code.save_cleaned_data.ensure_directories')
    def test_main_success(self, mock_ensure_dirs, mock_ingestion):
        """Test main function with successful ingestion."""
        mock_ingestion.return_value = pd.DataFrame({'col1': [1, 2, 3]})
        
        with patch('code.save_cleaned_data.INPUT_PATHS', {'PROCESSED_OUTPUT': os.path.join(self.test_dir, 'output.csv')}):
            result = main()
        
        assert result == 0, "Main should return 0 on success"
        mock_ensure_dirs.assert_called_once()
        mock_ingestion.assert_called_once()
    
    @patch('code.save_cleaned_data.run_ingestion_pipeline')
    @patch('code.save_cleaned_data.ensure_directories')
    def test_main_empty_dataset(self, mock_ensure_dirs, mock_ingestion):
        """Test main function with empty dataset."""
        mock_ingestion.return_value = pd.DataFrame()
        
        with patch('code.save_cleaned_data.INPUT_PATHS', {'PROCESSED_OUTPUT': os.path.join(self.test_dir, 'output.csv')}):
            result = main()
        
        assert result == 0, "Main should return 0 even with empty dataset"
    
    @patch('code.save_cleaned_data.run_ingestion_pipeline')
    def test_main_ingestion_failure(self, mock_ingestion):
        """Test main function when ingestion fails."""
        mock_ingestion.side_effect = Exception("Ingestion failed")
        
        result = main()
        
        assert result == 1, "Main should return 1 on failure"
    
    @patch('code.save_cleaned_data.run_ingestion_pipeline')
    @patch('code.save_cleaned_data.save_cleaned_dataset')
    def test_main_save_failure(self, mock_save, mock_ingestion):
        """Test main function when save fails."""
        mock_ingestion.return_value = pd.DataFrame({'col1': [1, 2, 3]})
        mock_save.side_effect = IOError("Save failed")
        
        result = main()
        
        assert result == 1, "Main should return 1 on save failure"