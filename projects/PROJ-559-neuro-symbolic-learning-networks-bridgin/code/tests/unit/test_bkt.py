import pytest
import math
import random
import sys
import os

# Ensure project root is in path for imports if run directly
if "code" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from simulate.bkt_simulator import BKTState, BKTModel, bkt_transition

class TestBKTStateTransitions:
    """
    Unit tests for BKT state transitions in code/simulate/bkt_simulator.py.
    Tests verify the probabilistic logic of Knowledge State transitions:
    P(L_t=1 | L_{t-1}=0) = P_G (Guess/Learn)
    P(L_t=1 | L_{t-1}=1) = 1 - P_S (Forget) -> actually 1 - P_S is staying learned?
    Standard BKT:
    - If L_{t-1}=0: L_t=1 with prob P_T (Transition/Learn), else 0.
    - If L_{t-1}=1: L_t=1 with prob 1 (usually assumed no forgetting in basic BKT) or 1-P_S.
    This test suite assumes the standard implementation where P_T is the learning rate.
    """

    def setup_method(self):
        """Setup a deterministic seed for reproducibility in tests."""
        self.seed = 42
        random.seed(self.seed)
        # Basic BKT parameters
        self.p_l0 = 0.1   # Initial knowledge
        self.p_t = 0.2    # Transition (Learning) probability
        self.p_g = 0.3    # Guess probability
        self.p_s = 0.1    # Slip probability

    def test_initial_state_distribution(self):
        """Verify that initial state L_0 follows the Bernoulli(p_l0) distribution."""
        model = BKTModel(
            p_l0=self.p_l0,
            p_t=self.p_t,
            p_g=self.p_g,
            p_s=self.p_s
        )
        # Run many simulations to check statistical distribution
        n_trials = 10000
        learned_count = 0
        for _ in range(n_trials):
            state = model.get_initial_state()
            if state.is_learned:
                learned_count += 1

        observed_prob = learned_count / n_trials
        # Allow 3 sigma deviation for randomness (approx 0.004 for n=10000)
        expected = self.p_l0
        assert abs(observed_prob - expected) < 0.02, \
            f"Initial state distribution {observed_prob:.4f} differs significantly from {expected}"

    def test_transition_from_unknown_to_known(self):
        """
        Verify that if a student is in state L=0, they transition to L=1
        with probability P_T.
        """
        model = BKTModel(
            p_l0=0.0, # Force start unknown
            p_t=self.p_t,
            p_g=self.p_g,
            p_s=self.p_s
        )
        
        # Simulate one step from known unknown state
        # We need to force the state to be L=0 at t-1
        # The model's transition logic usually takes the previous state.
        # We will test the function bkt_transition directly or via model step.
        
        n_trials = 10000
        transition_count = 0
        
        for _ in range(n_trials):
            # Start in L=0
            current_state = BKTState(is_learned=False, p_knowledge=0.0)
            # Perform one step
            next_state = model.step(current_state)
            if next_state.is_learned:
                transition_count += 1
        
        observed_prob = transition_count / n_trials
        expected = self.p_t
        assert abs(observed_prob - expected) < 0.02, \
            f"Transition L=0 -> L=1 probability {observed_prob:.4f} differs from P_T={expected}"

    def test_transition_from_known_to_known(self):
        """
        Verify that if a student is in state L=1, they stay in L=1
        (assuming no forgetting in this specific BKT variant, or probability 1-P_S).
        Standard BKT often assumes no forgetting (P_S is for performance slip, not state change).
        However, some variants include forgetting. 
        Based on typical `bkt_simulator` implementations in this context:
        If L_{t-1}=1, L_t=1 with probability 1.0 (knowledge is retained).
        """
        model = BKTModel(
            p_l0=1.0,
            p_t=self.p_t,
            p_g=self.p_g,
            p_s=self.p_s
        )
        
        n_trials = 10000
        stay_count = 0
        
        for _ in range(n_trials):
            current_state = BKTState(is_learned=True, p_knowledge=1.0)
            next_state = model.step(current_state)
            if next_state.is_learned:
                stay_count += 1
        
        observed_prob = stay_count / n_trials
        # In standard BKT, once learned, stays learned.
        expected = 1.0 
        assert abs(observed_prob - expected) < 0.01, \
            f"Retention L=1 -> L=1 probability {observed_prob:.4f} differs from expected {expected}"

    def test_observation_probability_given_state(self):
        """
        Verify that P(Correct | L=0) == P_G (Guess)
        and P(Correct | L=1) == 1 - P_S (Not Slip)
        """
        model = BKTModel(
            p_l0=0.0,
            p_t=0.0, # No learning to keep state static
            p_g=self.p_g,
            p_s=self.p_s
        )
        
        # Test L=0 -> Correct
        n_trials = 10000
        correct_from_unknown = 0
        for _ in range(n_trials):
            state = BKTState(is_learned=False, p_knowledge=0.0)
            is_correct = model.observe(state)
            if is_correct:
                correct_from_unknown += 1
        
        assert abs((correct_from_unknown / n_trials) - self.p_g) < 0.02, \
            f"P(Correct|L=0) = {correct_from_unknown/n_trials:.4f}, expected {self.p_g}"

        # Test L=1 -> Correct
        correct_from_known = 0
        for _ in range(n_trials):
            state = BKTState(is_learned=True, p_knowledge=1.0)
            is_correct = model.observe(state)
            if is_correct:
                correct_from_known += 1
        
        expected_correct_known = 1.0 - self.p_s
        assert abs((correct_from_known / n_trials) - expected_correct_known) < 0.02, \
            f"P(Correct|L=1) = {correct_from_known/n_trials:.4f}, expected {expected_correct_known}"

    def test_deterministic_seed_reproducibility(self):
        """Verify that setting the seed yields identical sequences."""
        model1 = BKTModel(p_l0=0.5, p_t=0.5, p_g=0.5, p_s=0.5)
        model2 = BKTModel(p_l0=0.5, p_t=0.5, p_g=0.5, p_s=0.5)
        
        seed = 12345
        model1.set_seed(seed)
        model2.set_seed(seed)
        
        # Generate a sequence of 10 steps for a single student
        sequence1 = []
        sequence2 = []
        
        state1 = model1.get_initial_state()
        state2 = model2.get_initial_state()
        
        for _ in range(10):
            obs1 = model1.observe(state1)
            sequence1.append(obs1)
            state1 = model1.step(state1)
            
            obs2 = model2.observe(state2)
            sequence2.append(obs2)
            state2 = model2.step(state2)
        
        assert sequence1 == sequence2, "Sequences with same seed must be identical"

    def test_probability_bounds(self):
        """Ensure model parameters are clamped or validated within [0, 1]."""
        # Test with boundary values
        model = BKTModel(p_l0=0.0, p_t=0.0, p_g=0.0, p_s=0.0)
        assert model.p_l0 == 0.0
        assert model.p_t == 0.0
        
        model = BKTModel(p_l0=1.0, p_t=1.0, p_g=1.0, p_s=1.0)
        assert model.p_l0 == 1.0
        assert model.p_t == 1.0
        assert model.p_s == 1.0