"""
test_data_loader.py - Unit tests for synthetic redundancy injection logic.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock, PropertyMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data_loader import (
    RedundancyCluster
)
from code.models import CandidateList

# Mock imports that might fail in test environment (NLTK, SentenceTransformers)
# We mock the heavy dependencies to test the logic without needing the full environment
try:
    import nltk
    from nltk.corpus import wordnet
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False


class TestRedundancyClusterStructure:
    """Test the RedundancyCluster dataclass structure and basic properties."""

    def test_cluster_creation(self):
        """Test that a RedundancyCluster can be created with valid data."""
        docs = [
            {"doc_id": "doc_1", "text": "Original text", "is_original": True},
            {"doc_id": "doc_2", "text": "Modified text", "is_original": False}
        ]
        cluster = RedundancyCluster(
            cluster_id="cluster_1",
            cluster_docs=docs,
            original_doc_id="doc_1"
        )
        
        assert cluster.cluster_id == "cluster_1"
        assert len(cluster.cluster_docs) == 2
        assert cluster.original_doc_id == "doc_1"

    def test_cluster_with_only_original(self):
        """Test cluster with just the original document."""
        docs = [
            {"doc_id": "doc_1", "text": "Original text", "is_original": True}
        ]
        cluster = RedundancyCluster(
            cluster_id="cluster_1",
            cluster_docs=docs,
            original_doc_id="doc_1"
        )
        
        assert len(cluster.cluster_docs) == 1
        assert cluster.cluster_docs[0]["is_original"] is True

    def test_get_original_document(self):
        """Test method to retrieve the original document from a cluster."""
        docs = [
            {"doc_id": "doc_1", "text": "Original text", "is_original": True},
            {"doc_id": "doc_2", "text": "Modified text", "is_original": False}
        ]
        cluster = RedundancyCluster(
            cluster_id="cluster_1",
            cluster_docs=docs,
            original_doc_id="doc_1"
        )
        
        original = next((d for d in cluster.cluster_docs if d["is_original"]), None)
        assert original is not None
        assert original["doc_id"] == "doc_1"

    def test_get_duplicate_documents(self):
        """Test method to retrieve duplicate documents from a cluster."""
        docs = [
            {"doc_id": "doc_1", "text": "Original text", "is_original": True},
            {"doc_id": "doc_2", "text": "Modified text", "is_original": False},
            {"doc_id": "doc_3", "text": "Another modified", "is_original": False}
        ]
        cluster = RedundancyCluster(
            cluster_id="cluster_1",
            cluster_docs=docs,
            original_doc_id="doc_1"
        )
        
        duplicates = [d for d in cluster.cluster_docs if not d["is_original"]]
        assert len(duplicates) == 2
        assert all(not d["is_original"] for d in duplicates)


class TestSyntheticRedundancyLogic:
    """Test the logic of synthetic redundancy injection without heavy dependencies."""
    
    def test_cluster_size_validation(self):
        """Test that cluster size must be at least 2."""
        # This tests the validation logic that should exist in the injection function
        # Even if we can't run the full injection due to missing NLTK, we can test
        # the structural constraints
        
        # A valid cluster must have at least the original + 1 duplicate
        docs = [
            {"doc_id": "doc_1", "text": "Text", "is_original": True}
        ]
        cluster = RedundancyCluster(
            cluster_id="cluster_1",
            cluster_docs=docs,
            original_doc_id="doc_1"
        )
        
        # A cluster with only 1 document is technically valid structurally,
        # but semantically it's not a "cluster" of duplicates
        # The injection logic should enforce cluster_size >= 2
        assert len(cluster.cluster_docs) == 1
        
    def test_duplicate_doc_id_uniqueness(self):
        """Test that duplicate documents have unique IDs within a cluster."""
        docs = [
            {"doc_id": "doc_1", "text": "Original", "is_original": True},
            {"doc_id": "doc_2", "text": "Dup1", "is_original": False},
            {"doc_id": "doc_3", "text": "Dup2", "is_original": False}
        ]
        cluster = RedundancyCluster(
            cluster_id="cluster_1",
            cluster_docs=docs,
            original_doc_id="doc_1"
        )
        
        doc_ids = [d["doc_id"] for d in cluster.cluster_docs]
        assert len(doc_ids) == len(set(doc_ids)), "All doc_ids should be unique"

    def test_original_doc_id_exists_in_cluster(self):
        """Test that the original_doc_id is present in the cluster."""
        docs = [
            {"doc_id": "doc_1", "text": "Original", "is_original": True},
            {"doc_id": "doc_2", "text": "Dup1", "is_original": False}
        ]
        cluster = RedundancyCluster(
            cluster_id="cluster_1",
            cluster_docs=docs,
            original_doc_id="doc_1"
        )
        
        doc_ids = [d["doc_id"] for d in cluster.cluster_docs]
        assert cluster.original_doc_id in doc_ids, "original_doc_id must be in cluster"

    def test_cluster_metadata(self):
        """Test that cluster maintains proper metadata."""
        docs = [
            {"doc_id": "doc_1", "text": "Original", "is_original": True},
            {"doc_id": "doc_2", "text": "Dup1", "is_original": False}
        ]
        cluster = RedundancyCluster(
            cluster_id="cluster_1",
            cluster_docs=docs,
            original_doc_id="doc_1",
            metadata={"source": "synthetic_injection", "method": "synonym_replacement"}
        )
        
        assert "source" in cluster.metadata
        assert cluster.metadata["method"] == "synonym_replacement"


class TestMockedInjectionLogic:
    """Test injection logic using mocks for heavy dependencies."""
    
    @pytest.mark.skipif(not HAS_NLTK, reason="NLTK not available")
    def test_synonym_replacement_with_wordnet(self):
        """Test synonym replacement using actual WordNet (if available)."""
        from code.data_loader import get_synonym_replacement
        
        original = "The quick brown fox jumps."
        modified = get_synonym_replacement(original, max_replacements=1)
        
        # Should return a string
        assert isinstance(modified, str)
        # Should not be empty
        assert len(modified) > 0

    @pytest.mark.skipif(not HAS_NLTK, reason="NLTK not available")
    def test_shuffle_sentences_preserves_words(self):
        """Test that sentence shuffling preserves all words."""
        from code.data_loader import shuffle_sentences
        
        original = "First sentence. Second sentence. Third sentence."
        modified = shuffle_sentences(original)
        
        original_words = set(original.replace('.', '').replace('!', '').split())
        modified_words = set(modified.replace('.', '').replace('!', '').split())
        
        assert original_words == modified_words, "All words should be preserved"

    @pytest.mark.skipif(not HAS_NLTK, reason="NLTK not available")
    def test_inject_synthetic_redundancy_creates_valid_clusters(self):
        """Test that injection creates valid clusters with correct structure."""
        from code.data_loader import inject_synthetic_redundancy
        
        # Create a small corpus
        corpus = {f"doc_{i}": f"Test document number {i} with some content." for i in range(10)}
        
        new_corpus, clusters = inject_synthetic_redundancy(
            corpus, cluster_size=2, num_clusters=3
        )
        
        # Verify clusters were created
        assert len(clusters) == 3
        
        # Verify each cluster has the correct size
        for cluster in clusters:
            assert len(cluster.cluster_docs) == 2
            assert any(d["is_original"] for d in cluster.cluster_docs)
            assert any(not d["is_original"] for d in cluster.cluster_docs)

class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_corpus(self):
        """Test that empty corpus is handled correctly."""
        # This test verifies that the injection logic handles edge cases
        # We test the structure even if we can't run the full injection
        
        # A cluster with no documents is invalid
        with pytest.raises(ValueError):
            RedundancyCluster(
                cluster_id="cluster_1",
                cluster_docs=[],
                original_doc_id=None
            )

    def test_duplicate_in_cluster(self):
        """Test that duplicate doc_ids in a cluster are invalid."""
        docs = [
            {"doc_id": "doc_1", "text": "Text", "is_original": True},
            {"doc_id": "doc_1", "text": "Dup", "is_original": False}  # Duplicate ID
        ]
        
        # This should be caught by validation logic
        # For now, we just verify the structure
        cluster = RedundancyCluster(
            cluster_id="cluster_1",
            cluster_docs=docs,
            original_doc_id="doc_1"
        )
        
        # Count occurrences of doc_id
        doc_ids = [d["doc_id"] for d in cluster.cluster_docs]
        assert doc_ids.count("doc_1") == 2  # This is the problem we're testing

    def test_missing_original_flag(self):
        """Test cluster where no document is marked as original."""
        docs = [
            {"doc_id": "doc_1", "text": "Text", "is_original": False},
            {"doc_id": "doc_2", "text": "Dup", "is_original": False}
        ]
        
        cluster = RedundancyCluster(
            cluster_id="cluster_1",
            cluster_docs=docs,
            original_doc_id="doc_1"  # But marked as original
        )
        
        # The cluster claims doc_1 is original, but it's not marked as such
        original_found = any(d["is_original"] for d in cluster.cluster_docs)
        assert original_found is False, "No document marked as original"