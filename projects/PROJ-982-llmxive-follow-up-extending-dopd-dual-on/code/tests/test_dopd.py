import pytest
import numpy as np
import sys
import os
import tempfile
from unittest.mock import MagicMock

# Add project root to path if not already present
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from env.privilege_mdp import PrivilegeMDP
from agents.student import TabularQStudent
from agents.teacher import TeacherOracle
from agents.baseline_estimator import BaselineEstimator
from training.dopd_distillation import DOPDTrainer
from training.uniform_distillation import UniformDistillationTrainer
from utils.seeding import seed_everything


@pytest.fixture
def env_instance():
    """Create a deterministic environment instance."""
    seed_everything(42)
    env = PrivilegeMDP(grid_size=4, seed=42)
    return env


@pytest.fixture
def student_agent(env_instance):
    """Create a student agent."""
    return TabularQStudent(env_instance, seed=42)


@pytest.fixture
def teacher_agent(env_instance):
    """Create a teacher agent."""
    return TeacherOracle(env_instance, seed=42)


@pytest.fixture
def baseline_estimator(env_instance):
    """Create a baseline estimator."""
    return BaselineEstimator(env_instance, seed=42)


@pytest.fixture
def dopd_config():
    """Configuration for DOPD training."""
    return {
        'advantage_threshold': 0.1,
        'min_weight': 0.0,
        'max_weight': 1.0,
        'learning_rate': 0.1,
        'gamma': 0.99,
        'epsilon': 0.1,
        'num_episodes': 100,
        'max_steps': 50
    }


@pytest.fixture
def uniform_config():
    """Configuration for Uniform training."""
    return {
        'distillation_weight': 1.0,
        'learning_rate': 0.1,
        'gamma': 0.99,
        'epsilon': 0.1,
        'num_episodes': 100,
        'max_steps': 50
    }


class TestDOPDSafetyChecks:
    """Tests for DOPD safety checks and edge cases."""

    def test_division_by_zero_prevention(self, env_instance, baseline_estimator):
        """Verify that zero advantage gaps are handled without division by zero."""
        # Create a scenario where advantage might be zero
        state = env_instance.reset()[0]
        action = 0
        
        # Mock baseline value to be exactly equal to Q-value
        q_val = 0.5
        baseline_val = 0.5
        
        # This should not raise a ZeroDivisionError
        advantage = q_val - baseline_val
        assert advantage == 0.0
        
        # DOPD trainer should handle this gracefully
        trainer = DOPDTrainer(env_instance, baseline_estimator, dopd_config, seed=42)
        
        # Simulate weight calculation with zero advantage
        weight = trainer._calculate_weight(advantage)
        # Weight should be clamped to min_weight (0.0) when advantage is 0
        assert weight >= dopd_config['min_weight']
        assert weight <= dopd_config['max_weight']


