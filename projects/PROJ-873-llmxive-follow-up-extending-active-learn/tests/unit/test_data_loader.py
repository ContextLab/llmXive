"""
test_data_loader.py - Unit tests for synthetic redundancy injection logic.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data_loader import (
    get_synonym_replacement,
    shuffle_sentences,
    inject_synthetic_redundancy,
    RedundancyCluster
)

class TestSynonymReplacement:
    def test_synonym_replacement_changes_text(self):
        """Test that synonym replacement actually modifies the text."""
        original = "This is a simple test document."
        modified = get_synonym_replacement(original, max_replacements=2)
        assert modified != original, "Synonym replacement should change the text"

    def test_synonym_replacement_preserves_structure(self):
        """Test that synonym replacement preserves sentence structure."""
        original = "The quick brown fox."
        modified = get_synonym_replacement(original, max_replacements=10)
        # Should have similar word count
        assert len(modified.split()) >= len(original.split()) - 1

class TestSentenceShuffling:
    def test_shuffle_changes_order(self):
        """Test that sentence shuffling changes the order."""
        original = "First sentence. Second sentence. Third sentence."
        modified = shuffle_sentences(original)
        # With 3 sentences, shuffling should likely change order
        # (There's a small chance it stays same, but very unlikely)
        assert modified != original or len(original.split('. ')) == 1

    def test_shuffle_preserves_content(self):
        """Test that sentence shuffling preserves all content."""
        original = "First sentence. Second sentence."
        modified = shuffle_sentences(original)
        original_words = set(original.replace('.', '').split())
        modified_words = set(modified.replace('.', '').split())
        assert original_words == modified_words, "Shuffling should preserve all words"

class TestInjectSyntheticRedundancy:
    def test_injection_creates_clusters(self):
        """Test that injection creates the expected number of clusters."""
        corpus = {f"doc_{i}": f"Text content {i}." for i in range(50)}
        cluster_size = 3
        num_clusters = 5

        new_corpus, clusters = inject_synthetic_redundancy(
            corpus, cluster_size=cluster_size, num_clusters=num_clusters
        )

        assert len(clusters) == num_clusters, f"Expected {num_clusters} clusters"

    def test_cluster_size_matches(self):
        """Test that each cluster has the correct number of documents."""
        corpus = {f"doc_{i}": f"Text content {i}." for i in range(100)}
        cluster_size = 4
        num_clusters = 3

        new_corpus, clusters = inject_synthetic_redundancy(
            corpus, cluster_size=cluster_size, num_clusters=num_clusters
        )

        for cluster in clusters:
            assert len(cluster.cluster_docs) == cluster_size, \
                f"Cluster should have {cluster_size} documents"

    def test_injection_adds_new_documents(self):
        """Test that injection adds new documents to the corpus."""
        original_size = 20
        corpus = {f"doc_{i}": f"Text content {i}." for i in range(original_size)}
        cluster_size = 3
        num_clusters = 2

        new_corpus, clusters = inject_synthetic_redundancy(
            corpus, cluster_size=cluster_size, num_clusters=num_clusters
        )

        expected_new_docs = num_clusters * (cluster_size - 1)
        assert len(new_corpus) == original_size + expected_new_docs, \
            f"Expected {original_size + expected_new_docs} documents"

    def test_clusters_contain_original(self):
        """Test that each cluster contains the original document."""
        corpus = {f"doc_{i}": f"Text content {i}." for i in range(30)}
        cluster_size = 3
        num_clusters = 2

        new_corpus, clusters = inject_synthetic_redundancy(
            corpus, cluster_size=cluster_size, num_clusters=num_clusters
        )

        for cluster in clusters:
            original_found = any(doc["is_original"] for doc in cluster.cluster_docs)
            assert original_found, "Each cluster should contain the original document"

    def test_near_duplicates_are_similar(self):
        """Test that injected duplicates are similar to the original."""
        # This is a structural test; actual similarity is tested in metrics tests
        corpus = {f"doc_{i}": f"This is a test document number {i}." for i in range(50)}
        cluster_size = 3
        num_clusters = 2

        new_corpus, clusters = inject_synthetic_redundancy(
            corpus, cluster_size=cluster_size, num_clusters=num_clusters
        )

        for cluster in clusters:
            original_text = next(d["text"] for d in cluster.cluster_docs if d["is_original"])
            for doc in cluster.cluster_docs:
                if not doc["is_original"]:
                    # Should not be identical
                    assert doc["text"] != original_text, "Duplicate should not be identical"

    def test_small_corpus_raises_error(self):
        """Test that too small corpus raises an error."""
        corpus = {f"doc_{i}": f"Text {i}." for i in range(2)}
        with pytest.raises(ValueError):
            inject_synthetic_redundancy(corpus, cluster_size=3, num_clusters=2)
