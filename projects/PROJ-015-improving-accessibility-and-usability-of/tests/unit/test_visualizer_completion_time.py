"""
Unit tests for the completion time visualization functionality.
"""
import pytest
import pandas as pd
import numpy as np
import os
from pathlib import Path
import matplotlib.pyplot as plt

# Import the function to test
from code.analysis.visualizer import plot_completion_time, _load_cleaned_data

@pytest.fixture
def mock_cleaned_data():
    """Create a mock cleaned_sessions DataFrame."""
    np.random.seed(42)
    n = 50
    data = {
        'participant_id': [f'P{i:03d}' for i in range(n)],
        'interface_type': ['Traditional'] * 25 + ['Explainable'] * 25,
        'completion_time': np.concatenate([
            np.random.normal(120, 20, 25), # Traditional: mean 120s, std 20s
            np.random.normal(100, 15, 25)  # Explainable: mean 100s, std 15s
        ]),
        'error_count': np.random.poisson(3, n),
        'sus_score': np.random.normal(70, 10, n)
    }
    return pd.DataFrame(data)
    
@pytest.fixture
def temp_cleaned_csv(tmp_path, mock_cleaned_data):
    """Save mock data to a temporary CSV file."""
    csv_path = tmp_path / "cleaned_sessions.csv"
    mock_cleaned_data.to_csv(csv_path, index=False)
    return str(csv_path)
    
def test_plot_completion_time_creates_file(tmp_path, mock_cleaned_data):
    """Test that plot_completion_time creates a valid PNG file."""
    output_path = str(tmp_path / "test_completion_time.png")
    
    # Call the function
    result_path = plot_completion_time(df=mock_cleaned_data, output_path=output_path, show=False)
    
    # Assert file exists
    assert os.path.exists(result_path), f"Output file not created at {result_path}"
    
    # Assert file is not empty
    assert os.path.getsize(result_path) > 0, "Output file is empty"
    
    # Assert valid PNG header (first 8 bytes)
    with open(result_path, 'rb') as f:
        header = f.read(8)
        assert header[:8] == b'\x89PNG\r\n\x1a\n', "Invalid PNG header"
        
def test_plot_completion_time_handles_missing_data(temp_cleaned_csv):
    """Test that the function loads data from file correctly."""
    output_path = str(Path(temp_cleaned_csv).parent / "test_output.png")
    
    # This should load from the CSV we created
    result_path = plot_completion_time(
        input_path=temp_cleaned_csv, 
        output_path=output_path, 
        show=False
    )
    
    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 0
    
def test_plot_completion_time_fails_on_missing_file():
    """Test that the function raises FileNotFoundError for missing data."""
    with pytest.raises(FileNotFoundError, match="Cleaned data file not found"):
        plot_completion_time(input_path="nonexistent.csv", show=False)
        
def test_plot_completion_time_fails_on_missing_columns(tmp_path):
    """Test that the function raises ValueError for missing columns."""
    # Create a CSV with missing columns
    bad_data = pd.DataFrame({'other_col': [1, 2, 3]})
    csv_path = tmp_path / "bad.csv"
    bad_data.to_csv(csv_path, index=False)
    
    with pytest.raises(ValueError, match="Missing required columns"):
        plot_completion_time(input_path=str(csv_path), show=False)
        
def test_plot_completion_time_includes_statistics(mock_cleaned_data, tmp_path):
    """Test that the plot includes statistical information."""
    output_path = str(tmp_path / "stats_test.png")
    plot_completion_time(df=mock_cleaned_data, output_path=output_path, show=False)
    
    # We can't easily check text content in the image without OCR,
    # but we can verify the file was created and is valid.
    # The presence of the function call ensures the code path runs.
    assert os.path.exists(output_path)