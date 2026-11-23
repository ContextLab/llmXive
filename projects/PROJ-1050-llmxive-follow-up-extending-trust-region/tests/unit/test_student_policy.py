"""
Unit tests for the Student Policy.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from student.policy import StudentPolicy

@pytest.fixture
def student_policy():
    """Create a test student policy."""
    return StudentPolicy(horizon=5, state_dim=10, action_dim=5)

def test_horizon_constraint_enforcement(student_policy):
    """Test that horizon constraint is enforced."""
    assert student_policy.horizon == 5
    
    # Get horizon status
    status = student_policy.get_horizon_status()
    assert status["horizon"] == 5
    assert "total_updates" in status

def test_student_policy_action_selection(student_policy):
    """Test that student policy selects valid actions."""
    state = np.random.randn(student_policy.state_dim)
    
    action = student_policy.get_action(state)
    
    assert isinstance(action, np.ndarray)
    assert len(action) == student_policy.action_dim
    assert np.sum(action) == 1.0

def test_student_policy_update(student_policy):
    """Test that student policy can be updated."""
    initial_weights = student_policy.weights.copy()
    
    # Perform update
    student_policy.update(loss_value=0.5, alpha=0.5)
    
    # Check that weights changed
    assert not np.allclose(student_policy.weights, initial_weights)
    assert student_policy.total_updates == 1

def test_student_policy_reset(student_policy):
    """Test that student policy can be reset."""
    student_policy.update(loss_value=0.5, alpha=0.5)
    
    student_policy.reset()
    
    assert student_policy.total_updates == 0
    assert len(student_policy.convergence_history) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
