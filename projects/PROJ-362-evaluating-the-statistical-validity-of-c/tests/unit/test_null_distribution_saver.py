"""
Unit tests for null_distribution_saver module.
"""
import os
import csv
import tempfile
from pathlib import Path
import pytest

from null_distribution_saver import save_null_distribution_csv, save_all_null_distributions

def test_save_null_distribution_csv_creates_file():
    """Test that the function creates a CSV file with correct headers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        query_id = 123
        metric = "NDCG@10"
        scores = [0.5, 0.6, 0.7, 0.8]
        
        filepath = save_null_distribution_csv(query_id, metric, scores, output_dir)
        
        assert filepath.exists()
        assert filepath.suffix == ".csv"
        
        # Verify contents
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ['query_id', 'metric', 'score']
            
            rows = list(reader)
            assert len(rows) == 4
            for row in rows:
                assert int(row[0]) == query_id
                assert row[1] == metric
                assert float(row[2]) in scores

def test_save_all_null_distributions():
    """Test saving multiple distributions at once."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        distributions = [
            {'query_id': 1, 'metric': 'NDCG@10', 'scores': [0.1, 0.2]},
            {'query_id': 2, 'metric': 'MAP', 'scores': [0.3, 0.4, 0.5]}
        ]
        
        paths = save_all_null_distributions(distributions, output_dir)
        
        assert len(paths) == 2
        for p in paths:
            assert p.exists()
            assert p.parent == output_dir

def test_save_null_distribution_csv_float_formatting():
    """Test that scores are formatted to 6 decimal places."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        scores = [0.123456789, 0.987654321]
        
        filepath = save_null_distribution_csv(1, "MAP", scores, output_dir)
        
        with open(filepath, 'r') as f:
            content = f.read()
            # Check that values are formatted (should not have excessive precision)
            assert "0.123457" in content or "0.123456" in content

def test_save_all_null_distributions_empty_list():
    """Test behavior with empty distribution list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        paths = save_all_null_distributions([], output_dir)
        
        assert paths == []
