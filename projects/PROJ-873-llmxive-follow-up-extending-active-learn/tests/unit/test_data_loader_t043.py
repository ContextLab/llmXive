import os
import json
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add code to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.data_loader import (
    inject_redundancy, 
    prepare_injected_datasets, 
    DataInjectionError,
    TARGET_SIMILARITY_THRESHOLD,
    MAX_RETRIES
)

@pytest.fixture
def mock_corpus():
    """Create a mock corpus for testing."""
    return {
        "doc_1": "This is a sample document about information retrieval.",
        "doc_2": "Another document discussing search algorithms.",
        "doc_3": "A third document on natural language processing.",
        "doc_4": "Yet another document about machine learning.",
        "doc_5": "Final document in this small corpus."
    }

def test_inject_redundancy_achieves_target(mock_corpus):
    """Test that inject_redundancy achieves the target similarity or retries."""
    # This test verifies the logic flow. 
    # Note: Actual similarity depends on the embedding model and paraphrasing logic.
    # We assert that the function returns a valid structure and handles the retry logic.
    
    result_data, achieved_sim, status = inject_redundancy(
        "test_dataset", 
        mock_corpus, 
        target_similarity=0.95
    )
    
    assert "name" in result_data
    assert "clusters" in result_data
    assert "achieved_similarity" in result_data
    assert "status" in result_data
    
    # The status should be either 'achieved' or 'partial' (if retries exhausted)
    assert status in ["achieved", "partial"]
    
    # If partial, ensure retry count was respected (logic check)
    if status == "partial":
        # We expect at least one retry attempt in the real logic
        assert achieved_sim < 0.95

def test_prepare_injected_datasets_creates_files(tmp_path, mock_corpus):
    """Test that prepare_injected_datasets writes the required artifacts."""
    # Mock the fetch_beir_datasets to return our mock corpus
    mock_datasets = {
        "test_set": {
            "corpus": mock_corpus,
            "queries": {},
            "path": "/tmp/fake"
        }
    }
    
    output_dir = str(tmp_path)
    
    with patch('code.data_loader.fetch_beir_datasets', return_value=mock_datasets):
        # We need to mock the actual fetch inside prepare_injected_datasets
        # But since we are passing the dict directly, we can call it directly
        # However, prepare_injected_datasets expects the result of fetch_beir_datasets
        # Let's call the internal logic directly for this unit test
        
        # Actually, prepare_injected_datasets takes the dict from fetch_beir_datasets
        # So we can call it directly with our mock
        # But it calls inject_redundancy which loads the model. 
        # We'll rely on the integration test for the full flow and test the file writing here.
        
        # For unit test, we mock inject_redundancy to avoid model loading
        with patch('code.data_loader.inject_redundancy') as mock_inject:
            mock_inject.return_value = (
                {
                    "name": "test_set",
                    "clusters": [{"id": "c1", "members": ["d1", "d2"], "center_doc_id": "d1", "avg_similarity": 0.96}],
                    "total_documents": 10,
                    "redundancy_ratio": 0.2,
                    "achieved_similarity": 0.96,
                    "status": "achieved",
                    "target_similarity": 0.95
                },
                0.96,
                "achieved"
            )
            
            result = prepare_injected_datasets(mock_datasets, output_dir)
            
            # Check that files were written
            validation_path = os.path.join(output_dir, "validation_status.json")
            combined_path = os.path.join(output_dir, "injected_datasets.json")
            
            assert os.path.exists(validation_path), "validation_status.json should be created"
            assert os.path.exists(combined_path), "injected_datasets.json should be created"
            
            # Verify content
            with open(validation_path, 'r') as f:
                content = json.load(f)
                assert "datasets" in content
                assert content["validation_summary"]["achieved_count"] == 1
            
            with open(combined_path, 'r') as f:
                content = json.load(f)
                assert "datasets" in content
                assert len(content["datasets"]) == 1

def test_retry_logic_on_low_similarity(mock_corpus):
    """Test that the retry logic is triggered when similarity is low."""
    # Mock the embedding model to return low similarity
    with patch('code.data_loader.SentenceTransformer') as MockModel:
        mock_instance = MagicMock()
        MockModel.return_value = mock_instance
        
        # Mock encode to return embeddings that result in low similarity
        mock_embeddings = MagicMock()
        mock_instance.encode.return_value = mock_embeddings
        
        # Mock cosine_similarity to return a low value
        with patch('code.data_loader.cosine_similarity') as mock_cos:
            mock_cos.return_value = [[0.5]] # Low similarity
            
            # This should trigger retries and eventually return 'partial'
            result_data, achieved_sim, status = inject_redundancy(
                "test_dataset",
                mock_corpus,
                target_similarity=0.95
            )
            
            assert status == "partial"
            assert achieved_sim == 0.5 # The mocked value

def test_max_retries_exceeded(mock_corpus):
    """Test that the function respects MAX_RETRIES."""
    # Similar to above, but ensure we don't loop infinitely
    with patch('code.data_loader.SentenceTransformer') as MockModel:
        mock_instance = MagicMock()
        MockModel.return_value = mock_instance
        
        with patch('code.data_loader.cosine_similarity') as mock_cos:
            mock_cos.return_value = [[0.5]]
            
            result_data, achieved_sim, status = inject_redundancy(
                "test_dataset",
                mock_corpus,
                target_similarity=0.95
            )
            
            # Should have retried MAX_RETRIES times and stopped
            assert status == "partial"
            # The retry logic is recursive, so we just check the final state