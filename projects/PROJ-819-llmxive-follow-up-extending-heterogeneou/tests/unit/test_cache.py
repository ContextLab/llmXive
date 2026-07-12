"""
Unit tests for the Semantic Cache module (T007) and utility functions (T008).

Tests hit/miss logic, basic cache operations, and cosine similarity calculations.
"""
import pytest
import numpy as np
import sys
import os
from pathlib import Path
import time

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.cache.semantic_cache import SemanticCache, CacheEntry
from code.cache.utils import cosine_similarity, threshold_check


class TestSemanticCache:
    """Tests for the SemanticCache class."""

    def test_init(self):
        """Test cache initialization."""
        cache = SemanticCache(max_size=10)
        assert len(cache) == 0
        assert cache.max_size == 10

    def test_put_and_get_exact(self):
        """Test putting an entry and retrieving it."""
        cache = SemanticCache(max_size=5)
        query_id = "test-001"
        embedding = np.array([1.0, 0.0, 0.0])
        output = "Expected output"
        
        cache.put(query_id, embedding, output)
        
        # Retrieve with perfect match
        result = cache.get_best_match(embedding, threshold=0.99)
        
        assert result is not None
        assert result[0] == query_id
        assert result[1] == output
        assert abs(result[2] - 1.0) < 1e-6

    def test_get_miss_below_threshold(self):
        """Test that a low similarity returns None."""
        cache = SemanticCache(max_size=5)
        query_id = "test-002"
        embedding = np.array([1.0, 0.0, 0.0])
        output = "Output A"
        
        cache.put(query_id, embedding, output)
        
        # Query with orthogonal vector (similarity 0.0)
        orthogonal = np.array([0.0, 1.0, 0.0])
        result = cache.get_best_match(orthogonal, threshold=0.9)
        
        assert result is None

    def test_lru_eviction(self):
        """Test that LRU eviction works when max_size is exceeded."""
        cache = SemanticCache(max_size=2)
        
        # Add 3 items
        e1 = np.array([1.0, 0.0])
        e2 = np.array([0.0, 1.0])
        e3 = np.array([0.5, 0.5])
        
        cache.put("id1", e1, "out1")
        cache.put("id2", e2, "out2")
        cache.put("id3", e3, "out3")
        
        # id1 should be evicted
        assert len(cache) == 2
        assert cache.contains("id1") is False
        assert cache.contains("id3") is True

    def test_update_lru_on_access(self):
        """Test that accessing an item moves it to MRU position."""
        cache = SemanticCache(max_size=2)
        
        e1 = np.array([1.0, 0.0])
        e2 = np.array([0.0, 1.0])
        
        cache.put("id1", e1, "out1")
        cache.put("id2", e2, "out2")
        
        # Access id1 to make it MRU
        cache.get_best_match(e1, threshold=0.0)
        
        # Add new item, should evict id2 (LRU)
        cache.put("id3", np.array([1.0, 1.0]), "out3")
        
        assert cache.contains("id1") is True
        assert cache.contains("id2") is False
        assert cache.contains("id3") is True

    def test_hit_rate_calculation(self):
        """Test hit/miss tracking logic."""
        cache = SemanticCache(max_size=5)
        emb = np.array([1.0, 0.0])
        
        # Miss initially
        cache.get_best_match(emb, threshold=0.9)
        assert cache.hit_rate == 0.0
        
        # Put item
        cache.put("q1", emb, "res1")
        
        # Hit
        cache.get_best_match(emb, threshold=0.9)
        # 1 hit, 2 total calls (1 miss, 1 hit) -> 0.5
        assert cache.hit_rate == 0.5

    def test_contains_method(self):
        """Test the contains helper method."""
        cache = SemanticCache(max_size=5)
        emb = np.array([1.0, 0.0])
        cache.put("q1", emb, "res1")
        
        assert cache.contains("q1") is True
        assert cache.contains("q2") is False


class TestCacheEntry:
    """Tests for the CacheEntry dataclass."""

    def test_entry_creation(self):
        """Test creating a CacheEntry."""
        emb = np.array([1.0, 2.0])
        entry = CacheEntry(embedding=emb, output="test", query_id="q1")
        
        assert np.array_equal(entry.embedding, emb)
        assert entry.output == "test"
        assert entry.query_id == "q1"
        assert isinstance(entry.timestamp, float)

    def test_embedding_conversion(self):
        """Test that list inputs are converted to numpy arrays."""
        entry = CacheEntry(embedding=[1.0, 2.0], output="test")
        assert isinstance(entry.embedding, np.ndarray)


class TestUtils:
    """Tests for utility functions (T008)."""

    def test_cosine_similarity_perfect_match(self):
        """Test cosine similarity for identical vectors."""
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([1.0, 2.0, 3.0])
        score = cosine_similarity(v1, v2)
        assert abs(score - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity for orthogonal vectors."""
        v1 = np.array([1.0, 0.0])
        v2 = np.array([0.0, 1.0])
        score = cosine_similarity(v1, v2)
        assert abs(score - 0.0) < 1e-6

    def test_cosine_similarity_opposite(self):
        """Test cosine similarity for opposite vectors (-1.0)."""
        v1 = np.array([1.0, 0.0])
        v2 = np.array([-1.0, 0.0])
        score = cosine_similarity(v1, v2)
        assert abs(score - (-1.0)) < 1e-6

    def test_cosine_similarity_zero_norm(self):
        """Test cosine similarity handles zero vectors."""
        v1 = np.array([0.0, 0.0])
        v2 = np.array([1.0, 1.0])
        score = cosine_similarity(v1, v2)
        assert score == 0.0

    def test_cosine_similarity_random_vectors(self):
        """Test cosine similarity with random vectors."""
        np.random.seed(42)
        v1 = np.random.rand(5)
        v2 = np.random.rand(5)
        score = cosine_similarity(v1, v2)
        # Score must be between -1 and 1
        assert -1.0 <= score <= 1.0

    def test_threshold_check_pass(self):
        """Test threshold check when condition is met."""
        assert threshold_check(0.95, 0.90) is True
        assert threshold_check(0.90, 0.90) is True

    def test_threshold_check_fail(self):
        """Test threshold check when condition is not met."""
        assert threshold_check(0.89, 0.90) is False
        assert threshold_check(-0.5, 0.0) is False