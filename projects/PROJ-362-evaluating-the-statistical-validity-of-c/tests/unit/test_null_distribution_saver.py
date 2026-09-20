"""
Unit tests for null_distribution_saver.py
"""

import os
import csv
import tempfile
import shutil
from pathlib import Path

import pytest

# We need to mock the config module or set up the environment so imports work.
# Since the task is to implement T017, we assume the module exists.
# We will create a temporary directory to simulate RESULTS_DIR behavior if needed,
# but here we test the function logic directly.

# Import the module under test
# Note: In a real CI, the project root would be in sys.path.
# We assume the runner sets this up.
from null_distribution_saver import save_null_distribution_csv, save_all_null_distributions

@pytest.fixture
def temp_output_dir():
    """Creates a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_save_null_distribution_csv_single_metric(temp_output_dir):
    """Test saving a single null distribution CSV."""
    query_id = "123"
    metric = "ndcg_at_10"
    scores = [0.5, 0.6, 0.55, 0.7]

    file_path = save_null_distribution_csv(query_id, metric, scores, Path(temp_output_dir))

    assert file_path.exists()
    assert file_path.name == f"{query_id}_{metric}.csv"

    with open(file_path, 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ['query_id', 'metric', 'score']

        rows = list(reader)
        assert len(rows) == len(scores)
        for i, row in enumerate(rows):
            assert row[0] == query_id
            assert row[1] == metric
            assert float(row[2]) == scores[i]

def test_save_all_null_distributions(temp_output_dir):
    """Test saving multiple null distributions at once."""
    data = [
        {'query_id': '1', 'metric': 'ndcg_at_10', 'scores': [0.1, 0.2]},
        {'query_id': '1', 'metric': 'map', 'scores': [0.3, 0.4]},
        {'query_id': '2', 'metric': 'ndcg_at_10', 'scores': [0.5]}
    ]

    paths = save_all_null_distributions(data, Path(temp_output_dir))

    assert len(paths) == 3
    for p in paths:
        assert p.exists()

    # Verify content of one file
    file_path = paths[0]
    with open(file_path, 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ['query_id', 'metric', 'score']
        rows = list(reader)
        assert len(rows) == 2

def test_save_all_null_distributions_empty_scores(temp_output_dir):
    """Test that empty scores are handled (skipped) with a warning."""
    data = [
        {'query_id': '1', 'metric': 'ndcg_at_10', 'scores': []}
    ]

    # This should not raise an exception, but log a warning and return empty list
    paths = save_all_null_distributions(data, Path(temp_output_dir))
    
    # The function skips items with no scores, so no file should be created for this item
    # depending on implementation, it might return a list of created files (empty here)
    assert len(paths) == 0