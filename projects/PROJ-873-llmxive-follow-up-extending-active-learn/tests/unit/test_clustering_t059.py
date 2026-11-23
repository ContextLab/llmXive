import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import numpy as np

from clustering import run_clustering_pipeline, cluster_documents, ClusteringFailureError
from models import RedundancyCluster

@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        {"id": "doc1", "text": "This is a test document about machine learning."},
        {"id": "doc2", "text": "This is a test document about deep learning."},
        {"id": "doc3", "text": "This is a test document about neural networks."},
        {"id": "doc4", "text": "Completely different topic about cooking recipes."},
        {"id": "doc5", "text": "Another unrelated topic about gardening tips."},
    ]

def test_clustering_with_valid_threshold(sample_documents):
    """Test clustering with a valid threshold that produces acceptable results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.json")
        output_path = os.path.join(tmpdir, "clusters.json")
        
        with open(input_path, 'w') as f:
            json.dump({"documents": sample_documents}, f)
        
        # Mock the embedding model to avoid heavy dependencies in unit tests
        with patch('clustering.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.random.rand(len(sample_documents), 384)
            mock_model.return_value = mock_instance
            
            result = run_clustering_pipeline(
                input_path=input_path,
                output_path=output_path,
                threshold=0.95,
                fallback_thresholds=[0.90, 0.85]
            )
            
            assert result['status'] == 'success'
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                clusters_data = json.load(f)
            
            assert 'clusters' in clusters_data
            assert 'threshold_used' in clusters_data
            assert clusters_data['false_positive_rate'] <= 0.10

def test_clustering_fallback_threshold(sample_documents):
    """Test that clustering relaxes threshold when initial attempt fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.json")
        output_path = os.path.join(tmpdir, "clusters.json")
        
        with open(input_path, 'w') as f:
            json.dump({"documents": sample_documents}, f)
        
        # Mock to simulate high false positive rate initially, then success with relaxed threshold
        call_count = [0]
        
        def mock_cosine_sim(v1, v2):
            call_count[0] += 1
            # First few calls return low similarity (causing false positives), then high
            if call_count[0] <= 5:
                return 0.85  # Low similarity
            else:
                return 0.98  # High similarity
        
        with patch('clustering.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.random.rand(len(sample_documents), 384)
            mock_model.return_value = mock_instance
            
            with patch('clustering.calculate_cosine_similarity_proxy', side_effect=mock_cosine_sim):
                result = run_clustering_pipeline(
                    input_path=input_path,
                    output_path=output_path,
                    threshold=0.95,
                    fallback_thresholds=[0.90]
                )
                
                # Should succeed with relaxed threshold
                assert result['status'] == 'success'
                assert result['threshold_used'] < 0.95

def test_clustering_failure_on_excessive_false_positives(sample_documents):
    """Test that clustering raises error when false positives exceed limit even after relaxation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.json")
        output_path = os.path.join(tmpdir, "clusters.json")
        
        with open(input_path, 'w') as f:
            json.dump({"documents": sample_documents}, f)
        
        # Mock to always return low similarity (causing high false positive rate)
        with patch('clustering.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.random.rand(len(sample_documents), 384)
            mock_model.return_value = mock_instance
            
            with patch('clustering.calculate_cosine_similarity_proxy', return_value=0.80):
                with pytest.raises(ClusteringFailureError) as exc_info:
                    run_clustering_pipeline(
                        input_path=input_path,
                        output_path=output_path,
                        threshold=0.95,
                        fallback_thresholds=[0.90, 0.85]
                    )
                
                assert "false positive rate" in str(exc_info.value).lower()
                assert "exceeds" in str(exc_info.value).lower()

def test_cluster_structure(sample_documents):
    """Test that clusters have the expected structure."""
    with patch('clustering.SentenceTransformer') as mock_model:
        mock_instance = MagicMock()
        mock_instance.encode.return_value = np.random.rand(len(sample_documents), 384)
        mock_model.return_value = mock_instance
        
        clusters = cluster_documents(sample_documents, threshold=0.5)
        
        assert len(clusters) > 0
        for cluster in clusters:
            assert hasattr(cluster, 'cluster_id')
            assert hasattr(cluster, 'member_ids')
            assert hasattr(cluster, 'representative_id')
            assert hasattr(cluster, 'jaccard_similarities')
            assert len(cluster.member_ids) >= 1
            assert cluster.representative_id in cluster.member_ids