"""
Unit tests for src/retrieval/query.py
"""
import os
import sys
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path if running from tests
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.query import (
    generate_query_vector,
    retrieve_nearest_neighbors,
    interpolate_weights,
    check_ood,
    save_latency_metrics,
    OOD_THRESHOLD
)

class TestQueryLatency:
    
    def test_generate_query_vector_shape(self):
        """Test that query vector has expected dimensionality (384 for MiniLM)"""
        # Note: This might take a few seconds to load the model
        vec, latency = generate_query_vector("test query")
        assert vec.shape == (384,), f"Expected shape (384,), got {vec.shape}"
        assert latency > 0, "Latency should be positive"

    def test_retrieve_nearest_neighbors(self):
        """Test retrieval logic"""
        # Create dummy vectors
        np.random.seed(42)
        vectors = np.random.rand(100, 384)
        query = np.random.rand(384)
        
        indices, distances, latency = retrieve_nearest_neighbors(query, vectors, k=5)
        
        assert len(indices) == 5
        assert len(distances) == 5
        assert all(0 <= d <= 2 for d in distances), "Cosine distance should be in [0, 2]"
        assert latency >= 0

    def test_interpolate_weights(self):
        """Test interpolation logic (dummy)"""
        indices = [0, 1, 2]
        distances = [0.1, 0.2, 0.3]
        
        synthesized, latency = interpolate_weights(indices, distances, method="cosine_weighted")
        assert latency >= 0
        # Synthesized is a placeholder in this module, shape check is minimal
        assert len(synthesized) == len(indices)

    def test_check_ood_pass(self):
        """Test OOD check passes for valid distance"""
        distances = [0.1, 0.2]
        # Should not raise
        check_ood(distances)

    def test_check_ood_fail(self):
        """Test OOD check raises for invalid distance"""
        distances = [0.6, 0.7] # Assuming threshold is 0.5
        with pytest.raises(ValueError, match="OOD"):
            check_ood(distances)

    def test_save_latency_metrics(self):
        """Test saving metrics to JSON"""
        metrics = {
            "embedding_latency_ms": 10.5,
            "retrieval_latency_ms": 5.2,
            "interpolation_latency_ms": 2.1,
            "total_skill_selection_latency_ms": 17.8
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            save_latency_metrics(metrics, Path(temp_path))
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded == metrics
        finally:
            os.unlink(temp_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])