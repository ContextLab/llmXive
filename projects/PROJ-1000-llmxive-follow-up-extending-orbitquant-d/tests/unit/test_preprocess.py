"""
Unit tests for code/data/preprocess.py
"""

import os
import sys
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.preprocess import split_data, write_csv


class TestSplitData:
    """Tests for the split_data function."""

    def test_split_ratio(self):
        """Test that split_data respects the test_ratio parameter."""
        data = [{'id': i} for i in range(100)]
        
        train, test = split_data(data, test_ratio=0.2, seed=42)
        
        assert len(train) == 80
        assert len(test) == 20
        assert len(train) + len(test) == 100

    def test_split_ratio_50(self):
        """Test 50/50 split."""
        data = [{'id': i} for i in range(100)]
        
        train, test = split_data(data, test_ratio=0.5, seed=42)
        
        assert len(train) == 50
        assert len(test) == 50

    def test_reproducibility(self):
        """Test that same seed produces same split."""
        data = [{'id': i} for i in range(100)]
        
        train1, test1 = split_data(data, test_ratio=0.2, seed=42)
        train2, test2 = split_data(data, test_ratio=0.2, seed=42)
        
        assert train1 == train2
        assert test1 == test2

    def test_different_seed(self):
        """Test that different seed produces different split."""
        data = [{'id': i} for i in range(100)]
        
        train1, _ = split_data(data, test_ratio=0.2, seed=42)
        train2, _ = split_data(data, test_ratio=0.2, seed=123)
        
        assert train1 != train2

    def test_empty_data(self):
        """Test handling of empty data."""
        data = []
        
        train, test = split_data(data, test_ratio=0.2, seed=42)
        
        assert len(train) == 0
        assert len(test) == 0


class TestWriteCsv:
    """Tests for the write_csv function."""

    def test_write_csv_creates_file(self):
        """Test that write_csv creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            data = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
            
            write_csv(data, output_path)
            
            assert output_path.exists()

    def test_write_csv_content(self):
        """Test that write_csv writes correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            data = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
            
            write_csv(data, output_path)
            
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0] == {'a': '1', 'b': '2'}
            assert rows[1] == {'a': '3', 'b': '4'}

    def test_write_csv_creates_directories(self):
        """Test that write_csv creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "test.csv"
            data = [{'a': 1}]
            
            write_csv(data, output_path)
            
            assert output_path.exists()

    def test_write_csv_empty_data_raises(self):
        """Test that write_csv raises ValueError for empty data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            
            try:
                write_csv([], output_path)
                assert False, "Expected ValueError"
            except ValueError:
                pass  # Expected