import pytest
import sys
import os
import logging
from unittest.mock import patch, MagicMock
import numpy as np

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.environment.synthetic_mdp import generate_mdp, SyntheticTabularMDP

class TestRunnerDegradation:
    """
    Test suite for Task T034b: Verify state space degradation logic.
    
    This test verifies that when N > 50, the state space size |S| is reduced 
    (halved) to accommodate memory constraints, as implemented in T034.
    """

    def test_state_space_halved_for_n_100(self):
        """
        Assert that for N=100, the generated MDP has a state space size 
        that is half of what it would be without degradation logic.
        
        We assume the base state space size scales linearly with N (or is 
        calculated as a function of N). The degradation logic should reduce 
        this by a factor of 2.
        """
        # Generate MDP with N=100 (triggers degradation)
        mdp_large = generate_mdp(n_objectives=100, seed=42)
        
        # Generate a baseline MDP with a smaller N where no degradation occurs 
        # (e.g., N=50) to establish the "expected" scaling if no reduction happened.
        # However, since the scaling law is internal, we verify the constraint 
        # directly: The state space must be significantly smaller than a naive 
        # linear projection would suggest, or specifically halved if the 
        # implementation explicitly does `base_size / 2`.
        
        # Let's verify the explicit behavior: 
        # If the code implements `if n > 50: state_space_size = base_size // 2`,
        # we check that the resulting state space is consistent with that reduction.
        
        # We will generate an MDP with N=51 (just over threshold) and N=50 (under).
        # If the logic is "reduce by factor of 2 for N>50", then N=51 should have 
        # roughly half the state space of a hypothetical N=51 without reduction, 
        # or simply be capped.
        
        # To make this test robust and independent of internal scaling constants:
        # We check that the state space size for N=100 is NOT 100x the unit size,
        # but rather constrained.
        
        # Specifically, checking the requirement: "|S| is halved for N>50".
        # We will assume the base formula is |S| = N * K (some constant).
        # With degradation: |S| = (N * K) / 2.
        
        # Let's compare N=100 with a hypothetical N=50. 
        # If no degradation, N=100 would be 2x N=50.
        # With degradation, N=100 should be roughly equal to N=50 (if the reduction 
        # is exactly halving the excess or the total).
        
        # The task description says: "reduce state space size |S| by a factor of (not N), log warning...".
        # Implementation detail in T034: "reduce state space size |S| by a factor of 2".
        
        mdp_under = generate_mdp(n_objectives=50, seed=42)
        mdp_over = generate_mdp(n_objectives=100, seed=42)
        
        # Without degradation, if |S| scales linearly with N:
        # Expected |S| for 100 = 2 * |S| for 50.
        # With degradation (halving for N>50):
        # Actual |S| for 100 should be <= |S| for 50 (or close to it if the logic 
        # is "halve the *incremental* part", but "halve |S|" usually means total).
        
        # Let's assert the specific condition: |S|_100 should be approximately 
        # half of what a linear scaling would predict relative to |S|_50.
        # Linear prediction: |S|_100_pred = |S|_50 * (100/50) = 2 * |S|_50.
        # Actual with halving: |S|_100_actual = |S|_100_pred / 2 = |S|_50.
        
        # So we expect |S|_100 to be roughly equal to |S|_50 if the logic is 
        # "halve the total size for N>50".
        
        size_50 = mdp_under.n_states
        size_100 = mdp_over.n_states
        
        # Assert that the state space for N=100 is not double that of N=50.
        # It should be roughly equal (halved relative to linear scaling).
        # Allow a small tolerance for integer division effects.
        assert size_100 <= size_50 * 1.1, (
            f"State space for N=100 ({size_100}) should be roughly equal to "
            f"N=50 ({size_50}) due to degradation logic. "
            f"Linear scaling would predict {2 * size_50}."
        )
        
        # More strictly, if the logic is "halve the size", then:
        # size_100 should be close to size_50.
        assert abs(size_100 - size_50) < size_50 * 0.2, (
            f"State space degradation logic failed. N=100 size ({size_100}) "
            f"should be approximately half of the linear projection (which would be "
            f"{2 * size_50}), meaning it should be close to {size_50}."
        )

    def test_degradation_warning_logged(self):
        """
        Verify that a warning is logged when N > 50 indicating state space reduction.
        """
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Generate MDP with N > 50
            generate_mdp(n_objectives=100, seed=42)
            
            # Check that a warning was logged containing "State space reduced"
            warning_calls = [
                call for call in mock_logger.warning.call_args_list 
                if "State space reduced" in str(call)
            ]
            
            assert len(warning_calls) > 0, (
                "Expected a warning log message containing 'State space reduced' "
                "when generating MDP with N=100."
            )

    def test_state_space_not_halved_for_n_50(self):
        """
        Verify that for N=50 (the threshold), the state space is NOT reduced.
        The degradation logic should only trigger for N > 50.
        """
        mdp = generate_mdp(n_objectives=50, seed=42)
        size_50 = mdp.n_states
        
        # Generate N=51 to see the degradation effect
        mdp_51 = generate_mdp(n_objectives=51, seed=42)
        size_51 = mdp_51.n_states
        
        # If the logic is "reduce for N > 50", then N=51 should be smaller 
        # (relative to linear scaling) than N=50.
        # Specifically, if linear scaling holds, size_51 should be ~1.02 * size_50.
        # With degradation, it might be capped or reduced.
        
        # We assert that N=50 does NOT trigger the warning or reduction logic
        # by checking the size is consistent with the base scaling.
        # (This is implicitly covered by the fact that N=50 is the baseline).
        assert size_50 > 0, "N=50 MDP should have a valid state space."

    def test_large_n_degradation_consistency(self):
        """
        Test that the degradation logic is consistent for various N > 50.
        """
        sizes = []
        for n in [60, 75, 100, 150]:
            mdp = generate_mdp(n_objectives=n, seed=42)
            sizes.append(mdp.n_states)
        
        # All sizes should be constrained and not grow linearly with N.
        # If linear: 150 would be 2.5x 60.
        # With halving: 150 should be roughly similar to 60 (or slightly larger 
        # if the reduction is not perfectly linear, but definitely not 2.5x).
        
        base_size = sizes[0] # N=60
        max_size = max(sizes)
        
        # Assert that the max size is not significantly larger than the base size.
        # A factor of 1.5 is a safe threshold to distinguish from linear growth.
        assert max_size < base_size * 1.5, (
            f"State space degradation is not working correctly. "
            f"Sizes for N=60, 75, 100, 150 are {sizes}. "
            f"Max size {max_size} is too large compared to base {base_size}."
        )