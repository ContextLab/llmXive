import pytest
import numpy as np
import sys
import os
from env.privilege_mdp import PrivilegeMDP
from agents.teacher import TeacherOracle
from agents.student import TabularQStudent
from utils.seeding import seed_everything, generate_seed_sequence
from typing import List, Dict, Tuple

# Fixtures for environment and agents
@pytest.fixture
def env_instance():
    """Create a standard environment instance for testing."""
    seed_everything(42)
    return PrivilegeMDP(grid_size=5, seed=42)

@pytest.fixture
def teacher_agent(env_instance):
    """Create a teacher agent with full state access."""
    return TeacherOracle(env_instance)

@pytest.fixture
def student_agent(env_instance):
    """Create a student agent with partial state access."""
    return TabularQStudent(env_instance, seed=42)

def test_teacher_student_observation_spaces(env_instance, teacher_agent, student_agent):
    """
    Contract test: Verify Teacher observes (O, H) and Student observes only O.
    Ensures information asymmetry as per FR-001.
    """
    # Reset environment to get initial state
    obs, _ = env_instance.reset(seed=42)
    
    # Teacher should receive the full state tuple (observation, hidden_state)
    teacher_obs = teacher_agent.get_observation(obs)
    assert isinstance(teacher_obs, tuple), "Teacher observation must be a tuple"
    assert len(teacher_obs) == 2, "Teacher observation must contain (O, H)"
    
    # Student should receive only the observable part
    student_obs = student_agent.get_observation(obs)
    assert not isinstance(student_obs, tuple) or (
        isinstance(student_obs, tuple) and len(student_obs) == 1
    ), "Student observation must not contain hidden state H"
    
    # Verify that teacher's observation includes H which is masked from student
    # If obs is (O, H), teacher gets (O, H), student gets O
    if isinstance(obs, tuple) and len(obs) == 2:
        o, h = obs
        assert np.array_equal(teacher_obs[0], o), "Teacher's O must match environment O"
        assert np.array_equal(teacher_obs[1], h), "Teacher's H must match environment H"
        # Student should only see O
        if isinstance(student_obs, tuple):
            assert np.array_equal(student_obs[0], o), "Student's O must match environment O"
            assert len(student_obs) == 1, "Student should not see H"
        else:
            assert np.array_equal(student_obs, o), "Student observation must be O"

def test_optimal_action_dependency(env_instance, teacher_agent, student_agent):
    """
    Contract test: Verify optimal action depends on H and asserting 
    reward_student_masked < reward_teacher.
    """
    # Run a few episodes to collect data
    total_teacher_reward = 0
    total_student_reward = 0
    num_episodes = 10
    
    for ep in range(num_episodes):
        # Reset with a specific seed to ensure reproducibility
        obs, _ = env_instance.reset(seed=ep)
        
        # Teacher acts with full knowledge
        teacher_action = teacher_agent.select_action(obs)
        next_obs, teacher_reward, terminated, truncated, _ = env_instance.step(teacher_action)
        total_teacher_reward += teacher_reward
        
        # Reset again for student
        obs, _ = env_instance.reset(seed=ep)
        
        # Student acts without knowledge of H (masked)
        student_action = student_agent.select_action(obs)
        next_obs, student_reward, terminated, truncated, _ = env_instance.step(student_action)
        total_student_reward += student_reward
        
        # Verify that the environment actually uses H in transitions/rewards
        # by checking that different H values (if they exist) lead to different outcomes
        # This is implicitly tested by the reward difference if H matters
    
    # Assert that teacher outperforms student significantly
    # This confirms that H provides valuable information
    assert total_teacher_reward >= total_student_reward, \
        f"Teacher reward ({total_teacher_reward}) should be >= Student reward ({total_student_reward})"
    
    # If the environment is properly designed, teacher should strictly outperform
    # in cases where H influences optimal action
    if total_teacher_reward > 0:
        assert total_teacher_reward > total_student_reward, \
            "Teacher should strictly outperform student when H influences optimal action"

