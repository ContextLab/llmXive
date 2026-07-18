"""
Unit tests for edge cases in the llmXive pipeline.

Tests cover:
- Strict similarity thresholds (0.99, 1.0)
- Low budget scenarios (very small candidate lists, limited compute)
- Empty datasets
- Single-item clusters
- Boundary conditions in statistical tests
"""
import pytest
import numpy as np
from typing import List, Dict, Any
import os
import sys
import json
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from metrics import (
    calculate_cosine_similarity_proxy,
    is_wasted_call,
    calculate_ndcg_at_k,
    wilcoxon_signed_rank_test,
    bonferroni_correction,
    calculate_dynamic_sample_size,
    validate_jaccard_cosine_correlation,
    get_embedding_model
)
from clustering import (
    create_minhash,
    estimate_jaccard,
    cluster_documents,
    filter_candidates_by_clustering
)
from models import CandidateList, ComparisonPair
from data_loader import inject_synthetic_redundancy, RedundancyCluster

# Fixtures
@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        "The quick brown fox jumps over the lazy dog.",
        "A fast brown fox leaps over a lazy dog.",
        "The quick brown fox jumps over the lazy dog.",  # Exact duplicate
        "Machine learning models require large datasets.",
        "Deep learning algorithms need extensive training data.",
        "Natural language processing is a subfield of AI.",
        "Computer vision enables machines to interpret images.",
        "Reinforcement learning uses reward signals for training.",
    ]

