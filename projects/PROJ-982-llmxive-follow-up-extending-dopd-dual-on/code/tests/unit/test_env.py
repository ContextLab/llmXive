"""
Unit tests for the ``PrivilegedGridEnv`` implementation.

These tests focus on the three core requirements:
  1. The hidden variable ``h`` is visible to the teacher but not to the student.
  2. The optimal action (i.e. reaching the goal) depends on the value of ``h``.
  3. The environment is reproducible when seeded and enforces the grid‑size limit.
"""
import pytest
import numpy as np

from env.privileged_grid import PrivilegedGridEnv

def test_grid_size_limit():
    """Creating an environment larger than 10×10 must raise ``ValueError``."""
    with pytest.raises(ValueError):
        PrivilegedGridEnv(grid_size=11)

def test_hidden_variable_visibility():
    """Teacher sees (x, y, h) while student sees only (x, y)."""
    env = PrivilegedGridEnv(grid_size=5, seed=123)
    full_obs, _ = env.reset(seed=123)

    # full_obs is ((x, y), h)
    assert isinstance(full_obs, tuple) and len(full_obs) == 2
    position, hidden = full_obs
    assert isinstance(position, tuple) and len(position) == 2
    assert isinstance(hidden, (int, np.integer))

    # Student observation should be just the position
    student_obs = env.get_student_observation()
    assert student_obs == position
    # Teacher observation should match the full tuple
    teacher_obs = env.get_teacher_observation()
    assert teacher_obs == full_obs

def test_optimal_action_depends_on_h():
    """
    When ``h == 0`` the goal is the top‑left corner (0,0);
    when ``h == 1`` the goal is the bottom‑right corner (grid‑1, grid‑1).
    We place the agent one step away from each goal and verify that the
    correct action yields the +1 reward only for the matching ``h``.
    """
    grid = 5
    env = PrivilegedGridEnv(grid_size=grid, seed=0)

    # ---- h == 0 case ----
    env.h = 0
    env.x, env.y = 1, 0                     # one step right from (0,0)
    obs, reward, terminated, truncated, _ = env.step(2)  # action 2 = left
    assert terminated is True
    assert reward == 1.0

    # Reset for h == 1 case
    env.reset(seed=0)
    env.h = 1
    env.x, env.y = grid - 2, grid - 1       # one step left from bottom‑right
    obs, reward, terminated, truncated, _ = env.step(3)  # action 3 = right
    assert terminated is True
    assert reward == 1.0

def test_seed_reproducibility():
    """Resetting with the same seed must produce identical start states."""
    seed = 42
    env1 = PrivilegedGridEnv(grid_size=5)
    obs1, _ = env1.reset(seed=seed)

    env2 = PrivilegedGridEnv(grid_size=5)
    obs2, _ = env2.reset(seed=seed)

    assert obs1 == obs2, "Identical seeds should yield identical initial states"

    # Different seeds should (with high probability) give different states
    env3 = PrivilegedGridEnv(grid_size=5)
    obs3, _ = env3.reset(seed=seed + 1)
    assert obs1 != obs3, "Different seeds should produce different initial states"