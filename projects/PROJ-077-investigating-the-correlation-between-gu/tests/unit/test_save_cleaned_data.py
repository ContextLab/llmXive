import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from save_cleaned_data import save_cleaned_dataset

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'participant_id': [1, 2, 3, 4, 5],
        'shannon_index': [3.2, 2.8, 3.5, 2.9, 3.1],
        'fluid_intelligence': [12.5, 11.2, 13.1, 10.8, 12.0],
        'age': [45, 52, 38, 61, 49],
        'sex': ['M', 'F', 'M', 'F', 'M'],
        'bmi': [24.5, 26.1, 22.3, 28.7, 25.0],
        'dqs': [65.2, 58.9, 72.1, 55.3, 68.4]
    }
    return pd.DataFrame(data)

def test_save_cleaned_dataset_creates_file(sample_dataframe):
    """Test that save_cleaned_dataset creates the output file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_cleaned_data.csv')
        save_cleaned_dataset(sample_dataframe, output_path)
        
        assert os.path.exists(output_path), "Output file was not created."
        
        # Verify file is not empty
        assert os.path.getsize(output_path) > 0, "Output file is empty."

def test_save_cleaned_dataset_includes_header_definitions(sample_dataframe):
    """Test that the saved file includes column definitions in the header."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_cleaned_data.csv')
        save_cleaned_dataset(sample_dataframe, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            second_line = f.readline().strip()
        
        assert first_line.startswith("# Column Definitions:"), "First line should be column definitions header."
        assert second_line.startswith("#"), "Second line should be a column definition."
        
        # Check that at least one column name appears in the header
        header_content = second_line.lower()
        assert 'participant_id' in header_content or 'shannon_index' in header_content, \
            "Column definitions should include column names."

def test_save_cleaned_dataset_data_integrity(sample_dataframe):
    """Test that the data is correctly saved and can be reloaded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_cleaned_data.csv')
        save_cleaned_dataset(sample_dataframe, output_path)
        
        # Read back the file, skipping the header comments
        df_reloaded = pd.read_csv(output_path, comment='#')
        
        assert len(df_reloaded) == len(sample_dataframe), "Row count mismatch."
        assert list(df_reloaded.columns) == list(sample_dataframe.columns), "Column names mismatch."
        
        # Check a few values
        assert df_reloaded.iloc[0]['participant_id'] == sample_dataframe.iloc[0]['participant_id']
        assert abs(df_reloaded.iloc[0]['shannon_index'] - sample_dataframe.iloc[0]['shannon_index']) < 1e-6

def test_save_cleaned_dataset_empty_dataframe_raises_error():
    """Test that saving an empty DataFrame raises a ValueError."""
    empty_df = pd.DataFrame()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_empty.csv')
        
        with pytest.raises(ValueError) as excinfo:
            save_cleaned_dataset(empty_df, output_path)
        
        assert "DataFrame is empty" in str(excinfo.value)

def test_save_cleaned_dataset_creates_directory_if_missing(sample_dataframe):
    """Test that the function creates the output directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a subdirectory path that doesn't exist yet
        nested_dir = os.path.join(tmpdir, 'level1', 'level2')
        output_path = os.path.join(nested_dir, 'test_cleaned_data.csv')
        
        # This should not raise an error
        save_cleaned_dataset(sample_dataframe, output_path)
        
        assert os.path.exists(output_path), "Output file was not created in nested directory."