def test_seed_consistency(env_instance):
    """
    Reproducibility test: Verify state distribution consistency across multiple seeds.
    This test ensures that the environment produces identical trajectories when
    initialized with the same seed, and different trajectories when seeds differ.
    """
    # Test 1: Same seed produces identical trajectories
    seed = 12345
    trajectories_1 = []
    trajectories_2 = []
    
    # Run first trajectory with seed
    obs, _ = env_instance.reset(seed=seed)
    trajectory_1 = [obs]
    for _ in range(20):  # Fixed length trajectory
        action = env_instance.action_space.sample()
        obs, reward, terminated, truncated, _ = env_instance.step(action)
        trajectory_1.append(obs)
        if terminated or truncated:
            break
    trajectories_1.append(trajectory_1)
    
    # Run second trajectory with SAME seed
    obs, _ = env_instance.reset(seed=seed)
    trajectory_2 = [obs]
    for _ in range(20):  # Fixed length trajectory
        action = env_instance.action_space.sample()
        obs, reward, terminated, truncated, _ = env_instance.step(action)
        trajectory_2.append(obs)
        if terminated or truncated:
            break
    trajectories_2.append(trajectory_2)
    
    # Compare trajectories - they should be identical
    assert len(trajectory_1) == len(trajectory_2), \
        f"Trajectory lengths differ: {len(trajectory_1)} vs {len(trajectory_2)}"
    
    for t1, t2 in zip(trajectory_1, trajectory_2):
        if isinstance(t1, tuple):
            assert len(t1) == len(t2), "Tuple state components differ in length"
            for c1, c2 in zip(t1, t2):
                assert np.array_equal(c1, c2), f"State components differ: {c1} vs {c2}"
        else:
            assert np.array_equal(t1, t2), f"State values differ: {t1} vs {t2}"
    
    # Test 2: Different seeds produce different trajectories (with high probability)
    # We run multiple trials to ensure we don't get unlucky with same outcomes
    different_found = False
    test_seeds = [11111, 22222, 33333]
    
    for test_seed in test_seeds:
        obs, _ = env_instance.reset(seed=test_seed)
        trajectory_test = [obs]
        for _ in range(20):
            action = env_instance.action_space.sample()
            obs, reward, terminated, truncated, _ = env_instance.step(action)
            trajectory_test.append(obs)
            if terminated or truncated:
                break
        
        # Compare with original trajectory
        if len(trajectory_1) != len(trajectory_test):
            different_found = True
            break
        
        is_different = False
        for t1, t2 in zip(trajectory_1, trajectory_test):
            if isinstance(t1, tuple):
                if len(t1) != len(t2):
                    is_different = True
                    break
                for c1, c2 in zip(t1, t2):
                    if not np.array_equal(c1, c2):
                        is_different = True
                        break
            else:
                if not np.array_equal(t1, t2):
                    is_different = True
                    break
            if is_different:
                break
        
        if is_different:
            different_found = True
            break
    
    # In a properly seeded environment, different seeds should produce different
    # initial states or transitions. If all test seeds produced identical results,
    # there might be a seeding issue.
    # Note: This assertion might fail in degenerate environments where all states
    # are identical, but for a grid-world MDP, different seeds should yield different
    # starting positions or hidden states.
    # We use a probabilistic check - if we found differences in any test, we pass.
    assert different_found, \
        "Different seeds produced identical trajectories - seeding may not be working correctly"
    
    # Test 3: Verify that generate_seed_sequence creates distinct seeds
    base_seed = 42
    num_seeds = 5
    seed_list = generate_seed_sequence(base_seed, num_seeds)
    
    assert len(seed_list) == num_seeds, \
        f"Expected {num_seeds} seeds, got {len(seed_list)}"
    
    # All seeds should be unique
    assert len(set(seed_list)) == num_seeds, \
        f"Generated seeds are not unique: {seed_list}"
    
    # All seeds should be different from base seed
    assert base_seed not in seed_list, \
        f"Base seed {base_seed} should not be in generated sequence"