class TestDOPDIntegration:
    """Integration tests for DOPD regime behavior."""

    def test_dopd_switches_weighting_low_advantage(self, env_instance, student_agent, 
                                                  teacher_agent, baseline_estimator, 
                                                  dopd_config):
        """
        Verify DOPD regime switches weighting when advantage gap < 0.1 per FR-002.
        
        This test ensures that when the teacher's advantage is low (below threshold),
        the DOPD trainer reduces the distillation weight, allowing the student to
        rely more on self-supervision.
        """
        seed_everything(42)
        
        # Create DOPD trainer
        trainer = DOPDTrainer(env_instance, baseline_estimator, dopd_config, seed=42)
        
        # Test case 1: Low advantage gap (< 0.1)
        low_advantage = 0.05  # Below threshold
        low_weight = trainer._calculate_weight(low_advantage)
        
        # Test case 2: High advantage gap (> 0.1)
        high_advantage = 0.5  # Above threshold
        high_weight = trainer._calculate_weight(high_advantage)
        
        # Verify that low advantage results in lower weight than high advantage
        assert low_weight < high_weight, (
            f"DOPD should assign lower weight to low advantage ({low_weight}) "
            f"than to high advantage ({high_weight})"
        )
        
        # Verify that low advantage weight is closer to min_weight
        expected_low_weight = dopd_config['min_weight'] + (
            (low_advantage / dopd_config['advantage_threshold']) * 
            (dopd_config['max_weight'] - dopd_config['min_weight'])
        )
        # Allow some tolerance for min-max normalization
        assert abs(low_weight - expected_low_weight) < 0.01, (
            f"Low advantage weight {low_weight} should be close to expected "
            f"{expected_low_weight}"
        )
        
        # Verify that high advantage weight is closer to max_weight
        expected_high_weight = dopd_config['max_weight']
        # High advantage should be clamped to max
        assert high_weight >= dopd_config['max_weight'] * 0.9, (
            f"High advantage weight {high_weight} should be close to max "
            f"{dopd_config['max_weight']}"
        )

    def test_dopd_vs_uniform_weighting_behavior(self, env_instance, student_agent,
                                                teacher_agent, baseline_estimator,
                                                dopd_config, uniform_config):
        """
        Verify DOPD regime switches weighting based on advantage while Uniform
        regime maintains fixed weighting regardless of advantage.
        """
        seed_everything(42)
        
        # Create both trainers
        dopd_trainer = DOPDTrainer(env_instance, baseline_estimator, dopd_config, seed=42)
        uniform_trainer = UniformDistillationTrainer(env_instance, uniform_config, seed=42)
        
        # Test across different advantage levels
        advantage_levels = [0.0, 0.05, 0.1, 0.3, 0.5, 1.0]
        
        dopd_weights = []
        uniform_weights = []
        
        for adv in advantage_levels:
            dopd_weights.append(dopd_trainer._calculate_weight(adv))
            uniform_weights.append(uniform_trainer._calculate_weight(adv))
        
        # DOPD weights should vary with advantage
        assert len(set(dopd_weights)) > 1, (
            "DOPD weights should vary across different advantage levels"
        )
        
        # Uniform weights should be constant (all equal to distillation_weight)
        assert len(set(uniform_weights)) == 1, (
            "Uniform weights should be constant regardless of advantage"
        )
        assert uniform_weights[0] == uniform_config['distillation_weight'], (
            f"Uniform weight {uniform_weights[0]} should equal "
            f"distillation_weight {uniform_config['distillation_weight']}"
        )
        
        # Verify DOPD switches behavior at threshold
        threshold_idx = advantage_levels.index(0.1)
        below_threshold = advantage_levels[:threshold_idx]
        above_threshold = advantage_levels[threshold_idx:]
        
        below_weights = [dopd_trainer._calculate_weight(adv) for adv in below_threshold]
        above_weights = [dopd_trainer._calculate_weight(adv) for adv in above_threshold]
        
        # Weights below threshold should generally be lower than above
        assert max(below_weights) <= min(above_weights), (
            f"DOPD weights below threshold {below_weights} should be <= "
            f"weights above threshold {above_weights}"
        )

    def test_dopd_student_convergence_with_dynamic_weighting(self, env_instance,
                                                            student_agent,
                                                            teacher_agent,
                                                            baseline_estimator,
                                                            dopd_config):
        """
        Verify that DOPD student can still converge when advantage weighting is dynamic.
        This ensures the switching mechanism doesn't prevent learning entirely.
        """
        seed_everything(42)
        
        # Create DOPD trainer
        trainer = DOPDTrainer(env_instance, baseline_estimator, dopd_config, seed=42)
        
        # Run a short training episode
        state, _ = env_instance.reset()
        total_reward = 0
        steps = 0
        
        for step in range(dopd_config['max_steps']):
            action = student_agent.select_action(state)
            next_state, reward, terminated, truncated, _ = env_instance.step(action)
            
            # Get teacher action for distillation
            teacher_action = teacher_agent.select_action(state)
            
            # Calculate advantage for weighting
            q_val = student_agent.q_table[state, action]
            baseline_val = baseline_estimator.estimate(state)
            advantage = q_val - baseline_val
            
            # Update student with dynamic weighting
            trainer.update_student(student_agent, state, action, reward, 
                                 next_state, teacher_action, advantage)
            
            total_reward += reward
            state = next_state
            steps += 1
            
            if terminated or truncated:
                break
        
        # Verify training completed without errors
        assert steps > 0, "Training should have executed at least one step"
        assert not np.any(np.isnan(student_agent.q_table)), "Q-table should not contain NaN values"
        
        # Verify some learning occurred (Q-values should have changed from initialization)
        initial_q = np.zeros_like(student_agent.q_table)
        assert not np.array_equal(student_agent.q_table, initial_q), (
            "Q-values should have been updated during training"
        )

    def test_dopd_edge_case_extreme_advantage_values(self, env_instance, baseline_estimator,
                                                    dopd_config):
        """
        Test DOPD behavior with extreme advantage values to ensure robustness.
        """
        seed_everything(42)
        
        trainer = DOPDTrainer(env_instance, baseline_estimator, dopd_config, seed=42)
        
        # Test with very large advantage
        large_advantage = 100.0
        large_weight = trainer._calculate_weight(large_advantage)
        assert large_weight == dopd_config['max_weight'], (
            f"Large advantage {large_advantage} should result in max weight {dopd_config['max_weight']}"
        )
        
        # Test with negative advantage (should be handled gracefully)
        negative_advantage = -0.5
        negative_weight = trainer._calculate_weight(negative_advantage)
        assert negative_weight >= dopd_config['min_weight'], (
            f"Negative advantage {negative_advantage} should result in weight >= min_weight"
        )
        assert negative_weight <= dopd_config['max_weight'], (
            f"Negative advantage {negative_advantage} should result in weight <= max_weight"
        )

    def test_dopd_threshold_boundary_conditions(self, env_instance, baseline_estimator,
                                               dopd_config):
        """
        Test behavior exactly at and near the advantage threshold boundary.
        """
        seed_everything(42)
        
        trainer = DOPDTrainer(env_instance, baseline_estimator, dopd_config, seed=42)
        threshold = dopd_config['advantage_threshold']
        
        # Test exactly at threshold
        at_threshold = trainer._calculate_weight(threshold)
        
        # Test just below threshold
        below_threshold = trainer._calculate_weight(threshold - 0.001)
        
        # Test just above threshold
        above_threshold = trainer._calculate_weight(threshold + 0.001)
        
        # Verify monotonic behavior around threshold
        assert below_threshold <= at_threshold <= above_threshold, (
            "Weight should be monotonically increasing with advantage"
        )
        
        # Verify threshold acts as a meaningful boundary
        # (weights should be distinctly different across the boundary)
        assert at_threshold > below_threshold or above_threshold > at_threshold, (
            "Threshold should create a meaningful transition in weighting"
        )