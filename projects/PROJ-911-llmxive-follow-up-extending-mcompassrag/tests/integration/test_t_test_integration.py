import pytest
import csv
import json
import tempfile
from pathlib import Path
import numpy as np

from code.t_test_metrics import run_pipeline

@pytest.fixture
def realistic_retrieval_data():
    """Generate a more realistic retrieval dataset for integration testing."""
    data = []
    queries = ['q1', 'q2', 'q3', 'q4', 'q5']
    methods = ['graph', 'neural']
    
    for q in queries:
        # Simulate 10 relevant docs per query
        relevant_docs = [f'd{i}' for i in range(1, 11)]
        
        for method in methods:
            # Simulate retrieval ranks
            for rank in range(1, 21):  # Top 20
                doc_id = f'd{rank}'
                # Random relevance (some relevant, some not)
                is_relevant = 1 if doc_id in relevant_docs and rank <= 10 else 0
                score = 1.0 - (rank * 0.05)
                
                data.append({
                    'query_id': q,
                    'method': method,
                    'rank': rank,
                    'doc_id': doc_id,
                    'score': score,
                    'is_relevant': is_relevant
                })
    
    return data

@pytest.fixture
def temp_retrieval_file(realistic_retrieval_data):
    """Create a temporary CSV file with realistic data."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.DictWriter(f, fieldnames=realistic_retrieval_data[0].keys())
        writer.writeheader()
        writer.writerows(realistic_retrieval_data)
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()

def test_end_to_end_pipeline(temp_retrieval_file):
    """Test the full integration of T029 pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / 'metrics.json'
        
        results = run_pipeline(
            retrieval_scores_file=temp_retrieval_file,
            output_file=output_file,
            k=10
        )
        
        # Verify structure
        assert results['task'] == 'T029'
        assert results['k'] == 10
        assert 'recall_at_k' in results
        assert 'graph' in results['recall_at_k']
        assert 'neural' in results['recall_at_k']
        assert 'paired_t_test' in results
        assert 'ratio' in results
        
        # Verify t-test results
        t_stat = results['paired_t_test']['t_statistic']
        p_value = results['paired_t_test']['p_value']
        assert isinstance(t_stat, float)
        assert isinstance(p_value, float)
        assert 0 <= p_value <= 1.0
        
        # Verify ratio
        ratio = results['ratio']['value']
        threshold = results['ratio']['threshold']
        assert isinstance(ratio, float)
        assert ratio >= 0.0
        assert threshold == 0.70
        assert isinstance(results['ratio']['meets_threshold'], bool)
        
        # Verify file output
        assert output_file.exists()
        with open(output_file, 'r') as f:
            saved = json.load(f)
        assert saved == results

def test_pipeline_with_various_k_values(temp_retrieval_file):
    """Test pipeline with different K values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for k in [5, 10, 20]:
            output_file = Path(tmpdir) / f'metrics_k{k}.json'
            
            results = run_pipeline(
                retrieval_scores_file=temp_retrieval_file,
                output_file=output_file,
                k=k
            )
            
            assert results['k'] == k
            assert 'recall_at_k' in results
            assert 'paired_t_test' in results
            assert 'ratio' in results

def test_pipeline_empty_results(temp_retrieval_file):
    """Test pipeline when there are no relevant documents."""
    # Create a file with no relevant documents
    data = []
    for q in ['q1', 'q2']:
        for method in ['graph', 'neural']:
            for rank in range(1, 11):
                data.append({
                    'query_id': q,
                    'method': method,
                    'rank': rank,
                    'doc_id': f'd{rank}',
                    'score': 0.5,
                    'is_relevant': 0
                })
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        temp_path = Path(f.name)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'metrics.json'
            
            results = run_pipeline(
                retrieval_scores_file=temp_path,
                output_file=output_file,
                k=10
            )
            
            # With no relevant docs, recall should be 0
            assert results['recall_at_k']['graph']['mean'] == 0.0
            assert results['recall_at_k']['neural']['mean'] == 0.0
    finally:
        temp_path.unlink()