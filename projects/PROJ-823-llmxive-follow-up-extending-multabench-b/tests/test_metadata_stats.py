"""
Unit tests for metadata_stats.py
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# Add code/ to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.metadata_stats import (
    load_dataset_list,
    load_raw_tabular_data,
    compute_cardinality,
    compute_missingness,
    compute_sparsity,
    compute_variance,
    compute_feature_stats,
    process_single_dataset,
    compute_all_stats,
    RAW_DATA_DIR,
    PROCESSED_DIR
)

@pytest.fixture
def temp_data_dir():
    """Creates a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    raw_dir = Path(temp_dir) / "data" / "raw"
    raw_dir.mkdir(parents=True)
    
    # Create a mock CSV
    df = pd.DataFrame({
        'feature_a': [1.0, 2.0, 3.0, np.nan],
        'feature_b': [0.0, 0.0, 0.0, 0.0],
        'feature_c': ['x', 'y', 'z', 'x']
    })
    mock_csv = raw_dir / "test_dataset.csv"
    df.to_csv(mock_csv, index=False)
    
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_compute_cardinality():
    df = pd.DataFrame({'col': [1, 2, 2, 3, np.nan]})
    # nunique excludes NaN by default
    assert compute_cardinality(df, 'col') == 3

def test_compute_missingness():
    df = pd.DataFrame({'col': [1, np.nan, 3, np.nan]})
    assert compute_missingness(df, 'col') == 0.5

def test_compute_sparsity_numeric():
    df = pd.DataFrame({'col': [0.0, 1.0, 0.0, 0.0]})
    assert compute_sparsity(df, 'col') == 0.75

def test_compute_sparsity_non_numeric():
    df = pd.DataFrame({'col': ['a', 'b', 'c']})
    assert compute_sparsity(df, 'col') == 0.0

def test_compute_variance():
    df = pd.DataFrame({'col': [1.0, 2.0, 3.0]})
    # Sample variance by default (ddof=1)
    assert compute_variance(df, 'col') == pytest.approx(1.0)

def test_compute_feature_stats():
    df = pd.DataFrame({
        'num': [1.0, 2.0, 0.0],
        'cat': ['a', 'b', 'c'],
        'nan_col': [1.0, np.nan, 2.0]
    })
    stats = compute_feature_stats(df)
    assert 'num' in stats
    assert 'nan_col' in stats
    assert 'cat' not in stats
    assert stats['num']['variance'] > 0

def test_process_single_dataset(temp_data_dir):
    # Patch the RAW_DATA_DIR
    original_dir = RAW_DATA_DIR
    with patch('analysis.metadata_stats.RAW_DATA_DIR', temp_data_dir / "data" / "raw"):
        result = process_single_dataset("test_dataset")
        assert result is not None
        assert result['dataset_id'] == 'test_dataset'
        assert 'cardinality' in result
        assert 'missingness' in result
        assert 'variance' in result

def test_compute_all_stats_creates_file(temp_data_dir):
    output_file = temp_data_dir / "data" / "processed" / "metadata_stats_summary.csv"
    # Patch dirs
    with patch('analysis.metadata_stats.RAW_DATA_DIR', temp_data_dir / "data" / "raw"):
        with patch('analysis.metadata_stats.PROCESSED_DIR', temp_data_dir / "data" / "processed"):
            with patch('analysis.metadata_stats.OUTPUT_FILE', output_file):
                result_path = compute_all_stats()
                assert result_path.exists()
                
                # Verify content
                df = pd.read_csv(result_path)
                assert 'dataset_id' in df.columns
                assert 'test_dataset' in df['dataset_id'].values
                assert len(df) == 1
