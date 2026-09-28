import os
import pandas as pd
import pytest
from pathlib import Path
import tempfile
import shutil

from code.save_cleaned_data import save_cleaned_dataset

class TestSaveCleanedData:
    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create a temporary directory for output files."""
        output_dir = tmp_path / "data" / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def test_save_cleaned_dataset_creates_file(self, temp_output_dir):
        """Test that save_cleaned_dataset creates the output file."""
        df = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'shannon_index': [2.5, 3.1, 2.8],
            'fluid_intelligence': [45, 50, 48]
        })
        output_path = str(temp_output_dir / "cleaned_data.csv")
        
        save_cleaned_dataset(df, output_path)
        
        assert os.path.exists(output_path), "Output file was not created."
        
        # Verify content
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 3, "Row count mismatch."
        assert list(loaded_df.columns) == ['participant_id', 'shannon_index', 'fluid_intelligence']

    def test_save_cleaned_dataset_empty_dataframe_raises(self, temp_output_dir):
        """Test that an empty DataFrame raises ValueError."""
        df = pd.DataFrame()
        output_path = str(temp_output_dir / "cleaned_data.csv")
        
        with pytest.raises(ValueError, match="Cannot save an empty DataFrame"):
            save_cleaned_dataset(df, output_path)

    def test_save_cleaned_dataset_directory_creation(self, tmp_path):
        """Test that the function creates directories if they don't exist."""
        df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
        output_path = str(tmp_path / "deep" / "nested" / "dir" / "cleaned_data.csv")
        
        save_cleaned_dataset(df, output_path)
        
        assert os.path.exists(output_path), "Nested directories were not created."
