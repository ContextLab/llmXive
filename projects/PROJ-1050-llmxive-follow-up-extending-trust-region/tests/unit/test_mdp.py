"""
Unit tests for the Reasoning MDP environment.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from env.reasoning_mdp import ReasoningMDP, State, Action

@pytest.fixture
def mdp():
    """Create a test MDP instance."""
    return ReasoningMDP(num_initial_states=5, max_depth=10, num_inference_rules=3)

def test_valid_state_transitions(mdp):
    """Test that state transitions are valid."""
    # Reset environment
    state = mdp.reset()
    assert isinstance(state, np.ndarray)
    assert len(state) == mdp.state_dim
    
    # Take a valid action
    valid_actions = mdp.get_valid_actions()
    assert len(valid_actions) > 0
    
    action = np.zeros(mdp.action_dim)
    action[valid_actions[0]] = 1.0
    
    next_state, reward, done, info = mdp.step(action)
    
    # Verify state transition
    assert isinstance(next_state, np.ndarray)
    assert len(next_state) == mdp.state_dim
    assert "effective_depth" in info
    assert "teacher_depth" in info

def test_invalid_action_penalty(mdp):
    """Test that invalid actions receive a penalty."""
    state = mdp.reset()
    
    # Force an invalid action (if possible)
    # In this implementation, most actions are valid, so we test the logic
    valid_actions = mdp.get_valid_actions()
    
    # Pick an action that might be invalid
    invalid_action_idx = (valid_actions[0] + 1) % mdp.action_dim
    if invalid_action_idx not in valid_actions:
        action = np.zeros(mdp.action_dim)
        action[invalid_action_idx] = 1.0
        
        next_state, reward, done, info = mdp.step(action)
        
        # Invalid actions should receive negative reward
        assert reward < 0
        assert info.get("valid", True) == False

def test_goal_reached_condition(mdp):
    """Test that goal is reached when depth limit is hit."""
    state = mdp.reset()
    
    # Run until max depth
    for _ in range(mdp.max_depth + 5):
        valid_actions = mdp.get_valid_actions()
        action = np.zeros(mdp.action_dim)
        action[valid_actions[0]] = 1.0
        
        next_state, reward, done, info = mdp.step(action)
        
        if done:
            assert info.get("goal_reached", False) or info.get("effective_depth", 0) >= mdp.max_depth
            break

def test_state_vector_representation(mdp):
    """Test that state vectors are correctly represented."""
    state = mdp.reset()
    
    # Check that state vector has correct dimension
    assert len(state) == mdp.state_dim
    
    # Check that current node is encoded
    current_node = int(np.argmax(state))
    assert 0 <= current_node < mdp.num_initial_states

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
