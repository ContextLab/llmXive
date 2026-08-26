import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from analysis.metadata_stats import (
    compute_sparsity_for_dataset,
    compute_missingness_for_dataset,
    compute_cardinality_for_dataset,
    compute_variance_for_dataset,
    compute_sparsity,
    save_summary_csv
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_compute_sparsity_for_dataset_with_zeros():
    """Test sparsity calculation with a dataframe containing zeros."""
    data = {
        'A': [0, 0, 1, 2, 0],
        'B': [0, 1, 2, 0, 0],
        'C': [1, 2, 3, 4, 5] # No zeros
    }
    df = pd.DataFrame(data)
    
    # Total cells = 5 * 3 = 15
    # Zeros = 2 (A) + 3 (B) + 0 (C) = 5
    # Sparsity = 5/15 = 0.333...
    sparsity = compute_sparsity_for_dataset(df)
    assert abs(sparsity - (5/15)) < 1e-6

def test_compute_sparsity_for_dataset_no_numerical():
    """Test sparsity calculation with a dataframe containing only non-numerical columns."""
    data = {
        'A': ['a', 'b', 'c'],
        'B': ['x', 'y', 'z']
    }
    df = pd.DataFrame(data)
    
    sparsity = compute_sparsity_for_dataset(df)
    assert sparsity == 0.0

def test_compute_sparsity_for_dataset_empty():
    """Test sparsity calculation with an empty dataframe."""
    df = pd.DataFrame()
    sparsity = compute_sparsity_for_dataset(df)
    assert sparsity == 0.0

def test_compute_missingness_for_dataset():
    """Test missingness calculation."""
    data = {
        'A': [1, np.nan, 3],
        'B': [np.nan, np.nan, 6]
    }
    df = pd.DataFrame(data)
    # Total = 6, Missing = 3, Rate = 0.5
    missingness = compute_missingness_for_dataset(df)
    assert missingness == 0.5

def test_compute_cardinality_for_dataset():
    """Test cardinality calculation."""
    data = {
        'A': ['x', 'x', 'y'], # 2 unique
        'B': ['p', 'q', 'r']  # 3 unique
    }
    df = pd.DataFrame(data)
    # Mean cardinality = (2 + 3) / 2 = 2.5
    cardinality = compute_cardinality_for_dataset(df)
    assert cardinality == 2.5

def test_compute_variance_for_dataset():
    """Test variance calculation."""
    data = {
        'A': [1, 2, 3, 4, 5],
        'B': [10, 20, 30, 40, 50]
    }
    df = pd.DataFrame(data)
    # Variance of A: 2.5, Variance of B: 250.0 (sample variance by default)
    # Mean variance = (2.5 + 250.0) / 2 = 126.25
    variance = compute_variance_for_dataset(df)
    # Allow small float tolerance
    assert abs(variance - 126.25) < 0.01

def test_save_summary_csv(tmp_path):
    """Test saving results to CSV."""
    results = [
        {"dataset_id": "ds1", "sparsity": 0.1},
        {"dataset_id": "ds2", "sparsity": 0.2}
    ]
    output_path = tmp_path / "test_output.csv"
    
    save_summary_csv(results, output_path, "sparsity")
    
    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert list(df.columns) == ["dataset_id", "sparsity"]
    assert len(df) == 2
    assert df.iloc[0]["dataset_id"] == "ds1"
    assert df.iloc[0]["sparsity"] == 0.1
