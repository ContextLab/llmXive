import os
import csv
import tempfile
import shutil
import pytest
from code.null_distribution_saver import save_null_distribution_csv, save_all_null_distributions

@pytest.fixture
def temp_dir():
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

def test_save_single_null_distribution(temp_dir):
    """Test saving a single null distribution CSV."""
    query_id = 1
    metric = "NDCG@10"
    scores = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    path = save_null_distribution_csv(query_id, metric, scores, temp_dir)
    
    assert os.path.exists(path)
    with open(path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ['query_id', 'metric', 'score']
        
        rows = list(reader)
        assert len(rows) == 5
        for i, row in enumerate(rows):
            assert int(row[0]) == query_id
            assert row[1] == metric
            assert float(row[2]) == scores[i]

def test_save_all_null_distributions(temp_dir):
    """Test saving multiple null distributions."""
    results = [
        {'query_id': 1, 'metric': 'NDCG@10', 'null_scores': [0.1, 0.2]},
        {'query_id': 2, 'metric': 'MAP', 'null_scores': [0.3, 0.4, 0.5]}
    ]
    
    paths = save_all_null_distributions(results, temp_dir)
    
    assert len(paths) == 2
    for p in paths:
        assert os.path.exists(p)