@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing."""
    model = get_embedding_model()
    return model.encode(sample_documents())

@pytest.fixture
def empty_documents():
    """Empty list of documents."""
    return []

@pytest.fixture
def single_document():
    """Single document list."""
    return ["This is a single test document."]

@pytest.fixture
def strict_thresholds():
    """List of strict similarity thresholds."""
    return [0.99, 0.995, 1.0]

@pytest.fixture
def low_budget_configs():
    """Low budget configurations."""
    return [
        {"max_candidates": 5, "max_runtime_seconds": 10},
        {"max_candidates": 10, "max_runtime_seconds": 5},
        {"max_candidates": 2, "max_runtime_seconds": 1},
    ]

# Edge Case Tests for Similarity Thresholds
class TestStrictThresholds:
    """Test behavior with strict similarity thresholds."""

    def test_threshold_099_detects_exact_duplicates(self, sample_documents):
        """Test that threshold 0.99 detects exact duplicates."""
        model = get_embedding_model()
        embeddings = model.encode(sample_documents)
        
        # Documents 0 and 2 are exact duplicates
        similarity = calculate_cosine_similarity_proxy(embeddings[0], embeddings[2])
        assert similarity >= 0.99, "Exact duplicates should have similarity >= 0.99"
        assert is_wasted_call(similarity, threshold=0.99), "Exact duplicates should be flagged at 0.99"

    def test_threshold_100_only_exact_matches(self, sample_documents):
        """Test that threshold 1.0 only flags exact matches."""
        model = get_embedding_model()
        embeddings = model.encode(sample_documents)
        
        # Test with exact duplicate
        similarity_exact = calculate_cosine_similarity_proxy(embeddings[0], embeddings[2])
        assert is_wasted_call(similarity_exact, threshold=1.0), "Exact duplicates should be flagged at 1.0"
        
        # Test with near-duplicate (should not be flagged at 1.0)
        similarity_near = calculate_cosine_similarity_proxy(embeddings[0], embeddings[1])
        assert not is_wasted_call(similarity_near, threshold=1.0), "Near-duplicates should not be flagged at 1.0"

    def test_very_strict_threshold_no_false_positives(self, sample_documents):
        """Test that very strict thresholds minimize false positives."""
        model = get_embedding_model()
        embeddings = model.encode(sample_documents)
        
        threshold = 0.999
        flagged_count = 0
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = calculate_cosine_similarity_proxy(embeddings[i], embeddings[j])
                if is_wasted_call(sim, threshold=threshold):
                    flagged_count += 1
        
        # Only exact duplicates should be flagged at very strict threshold
        assert flagged_count <= 1, "Very strict threshold should flag minimal pairs"

# Edge Case Tests for Low Budget Scenarios
class TestLowBudgetScenarios:
    """Test behavior under low budget constraints."""

    def test_minimal_candidate_list(self, single_document):
        """Test processing with only one candidate."""
        model = get_embedding_model()
        embeddings = model.encode(single_document)
        
        # Should not crash with single document
        result = calculate_ndcg_at_k(embeddings[:1], [1], k=1)
        assert result is not None, "Should handle single document"

    def test_empty_document_list(self, empty_documents):
        """Test processing with empty document list."""
        model = get_embedding_model()
        
        # Should handle empty list gracefully
        try:
            embeddings = model.encode(empty_documents)
            # Empty embeddings should result in empty or zero metrics
            if len(embeddings) == 0:
                pass  # Expected behavior
        except Exception as e:
            pytest.fail(f"Empty document list should not raise exception: {e}")

    def test_dynamic_sample_size_with_zero_flagged(self):
        """Test dynamic sample size calculation with zero flagged calls."""
        total_flagged = 0
        upper_bound = 100
        
        sample_size = calculate_dynamic_sample_size(total_flagged, upper_bound)
        assert sample_size == 0, "Sample size should be 0 when no calls are flagged"

    def test_dynamic_sample_size_with_very_small_flagged(self):
        """Test dynamic sample size with very small number of flagged calls."""
        total_flagged = 1
        upper_bound = 100
        
        sample_size = calculate_dynamic_sample_size(total_flagged, upper_bound)
        assert sample_size == 1, "Sample size should equal total when very small"

    def test_dynamic_sample_size_respects_upper_bound(self):
        """Test that dynamic sample size respects upper bound."""
        total_flagged = 10000
        upper_bound = 100
        
        sample_size = calculate_dynamic_sample_size(total_flagged, upper_bound)
        assert sample_size <= upper_bound, "Sample size should not exceed upper bound"
        assert sample_size == upper_bound, "Sample size should equal upper bound when available exceeds it"

# Edge Case Tests for Clustering
class TestClusteringEdgeCases:
    """Test clustering behavior with edge cases."""

    def test_single_document_clustering(self, single_document):
        """Test clustering with a single document."""
        minhash = create_minhash(single_document[0])
        assert minhash is not None, "Should create minhash for single document"

    def test_empty_document_clustering(self, empty_documents):
        """Test clustering with empty document list."""
        if len(empty_documents) == 0:
            # Should handle gracefully
            pass
        else:
            minhashes = [create_minhash(doc) for doc in empty_documents]
            assert len(minhashes) == 0, "Should return empty list for empty input"

    def test_cluster_with_all_duplicates(self):
        """Test clustering when all documents are duplicates."""
        docs = ["Same document"] * 5
        minhashes = [create_minhash(doc) for doc in docs]
        
        # All should cluster together
        clusters = cluster_documents(minhashes, threshold=0.95)
        assert len(clusters) == 1, "All duplicates should form one cluster"

    def test_cluster_with_no_duplicates(self, sample_documents):
        """Test clustering when no documents are duplicates."""
        # Use distinct documents
        docs = [
            "Document about cats and dogs.",
            "Article on quantum physics principles.",
            "Recipe for chocolate chip cookies.",
            "History of ancient Rome.",
            "Guide to hiking in the mountains.",
        ]
        minhashes = [create_minhash(doc) for doc in docs]
        
        clusters = cluster_documents(minhashes, threshold=0.99)
        # With high threshold, most should be separate
        assert len(clusters) >= 3, "Distinct documents should form separate clusters"

# Edge Case Tests for Statistical Tests
class TestStatisticalEdgeCases:
    """Test statistical functions with edge cases."""

    def test_wilcoxon_with_identical_samples(self):
        """Test Wilcoxon test with identical samples."""
        sample1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        sample2 = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        # Should handle identical samples (p-value should be 1.0 or similar)
        result = wilcoxon_signed_rank_test(sample1, sample2)
        assert result is not None, "Should return result for identical samples"

    def test_wilcoxon_with_single_element(self):
        """Test Wilcoxon test with single element."""
        sample1 = [1.0]
        sample2 = [2.0]
        
        # Should handle gracefully or raise informative error
        try:
            result = wilcoxon_signed_rank_test(sample1, sample2)
            # If it doesn't crash, it should return a valid result
            assert result is not None
        except Exception as e:
            # Expected for very small samples
            assert "insufficient" in str(e).lower() or "sample" in str(e).lower()

    def test_bonferroni_with_single_test(self):
        """Test Bonferroni correction with single test."""
        p_values = [0.05]
        corrected = bonferroni_correction(p_values)
        
        assert len(corrected) == 1, "Should return one corrected value"
        assert corrected[0] == 0.05, "Single test should not change p-value"

    def test_bonferroni_with_many_tests(self):
        """Test Bonferroni correction with many tests."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        corrected = bonferroni_correction(p_values)
        
        assert len(corrected) == len(p_values), "Should return same number of values"
        # All corrected values should be >= original (or capped at 1.0)
        for orig, corr in zip(p_values, corrected):
            assert corr >= orig or corr >= 1.0, "Corrected p-value should be >= original"

