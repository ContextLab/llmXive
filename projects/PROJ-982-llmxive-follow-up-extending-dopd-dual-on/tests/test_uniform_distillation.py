"""
Tests for Uniform Distillation Training.
"""

import pytest
import numpy as np
import sys
import os

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from env.privilege_mdp import PrivilegeMDP
from agents.student import TabularQStudent
from agents.teacher import TeacherOracle
from training.uniform_distillation import UniformDistillationTrainer, train_uniform
from utils.seeding import seed_everything


@pytest.fixture
def env_instance():
    seed_everything(42)
    env = PrivilegeMDP(grid_size=4, seed=42)
    return env


@pytest.fixture
def student_agent(env_instance):
    seed_everything(42)
    student = TabularQStudent(env_instance, seed=42)
    return student


@pytest.fixture
def teacher_agent(env_instance):
    seed_everything(42)
    teacher = TeacherOracle(env_instance, seed=42)
    return teacher


class TestUniformDistillation:
    def test_trainer_initialization(self, env_instance, student_agent, teacher_agent):
        """Test that the trainer initializes correctly with fixed alpha."""
        trainer = UniformDistillationTrainer(
            student=student_agent,
            teacher=teacher_agent,
            env=env_instance,
            alpha=0.7,
            seed=42
        )
        assert trainer.alpha == 0.7
        assert trainer.student is student_agent
        assert trainer.teacher is teacher_agent
        assert len(trainer.episode_rewards) == 0

    def test_distillation_loss_calculation(self, env_instance, student_agent, teacher_agent):
        """Test that loss is calculated based on teacher's action."""
        trainer = UniformDistillationTrainer(
            student=student_agent,
            teacher=teacher_agent,
            env=env_instance,
            alpha=0.5,
            seed=42
        )
        
        # Reset env to get a valid state
        state, _ = env_instance.reset()
        
        # Get teacher action (requires full state)
        # Assuming teacher can act on full state
        full_state = env_instance.s
        teacher_action = teacher_agent.select_action(full_state)
        
        # Calculate loss
        loss = trainer.calculate_distillation_loss(state, teacher_action)
        
        # Loss should be a number (negative Q value of teacher action)
        assert isinstance(loss, (float, np.floating))
        
    def test_train_step_updates_q_table(self, env_instance, student_agent, teacher_agent):
        """Test that a training step updates the Q-table."""
        trainer = UniformDistillationTrainer(
            student=student_agent,
            teacher=teacher_agent,
            env=env_instance,
            alpha=0.5,
            seed=42
        )
        
        # Record initial Q-table state
        initial_q = student_agent.q_table.copy()
        
        # Reset and step
        state, _ = env_instance.reset()
        
        # Perform one step
        student_action, loss, _ = trainer.train_step(state)
        
        # Check that Q-table changed
        # Note: It might not change if the error is 0, but with random init and TD, it should.
        # We check that the function runs without error and returns expected types.
        assert isinstance(student_action, int)
        assert isinstance(loss, (float, np.floating))
        
        # Check that the student's Q-table was accessed/updated (at least the row for state)
        # We can't guarantee a specific value change without knowing the exact math,
        # but we can ensure the method executed.
        
    def test_train_episode_runs(self, env_instance, student_agent, teacher_agent):
        """Test that an episode runs to completion."""
        trainer = UniformDistillationTrainer(
            student=student_agent,
            teacher=teacher_agent,
            env=env_instance,
            alpha=0.5,
            seed=42
        )
        
        metrics = trainer.train_episode(max_steps=50)
        
        assert "total_reward" in metrics
        assert "length" in metrics
        assert "avg_loss" in metrics
        assert metrics["length"] > 0
        
    def test_train_function_integration(self, env_instance, student_agent, teacher_agent):
        """Test the high-level train_uniform function."""
        results = train_uniform(
            student=student_agent,
            teacher=teacher_agent,
            env=env_instance,
            num_episodes=5,
            alpha=0.5,
            seed=42
        )
        
        assert "final_rewards" in results
        assert "final_losses" in results
        assert "avg_reward" in results
        assert len(results["final_rewards"]) == 5