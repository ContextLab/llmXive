import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

# Import the functions to test from the stats module
# Note: We assume stats.py exposes these names as per the API surface
from stats import (
    detect_divergence,
    run_permutation_test,
    run_mcnemar_test,
    run_ttest_token_usage,
    apply_bonferroni_correction,
    load_simulation_results
)

class TestDivergenceDetection:
    def test_no_divergence(self):
        """Test case where all trajectories are identical."""
        dynamic = [
            {'trajectory_id': 'T1', 'final_state': 'state_A', 'outcome': 'win'},
            {'trajectory_id': 'T2', 'final_state': 'state_B', 'outcome': 'loss'}
        ]
        static = [
            {'trajectory_id': 'T1', 'final_state': 'state_A', 'outcome': 'win'},
            {'trajectory_id': 'T2', 'final_state': 'state_B', 'outcome': 'loss'}
        ]
        
        result = detect_divergence(dynamic, static)
        
        assert result['is_divergent'] is False
        assert result['divergent_trajectory_ids'] == []
        assert result['total_pairs_checked'] == 2

    def test_partial_divergence(self):
        """Test case where some trajectories diverge."""
        dynamic = [
            {'trajectory_id': 'T1', 'final_state': 'state_A', 'outcome': 'win'},
            {'trajectory_id': 'T2', 'final_state': 'state_C', 'outcome': 'win'}  # Different
        ]
        static = [
            {'trajectory_id': 'T1', 'final_state': 'state_A', 'outcome': 'win'},
            {'trajectory_id': 'T2', 'final_state': 'state_B', 'outcome': 'loss'}
        ]
        
        result = detect_divergence(dynamic, static)
        
        assert result['is_divergent'] is True
        assert 'T2' in result['divergent_trajectory_ids']
        assert result['divergent_count'] == 1

    def test_missing_pair(self):
        """Test case where a trajectory is missing in one set."""
        dynamic = [
            {'trajectory_id': 'T1', 'final_state': 'state_A', 'outcome': 'win'},
            {'trajectory_id': 'T3', 'final_state': 'state_D', 'outcome': 'win'}  # Missing in static
        ]
        static = [
            {'trajectory_id': 'T1', 'final_state': 'state_A', 'outcome': 'win'}
        ]
        
        result = detect_divergence(dynamic, static)
        
        assert result['is_divergent'] is True
        assert 'T3' in result['divergent_trajectory_ids']

class TestMcNemarTest:
    def test_mcnemar_basic(self):
        """Test McNemar's test with basic contingency table."""
        # Table: [[both_win, dyn_win_static_lose], [dyn_lose_static_win, both_lose]]
        # Example: 10 both win, 5 dyn win static lose, 2 dyn lose static win, 3 both lose
        contingency = [[10, 5], [2, 3]]
        
        result = run_mcnemar_test(15, 20, 12, 17, contingency)
        
        assert 'p_value' in result
        assert result['test_type'] == 'mcnemar_test'
        assert result['b'] == 5
        assert result['c'] == 2

    def test_mcnemar_no_discordant(self):
        """Test McNemar's test with no discordant pairs."""
        contingency = [[10, 0], [0, 5]]
        
        result = run_mcnemar_test(10, 10, 5, 5, contingency)
        
        assert result['p_value'] == 1.0
        assert result['reason'] == 'No discordant pairs found'

class TestPermutationTest:
    def test_permutation_basic(self):
        """Test permutation test with small sample."""
        result = run_permutation_test(10, 20, 8, 20, n_permutations=100)
        
        assert 'p_value' in result
        assert 0.0 <= result['p_value'] <= 1.0
        assert result['test_type'] == 'permutation_test'

class TestTokenUsageTest:
    def test_ttest_token_usage(self):
        """Test t-test for token usage."""
        dynamic_tokens = [3000, 3200, 3100, 2900, 3050]
        static_tokens = [4000, 4100, 3900, 4050, 4000]
        
        result = run_ttest_token_usage(dynamic_tokens, static_tokens)
        
        assert 'p_value' in result
        assert 'test_type' in result
        assert 0.0 <= result['p_value'] <= 1.0

class TestBonferroniCorrection:
    def test_bonferroni_basic(self):
        """Test Bonferroni correction."""
        p_values = [0.01, 0.05, 0.001]
        adjusted = apply_bonferroni_correction(p_values, n_tests=3)
        
        assert len(adjusted) == 3
        assert adjusted[0] == 0.03  # 0.01 * 3
        assert adjusted[1] == 0.15  # 0.05 * 3
        assert adjusted[2] == 0.003 # 0.001 * 3
        
        # Check cap at 1.0
        p_values_high = [0.5, 0.6, 0.7]
        adjusted_high = apply_bonferroni_correction(p_values_high, n_tests=3)
        assert adjusted_high[2] == 1.0  # 2.1 capped to 1.0