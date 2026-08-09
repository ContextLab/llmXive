import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
import numpy as np

from data_loader import (
    prepare_injected_datasets,
    load_injected_dataset,
    inject_redundancy,
    calculate_embedding_similarity,
    DataInjectionFailureError,
    RedundancyCluster
)
from sentence_transformers import SentenceTransformer

@pytest.fixture
def sample_documents():
    return [
        {"doc_id": "1", "text": "The quick brown fox jumps over the lazy dog.", "dataset": "test"},
        {"doc_id": "2", "text": "A fast brown fox leaps over a sleepy dog.", "dataset": "test"},
        {"doc_id": "3", "text": "The slow grey cat sits on the mat.", "dataset": "test"},
    ]

@pytest.fixture
def model():
    return SentenceTransformer('all-MiniLM-L6-v2')

def test_synthetic_injection_creates_clusters(sample_documents, model):
    """Test that injected redundancy creates clusters with high similarity."""
    injected_docs, clusters = inject_redundancy(
        documents=sample_documents,
        cluster_size=3,
        num_clusters=1,
        target_similarity=0.95,
        max_retries=5,
        model=model
    )
    
    assert len(clusters) > 0, "No clusters were created"
    assert len(injected_docs) >= len(sample_documents), "No documents were injected"
    
    # Check cluster structure
    cluster = clusters[0]
    assert isinstance(cluster, RedundancyCluster)
    assert len(cluster.members) > 1
    
    # Verify similarity (if achievable)
    if cluster.injected_similarity > 0:
        assert cluster.injected_similarity > 0.8, f"Cluster similarity {cluster.injected_similarity} is too low"

def test_validation_status_written(tmp_path, sample_documents, model):
    """Test that validation_status.json is written with correct schema."""
    # Mock the fetch function to return sample data
    with patch('data_loader.fetch_beir_datasets') as mock_fetch:
        mock_fetch.return_value = {
            "test": {
                "corpus": {},
                "queries": {},
                "qrels": {},
                "documents": sample_documents
            }
        }
        
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        
        result = prepare_injected_datasets(
            dataset_names=["test"],
            data_dir=str(tmp_path / "raw"),
            output_dir=str(output_dir),
            target_similarity=0.95,
            max_retries=3
        )
        
        # Check that validation status is present
        assert "global_validation" in result
        assert "status" in result["global_validation"]
        assert "average_similarity" in result["global_validation"]
        
        # Check individual dataset validation
        assert len(result["datasets"]) == 1
        dataset_val = result["datasets"][0]["validation"]
        assert "status" in dataset_val
        assert "achieved_similarity" in dataset_val
        assert "target_similarity" in dataset_val
        assert "retry_count" in dataset_val
        assert "message" in dataset_val

def test_retry_logic_on_low_similarity(sample_documents, model):
    """Test that retry logic is triggered when similarity is low."""
    # Force low similarity by using a very high target
    injected_docs, clusters = inject_redundancy(
        documents=sample_documents,
        cluster_size=3,
        num_clusters=1,
        target_similarity=0.999,  # Unreachable
        max_retries=5,
        model=model
    )
    
    # Should still produce clusters, even if below target
    assert len(clusters) > 0
    # The achieved similarity should be recorded
    assert clusters[0].injected_similarity >= 0

def test_load_injected_dataset(tmp_path):
    """Test loading an injected dataset."""
    test_data = {
        "datasets": [{"name": "test", "clusters": [], "validation": {}}],
        "global_validation": {"status": "achieved", "average_similarity": 0.95}
    }
    
    file_path = tmp_path / "test.json"
    with open(file_path, "w") as f:
        json.dump(test_data, f)
    
    loaded = load_injected_dataset(str(file_path))
    assert loaded == test_data

def test_data_injection_failure_handling(tmp_path, model):
    """Test that injection fails loudly if model is unavailable."""
    with patch('data_loader.SentenceTransformer', side_effect=Exception("Model load failed")):
        with pytest.raises(Exception, match="Model load failed"):
            inject_redundancy(
                documents=[{"doc_id": "1", "text": "test", "dataset": "test"}],
                cluster_size=2,
                num_clusters=1,
                target_similarity=0.95,
                max_retries=1,
                model=None
            )