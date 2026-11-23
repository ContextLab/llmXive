"""
Tests for the Generalization Test Module (T019).
"""

import pytest
import numpy as np
import sys
import os

# Ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from env.privilege_mdp import PrivilegeMDP
from agents.teacher import TeacherOracle
from agents.student import TabularQStudent
from analysis.generalization_test import (
    evaluate_agent_in_masked_mode,
    calculate_performance_drop,
    run_generalization_analysis
)
from utils.seeding import seed_everything


def test_evaluate_agent_in_masked_mode():
    """Test that the evaluation function runs and returns expected keys."""
    seed_everything(42)
    env = PrivilegeMDP(grid_size=5, seed=42)
    agent = TabularQStudent(env, seed=42)
    
    # Run evaluation for a few episodes
    stats = evaluate_agent_in_masked_mode(env, agent, num_episodes=5, max_steps=20, seed=42)
    
    assert 'total_reward' in stats
    assert 'avg_reward' in stats
    assert 'success_rate' in stats
    assert 'steps_per_episode' in stats
    assert len(stats['steps_per_episode']) == 5
    assert isinstance(stats['total_reward'], float)


def test_calculate_performance_drop():
    """Test the performance drop calculation logic."""
    # Case 1: Normal drop
    drop = calculate_performance_drop(acc_unmasked=10.0, acc_masked=5.0, r_max=10.0)
    assert drop == 0.5
    
    # Case 2: No drop
    drop_no_drop = calculate_performance_drop(acc_unmasked=10.0, acc_masked=10.0, r_max=10.0)
    assert drop_no_drop == 0.0
    
    # Case 3: Negative drop (Student outperforms Teacher? Should be possible in noise)
    drop_neg = calculate_performance_drop(acc_unmasked=5.0, acc_masked=10.0, r_max=10.0)
    assert drop_neg == -0.5
    
    # Case 4: Division by zero
    with pytest.raises(ValueError):
        calculate_performance_drop(acc_unmasked=10.0, acc_masked=5.0, r_max=0.0)


def test_run_generalization_analysis():
    """Test the full analysis pipeline."""
    seed_everything(42)
    env = PrivilegeMDP(grid_size=5, seed=42)
    teacher = TeacherOracle(env)
    student = TabularQStudent(env, seed=42)
    
    results = run_generalization_analysis(
        env, student, teacher, num_episodes=5, max_steps=20, seed=42
    )
    
    assert 'teacher_stats' in results
    assert 'student_stats' in results
    assert 'performance_drop' in results
    assert 'r_max' in results
    
    # Verify types
    assert isinstance(results['teacher_stats']['avg_reward'], float)
    assert isinstance(results['student_stats']['avg_reward'], float)
    assert isinstance(results['performance_drop'], float)