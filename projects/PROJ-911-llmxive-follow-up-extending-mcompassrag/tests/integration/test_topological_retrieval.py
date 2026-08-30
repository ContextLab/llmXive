import json
import csv
import os
import pytest
from pathlib import Path
import tempfile
import networkx as nx

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import PROCESSED_DIR, RESULTS_DIR
from code.topology_extractor import (
    extract_features_for_retrieved_docs,
    save_retrieved_features,
    load_graphs,
    load_retrieval_scores,
    calculate_topological_metrics
)

@pytest.fixture
def sample_graphs():
    """Create sample graphs for testing."""
    graphs = {
        "doc_1": {
            "nodes": ["term_a", "term_b", "term_c"],
            "edges": [("term_a", "term_b"), ("term_b", "term_c")]
        },
        "doc_2": {
            "nodes": ["term_x", "term_y"],
            "edges": [("term_x", "term_y")]
        },
        "doc_3": {
            "nodes": ["term_p", "term_q", "term_r", "term_s"],
            "edges": [
                ("term_p", "term_q"),
                ("term_q", "term_r"),
                ("term_r", "term_s"),
                ("term_s", "term_p")
            ]
        }
    }
    return graphs

@pytest.fixture
def sample_retrieval_scores():
    """Create sample retrieval scores for testing."""
    scores = [
        {"query_id": "q_1", "doc_id": "doc_1", "rank": "1", "score": "0.95"},
        {"query_id": "q_1", "doc_id": "doc_2", "rank": "2", "score": "0.85"},
        {"query_id": "q_1", "doc_id": "doc_3", "rank": "3", "score": "0.75"},
        {"query_id": "q_2", "doc_id": "doc_1", "rank": "1", "score": "0.90"},
        {"query_id": "q_2", "doc_id": "doc_3", "rank": "2", "score": "0.80"},
        {"query_id": "q_2", "doc_id": "doc_2", "rank": "3", "score": "0.70"},
    ]
    return scores

def test_extract_features_for_retrieved_docs(sample_graphs, sample_retrieval_scores):
    """Test that features are extracted only for top-k retrieved documents."""
    k = 2
    features = extract_features_for_retrieved_docs(sample_graphs, sample_retrieval_scores, k=k)
    
    # Should have 2 features per query (top 2)
    assert len(features) == 4  # 2 queries * 2 docs each
    
    # Check that we have the right documents
    doc_ids = [f['doc_id'] for f in features]
    assert 'doc_1' in doc_ids
    assert 'doc_2' in doc_ids
    assert 'doc_3' in doc_ids  # doc_3 is in top 2 for q_2 (rank 2)
    
    # Check that ranks are correct
    for f in features:
        assert f['rank'] <= k
        
    # Check that required fields exist
    required_fields = ['query_id', 'doc_id', 'rank', 'retrieval_score', 'num_nodes', 'num_edges']
    for f in features:
        for field in required_fields:
            assert field in f, f"Missing field {field} in feature record"

def test_extract_features_empty_graphs(sample_retrieval_scores):
    """Test handling of empty graphs."""
    empty_graphs = {}
    features = extract_features_for_retrieved_docs(empty_graphs, sample_retrieval_scores, k=2)
    assert len(features) == 0

def test_extract_features_missing_doc(sample_graphs, sample_retrieval_scores):
    """Test handling of missing document in graphs."""
    # Add a score for a doc that doesn't exist in graphs
    scores_with_missing = sample_retrieval_scores + [
        {"query_id": "q_3", "doc_id": "nonexistent_doc", "rank": "1", "score": "0.99"}
    ]
    features = extract_features_for_retrieved_docs(sample_graphs, scores_with_missing, k=2)
    
    # Should not include the nonexistent doc
    doc_ids = [f['doc_id'] for f in features]
    assert 'nonexistent_doc' not in doc_ids

def test_calculate_topological_metrics():
    """Test topological metrics calculation."""
    G = nx.Graph()
    G.add_edges_from([('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'a')])
    
    metrics = calculate_topological_metrics(G)
    
    assert metrics['num_nodes'] == 4
    assert metrics['num_edges'] == 4
    assert metrics['avg_degree'] == 2.0
    assert metrics['max_degree'] == 2.0
    assert metrics['modularity'] >= 0.0  # Should be non-negative
    assert metrics['avg_path_length'] > 0.0

def test_save_retrieved_features(tmp_path):
    """Test saving features to CSV."""
    features = [
        {
            'query_id': 'q_1',
            'doc_id': 'doc_1',
            'rank': 1,
            'retrieval_score': 0.95,
            'num_nodes': 3,
            'num_edges': 2
        },
        {
            'query_id': 'q_1',
            'doc_id': 'doc_2',
            'rank': 2,
            'retrieval_score': 0.85,
            'num_nodes': 2,
            'num_edges': 1
        }
    ]
    
    output_file = tmp_path / "test_retrieved_features.csv"
    save_retrieved_features(features, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 2
    assert rows[0]['query_id'] == 'q_1'
    assert rows[0]['doc_id'] == 'doc_1'
    assert rows[0]['rank'] == '1'

def test_no_topology_used_for_ranking(sample_graphs, sample_retrieval_scores):
    """
    Verify that the extraction process does not modify the ranking scores.
    The retrieval scores should remain exactly as provided.
    """
    features = extract_features_for_retrieved_docs(sample_graphs, sample_retrieval_scores, k=2)
    
    # Check that retrieval_score in features matches the input
    for f in features:
        query_id = f['query_id']
        doc_id = f['doc_id']
        
        # Find the original score
        original_score = None
        for s in sample_retrieval_scores:
            if s['query_id'] == query_id and s['doc_id'] == doc_id:
                original_score = float(s['score'])
                break
        
        assert original_score is not None
        assert abs(f['retrieval_score'] - original_score) < 1e-6

def test_empty_features_file_created():
    """Test that an empty CSV with headers is created when no features."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = Path(tmp_dir) / "empty_retrieved_features.csv"
        save_retrieved_features([], output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            content = f.read()
            # Should have headers
            assert 'query_id' in content
            assert 'doc_id' in content
            assert 'rank' in content
            # Should have no data rows
            lines = content.strip().split('\n')
            assert len(lines) == 1  # Only header row
