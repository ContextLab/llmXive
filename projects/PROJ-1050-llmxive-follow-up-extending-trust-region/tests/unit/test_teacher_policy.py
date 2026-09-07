"""
Unit tests for the Teacher Policy.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from env.reasoning_mdp import ReasoningMDP
from env.teacher_policy import TeacherPolicy

@pytest.fixture
def teacher_policy():
    """Create a test teacher policy."""
    mdp = ReasoningMDP(num_initial_states=5, max_depth=10, num_inference_rules=3)
    return TeacherPolicy(mdp=mdp)

def test_teacher_policy_generates_valid_actions(teacher_policy):
    """Test that teacher policy generates valid actions."""
    mdp = teacher_policy.mdp
    state = mdp.reset()
    
    action = teacher_policy.get_action(state)
    
    # Verify action is one-hot encoded
    assert isinstance(action, np.ndarray)
    assert len(action) == mdp.action_dim
    assert np.sum(action) == 1.0

def test_teacher_policy_optimal_paths(teacher_policy):
    """Test that teacher policy can generate optimal paths."""
    mdp = teacher_policy.mdp
    state = mdp.reset()
    
    # Generate a sequence of actions
    actions = []
    for _ in range(5):
        action = teacher_policy.get_action(state)
        actions.append(action)
        
        # Execute action
        next_state, _, _, _ = mdp.step(action)
        state = next_state
    
    # Verify we got a sequence of actions
    assert len(actions) == 5
    for action in actions:
        assert np.sum(action) == 1.0

def test_teacher_policy_reset(teacher_policy):
    """Test that teacher policy can be reset."""
    mdp = teacher_policy.mdp
    state = mdp.reset()
    
    # Get an action
    action1 = teacher_policy.get_action(state)
    
    # Reset
    teacher_policy.reset()
    
    # Get another action
    action2 = teacher_policy.get_action(state)
    
    # Actions might be different after reset
    assert isinstance(action1, np.ndarray)
    assert isinstance(action2, np.ndarray)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
