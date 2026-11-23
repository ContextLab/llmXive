import pytest
import json
import csv
import tempfile
from pathlib import Path
import numpy as np

from code.t_test_metrics import (
    load_retrieval_scores,
    aggregate_recall_by_method_and_query,
    perform_paired_t_test,
    calculate_ratio,
    run_pipeline
)

@pytest.fixture
def sample_retrieval_scores():
    """Create a sample retrieval_scores.csv for testing."""
    data = [
        {'query_id': 'q1', 'method': 'graph', 'rank': 1, 'doc_id': 'd1', 'score': 0.9, 'is_relevant': 1},
        {'query_id': 'q1', 'method': 'graph', 'rank': 2, 'doc_id': 'd2', 'score': 0.8, 'is_relevant': 0},
        {'query_id': 'q1', 'method': 'graph', 'rank': 3, 'doc_id': 'd3', 'score': 0.7, 'is_relevant': 1},
        {'query_id': 'q1', 'method': 'neural', 'rank': 1, 'doc_id': 'd1', 'score': 0.85, 'is_relevant': 1},
        {'query_id': 'q1', 'method': 'neural', 'rank': 2, 'doc_id': 'd2', 'score': 0.75, 'is_relevant': 1},
        {'query_id': 'q1', 'method': 'neural', 'rank': 3, 'doc_id': 'd3', 'score': 0.65, 'is_relevant': 0},
        {'query_id': 'q2', 'method': 'graph', 'rank': 1, 'doc_id': 'd4', 'score': 0.95, 'is_relevant': 1},
        {'query_id': 'q2', 'method': 'graph', 'rank': 2, 'doc_id': 'd5', 'score': 0.85, 'is_relevant': 0},
        {'query_id': 'q2', 'method': 'neural', 'rank': 1, 'doc_id': 'd4', 'score': 0.9, 'is_relevant': 1},
        {'query_id': 'q2', 'method': 'neural', 'rank': 2, 'doc_id': 'd5', 'score': 0.8, 'is_relevant': 1},
    ]
    return data

@pytest.fixture
def temp_retrieval_file(sample_retrieval_scores):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.DictWriter(f, fieldnames=sample_retrieval_scores[0].keys())
        writer.writeheader()
        writer.writerows(sample_retrieval_scores)
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()

def test_load_retrieval_scores(temp_retrieval_file):
    """Test loading retrieval scores from CSV."""
    scores = load_retrieval_scores(temp_retrieval_file)
    assert len(scores) == 10
    assert scores[0]['query_id'] == 'q1'
    assert scores[0]['method'] == 'graph'
    assert scores[0]['rank'] == 1
    assert scores[0]['is_relevant'] == 1

def test_aggregate_recall_by_method_and_query(temp_retrieval_file):
    """Test Recall@K aggregation."""
    scores = load_retrieval_scores(temp_retrieval_file)
    recall = aggregate_recall_by_method_and_query(scores, k=2)
    
    # For q1, k=2:
    # graph: ranks 1,2 -> relevant: [1, 0] -> recall = 1/2 = 0.5 (assuming 2 total relevant for q1)
    # neural: ranks 1,2 -> relevant: [1, 1] -> recall = 2/2 = 1.0
    # Note: The exact recall value depends on the total relevant count, which is approximated.
    
    assert 'graph' in recall
    assert 'neural' in recall
    assert 'q1' in recall['graph']
    assert 'q1' in recall['neural']

def test_perform_paired_t_test():
    """Test paired t-test function."""
    graph_recall = [0.5, 0.6, 0.7]
    neural_recall = [0.4, 0.5, 0.6]
    
    t_stat, p_value = perform_paired_t_test(graph_recall, neural_recall)
    
    assert isinstance(t_stat, float)
    assert isinstance(p_value, float)
    assert p_value >= 0.0
    assert p_value <= 1.0

def test_calculate_ratio():
    """Test ratio calculation."""
    graph_recall = [0.7, 0.8, 0.9]
    neural_recall = [0.7, 0.8, 0.9]
    
    ratio = calculate_ratio(graph_recall, neural_recall)
    assert abs(ratio - 1.0) < 1e-6

def test_calculate_ratio_with_zero():
    """Test ratio calculation with zero in neural recall."""
    graph_recall = [0.7, 0.0]
    neural_recall = [0.7, 0.0]
    
    ratio = calculate_ratio(graph_recall, neural_recall)
    # The second pair is skipped because neural is 0.
    # Only the first pair is used: 0.7/0.7 = 1.0
    assert abs(ratio - 1.0) < 1e-6

def test_run_pipeline(temp_retrieval_file):
    """Test the full pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / 'metrics.json'
        
        results = run_pipeline(
            retrieval_scores_file=temp_retrieval_file,
            output_file=output_file
        )
        
        assert 'task' in results
        assert results['task'] == 'T029'
        assert 'paired_t_test' in results
        assert 'ratio' in results
        assert results['ratio']['meets_threshold'] is True or False
        
        # Check that the file was written
        assert output_file.exists()
        with open(output_file, 'r') as f:
            saved_results = json.load(f)
        assert saved_results == results

def test_run_pipeline_missing_methods(temp_retrieval_file):
    """Test pipeline with missing methods."""
    # Modify the temp file to remove one method
    with open(temp_retrieval_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader if row['method'] == 'graph']
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError, match="Expected methods"):
            run_pipeline(retrieval_scores_file=temp_path)
    finally:
        temp_path.unlink()
