"""Unit tests for semantic stability analysis module."""
import numpy as np
import pytest

from code.analysis.stability import (
    compute_cosine_similarity,
    compute_embeddings,
    group_generations_by_condition,
    StabilityError,
)
from sentence_transformers import SentenceTransformer


class TestCosineSimilarity:
    """Tests for compute_cosine_similarity function."""

    def test_identical_vectors(self):
        """Identical vectors should have similarity 1.0."""
        vec_a = np.array([1.0, 2.0, 3.0])
        vec_b = np.array([1.0, 2.0, 3.0])
        sim = compute_cosine_similarity(vec_a, vec_b)
        assert abs(sim - 1.0) < 1e-6, f"Expected 1.0, got {sim}"

    def test_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity 0.0."""
        vec_a = np.array([1.0, 0.0, 0.0])
        vec_b = np.array([0.0, 1.0, 0.0])
        sim = compute_cosine_similarity(vec_a, vec_b)
        assert abs(sim - 0.0) < 1e-6, f"Expected 0.0, got {sim}"

    def test_opposite_vectors(self):
        """Opposite vectors should have similarity -1.0."""
        vec_a = np.array([1.0, 2.0, 3.0])
        vec_b = np.array([-1.0, -2.0, -3.0])
        sim = compute_cosine_similarity(vec_a, vec_b)
        assert abs(sim - (-1.0)) < 1e-6, f"Expected -1.0, got {sim}"

    def test_zero_vector(self):
        """Zero vector should result in similarity 0.0 (division by zero handled)."""
        vec_a = np.array([0.0, 0.0, 0.0])
        vec_b = np.array([1.0, 2.0, 3.0])
        sim = compute_cosine_similarity(vec_a, vec_b)
        assert sim == 0.0, f"Expected 0.0 for zero vector, got {sim}"

    def test_shape_mismatch(self):
        """Different shapes should raise ValueError."""
        vec_a = np.array([1.0, 2.0])
        vec_b = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            compute_cosine_similarity(vec_a, vec_b)

    def test_known_similarity(self):
        """Test with known values to ensure numerical stability."""
        # Two vectors with known cosine similarity
        vec_a = np.array([3.0, 0.0, 4.0])
        vec_b = np.array([0.0, 5.0, 0.0])
        # Dot product = 0, so similarity should be 0
        sim = compute_cosine_similarity(vec_a, vec_b)
        assert abs(sim) < 1e-6, f"Expected ~0.0, got {sim}"

        # Another pair
        vec_c = np.array([1.0, 1.0, 1.0])
        vec_d = np.array([1.0, 1.0, 0.0])
        # Dot = 2, |c| = sqrt(3), |d| = sqrt(2)
        # sim = 2 / (sqrt(3)*sqrt(2)) = 2 / sqrt(6) ≈ 0.8165
        expected = 2.0 / np.sqrt(6.0)
        sim = compute_cosine_similarity(vec_c, vec_d)
        assert abs(sim - expected) < 1e-4, f"Expected {expected}, got {sim}"


class TestGroupGenerations:
    """Tests for group_generations_by_condition function."""

    def test_empty_list(self):
        """Empty input should return empty dict."""
        result = group_generations_by_condition([])
        assert result == {}

    def test_single_record(self):
        """Single record creates one group."""
        data = [{"prompt_id": "p1", "strategy": "s1", "text": "hello"}]
        result = group_generations_by_condition(data)
        assert len(result) == 1
        assert ("p1", "s1") in result
        assert len(result[("p1", "s1")]) == 1

    def test_multiple_groups(self):
        """Multiple records are grouped correctly."""
        data = [
            {"prompt_id": "p1", "strategy": "s1", "text": "a"},
            {"prompt_id": "p1", "strategy": "s1", "text": "b"},
            {"prompt_id": "p2", "strategy": "s1", "text": "c"},
            {"prompt_id": "p1", "strategy": "s2", "text": "d"},
        ]
        result = group_generations_by_condition(data)
        assert len(result) == 3
        assert len(result[("p1", "s1")]) == 2
        assert len(result[("p2", "s1")]) == 1
        assert len(result[("p1", "s2")]) == 1

    def test_missing_keys(self):
        """Missing prompt_id or strategy defaults to 'unknown'."""
        data = [{"text": "x"}]
        result = group_generations_by_condition(data)
        assert ("unknown", "unknown") in result


class TestEmbeddingComputation:
    """Tests for compute_embeddings function."""

    def test_empty_list(self):
        """Empty text list returns empty array."""
        model = SentenceTransformer("all-MiniLM-L6-v2")
        result = compute_embeddings([], model)
        assert result.size == 0

    def test_single_text(self):
        """Single text returns array of shape (1, dim)."""
        model = SentenceTransformer("all-MiniLM-L6-v2")
        texts = ["test sentence"]
        result = compute_embeddings(texts, model)
        assert result.shape[0] == 1
        assert result.ndim == 2

    def test_multiple_texts(self):
        """Multiple texts return array of correct shape."""
        model = SentenceTransformer("all-MiniLM-L6-v2")
        texts = ["one", "two", "three"]
        result = compute_embeddings(texts, model)
        assert result.shape[0] == 3
        assert result.ndim == 2
        # Check that embeddings are not all zeros
        assert not np.allclose(result, 0)

    def test_batch_processing(self):
        """Batch processing should yield same results as single."""
        model = SentenceTransformer("all-MiniLM-L6-v2")
        texts = ["sentence A", "sentence B", "sentence C", "sentence D"]

        result_batch = compute_embeddings(texts, model, batch_size=2)
        result_single = compute_embeddings(texts, model, batch_size=len(texts))

        assert np.allclose(result_batch, result_single, atol=1e-5)