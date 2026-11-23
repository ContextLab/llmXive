import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from metrics import (
    extract_clip_image_embedding,
    extract_clip_text_embedding,
    compute_cosine_similarity,
    compute_image_text_similarity,
    batch_compute_image_text_similarity,
    compute_lpips_distance,
    compute_lpips_distance_from_paths,
    compute_cesr_score,
    compute_lpips_matrix
)

class TestMetrics:
    """Test suite for metrics module."""

    def test_extract_clip_image_embedding(self):
        """Test CLIP image embedding extraction."""
        # Create a dummy image path
        dummy_path = Path("/tmp/dummy.png")
        
        # Should return a 512-dimensional vector
        embedding = extract_clip_image_embedding(dummy_path)
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (512,)

    def test_extract_clip_text_embedding(self):
        """Test CLIP text embedding extraction."""
        text = "test prompt"
        embedding = extract_clip_text_embedding(text)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (512,)

    def test_compute_cosine_similarity(self):
        """Test cosine similarity computation."""
        emb1 = np.array([1.0, 0.0, 0.0])
        emb2 = np.array([1.0, 0.0, 0.0])
        emb3 = np.array([0.0, 1.0, 0.0])
        
        # Identical vectors should have similarity 1.0
        assert abs(compute_cosine_similarity(emb1, emb2) - 1.0) < 1e-6
        
        # Orthogonal vectors should have similarity 0.0
        assert abs(compute_cosine_similarity(emb1, emb3)) < 1e-6

    def test_compute_image_text_similarity(self):
        """Test image-text similarity computation."""
        dummy_path = Path("/tmp/dummy.png")
        text = "test prompt"
        
        similarity = compute_image_text_similarity(dummy_path, text)
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0

    def test_batch_compute_image_text_similarity(self):
        """Test batch image-text similarity computation."""
        dummy_paths = [Path("/tmp/dummy1.png"), Path("/tmp/dummy2.png")]
        texts = ["prompt1", "prompt2"]
        
        similarities = batch_compute_image_text_similarity(dummy_paths, texts)
        assert len(similarities) == 2
        assert all(isinstance(s, float) for s in similarities)

    def test_compute_lpips_distance(self):
        """Test LPIPS distance computation."""
        dummy_path1 = Path("/tmp/dummy1.png")
        dummy_path2 = Path("/tmp/dummy2.png")
        
        distance = compute_lpips_distance(dummy_path1, dummy_path2)
        assert isinstance(distance, float)
        assert 0.0 <= distance <= 1.0

    def test_compute_lpips_distance_from_paths(self):
        """Test LPIPS distance from paths."""
        dummy_path1 = Path("/tmp/dummy1.png")
        dummy_path2 = Path("/tmp/dummy2.png")
        
        distance = compute_lpips_distance_from_paths(dummy_path1, dummy_path2)
        assert isinstance(distance, float)

    def test_compute_cesr_score(self):
        """Test CESR score computation."""
        query_emb = np.random.random(512)
        ref_embs = [np.random.random(512) for _ in range(5)]
        distr_embs = [np.random.random(512) for _ in range(3)]
        
        cesr_norm, cesr_base = compute_cesr_score(query_emb, ref_embs, distr_embs)
        
        assert isinstance(cesr_norm, float)
        assert isinstance(cesr_base, float)

    def test_compute_cesr_score_empty_references(self):
        """Test CESR with empty references."""
        query_emb = np.random.random(512)
        
        cesr_norm, cesr_base = compute_cesr_score(query_emb, [], [])
        
        assert cesr_norm == 0.0
        assert cesr_base == 0.0

    def test_compute_lpips_matrix(self):
        """Test LPIPS distance matrix computation."""
        dummy_paths = [Path("/tmp/dummy1.png"), Path("/tmp/dummy2.png"), Path("/tmp/dummy3.png")]
        
        matrix = compute_lpips_matrix(dummy_paths)
        
        assert matrix.shape == (3, 3)
        assert np.allclose(matrix, matrix.T)  # Symmetric
        assert np.allclose(np.diag(matrix), 0.0)  # Diagonal is zero

if __name__ == "__main__":
    pytest.main([__file__, "-v"])