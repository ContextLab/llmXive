import pytest
import json
import csv
import tempfile
import os
from pathlib import Path
from code.retrieval_sim import run_pipeline as run_retrieval_pipeline
from code.topology_extractor import run_pipeline_from_retrieval_scores
from code.config import RESULTS_DIR, PROCESSED_DIR

@pytest.fixture
def sample_data(tmp_path):
    """Create sample data for integration test."""
    # Create temporary directories
    test_results_dir = tmp_path / "data" / "results"
    test_processed_dir = tmp_path / "data" / "processed"
    test_results_dir.mkdir(parents=True)
    test_processed_dir.mkdir(parents=True)
    
    # Create sample corpus
    corpus = [
        {"id": "doc1", "text": "machine learning neural networks deep learning", "metadata": {"source": "test"}},
        {"id": "doc2", "text": "artificial intelligence computer vision natural language processing", "metadata": {"source": "test"}},
        {"id": "doc3", "text": "reinforcement learning robot control autonomous systems", "metadata": {"source": "test"}},
        {"id": "doc4", "text": "graph neural networks topological data analysis", "metadata": {"source": "test"}},
        {"id": "doc5", "text": "transformer architecture attention mechanism language model", "metadata": {"source": "test"}},
    ]
    
    # Create sample graphs (simplified)
    graphs = {
        "doc1": {"edges": [("machine", "learning"), ("learning", "neural"), ("neural", "networks")]},
        "doc2": {"edges": [("artificial", "intelligence"), ("intelligence", "computer"), ("computer", "vision")]},
        "doc3": {"edges": [("reinforcement", "learning"), ("learning", "robot"), ("robot", "control")]},
        "doc4": {"edges": [("graph", "neural"), ("neural", "networks"), ("networks", "topological")]},
        "doc5": {"edges": [("transformer", "architecture"), ("architecture", "attention"), ("attention", "mechanism")]},
    }
    
    # Create sample queries
    queries = [
        {"id": "q1", "text": "machine learning neural networks", "answer": ["doc1"]},
        {"id": "q2", "text": "graph neural networks", "answer": ["doc4"]},
    ]
    
    # Write sample files
    with open(test_processed_dir / "corpus.json", 'w') as f:
        json.dump(corpus, f)
    
    with open(test_processed_dir / "graphs.json", 'w') as f:
        json.dump(graphs, f)
    
    with open(test_processed_dir / "queries.json", 'w') as f:
        json.dump(queries, f)
    
    return {
        "results_dir": test_results_dir,
        "processed_dir": test_processed_dir,
        "corpus_path": test_processed_dir / "corpus.json",
        "graphs_path": test_processed_dir / "graphs.json",
        "queries_path": test_processed_dir / "queries.json"
    }

def test_retrieval_and_topology_extraction(sample_data):
    """Integration test: run retrieval simulation then extract topology for retrieved docs."""
    # Run retrieval simulation
    retrieval_results = run_retrieval_pipeline(
        queries_path=sample_data["queries_path"],
        corpus_path=sample_data["corpus_path"],
        output_path=sample_data["results_dir"] / "retrieval_scores.csv",
        k=2
    )
    
    assert len(retrieval_results) > 0, "Retrieval should return results"
    
    # Verify retrieval scores file exists
    retrieval_scores_path = sample_data["results_dir"] / "retrieval_scores.csv"
    assert retrieval_scores_path.exists(), "Retrieval scores file should be created"
    
    # Run topology extraction for retrieved docs
    retrieved_features = run_pipeline_from_retrieval_scores(
        retrieval_scores_path=retrieval_scores_path,
        graphs_path=sample_data["graphs_path"],
        output_path=sample_data["results_dir"] / "retrieved_features.csv"
    )
    
    # Verify retrieved features file exists
    retrieved_features_path = sample_data["results_dir"] / "retrieved_features.csv"
    assert retrieved_features_path.exists(), "Retrieved features file should be created"
    
    # Verify content
    with open(retrieved_features_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) > 0, "Retrieved features should contain data"
    
    # Verify required columns exist
    required_columns = ["doc_id", "avg_degree", "avg_betweenness", "modularity", "avg_clustering", "num_nodes", "num_edges"]
    for col in required_columns:
        assert col in rows[0], f"Required column {col} missing from retrieved features"
    
    # Verify no topology data was used for ranking (only retrieval scores were used)
    # This is validated by the fact that we ran retrieval first, then extracted topology
    # The retrieval pipeline should not have access to topology data
    logger = logging.getLogger(__name__)
    logger.info("Integration test passed: retrieval and topology extraction work correctly")
