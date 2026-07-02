"""
Unit tests for the save_cleaned_data script (T013).
"""
import pytest
import pandas as pd
from pathlib import Path
import os
import sys
import tempfile
import shutil

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from save_cleaned_data import (
    load_cleaned_data,
    validate_cleaned_data,
    save_cleaned_data,
    REQUIRED_COLUMNS
)
from exceptions import DataValidationError

class TestSaveCleanedData:
    """Tests for the T013 save cleaned data functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_path = tempfile.mkdtemp()
        yield Path(temp_path)
        shutil.rmtree(temp_path)

    @pytest.fixture
    def valid_cleaned_df(self):
        """Create a valid cleaned DataFrame for testing."""
        data = {
            'news_exposure_freq': [1, 2, 3, 4, 5],
            'anxiety_score': [10, 12, 15, 18, 20],
            'baseline_anxiety': [5, 6, 7, 8, 9],
            'age': [20, 25, 30, 35, 40],
            'gender': ['M', 'F', 'M', 'F', 'M']
        }
        return pd.DataFrame(data)

    def test_load_cleaned_data_file_not_found(self, temp_dir):
        """Test that load_cleaned_data raises FileNotFoundError if file doesn't exist."""
        non_existent_path = temp_dir / "non_existent.csv"
        with pytest.raises(FileNotFoundError):
            load_cleaned_data(non_existent_path)

    def test_load_cleaned_data_success(self, temp_dir, valid_cleaned_df):
        """Test successful loading of cleaned data."""
        file_path = temp_dir / "test_data.csv"
        valid_cleaned_df.to_csv(file_path, index=False)
        
        loaded_df = load_cleaned_data(file_path)
        assert loaded_df.equals(valid_cleaned_df)
        assert len(loaded_df) == 5

    def test_validate_cleaned_data_missing_columns(self, valid_cleaned_df):
        """Test that validate_cleaned_data raises error for missing columns."""
        # Remove a required column
        invalid_df = valid_cleaned_df.drop(columns=['news_exposure_freq'])
        
        with pytest.raises(DataValidationError, match="Missing required columns"):
            validate_cleaned_data(invalid_df)

    def test_validate_cleaned_data_null_primary_vars(self, valid_cleaned_df):
        """Test that validate_cleaned_data raises error for null primary variables."""
        # Introduce null in primary variable
        invalid_df = valid_cleaned_df.copy()
        invalid_df.loc[0, 'news_exposure_freq'] = None
        
        with pytest.raises(DataValidationError, match="Primary variable.*has.*null values"):
            validate_cleaned_data(invalid_df)

    def test_validate_cleaned_data_success(self, valid_cleaned_df):
        """Test successful validation of cleaned data."""
        # Should not raise any exception
        try:
            validate_cleaned_data(valid_cleaned_df)
        except Exception as e:
            pytest.fail(f"validate_cleaned_data raised unexpected exception: {e}")

    def test_save_cleaned_data(self, temp_dir, valid_cleaned_df):
        """Test successful saving of cleaned data."""
        output_path = temp_dir / "output.csv"
        save_cleaned_data(valid_cleaned_df, output_path)
        
        assert output_path.exists()
        
        # Verify content
        saved_df = pd.read_csv(output_path)
        assert saved_df.equals(valid_cleaned_df)
        assert len(saved_df) == 5

    def test_save_cleaned_data_directory_creation(self, temp_dir, valid_cleaned_df):
        """Test that save_cleaned_data creates parent directories if needed."""
        output_path = temp_dir / "subdir" / "output.csv"
        save_cleaned_data(valid_cleaned_df, output_path)
        
        assert output_path.exists()