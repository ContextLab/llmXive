"""
Unit tests for T008c: fetch_merged_counts
"""
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import sys
import os

# Add code directory to path
project_root = Path(__file__).resolve().parents[2]
code_dir = project_root / "code"
sys.path.insert(0, str(code_dir))

from data.fetch_merged_counts import merge_and_count, save_count, load_data_chunked_or_full

class TestMergeAndCount:
    def test_merge_handles_missing_keys(self):
        """Test that merge fails if required keys are missing."""
        df1 = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        df2 = pd.DataFrame({'a': [1, 2], 'c': [5, 6]})
        
        with pytest.raises(ValueError):
            merge_and_count(df1, df2)

    def test_merge_returns_correct_count(self):
        """Test that merge returns the correct number of rows."""
        df1 = pd.DataFrame({
            'iso_code': ['USA', 'CAN', 'MEX'],
            'year': [2000, 2000, 2000],
            'value1': [1, 2, 3]
        })
        df2 = pd.DataFrame({
            'iso_code': ['USA', 'CAN', 'MEX'],
            'year': [2000, 2000, 2000],
            'value2': [10, 20, 30]
        })
        
        count, merged = merge_and_count(df1, df2)
        assert count == 3
        assert len(merged) == 3
        assert 'value1' in merged.columns
        assert 'value2' in merged.columns

    def test_merge_handles_partial_overlap(self):
        """Test merge when only some keys overlap."""
        df1 = pd.DataFrame({
            'iso_code': ['USA', 'CAN'],
            'year': [2000, 2000],
            'value1': [1, 2]
        })
        df2 = pd.DataFrame({
            'iso_code': ['USA', 'MEX'],
            'year': [2000, 2000],
            'value2': [10, 30]
        })
        
        count, merged = merge_and_count(df1, df2)
        assert count == 1
        assert len(merged) == 1
        assert merged.iloc[0]['iso_code'] == 'USA'

class TestSaveCount:
    def test_save_count_creates_json(self):
        """Test that save_count creates a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "counts.json"
            save_count(42, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert data['total_merged'] == 42

class TestLoadDataChunkedOrFull:
    def test_load_full_file(self):
        """Test loading a small file fully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.csv"
            df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
            df.to_csv(file_path, index=False)
            
            loaded_df = load_data_chunked_or_full(file_path)
            assert len(loaded_df) == 3
            assert list(loaded_df.columns) == ['a', 'b']

    def test_load_missing_file(self):
        """Test that loading a missing file raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "nonexistent.csv"
            with pytest.raises(FileNotFoundError):
                load_data_chunked_or_full(file_path)