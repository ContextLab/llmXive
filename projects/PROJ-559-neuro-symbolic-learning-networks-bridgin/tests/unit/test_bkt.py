import pytest
import math
import random
import sys
import os
from simulate.bkt_simulator import BKTState, BKTModel, bkt_transition, BKTSimulator
from utils.config import set_seeds

class TestBKTStateTransitions:
    """
    Unit tests for BKT state transitions.
    Validates the core logic of the Bayesian Knowledge Tracing model.
    """

    def setup_method(self):
        """Set up test fixtures."""
        set_seeds(42)
        self.model = BKTModel()
        
    def test_initial_state(self):
        """Test that initial state is correctly set."""
        state = BKTState(skill_id="test", L0=0.1, P=0.3, S=0.1, G=0.2)
        assert state.skill_id == "test"
        assert state.L0 == 0.1
        assert state.trial_count == 0
        assert state.last_correct is None

    def test_learning_transition_l0_to_l1(self):
        """
        Test that a correct response increases knowledge probability.
        Specifically: P(L|Correct) > L0 when P, S, G are reasonable.
        """
        state = BKTState(skill_id="math", L0=0.1, P=0.3, S=0.1, G=0.2)
        
        # Simulate a correct response
        new_state, posterior = bkt_transition(state, correct=True)
        
        # Posterior should be higher than prior L0
        # P(L|C) = (L0 * (1-S)) / (L0*(1-S) + (1-L0)*G)
        #        = (0.1 * 0.9) / (0.1*0.9 + 0.9*0.2)
        #        = 0.09 / (0.09 + 0.18) = 0.09 / 0.27 = 0.333...
        expected_posterior = (0.1 * 0.9) / (0.1 * 0.9 + 0.9 * 0.2)
        
        assert math.isclose(posterior, expected_posterior, rel_tol=1e-5)
        assert new_state.trial_count == 1
        assert new_state.last_correct is True
        # The next knowledge probability should be higher than L0
        assert new_state.current_knowledge > state.L0

    def test_forgetting_slip(self):
        """
        Test that a slip (correct knowledge, incorrect response) lowers confidence.
        """
        state = BKTState(skill_id="math", L0=0.9, P=0.1, S=0.1, G=0.1)
        # Force state to be "known"
        state.current_knowledge = 0.95 
        
        new_state, posterior = bkt_transition(state, correct=False)
        
        # Posterior should be lower than prior
        assert posterior < state.current_knowledge
        assert new_state.last_correct is False

    def test_deterministic_seed_support(self):
        """
        Test that the simulator produces identical results with the same seed.
        Addresses Von Neumann's stability concern.
        """
        seed = 12345
        skill = "test_skill"
        
        # First run
        set_seeds(seed)
        sim1 = BKTSimulator(BKTModel(), seed=seed)
        logs1 = sim1.simulate_student(skill, num_trials=5)
        
        # Second run with same seed
        set_seeds(seed)
        sim2 = BKTSimulator(BKTModel(), seed=seed)
        logs2 = sim2.simulate_student(skill, num_trials=5)
        
        # Compare logs
        assert len(logs1) == len(logs2)
        for l1, l2 in zip(logs1, logs2):
            assert l1['correct'] == l2['correct']
            assert math.isclose(l1['posterior_probability'], l2['posterior_probability'])

    def test_boundary_conditions(self):
        """Test edge cases: S=0, G=0, P=1."""
        # Perfect learning, no slip, no guess
        state = BKTState(skill_id="perfect", L0=0.0, P=1.0, S=0.0, G=0.0)
        
        # First trial: must guess (G=0) -> incorrect
        new_state, posterior = bkt_transition(state, correct=False)
        assert posterior == 0.0 # Can't know if incorrect and G=0
        
        # Second trial: must guess again? No, P=1 means if they tried they learn.
        # But if they don't know, they guess. G=0 -> always wrong.
        # So they never learn? 
        # Wait: P(L_{t+1}) = P(L_t|O_t) + (1-P(L_t|O_t))*P
        # If P=1, then next state becomes 1.0 immediately after the first update.
        # But to get correct, they need to know. If G=0, they can't get correct without knowing.
        # If L0=0, they start not knowing. G=0 -> incorrect. Posterior=0.
        # Next L = 0 + (1-0)*1 = 1.0.
        # So on next trial, they know.
        
        assert new_state.current_knowledge == 1.0 # Next trial they know

    def test_invalid_probabilities(self):
        """Test behavior with invalid probabilities (should handle gracefully or raise)."""
        # We don't strictly validate in the simulator to allow flexibility,
        # but we ensure no NaN/Inf results.
        state = BKTState(skill_id="bad", L0=1.5, P=0.5, S=0.5, G=0.5)
        new_state, posterior = bkt_transition(state, correct=True)
        # Should produce a valid float, even if inputs were weird
        assert math.isfinite(posterior)
        assert math.isfinite(new_state.current_knowledge)
