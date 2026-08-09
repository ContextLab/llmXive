import pytest
import numpy as np
from matching import find_top_matches, build_tfidf_vectors, apply_sensitivity_analysis
import logging

# Set up logging for tests
logging.basicConfig(level=logging.INFO)

class TestFindTopMatches:
    """Test deterministic tie-breaking rule for multiple matches."""

    def test_basic_top_k(self):
        """Test basic functionality of finding top k matches."""
        # Create a simple query vector
        query = np.array([1.0, 0.0, 0.0])
        
        # Create candidate vectors with varying similarities
        candidates = np.array([
            [0.9, 0.1, 0.0],  # High similarity
            [0.5, 0.4, 0.1],  # Medium similarity
            [0.2, 0.3, 0.5],  # Low similarity
        ])
        
        story_ids = ['story_a', 'story_b', 'story_c']
        
        matches = find_top_matches(query, candidates, k=2, story_ids=story_ids)
        
        assert len(matches) == 2
        assert matches[0]['story_id'] == 'story_a'
        assert matches[0]['rank'] == 1
        assert matches[1]['story_id'] == 'story_b'
        assert matches[1]['rank'] == 2

    def test_deterministic_tie_breaking(self):
        """Test that ties are broken deterministically by highest raw score (first in list)."""
        # Create a query vector
        query = np.array([1.0, 0.0, 0.0])
        
        # Create candidate vectors with EXACTLY the same similarity to query
        # This creates a tie situation
        candidates = np.array([
            [0.8, 0.2, 0.0],  # Same similarity as below
            [0.8, 0.2, 0.0],  # Same similarity as above
            [0.8, 0.2, 0.0],  # Same similarity as above
        ])
        
        story_ids = ['first_story', 'second_story', 'third_story']
        
        matches = find_top_matches(query, candidates, k=3, story_ids=story_ids)
        
        # With deterministic tie-breaking, the first item in the list should be ranked first
        # because it has the lowest index among tied items
        assert len(matches) == 3
        assert matches[0]['story_id'] == 'first_story'
        assert matches[0]['rank'] == 1
        assert matches[1]['story_id'] == 'second_story'
        assert matches[1]['rank'] == 2
        assert matches[2]['story_id'] == 'third_story'
        assert matches[2]['rank'] == 3

    def test_partial_tie_breaking(self):
        """Test tie-breaking when only some items are tied."""
        query = np.array([1.0, 0.0, 0.0])
        
        # Create candidates where first two have same similarity, third is different
        candidates = np.array([
            [0.9, 0.1, 0.0],  # High similarity
            [0.9, 0.1, 0.0],  # Same as above - tie
            [0.5, 0.4, 0.1],  # Lower similarity
        ])
        
        story_ids = ['high_a', 'high_b', 'low']
        
        matches = find_top_matches(query, candidates, k=3, story_ids=story_ids)
        
        # First two should be tied and ordered by index
        assert matches[0]['story_id'] == 'high_a'
        assert matches[0]['rank'] == 1
        assert matches[1]['story_id'] == 'high_b'
        assert matches[1]['rank'] == 2
        assert matches[2]['story_id'] == 'low'
        assert matches[2]['rank'] == 3

    def test_empty_candidates(self):
        """Test handling of empty candidate list."""
        query = np.array([1.0, 0.0, 0.0])
        candidates = np.array([]).reshape(0, 3)
        
        matches = find_top_matches(query, candidates, k=3)
        
        assert len(matches) == 0

    def test_k_larger_than_candidates(self):
        """Test when k is larger than number of candidates."""
        query = np.array([1.0, 0.0, 0.0])
        candidates = np.array([
            [0.9, 0.1, 0.0],
            [0.5, 0.4, 0.1],
        ])
        story_ids = ['story_a', 'story_b']
        
        matches = find_top_matches(query, candidates, k=5, story_ids=story_ids)
        
        # Should return only available matches
        assert len(matches) == 2
        assert matches[0]['rank'] == 1
        assert matches[1]['rank'] == 2

class TestBuildTfidfVectors:
    """Test TF-IDF vector construction excluding pronouns."""

    def test_exclude_pronouns(self):
        """Test that pronouns are excluded from TF-IDF vectors."""
        stories = [
            {'story_id': '1', 'text': 'I went to the store and I bought milk'},
            {'story_id': '2', 'text': 'She went to the store and she bought bread'},
        ]
        
        story_ids, vectors, vectorizer = build_tfidf_vectors(stories, exclude_pronouns=True)
        
        assert len(story_ids) == 2
        assert vectors.shape[0] == 2
        
        # Check that pronouns are not in the vocabulary
        feature_names = vectorizer.get_feature_names_out()
        pronouns = ['i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours', 
                   'you', 'your', 'yours', 'he', 'him', 'his', 'she', 'her', 'hers']
        
        for pronoun in pronouns:
            assert pronoun not in feature_names, f"Pronoun '{pronoun}' should be excluded"

    def test_include_pronouns(self):
        """Test that pronouns are included when exclude_pronouns=False."""
        stories = [
            {'story_id': '1', 'text': 'I went to the store'},
        ]
        
        story_ids, vectors, vectorizer = build_tfidf_vectors(stories, exclude_pronouns=False)
        
        feature_names = vectorizer.get_feature_names_out()
        assert 'i' in feature_names

class TestSensitivityAnalysis:
    """Test sensitivity analysis functionality."""

    def test_sensitivity_analysis_structure(self):
        """Test that sensitivity analysis returns correct structure."""
        thresholds = [0.25, 0.30, 0.35]
        
        # Create dummy data
        query_vectors = np.array([[1.0, 0.0, 0.0]])
        candidate_vectors = np.array([[0.9, 0.1, 0.0], [0.5, 0.4, 0.1]])
        story_ids = ['a', 'b']
        
        results = apply_sensitivity_analysis(
            thresholds=thresholds,
            query_vectors=query_vectors,
            candidate_vectors=candidate_vectors,
            story_ids=story_ids
        )
        
        assert 'thresholds' in results
        assert 'results' in results
        assert 'summary' in results
        assert len(results['results']) == len(thresholds)
        assert all('threshold' in r and 'sample_size' in r for r in results['results'])
        assert 'is_significant' in results['summary']

    def test_sensitivity_analysis_with_no_matches(self):
        """Test sensitivity analysis when no matches exceed threshold."""
        thresholds = [0.95, 0.99]  # Very high thresholds
        
        query_vectors = np.array([[1.0, 0.0, 0.0]])
        candidate_vectors = np.array([[0.5, 0.4, 0.1]])  # Low similarity
        story_ids = ['a']
        
        results = apply_sensitivity_analysis(
            thresholds=thresholds,
            query_vectors=query_vectors,
            candidate_vectors=candidate_vectors,
            story_ids=story_ids
        )
        
        # All sample sizes should be 0
        for r in results['results']:
            assert r['sample_size'] == 0