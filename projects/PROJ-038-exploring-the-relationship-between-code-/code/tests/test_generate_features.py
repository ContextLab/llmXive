"""
Tests for the generate_features module.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generate_features import load_csv_safely, merge_metrics

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def setup_test_files(temp_dir):
    """Create dummy CSV files for testing."""
    # CC Data
    cc_df = pd.DataFrame({
        'file_path': ['a.java', 'b.java', 'c.java'],
        'cc': [5, 12, 3]
    })
    cc_path = temp_dir / "cc.csv"
    cc_df.to_csv(cc_path, index=False)

    # Halstead Data
    hal_df = pd.DataFrame({
        'file_path': ['a.java', 'b.java', 'c.java'],
        'halstead': [10.5, 20.1, 5.0]
    })
    hal_path = temp_dir / "hal.csv"
    hal_df.to_csv(hal_path, index=False)

    # LOC Data
    loc_df = pd.DataFrame({
        'file_path': ['a.java', 'b.java', 'c.java'],
        'loc': [100, 250, 50]
    })
    loc_path = temp_dir / "loc.csv"
    loc_df.to_csv(loc_path, index=False)

    # Labels Data
    lbl_df = pd.DataFrame({
        'file_path': ['a.java', 'b.java', 'c.java'],
        'is_buggy': [1, 0, 0]
    })
    lbl_path = temp_dir / "lbl.csv"
    lbl_df.to_csv(lbl_path, index=False)

    return {
        'cc': cc_path,
        'hal': hal_path,
        'loc': loc_path,
        'lbl': lbl_path,
        'temp_dir': temp_dir
    }

def test_load_csv_safely_success(setup_test_files):
    df = load_csv_safely(setup_test_files['cc'], required_columns=['file_path', 'cc'])
    assert len(df) == 3
    assert 'cc' in df.columns

def test_load_csv_safely_missing_file(temp_dir):
    missing_path = temp_dir / "nonexistent.csv"
    with pytest.raises(FileNotFoundError):
        load_csv_safely(missing_path)

def test_load_csv_safely_missing_columns(setup_test_files):
    with pytest.raises(ValueError):
        load_csv_safely(setup_test_files['cc'], required_columns=['file_path', 'missing_col'])

def test_merge_metrics(setup_test_files):
    """Test the merge logic produces the correct output."""
    output_path = setup_test_files['temp_dir'] / "merged.csv"
    
    cc_df = pd.read_csv(setup_test_files['cc'])
    hal_df = pd.read_csv(setup_test_files['hal'])
    loc_df = pd.read_csv(setup_test_files['loc'])
    lbl_df = pd.read_csv(setup_test_files['lbl'])

    result = merge_metrics(cc_df, hal_df, loc_df, lbl_df, output_path)

    # Verify columns
    expected_cols = ['file_path', 'cc', 'halstead', 'loc', 'is_buggy']
    assert list(result.columns) == expected_cols

    # Verify row count (inner join on all 3 files)
    assert len(result) == 3

    # Verify specific values
    assert result.iloc[0]['cc'] == 5
    assert result.iloc[0]['halstead'] == 10.5
    assert result.iloc[0]['is_buggy'] == 1

    # Verify file was written
    assert output_path.exists()

def test_merge_metrics_inner_join(setup_test_files):
    """Test that rows missing in one file are dropped (inner join)."""
    # Modify one df to have a different file
    cc_df = pd.read_csv(setup_test_files['cc'])
    hal_df = pd.read_csv(setup_test_files['hal'])
    loc_df = pd.read_csv(setup_test_files['loc'])
    lbl_df = pd.read_csv(setup_test_files['lbl'])

    # Remove 'c.java' from Halstead
    hal_df = hal_df[hal_df['file_path'] != 'c.java']
    
    output_path = setup_test_files['temp_dir'] / "merged_inner.csv"
    result = merge_metrics(cc_df, hal_df, loc_df, lbl_df, output_path)

    # 'c.java' should be dropped
    assert len(result) == 2
    assert 'c.java' not in result['file_path'].values