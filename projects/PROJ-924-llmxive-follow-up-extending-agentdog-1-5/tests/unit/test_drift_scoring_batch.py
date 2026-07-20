import pytest
import numpy as np
import tracemalloc
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from drift_scoring import batch_process_logs, compute_cosine_distance
from config import update_config

@pytest.fixture
def mock_centroids():
    # Create dummy centroids
    return np.random.rand(10, 384).astype(np.float32)

@pytest.fixture
def mock_model():
    # Mock the SentenceTransformer model
    model = MagicMock()
    model.encode = MagicMock(return_value=np.random.rand(1, 384).astype(np.float32))
    return model

def test_batch_process_logs_empty_logs(mock_centroids, mock_model):
    """Test that empty logs are handled correctly with score 2.0 and review_flag True."""
    logs = [
        {"log_id": "1", "text": ""},
        {"log_id": "2", "text": "   "},
        {"log_id": "3", "text": "Normal log text"}
    ]
    
    results = batch_process_logs(logs, mock_model, mock_centroids)
    
    assert len(results) == 3
    assert results[0]["drift_score"] == 2.0
    assert results[0]["review_flag"] is True
    assert results[1]["drift_score"] == 2.0
    assert results[1]["review_flag"] is True
    assert results[2]["drift_score"] != 2.0 # Should be a calculated distance
    assert results[2]["review_flag"] is False

def test_batch_process_logs_memory_limit(mock_centroids, mock_model):
    """Test that batch processing respects memory limits."""
    logs = [{"log_id": f"{i}", "text": "test log"} for i in range(100)]
    
    # Mock tracemalloc to simulate high memory usage
    with patch('drift_scoring.tracemalloc') as mock_tracemalloc:
        # Set peak memory to exceed the limit (e.g., 8GB when limit is 7GB)
        mock_tracemalloc.get_traced_memory.return_value = (100, 8 * (1024 ** 3))
        
        # Update config to set limit to 7GB
        update_config({"max_memory_gb": 7})
        
        with pytest.raises(MemoryError) as exc_info:
            batch_process_logs(logs, mock_model, mock_centroids)
        
        assert "exceeded limit" in str(exc_info.value)

def test_batch_process_logs_normal_execution(mock_centroids, mock_model):
    """Test normal execution without memory issues."""
    logs = [{"log_id": f"{i}", "text": f"log text {i}"} for i in range(10)]
    
    # Mock tracemalloc to return low memory usage
    with patch('drift_scoring.tracemalloc') as mock_tracemalloc:
        mock_tracemalloc.get_traced_memory.return_value = (100, 1 * (1024 ** 3)) # 1GB
        update_config({"max_memory_gb": 7})
        
        results = batch_process_logs(logs, mock_model, mock_centroids)
        
        assert len(results) == 10
        for r in results:
            assert "drift_score" in r
            assert "review_flag" in r
            assert "log_id" in r
            assert r["review_flag"] is False # Assuming non-empty text
            assert r["drift_score"] != 2.0