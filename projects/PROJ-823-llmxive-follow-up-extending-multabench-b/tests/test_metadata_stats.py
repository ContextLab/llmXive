import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.metadata_stats import (
    load_dataset_list,
    load_raw_tabular_data,
    compute_variance_for_dataset,
    compute_feature_stats,
    process_single_dataset,
    save_summary_csv,
    main
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    raw_dir = Path(temp_dir) / "raw"
    raw_dir.mkdir()
    
    # Create a mock dataset_list.json
    dataset_list = {
        "datasets": ["test_ds_1", "test_ds_2"]
    }
    with open(raw_dir / "dataset_list.json", 'w') as f:
        json.dump(dataset_list, f)
    
    # Create mock CSV files
    df1 = pd.DataFrame({
        "num_col1": [1.0, 2.0, 3.0, 4.0, 5.0],
        "num_col2": [10.0, 20.0, 30.0, 40.0, 50.0],
        "cat_col": ["A", "B", "A", "C", "B"]
    })
    df1.to_csv(raw_dir / "test_ds_1.csv", index=False)
    
    df2 = pd.DataFrame({
        "num_col1": [5.0, 5.0, 5.0, 5.0, 5.0], # Zero variance
        "num_col2": [1.0, 2.0, 3.0, 4.0, 5.0],
        "num_col3": [2.0, 4.0, 6.0, 8.0, 10.0]
    })
    df2.to_csv(raw_dir / "test_ds_2.csv", index=False)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_compute_variance_for_dataset():
    """Test variance computation for a simple dataset."""
    df = pd.DataFrame({
        "a": [1, 2, 3, 4, 5],
        "b": [10, 20, 30, 40, 50],
        "c": ["x", "y", "z", "x", "y"]
    })
    
    variance = compute_variance_for_dataset(df)
    
    assert "a" in variance
    assert "b" in variance
    assert "c" in variance
    
    # Variance of [1,2,3,4,5] is 2.5
    assert abs(variance["a"] - 2.5) < 1e-5
    # Variance of [10,20,30,40,50] is 250.0
    assert abs(variance["b"] - 250.0) < 1e-5
    # Non-numeric should be 0.0
    assert variance["c"] == 0.0

def test_compute_variance_zero_variance():
    """Test variance computation when all values are the same."""
    df = pd.DataFrame({
        "a": [5, 5, 5, 5],
        "b": [1, 2, 3, 4]
    })
    
    variance = compute_variance_for_dataset(df)
    
    assert variance["a"] == 0.0
    assert variance["b"] > 0.0

def test_process_single_dataset(temp_data_dir):
    """Test processing a single dataset from disk."""
    # Temporarily override the RAW_DATA_DIR constant
    import analysis.metadata_stats as ms
    original_raw_dir = ms.RAW_DATA_DIR
    ms.RAW_DATA_DIR = Path(temp_data_dir) / "raw"
    
    try:
        result = process_single_dataset("test_ds_1")
        assert result is not None
        assert result["dataset_id"] == "test_ds_1"
        assert "mean_variance" in result
        assert result["mean_variance"] > 0
    finally:
        ms.RAW_DATA_DIR = original_raw_dir

def test_save_summary_csv(temp_data_dir):
    """Test saving summary CSV."""
    results = [
        {"dataset_id": "ds1", "mean_variance": 2.5},
        {"dataset_id": "ds2", "mean_variance": 10.0}
    ]
    
    output_path = Path(temp_data_dir) / "output_variance.csv"
    save_summary_csv(results, output_path, "variance")
    
    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert "dataset_id" in df.columns
    assert "variance" in df.columns
    assert len(df) == 2
    assert df.iloc[0]["dataset_id"] == "ds1"
    assert abs(df.iloc[0]["variance"] - 2.5) < 1e-5