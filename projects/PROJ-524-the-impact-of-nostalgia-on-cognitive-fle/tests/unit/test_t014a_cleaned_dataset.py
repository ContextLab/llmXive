"""
Unit tests for T014a: Generate Cleaned Dataset

Tests the functionality of creating the final cleaned dataset from
the intermediate cleaned dataset.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest

# Add the code directory to the path
import sys
from unittest.mock import patch, MagicMock

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from task_t014a_create_cleaned_dataset import (
    create_cleaned_dataset,
    REQUIRED_COLUMNS,
    load_intermediate_dataset,
    save_cleaned_dataset
)

class TestT014aCleanedDataset:
    """Tests for the T014a cleaned dataset generation."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    @pytest.fixture
    def sample_intermediate_data(self):
        """Create sample intermediate data."""
        data = {
            'participant_id': [1, 2, 3, 4, 5],
            'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control', 'nostalgia'],
            'perseverative_errors': [5, 8, 4, 9, 6],
            'categories_completed': [3, 2, 4, 1, 3],
            'age': [68, 72, 65, 70, 69],
            'extra_column': ['a', 'b', 'c', 'd', 'e']  # Extra column to be removed
        }
        return pd.DataFrame(data)
    
    def test_create_cleaned_dataset_selects_correct_columns(self, sample_intermediate_data):
        """Test that only required columns are selected."""
        result = create_cleaned_dataset(sample_intermediate_data)
        
        # Check that only required columns are present
        assert list(result.columns) == REQUIRED_COLUMNS
        
        # Check that extra columns are removed
        assert 'extra_column' not in result.columns
        
        # Check that all required columns are present
        for col in REQUIRED_COLUMNS:
            assert col in result.columns
    
    def test_create_cleaned_dataset_preserves_data(self, sample_intermediate_data):
        """Test that data values are preserved correctly."""
        result = create_cleaned_dataset(sample_intermediate_data)
        
        # Check that data is preserved
        assert result['participant_id'].tolist() == [1, 2, 3, 4, 5]
        assert result['stimulus_type'].tolist() == ['nostalgia', 'control', 'nostalgia', 'control', 'nostalgia']
        assert result['age'].tolist() == [68, 72, 65, 70, 69]
    
    def test_create_cleaned_dataset_raises_on_missing_columns(self, temp_dir):
        """Test that an error is raised when required columns are missing."""
        # Create data with missing required columns
        incomplete_data = pd.DataFrame({
            'participant_id': [1, 2],
            'stimulus_type': ['nostalgia', 'control']
            # Missing: perseverative_errors, categories_completed, age
        })
        
        with pytest.raises(ValueError) as exc_info:
            create_cleaned_dataset(incomplete_data)
        
        # Check that the error message mentions missing columns
        assert "Missing required columns" in str(exc_info.value)
        assert "perseverative_errors" in str(exc_info.value)
    
    def test_save_cleaned_dataset_creates_file(self, temp_dir, sample_intermediate_data):
        """Test that save_cleaned_dataset creates the output file."""
        output_path = temp_dir / "test_output.csv"
        
        # Create the dataset
        result = create_cleaned_dataset(sample_intermediate_data)
        
        # Save it
        save_cleaned_dataset(result, output_path)
        
        # Verify the file was created
        assert output_path.exists()
        
        # Verify the content
        loaded = pd.read_csv(output_path)
        assert list(loaded.columns) == REQUIRED_COLUMNS
        assert len(loaded) == len(sample_intermediate_data)
    
    def test_save_cleaned_dataset_creates_directory(self, temp_dir, sample_intermediate_data):
        """Test that save_cleaned_dataset creates parent directories if needed."""
        output_path = temp_dir / "subdir" / "nested" / "test_output.csv"
        
        # Create the dataset
        result = create_cleaned_dataset(sample_intermediate_data)
        
        # Save it (should create subdir/nested)
        save_cleaned_dataset(result, output_path)
        
        # Verify the file was created
        assert output_path.exists()
        
        # Verify the parent directories were created
        assert (temp_dir / "subdir" / "nested").exists()
    
    def test_required_columns_constant(self):
        """Test that REQUIRED_COLUMNS contains the expected values."""
        expected = [
            'participant_id',
            'stimulus_type',
            'perseverative_errors',
            'categories_completed',
            'age'
        ]
        assert REQUIRED_COLUMNS == expected
        assert len(REQUIRED_COLUMNS) == 5