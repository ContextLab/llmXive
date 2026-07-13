import pytest
import math
import random
import sys
import os
from simulate.bkt_simulator import BKTState, BKTModel, bkt_transition

class TestBKTStateTransitions:
    """Unit tests for BKT state transitions ensuring deterministic behavior."""

    def setup_method(self):
        """Setup test fixtures with deterministic seeds."""
        random.seed(42)
        # Standard BKT parameters: P(L0), P(T), P(S), P(G)
        self.params = {
            'p_l0': 0.0,  # Initial knowledge
            'p_t': 0.01,  # Transition probability (learning)
            'p_s': 0.1,   # Slip probability
            'p_g': 0.3    # Guess probability
        }
        self.model = BKTModel(
            p_l0=self.params['p_l0'],
            p_t=self.params['p_t'],
            p_s=self.params['p_s'],
            p_g=self.params['p_g']
        )

    def test_initial_state(self):
        """Verify model starts in state L0 (unknown)."""
        assert self.model.state == BKTState.L0
        assert self.model.knowledge_level == 0.0

    def test_state_transition_known_to_unknown_impossible(self):
        """Verify that once learned (L1), state cannot revert to L0."""
        # Manually set to L1
        self.model.state = BKTState.L1
        self.model.knowledge_level = 1.0
        
        # Simulate a step with a correct answer
        # In L1, correct answer keeps us in L1
        next_state, obs = self.model.step(correct=True)
        
        # Should remain in L1 (absorbing state for knowledge)
        assert next_state == BKTState.L1
        assert self.model.state == BKTState.L1

    def test_learning_transition_l0_to_l1(self):
        """Test transition from L0 to L1 given learning probability."""
        # Start in L0
        self.model.state = BKTState.L0
        self.model.knowledge_level = self.params['p_l0']
        
        # Simulate multiple steps to trigger learning transition
        # Since p_t is small (0.01), we need to check the logic
        # We will force a transition by checking the internal logic or
        # running a deterministic sequence if the random seed allows.
        
        # For this unit test, we verify the logic by checking the transition
        # probability calculation directly if accessible, or by simulating
        # a known path.
        
        # Reset to L0
        self.model.state = BKTState.L0
        self.model.knowledge_level = self.params['p_l0']
        
        # We will test the bkt_transition function directly for logic verification
        # because stochastic simulation might not trigger the transition in one run.
        # However, the model.step() should use this logic.
        
        # Let's verify the state change logic:
        # If in L0, and we "learn" (prob p_t), we move to L1.
        # We can't easily force this without mocking random, so we test the
        # resulting state distribution or the logic of the step function.
        
        # Instead, let's test the deterministic case: if p_t is high.
        high_t_model = BKTModel(p_l0=0.0, p_t=1.0, p_s=0.0, p_g=0.0)
        high_t_model.state = BKTState.L0
        high_t_model.knowledge_level = 0.0
        
        # With p_t=1.0, next step MUST transition to L1
        next_state, obs = high_t_model.step(correct=True)
        assert next_state == BKTState.L1, "Should transition to L1 with p_t=1.0"
        assert high_t_model.state == BKTState.L1

    def test_slip_in_l1(self):
        """Test that a slip (wrong answer) in L1 results in observation 'wrong' but state remains L1."""
        self.model.state = BKTState.L1
        self.model.knowledge_level = 1.0
        
        # Force a slip by setting p_s=1.0 for this specific test instance
        slip_model = BKTModel(p_l0=0.0, p_t=0.0, p_s=1.0, p_g=0.0)
        slip_model.state = BKTState.L1
        slip_model.knowledge_level = 1.0
        
        next_state, obs = slip_model.step(correct=True) # Correct answer requested, but slip occurs
        
        # State should remain L1 (knowledge is not lost)
        assert next_state == BKTState.L1
        # Observation should be wrong due to slip
        assert obs == False

    def test_guess_in_l0(self):
        """Test that a guess in L0 results in observation 'correct' but state remains L0."""
        self.model.state = BKTState.L0
        self.model.knowledge_level = 0.0
        
        # Force a guess by setting p_g=1.0
        guess_model = BKTModel(p_l0=0.0, p_t=0.0, p_s=0.0, p_g=1.0)
        guess_model.state = BKTState.L0
        guess_model.knowledge_level = 0.0
        
        next_state, obs = guess_model.step(correct=True)
        
        # State should remain L0 (no learning yet)
        assert next_state == BKTState.L0
        # Observation should be correct due to guess
        assert obs == True

    def test_knowledge_level_update(self):
        """Verify knowledge level increases upon transition to L1."""
        model = BKTModel(p_l0=0.0, p_t=1.0, p_s=0.0, p_g=0.0)
        model.state = BKTState.L0
        model.knowledge_level = 0.0
        
        assert model.knowledge_level == 0.0
        
        model.step(correct=True)
        
        # After transition to L1, knowledge level should be 1.0
        assert model.state == BKTState.L1
        assert model.knowledge_level == 1.0

    def test_bkt_transition_logic(self):
        """Direct test of the bkt_transition function logic."""
        # Test L0 -> L1 transition logic
        # If current state is L0, and learning occurs, next is L1
        # We simulate the probability check logic
        
        # Case 1: In L0, learning occurs (random < p_t)
        # Since we can't easily control random here without mocking,
        # we rely on the high p_t test above.
        
        # Case 2: In L1, state stays L1
        result = bkt_transition(BKTState.L1, 0.01)
        assert result == BKTState.L1, "L1 is an absorbing state for knowledge"

    def test_deterministic_seed(self):
        """Verify that same seed produces same sequence of states."""
        seed = 12345
        random.seed(seed)
        model1 = BKTModel(p_l0=0.1, p_t=0.5, p_s=0.1, p_g=0.1)
        
        random.seed(seed)
        model2 = BKTModel(p_l0=0.1, p_t=0.5, p_s=0.1, p_g=0.1)
        
        # Run 10 steps
        for i in range(10):
            s1, o1 = model1.step(correct=True)
            s2, o2 = model2.step(correct=True)
            
            assert s1 == s2, f"State mismatch at step {i}"
            assert o1 == o2, f"Observation mismatch at step {i}"

    def test_observation_probability_in_l0(self):
        """Test observation probability in L0 is P(G)."""
        # If p_g is 0.5, and we run many trials, approx 50% should be correct
        # But for a unit test, we test the logic with p_g=1.0 and p_g=0.0
        
        model_no_guess = BKTModel(p_l0=0.0, p_t=0.0, p_s=0.0, p_g=0.0)
        model_no_guess.state = BKTState.L0
        obs_0, _ = model_no_guess.step(correct=True)
        assert obs_0 == False, "With p_g=0, should always be wrong in L0"
        
        model_yes_guess = BKTModel(p_l0=0.0, p_t=0.0, p_s=0.0, p_g=1.0)
        model_yes_guess.state = BKTState.L0
        obs_1, _ = model_yes_guess.step(correct=True)
        assert obs_1 == True, "With p_g=1, should always be correct in L0"

    def test_observation_probability_in_l1(self):
        """Test observation probability in L1 is 1-P(S)."""
        model_no_slip = BKTModel(p_l0=0.0, p_t=0.0, p_s=0.0, p_g=0.0)
        model_no_slip.state = BKTState.L1
        obs_0, _ = model_no_slip.step(correct=True)
        assert obs_0 == True, "With p_s=0, should always be correct in L1"
        
        model_yes_slip = BKTModel(p_l0=0.0, p_t=0.0, p_s=1.0, p_g=0.0)
        model_yes_slip.state = BKTState.L1
        obs_1, _ = model_yes_slip.step(correct=True)
        assert obs_1 == False, "With p_s=1, should always be wrong in L1"

    def test_state_enum_values(self):
        """Ensure BKTState enum values are as expected."""
        assert BKTState.L0.value == 0
        assert BKTState.L1.value == 1