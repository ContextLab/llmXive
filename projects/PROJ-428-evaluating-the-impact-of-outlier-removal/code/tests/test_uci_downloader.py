import os
import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.uci_downloader import identify_continuous_columns, clean_and_process_dataset

class TestIdentifyContinuousColumns:
    def test_identify_mixed_types(self):
        """Test that only numeric columns are identified."""
        data = {
            'A': [1, 2, 3],
            'B': [1.0, 2.0, 3.0],
            'C': ['x', 'y', 'z'],
            'D': ['1', '2', '3']
        }
        df = pd.DataFrame(data)
        cols = identify_continuous_columns(df)
        assert 'A' in cols
        assert 'B' in cols
        assert 'C' not in cols
        assert 'D' not in cols

    def test_identify_all_numeric(self):
        data = {
            'X': [1, 2, 3],
            'Y': [4.0, 5.0, 6.0]
        }
        df = pd.DataFrame(data)
        cols = identify_continuous_columns(df)
        assert len(cols) == 2
        assert set(cols) == {'X', 'Y'}

class TestCleanAndProcessDataset:
    def test_clean_and_process_with_missing(self):
        """Test cleaning logic with '?' missing values."""
        data = {
            'val1': [1, 2, '?', 4, 5],
            'val2': [10.0, '?', 30.0, 40.0, 50.0],
            'cat': ['a', 'b', 'c', 'd', 'e']
        }
        df = pd.DataFrame(data)
        
        raw_path = Path("fake/path.csv")
        
        clean_df, metadata = clean_and_process_dataset(df, "TestSet", raw_path)
        
        assert 'cat' not in clean_df.columns
        assert len(clean_df) == 3
        
        assert 'baseline_variances' in metadata
        assert 'val1' in metadata['baseline_variances']
        assert 'val2' in metadata['baseline_variances']

    def test_clean_and_process_no_continuous(self):
        """Test behavior when no continuous columns are found."""
        data = {
            'cat1': ['a', 'b', 'c'],
            'cat2': ['x', 'y', 'z']
        }
        df = pd.DataFrame(data)
        raw_path = Path("fake/path.csv")
        
        clean_df, metadata = clean_and_process_dataset(df, "TestSet", raw_path)
        
        assert clean_df.empty
        assert metadata == {}
