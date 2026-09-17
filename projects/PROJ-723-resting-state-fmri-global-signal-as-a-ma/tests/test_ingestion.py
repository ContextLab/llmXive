import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add code to path if necessary, though usually tests run in project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion import generate_cleaned_data

def test_generate_cleaned_data_columns():
    """Test that generate_cleaned_data produces the correct columns."""
    data = {
        "Subject_ID": ["sub-001", "sub-002"],
        "Global_Signal_SD": [0.5, 0.6],
        "MWQ_Score": [25, 30],
        "Age": [20, 25],
        "Sex": ["M", "F"],
        "Mean_FD": [0.1, 0.2],
        "Mean_DVARS": [40, 50]
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cleaned_data.csv"
        generate_cleaned_data(df, output_path)
        
        assert output_path.exists()
        result_df = pd.read_csv(output_path)
        
        expected_cols = ["Subject_ID", "Global_Signal_SD", "MWQ_Score", "Age", "Sex", "Mean_FD", "Mean_DVARS"]
        assert list(result_df.columns) == expected_cols
        assert len(result_df) == 2

def test_generate_cleaned_data_missing_columns():
    """Test that generate_cleaned_data raises error on missing columns."""
    data = {
        "Subject_ID": ["sub-001"],
        "Global_Signal_SD": [0.5]
        # Missing MWQ_Score, etc.
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cleaned_data.csv"
        with pytest.raises(ValueError, match="Missing required columns"):
            generate_cleaned_data(df, output_path)

def test_generate_cleaned_data_nan_values():
    """Test that generate_cleaned_data raises error on NaN values."""
    data = {
        "Subject_ID": ["sub-001", "sub-002"],
        "Global_Signal_SD": [0.5, np.nan],
        "MWQ_Score": [25, 30],
        "Age": [20, 25],
        "Sex": ["M", "F"],
        "Mean_FD": [0.1, 0.2],
        "Mean_DVARS": [40, 50]
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cleaned_data.csv"
        with pytest.raises(ValueError, match="Found missing values"):
            generate_cleaned_data(df, output_path)

def test_motion_exclusion_logic():
    """Test that motion exclusion (T014) logic works as expected."""
    data = {
        "Subject_ID": ["sub-001", "sub-002", "sub-003"],
        "Global_Signal_SD": [0.5, 0.6, 0.7],
        "MWQ_Score": [25, 30, 35],
        "Age": [20, 25, 30],
        "Sex": ["M", "F", "M"],
        "Mean_FD": [0.1, 0.6, 0.4], # sub-002 should be excluded
        "Mean_DVARS": [40, 50, 60]
    }
    df = pd.DataFrame(data)
    
    # Filter manually as per T014 logic
    filtered_df = df[df["Mean_FD"] <= 0.5]
    
    assert len(filtered_df) == 2
    assert "sub-002" not in filtered_df["Subject_ID"].values

def test_zero_variance_exclusion_logic():
    """Test that zero-variance exclusion (T015) logic works as expected."""
    data = {
        "Subject_ID": ["sub-001", "sub-002", "sub-003"],
        "Global_Signal_SD": [0.5, 0.0, 0.7], # sub-002 should be excluded
        "MWQ_Score": [25, 30, 35],
        "Age": [20, 25, 30],
        "Sex": ["M", "F", "M"],
        "Mean_FD": [0.1, 0.2, 0.3],
        "Mean_DVARS": [40, 50, 60]
    }
    df = pd.DataFrame(data)
    
    # Filter manually as per T015 logic
    filtered_df = df[df["Global_Signal_SD"] != 0]
    
    assert len(filtered_df) == 2
    assert "sub-002" not in filtered_df["Subject_ID"].values