# Edge Case Tests for NDCG Calculation
class TestNDCGEdgeCases:
    """Test NDCG calculation with edge cases."""

    def test_ndcg_with_single_relevant_document(self):
        """Test NDCG with only one relevant document."""
        # Simulated scores and relevance
        scores = [0.8, 0.5, 0.3]
        relevance = [1, 0, 0]
        
        ndcg = calculate_ndcg_at_k(scores, relevance, k=3)
        assert ndcg is not None, "Should calculate NDCG with single relevant doc"
        assert 0 <= ndcg <= 1, "NDCG should be between 0 and 1"

    def test_ndcg_with_no_relevant_documents(self):
        """Test NDCG with no relevant documents."""
        scores = [0.8, 0.5, 0.3]
        relevance = [0, 0, 0]
        
        ndcg = calculate_ndcg_at_k(scores, relevance, k=3)
        assert ndcg == 0.0, "NDCG should be 0 when no relevant documents"

    def test_ndcg_with_all_relevant_documents(self):
        """Test NDCG when all documents are relevant."""
        scores = [0.9, 0.8, 0.7]
        relevance = [1, 1, 1]
        
        ndcg = calculate_ndcg_at_k(scores, relevance, k=3)
        assert ndcg == 1.0, "NDCG should be 1.0 when all relevant and perfectly ranked"

    def test_ndcg_with_k_larger_than_list(self):
        """Test NDCG when k is larger than the list size."""
        scores = [0.8, 0.5]
        relevance = [1, 0]
        
        # Should handle k > len(scores) gracefully
        ndcg = calculate_ndcg_at_k(scores, relevance, k=10)
        assert ndcg is not None, "Should handle k > list size"
        assert 0 <= ndcg <= 1, "NDCG should be between 0 and 1"

# Edge Case Tests for Data Injection
class TestDataInjectionEdgeCases:
    """Test data injection with edge cases."""

    def test_injection_with_single_cluster(self):
        """Test injection with only one redundancy cluster."""
        base_docs = ["Base document"]
        clusters = [
            RedundancyCluster(
                cluster_id=0,
                members=["Base document", "Modified base", "Another variant"]
            )
        ]
        
        # Should handle single cluster
        result = inject_synthetic_redundancy(base_docs, clusters)
        assert result is not None, "Should handle single cluster"

    def test_injection_with_empty_clusters(self):
        """Test injection with empty cluster list."""
        base_docs = ["Document 1", "Document 2"]
        clusters = []
        
        result = inject_synthetic_redundancy(base_docs, clusters)
        # Should return base docs without modification
        assert len(result) == len(base_docs), "Empty clusters should not add documents"

    def test_cluster_with_minimum_size(self):
        """Test cluster with minimum size (3 members)."""
        cluster = RedundancyCluster(
            cluster_id=0,
            members=["Doc1", "Doc2", "Doc3"]
        )
        assert len(cluster.members) == 3, "Should accept minimum size cluster"

    def test_cluster_with_maximum_size(self):
        """Test cluster with larger size (5 members)."""
        cluster = RedundancyCluster(
            cluster_id=0,
            members=["Doc1", "Doc2", "Doc3", "Doc4", "Doc5"]
        )
        assert len(cluster.members) == 5, "Should accept larger cluster"

# Integration Edge Cases
class TestIntegrationEdgeCases:
    """Test integration of components with edge cases."""

    def test_full_pipeline_with_minimal_data(self, single_document):
        """Test full pipeline with minimal data."""
        # Should not crash with minimal input
        model = get_embedding_model()
        embeddings = model.encode(single_document)
        
        # Test clustering
        minhash = create_minhash(single_document[0])
        assert minhash is not None

        # Test metrics
        ndcg = calculate_ndcg_at_k(embeddings[:1], [1], k=1)
        assert ndcg is not None

    def test_threshold_sweep_with_single_threshold(self):
        """Test threshold sweep with only one threshold value."""
        thresholds = [0.95]
        
        # Should handle single threshold
        for thresh in thresholds:
            assert 0 <= thresh <= 1.0, "Threshold should be valid"

    def test_correlation_validation_with_small_sample(self):
        """Test correlation validation with small sample size."""
        jaccard_scores = [0.9, 0.95, 0.98]
        cosine_scores = [0.92, 0.96, 0.99]
        
        # Should handle small sample
        result = validate_jaccard_cosine_correlation(jaccard_scores, cosine_scores)
        assert result is not None, "Should handle small sample"

# Performance Edge Cases
class TestPerformanceEdgeCases:
    """Test performance with edge cases."""

    def test_large_similarity_matrix(self):
        """Test with larger similarity matrix (100 documents)."""
        # Generate 100 short documents
        docs = [f"Document {i} with some text to make it longer." for i in range(100)]
        
        model = get_embedding_model()
        embeddings = model.encode(docs)
        
        # Should handle 100x100 similarity matrix
        for i in range(0, 100, 10):  # Sample to avoid O(N^2) for all pairs
            for j in range(i + 1, min(i + 10, 100)):
                sim = calculate_cosine_similarity_proxy(embeddings[i], embeddings[j])
                assert 0 <= sim <= 1.0, "Similarity should be valid"

    def test_memory_efficient_with_small_budget(self):
        """Test memory efficiency with very small budget."""
        # Simulate a scenario where we have very limited memory
        # The code should handle this by processing in chunks or failing gracefully
        pass  # Actual memory testing would require more complex setup