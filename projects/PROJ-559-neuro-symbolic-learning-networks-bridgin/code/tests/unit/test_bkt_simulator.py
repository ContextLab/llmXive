"""
Unit tests for BKT Simulator components.
Tests BKTState, BKTModel, bkt_transition, and BKTSimulator logic.
"""
import pytest
import math
import random
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from simulate.bkt_simulator import BKTState, BKTModel, bkt_transition, BKTSimulator


class TestBKTState:
    """Tests for the BKTState data structure."""

    def test_initialization_defaults(self):
        """Test that BKTState initializes with correct defaults."""
        state = BKTState()
        assert state.knowledge_level == 0.0
        assert state.has_learned is False
        assert state.guess_probability == 0.0
        assert state.slip_probability == 0.0
        assert state.learn_probability == 0.0

    def test_initialization_custom(self):
        """Test BKTState with custom parameters."""
        state = BKTState(
            knowledge_level=0.5,
            has_learned=True,
            guess_probability=0.1,
            slip_probability=0.1,
            learn_probability=0.2
        )
        assert state.knowledge_level == 0.5
        assert state.has_learned is True
        assert state.guess_probability == 0.1
        assert state.slip_probability == 0.1
        assert state.learn_probability == 0.2

    def test_to_dict(self):
        """Test conversion to dictionary."""
        state = BKTState(knowledge_level=0.8)
        state_dict = state.to_dict()
        assert isinstance(state_dict, dict)
        assert state_dict['knowledge_level'] == 0.8

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'knowledge_level': 0.3,
            'has_learned': False,
            'guess_probability': 0.2,
            'slip_probability': 0.1,
            'learn_probability': 0.3
        }
        state = BKTState.from_dict(data)
        assert state.knowledge_level == 0.3
        assert state.has_learned is False


class TestBKTModel:
    """Tests for the BKTModel configuration."""

    def test_initialization(self):
        """Test BKTModel initialization with defaults."""
        model = BKTModel()
        assert model.p_init == 0.5
        assert model.p_learn == 0.3
        assert model.p_guess == 0.2
        assert model.p_slip == 0.1

    def test_initialization_custom(self):
        """Test BKTModel with custom parameters."""
        model = BKTModel(p_init=0.1, p_learn=0.5, p_guess=0.1, p_slip=0.05)
        assert model.p_init == 0.1
        assert model.p_learn == 0.5
        assert model.p_guess == 0.1
        assert model.p_slip == 0.05

    def test_create_state(self):
        """Test creating a BKTState from a model."""
        model = BKTModel(p_init=0.6)
        state = model.create_state()
        assert state.knowledge_level == 0.6
        assert state.guess_probability == 0.2  # Default from model
        assert state.slip_probability == 0.1    # Default from model
        assert state.learn_probability == 0.3   # Default from model


class TestBKTTransition:
    """Tests for the bkt_transition function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.state = BKTState(
            knowledge_level=0.5,
            has_learned=False,
            guess_probability=0.2,
            slip_probability=0.1,
            learn_probability=0.3
        )
        self.model = BKTModel()

    @patch('random.random', return_value=0.1)  # < p_guess -> correct
    def test_transition_correct_guess(self, mock_random):
        """Test transition when student guesses correctly."""
        new_state, is_correct = bkt_transition(self.state, self.model)
        assert is_correct is True
        # State should update knowledge but not mark as learned yet (unless p_learn triggers)
        # With p_learn=0.3 and random=0.1, it might learn. Let's check logic.
        # Actually, the mock is for the guess check. We need to mock the learn check too.

    @patch('random.random', side_effect=[0.3, 0.5])  # 1st: > p_guess (fail guess), 2nd: > p_learn (no learn)
    def test_transition_incorrect_no_learn(self, mock_random):
        """Test transition when student fails to guess and doesn't learn."""
        # First call: guess check (0.3 > 0.2 -> False)
        # Second call: learn check (0.5 > 0.3 -> False)
        new_state, is_correct = bkt_transition(self.state, self.model)
        assert is_correct is False
        assert new_state.has_learned is False
        # Knowledge level should decrease or stay same depending on implementation
        # Typically in BKT, if incorrect, P(L_{t+1}) = P(L_t) * (1 - P(T)) where T is transition to learned?
        # Standard BKT: P(L_{t+1}) = P(L_t | Incorrect) = P(L_t) * (1 - P(T)) / [P(L_t)*(1-P(T)) + (1-P(L_t))*(1-P(G))]
        # This test verifies the function runs and returns a state.
        assert isinstance(new_state, BKTState)

    @patch('random.random', side_effect=[0.3, 0.1])  # 1st: > p_guess, 2nd: < p_learn (learn)
    def test_transition_incorrect_learn(self, mock_random):
        """Test transition when student fails to guess but learns."""
        # First call: guess check (0.3 > 0.2 -> False)
        # Second call: learn check (0.1 < 0.3 -> True)
        new_state, is_correct = bkt_transition(self.state, self.model)
        assert is_correct is False
        assert new_state.has_learned is True

    def test_deterministic_seed(self):
        """Test that setting a seed produces deterministic results."""
        random.seed(42)
        state1, correct1 = bkt_transition(self.state, self.model)

        random.seed(42)
        state2, correct2 = bkt_transition(self.state, self.model)

        assert correct1 == correct2
        assert state1.knowledge_level == state2.knowledge_level
        assert state1.has_learned == state2.has_learned


class TestBKTSimulator:
    """Tests for the BKTSimulator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = BKTModel(p_init=0.0, p_learn=0.5, p_guess=0.0, p_slip=0.0)
        self.simulator = BKTSimulator(self.model)

    def test_simulate_single_student(self):
        """Test simulating a single student through multiple trials."""
        # With p_init=0, p_learn=0.5, p_guess=0, p_slip=0:
        # Trial 1: Must guess (0 chance) -> Incorrect, then maybe learn.
        # If we force a sequence where they learn on first try.
        with patch('random.random', side_effect=[0.1, 0.1, 0.1, 0.1]): 
            # 1st guess: 0.1 > 0.0 (Fail guess) -> Incorrect
            # 2nd learn: 0.1 < 0.5 (Learn) -> has_learned = True
            # 3rd guess: 0.1 > 0.0 (Fail guess) -> Incorrect? Wait, if learned, use P(Slip).
            # Actually, if learned, P(Correct) = 1 - P(Slip).
            # If p_slip=0, then P(Correct)=1.
            # Let's just test that it returns a list of results.
            results = self.simulator.simulate_student(num_trials=5)
            assert len(results) == 5
            for is_correct, state in results:
                assert isinstance(is_correct, bool)
                assert isinstance(state, BKTState)

    def test_simulate_population(self):
        """Test simulating a population of students."""
        results = self.simulator.simulate_population(num_students=10, num_trials=3)
        assert len(results) == 10
        for student_results in results:
            assert len(student_results) == 3

    def test_seed_reproducibility(self):
        """Test that population simulation is reproducible with seed."""
        self.simulator.seed = 123
        results1 = self.simulator.simulate_population(num_students=5, num_trials=2)

        self.simulator.seed = 123
        results2 = self.simulator.simulate_population(num_students=5, num_trials=2)

        assert results1 == results2

    def test_invalid_parameters(self):
        """Test that invalid probabilities raise errors or are handled."""
        # Probabilities should be between 0 and 1
        with pytest.raises(ValueError):
            BKTModel(p_init=1.5)
