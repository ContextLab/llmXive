import os
import csv
import tempfile
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from null_distribution_saver import save_null_distribution_csv, save_all_null_distributions

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_save_single_distribution(temp_dir):
    query_id = 1
    metric = "NDCG@10"
    scores = [0.5, 0.6, 0.55, 0.7]
    
    file_path = save_null_distribution_csv(query_id, metric, scores, temp_dir)
    
    assert file_path.exists()
    assert file_path.name == f"q{query_id}_{metric}.csv"
    
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert headers == ['query_id', 'metric', 'score']
        
        rows = list(reader)
        assert len(rows) == len(scores)
        for i, row in enumerate(rows):
            assert int(row[0]) == query_id
            assert row[1] == metric
            assert float(row[2]) == scores[i]

def test_save_all_distributions(temp_dir):
    distributions = {
        1: {"NDCG@10": [0.1, 0.2], "MAP": [0.3, 0.4]},
        2: {"NDCG@10": [0.5]}
    }
    
    files = save_all_null_distributions(distributions, temp_dir)
    
    assert len(files) == 3
    
    expected_names = {
        "q1_NDCG@10.csv",
        "q1_MAP.csv",
        "q2_NDCG@10.csv"
    }
    actual_names = {f.name for f in files}
    assert actual_names == expected_names