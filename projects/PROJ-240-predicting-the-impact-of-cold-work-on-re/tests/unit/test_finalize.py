import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.finalize_dataset import (
    load_engineered_data,
    enforce_row_cap,
    save_final_dataset,
    MAX_ROWS
)

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    data = {
        'cold_work': np.random.rand(100) * 100,
        'Mn_content': np.random.rand(100),
        'Mg_content': np.random.rand(100),
        'Si_content': np.random.rand(100),
        'Cu_content': np.random.rand(100),
        'temperature': np.random.rand(100) * 500 + 200,
        'time_to_peak': np.random.rand(100) * 1000,
        'cold_work_Mn': np.random.rand(100),
        'cold_work_Mg': np.random.rand(100),
        'cold_work_Si': np.random.rand(100),
        'cold_work_Cu': np.random.rand(100),
    }
    return pd.DataFrame(data)

@pytest.fixture
def large_sample_df():
    """Create a large DataFrame exceeding the cap."""
    data = {
        'cold_work': np.random.rand(20000) * 100,
        'Mn_content': np.random.rand(20000),
        'Mg_content': np.random.rand(20000),
        'Si_content': np.random.rand(20000),
        'Cu_content': np.random.rand(20000),
        'temperature': np.random.rand(20000) * 500 + 200,
        'time_to_peak': np.random.rand(20000) * 1000,
        'cold_work_Mn': np.random.rand(20000),
        'cold_work_Mg': np.random.rand(20000),
        'cold_work_Si': np.random.rand(20000),
        'cold_work_Cu': np.random.rand(20000),
    }
    return pd.DataFrame(data)

def test_enforce_row_cap_under_limit(sample_df):
    """Test that data under the limit is returned unchanged."""
    result = enforce_row_cap(sample_df, MAX_ROWS)
    assert len(result) == len(sample_df)
    assert result.equals(sample_df)

def test_enforce_row_cap_over_limit(large_sample_df):
    """Test that data over the limit is truncated correctly."""
    result = enforce_row_cap(large_sample_df, MAX_ROWS)
    assert len(result) == MAX_ROWS
    # Verify it's the first N rows
    assert result.iloc[0].equals(large_sample_df.iloc[0])
    assert result.iloc[-1].equals(large_sample_df.iloc[MAX_ROWS - 1])

def test_save_final_dataset_creates_file(tmp_path, sample_df):
    """Test that save_final_dataset creates the file and writes data."""
    output_path = tmp_path / "test_output.csv"
    result_path = save_final_dataset(sample_df, output_path)
    
    assert result_path.exists()
    assert result_path == output_path
    
    # Verify content
    loaded_df = pd.read_csv(result_path)
    assert len(loaded_df) == len(sample_df)
    assert list(loaded_df.columns) == list(sample_df.columns)

def test_load_engineered_data_missing_file():
    """Test that loading a missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_engineered_data(Path("/nonexistent/path/file.csv"))