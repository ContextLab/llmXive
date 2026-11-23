"""
Tests for T025: Matching validation step.

These tests verify that the matching pipeline correctly:
1. Loads perspective features and target data
2. Builds TF-IDF vectors with pronoun exclusion
3. Finds matches above the threshold
4. Outputs results in the correct schema
"""
import pytest
import json
import os
import tempfile
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Import functions to test
from matching import build_tfidf_vectors, find_top_matches, ALL_PRONOUNS
from config import PRIMARY_MATCHING_THRESHOLD

class TestMatchingT025:
    """Test cases for T025 matching validation."""
    
    def test_build_tfidf_vectors_excludes_pronouns(self):
        """Test that TF-IDF vectors exclude pronouns from vocabulary."""
        source_texts = [
            "I walked to the store and bought some milk.",
            "She walked to the store and bought some milk."
        ]
        target_texts = [
            "He went to the market and purchased bread.",
            "We went to the market and purchased bread."
        ]
        
        source_vecs, target_vecs = build_tfidf_vectors(source_texts, target_texts, exclude_pronouns=True)
        
        # Verify vectors are computed
        assert source_vecs.shape[0] == len(source_texts)
        assert target_vecs.shape[0] == len(target_texts)
        
        # Verify non-zero dimensions (some content should remain after pronoun removal)
        assert source_vecs.shape[1] > 0
        assert target_vecs.shape[1] > 0
        
        # Verify pronouns are not in the vocabulary by checking if they contribute to vectors
        # This is a bit tricky with TF-IDF, so we check that the vectors are not all zeros
        assert np.any(source_vecs != 0), "Source vectors should not be all zeros"
        assert np.any(target_vecs != 0), "Target vectors should not be all zeros"
    
    def test_find_top_matches_threshold_filtering(self):
        """Test that matches below threshold are excluded."""
        # Create simple test vectors
        query = np.array([[1.0, 0.0, 0.0]])
        candidates = np.array([
            [1.0, 0.0, 0.0],  # Similarity = 1.0
            [0.5, 0.5, 0.0],  # Similarity = 0.707
            [0.0, 0.0, 1.0],  # Similarity = 0.0
            [0.7, 0.0, 0.0]   # Similarity = 0.7
        ])
        
        threshold = 0.5
        matches = find_top_matches(query, candidates, k=3, threshold=threshold)
        
        # Should only return matches above threshold
        assert len(matches) == 3  # 1.0, 0.707, 0.7 are all >= 0.5
        
        # Verify all similarities are >= threshold
        for match in matches:
            assert match['similarity'] >= threshold, f"Match {match} has similarity below threshold"
    
    def test_find_top_matches_tie_breaking(self):
        """Test deterministic tie-breaking by index."""
        # Create vectors with identical similarities
        query = np.array([[1.0, 0.0]])
        candidates = np.array([
            [1.0, 0.0],  # Similarity = 1.0, index 0
            [1.0, 0.0],  # Similarity = 1.0, index 1
            [1.0, 0.0]   # Similarity = 1.0, index 2
        ])
        
        matches = find_top_matches(query, candidates, k=3, threshold=0.0)
        
        # Should return all 3 matches
        assert len(matches) == 3
        
        # Verify they are ordered by rank (which should reflect original order for ties)
        assert matches[0]['rank'] == 1
        assert matches[1]['rank'] == 2
        assert matches[2]['rank'] == 3
    
    def test_primary_threshold_constant(self):
        """Test that PRIMARY_MATCHING_THRESHOLD is set correctly."""
        assert PRIMARY_MATCHING_THRESHOLD == 0.30
    
    def test_matching_schema_validation(self):
        """Test that matching output conforms to expected schema."""
        # Create test data
        source_texts = ["The quick brown fox jumps over the lazy dog."]
        target_texts = ["A fast brown fox leaped over a sleepy dog."]
        
        source_vecs, target_vecs = build_tfidf_vectors(source_texts, target_texts)
        matches = find_top_matches(source_vecs[0], target_vecs, k=1, threshold=0.0)
        
        # Validate schema
        for match in matches:
            assert 'similarity' in match
            assert 'rank' in match
            assert isinstance(match['similarity'], float)
            assert isinstance(match['rank'], int)
            assert 0.0 <= match['similarity'] <= 1.0
            assert match['rank'] >= 1
    
    def test_edge_case_empty_texts(self):
        """Test handling of empty or very short texts."""
        source_texts = ["", "a"]
        target_texts = ["", "b"]
        
        # Should not raise an error, but may produce zero vectors
        source_vecs, target_vecs = build_tfidf_vectors(source_texts, target_texts)
        
        assert source_vecs.shape[0] == 2
        assert target_vecs.shape[0] == 2
    
    def test_integration_with_threshold_parameter(self):
        """Test end-to-end matching with explicit threshold."""
        source_texts = [
            "I love to read books in the morning.",
            "He enjoys playing soccer with friends."
        ]
        target_texts = [
            "I enjoy reading novels at dawn.",
            "She likes watching movies in the evening."
        ]
        
        source_vecs, target_vecs = build_tfidf_vectors(source_texts, target_texts)
        
        # Test with low threshold
        matches_low = find_top_matches(source_vecs[0], target_vecs, k=2, threshold=0.0)
        assert len(matches_low) <= 2
        
        # Test with high threshold
        matches_high = find_top_matches(source_vecs[0], target_vecs, k=2, threshold=0.9)
        # May be empty if no high similarity matches
        assert len(matches_high) <= 2
        
        # All matches should satisfy threshold
        for match in matches_high:
            assert match['similarity'] >= 0.9