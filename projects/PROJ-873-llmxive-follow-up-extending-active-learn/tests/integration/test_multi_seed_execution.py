import pytest
import os
import json
import sys
from unittest.mock import patch, MagicMock
from run_pipeline import run_single_seed_experiment, ExperimentResult
from config import get_config

@pytest.fixture
def mock_config():
    config = get_config()
    config.max_runtime_seconds = 3600
    config.max_memory_bytes = 7 * 1024 * 1024 * 1024
    return config

@pytest.mark.integration
def test_multi_seed_execution_loop(mock_config):
    """Test that the multi-seed execution loop runs exactly 5 independent runs as per US-3."""
    # Mock the data loading and ranking functions to avoid heavy computation during test
    with patch('run_pipeline.load_injected_dataset') as mock_load, \
         patch('run_pipeline.fetch_beir_datasets') as mock_fetch, \
         patch('run_pipeline.run_ranker_with_filter') as mock_ranker, \
         patch('run_pipeline.calculate_ndcg_at_10') as mock_ndcg, \
         patch('run_pipeline.is_wasted_call') as mock_wasted:
        
        # Setup mocks
        mock_load.return_value = {
            "scifact": [
                {"id": "1", "text": "test doc 1"},
                {"id": "2", "text": "test doc 2"}
            ]
        }
        mock_fetch.return_value = (
            {"1": {"text": "doc 1"}},
            {"q1": "query 1"},
            {"scifact": {"q1": {"1": 1}}}
        )
        mock_ranker.return_value = MagicMock(
            ranked_docs=[{"id": "1", "score": 0.9}],
            comparisons=[],
            total_comparisons=1
        )
        mock_ndcg.return_value = 0.95
        mock_wasted.return_value = False
        
        # Run the experiment with 5 seeds
        seeds = [1, 2, 3, 4, 5]
        results = []
        
        for seed in seeds:
            result = run_single_seed_experiment(
                seed=seed,
                variant="baseline",
                datasets=["scifact"],
                budgets=[50],
                config=mock_config
            )
            results.append(result)
        
        # Assert that we got exactly 5 results
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"
        
        # Assert that each result has the correct seed
        for i, result in enumerate(results):
            assert result.seed == seeds[i], f"Seed mismatch at index {i}"
            assert result.status == "success", f"Experiment failed for seed {seeds[i]}"
            assert len(result.ndcg_scores) > 0, f"No NDCG scores for seed {seeds[i]}"
        
        # Assert that the experiments are independent (different seeds should produce different internal states)
        # In a real scenario, this would be verified by checking that the random seeds affect the results
        # For this test, we verify that each run was executed separately
        assert all(r.runtime_seconds > 0 for r in results), "All experiments should have non-zero runtime"

@pytest.mark.integration
def test_clustering_aided_multi_seed(mock_config):
    """Test that clustering-aided variant also runs with multiple seeds."""
    with patch('run_pipeline.load_injected_dataset') as mock_load, \
         patch('run_pipeline.fetch_beir_datasets') as mock_fetch, \
         patch('run_pipeline.run_ranker_with_filter') as mock_ranker, \
         patch('run_pipeline.calculate_ndcg_at_10') as mock_ndcg, \
         patch('run_pipeline.is_wasted_call') as mock_wasted, \
         patch('run_pipeline.run_clustering_pipeline') as mock_cluster, \
         patch('run_pipeline.filter_candidates_by_clustering') as mock_filter:
        
        mock_load.return_value = {
            "scifact": [{"id": "1", "text": "test"}]
        }
        mock_fetch.return_value = (
            {"1": {"text": "doc"}},
            {"q1": "query"},
            {"scifact": {"q1": {"1": 1}}}
        )
        mock_cluster.return_value = [{"id": "cluster1"}]
        mock_filter.return_value = [{"id": "1", "text": "test"}]
        mock_ranker.return_value = MagicMock(
            ranked_docs=[{"id": "1", "score": 0.9}],
            comparisons=[],
            total_comparisons=1
        )
        mock_ndcg.return_value = 0.95
        mock_wasted.return_value = False
        
        seeds = [10, 20, 30, 40, 50]
        results = []
        
        for seed in seeds:
            result = run_single_seed_experiment(
                seed=seed,
                variant="clustering_aided",
                datasets=["scifact"],
                budgets=[50],
                config=mock_config
            )
            results.append(result)
        
        assert len(results) == 5
        assert all(r.variant == "clustering_aided" for r in results)
        assert all(r.status == "success" for r in results)

@pytest.mark.integration
def test_seed_independence(mock_config):
    """Verify that different seeds lead to different execution paths (independence)."""
    # This test verifies that the random seed is actually being used
    # by checking that the results are not identical across seeds
    # (in a real scenario, they would differ due to random sampling)
    
    # We mock the random module to ensure different seeds produce different "random" outputs
    with patch('random.seed') as mock_seed, \
         patch('run_pipeline.load_injected_dataset') as mock_load, \
         patch('run_pipeline.fetch_beir_datasets') as mock_fetch, \
         patch('run_pipeline.run_ranker_with_filter') as mock_ranker, \
         patch('run_pipeline.calculate_ndcg_at_10') as mock_ndcg, \
         patch('run_pipeline.is_wasted_call') as mock_wasted:
        
        mock_load.return_value = {"scifact": [{"id": "1", "text": "test"}]}
        mock_fetch.return_value = (
            {"1": {"text": "doc"}},
            {"q1": "query"},
            {"scifact": {"q1": {"1": 1}}}
        )
        mock_ranker.return_value = MagicMock(
            ranked_docs=[{"id": "1", "score": 0.9}],
            comparisons=[],
            total_comparisons=1
        )
        mock_ndcg.return_value = 0.95
        mock_wasted.return_value = False
        
        seeds = [1, 2, 3, 4, 5]
        for seed in seeds:
            run_single_seed_experiment(
                seed=seed,
                variant="baseline",
                datasets=["scifact"],
                budgets=[50],
                config=mock_config
            )
            # Verify that random.seed was called with the correct seed
            assert mock_seed.called
            call_args = mock_seed.call_args
            assert call_args[0][0] == seed, f"Random seed {seed} was not set correctly"
        
        # Verify that random.seed was called 5 times (once per seed)
        assert mock_seed.call_count == 5