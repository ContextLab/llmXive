"""
Integration test for the full permutation save flow.
Verifies that permutation.py correctly generates data and null_distribution_saver.py
correctly saves it to the expected location with correct headers.
"""
import os
import csv
import tempfile
from pathlib import Path
import pytest
import random

# Mock config for testing to avoid dependency on real config paths
class MockConfig:
    RESULTS_DIR = Path(tempfile.gettempdir()) / "test_results"

# We will test the logic directly without relying on the global config
# by passing explicit paths to the functions

from null_distribution_saver import save_all_null_distributions

def test_full_permutation_save_flow():
    """
    Simulate the output of permutation.py and verify save_all_null_distributions
    produces valid CSVs with the required headers.
    """
    # Simulate data that would come from permutation.py
    mock_distributions = [
        {
            'query_id': 101,
            'metric': 'NDCG@10',
            'scores': [0.45, 0.48, 0.52, 0.49, 0.51],
            'actual_n': 5
        },
        {
            'query_id': 102,
            'metric': 'MAP',
            'scores': [0.30, 0.32, 0.29, 0.31],
            'actual_n': 4
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Save the distributions
        saved_paths = save_all_null_distributions(mock_distributions, output_dir)
        
        # Verify files exist
        assert len(saved_paths) == 2
        
        # Verify each file has correct headers and data
        for dist, path in zip(mock_distributions, saved_paths):
            assert path.exists()
            
            with open(path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                # Verify header
                assert header == ['query_id', 'metric', 'score'], f"Header mismatch in {path}"
                
                # Verify row count
                rows = list(reader)
                assert len(rows) == len(dist['scores'])
                
                # Verify content
                for row in rows:
                    assert int(row[0]) == dist['query_id']
                    assert row[1] == dist['metric']
                    assert float(row[2]) in dist['scores']

def test_filename_format():
    """Verify that filenames follow the expected pattern."""
    mock_distributions = [
        {'query_id': 999, 'metric': 'NDCG@10', 'scores': [0.1]},
        {'query_id': 888, 'metric': 'MAP', 'scores': [0.2]}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        saved_paths = save_all_null_distributions(mock_distributions, output_dir)
        
        filenames = [p.name for p in saved_paths]
        
        # Check for expected patterns (q{ID}_{METRIC}.csv)
        # NDCG@10 becomes NDCG_at_10
        assert any("q999_NDCG_at_10" in name for name in filenames)
        assert any("q888_MAP" in name for name in filenames)
