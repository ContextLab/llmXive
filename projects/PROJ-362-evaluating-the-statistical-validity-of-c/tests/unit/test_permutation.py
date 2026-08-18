"""
Unit tests for permutation logic in code/permutation.py.
"""

import pytest
import random
from code.permutation import shuffle_relevance_labels, compute_permuted_scores, run_permutation_test

# Test data
SAMPLE_LABELS = [3, 2, 2, 1, 1, 0, 0, 0]
SAMPLE_QUERY_ID = 101


class TestShuffleRelevanceLabels:
    def test_shuffle_returns_new_list(self):
        """Verify shuffle returns a new list, not modifying original."""
        original = SAMPLE_LABELS.copy()
        shuffled = shuffle_relevance_labels(original)
        
        assert shuffled is not original
        assert shuffled == sorted(shuffled, reverse=False) # Just check it's a permutation
        assert original == SAMPLE_LABELS # Original unchanged

    def test_shuffle_preserves_elements(self):
        """Verify shuffled list contains exactly the same elements."""
        shuffled = shuffle_relevance_labels(SAMPLE_LABELS)
        assert sorted(shuffled) == sorted(SAMPLE_LABELS)

    def test_deterministic_with_seed(self):
        """Verify same seed produces same shuffle."""
        seed = 42
        shuffled1 = shuffle_relevance_labels(SAMPLE_LABELS, seed=seed)
        shuffled2 = shuffle_relevance_labels(SAMPLE_LABELS, seed=seed)
        
        assert shuffled1 == shuffled2

    def test_different_seeds_produce_different_results(self):
        """Verify different seeds usually produce different results."""
        # Note: theoretically possible to get same result, but extremely unlikely
        shuffled1 = shuffle_relevance_labels(SAMPLE_LABELS, seed=1)
        shuffled2 = shuffle_relevance_labels(SAMPLE_LABELS, seed=2)
        
        # We assert they are not equal to ensure randomness is working
        # If they happen to be equal (very rare), the test is still logically sound
        # but we expect them to differ.
        assert shuffled1 != shuffled2, "Different seeds produced identical shuffles (unexpected)"


class TestComputePermutedScores:
    def test_returns_list_of_scores(self):
        """Verify function returns a list of floats."""
        scores, count = compute_permuted_scores(
            SAMPLE_QUERY_ID, 
            SAMPLE_LABELS, 
            lambda x: sum(x), # Dummy metric
            num_permutations=5
        )
        assert isinstance(scores, list)
        assert len(scores) == 5
        assert all(isinstance(s, float) or isinstance(s, int) for s in scores)

    def test_actual_count_matches_target(self):
        """Verify N_actual equals num_permutations when successful."""
        scores, count = compute_permuted_scores(
            SAMPLE_QUERY_ID,
            SAMPLE_LABELS,
            lambda x: sum(x),
            num_permutations=10
        )
        assert count == 10

    def test_deterministic_with_seed(self):
        """Verify same seed produces same scores."""
        seed = 123
        scores1, _ = compute_permuted_scores(
            SAMPLE_QUERY_ID,
            SAMPLE_LABELS,
            lambda x: sum(x),
            num_permutations=5,
            seed=seed
        )
        scores2, _ = compute_permuted_scores(
            SAMPLE_QUERY_ID,
            SAMPLE_LABELS,
            lambda x: sum(x),
            num_permutations=5,
            seed=seed
        )
        assert scores1 == scores2


class TestRunPermutationTest:
    def test_ndcg_metric(self):
        """Test run_permutation_test with NDCG@10."""
        # Use a simple metric function that mimics ndcg behavior for testing
        # We can't easily test the exact ndcg value without full implementation context here
        # but we test the structure and N_actual logging
        result = run_permutation_test(
            query_id=SAMPLE_QUERY_ID,
            relevance_labels=SAMPLE_LABELS,
            metric_name='ndcg@10',
            num_permutations=5,
            seed=42
        )
        
        assert 'query_id' in result
        assert 'metric' in result
        assert 'null_distribution' in result
        assert 'N_actual' in result
        assert result['query_id'] == SAMPLE_QUERY_ID
        assert result['metric'] == 'ndcg@10'
        assert len(result['null_distribution']) == result['N_actual']
        assert result['N_actual'] == 5

    def test_map_metric(self):
        """Test run_permutation_test with MAP."""
        result = run_permutation_test(
            query_id=SAMPLE_QUERY_ID,
            relevance_labels=SAMPLE_LABELS,
            metric_name='map',
            num_permutations=5,
            seed=42
        )
        
        assert result['metric'] == 'map'
        assert len(result['null_distribution']) == 5
        assert result['N_actual'] == 5

    def test_invalid_metric(self):
        """Test that invalid metric raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported metric"):
            run_permutation_test(
                query_id=SAMPLE_QUERY_ID,
                relevance_labels=SAMPLE_LABELS,
                metric_name='invalid_metric',
                num_permutations=5
            )
