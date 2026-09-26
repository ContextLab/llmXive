"""
Contract test for T041d: Verify markov_state.json structure.
"""
import json
import pytest
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_processed_dir


def test_markov_state_exists():
    """T017b: Verify markov_state.json exists."""
    processed_dir = get_processed_dir()
    state_path = processed_dir / "markov_state.json"
    assert state_path.exists(), f"markov_state.json not found at {state_path}"


def test_markov_state_structure():
    """T017b: Verify markov_state.json has correct keys and order."""
    processed_dir = get_processed_dir()
    state_path = processed_dir / "markov_state.json"
    
    with open(state_path, 'r') as f:
        data = json.load(f)
    
    assert "transition_matrix" in data, "Missing 'transition_matrix' key"
    assert "alphabet" in data, "Missing 'alphabet' key"
    assert "order" in data, "Missing 'order' key"
    
    assert data["order"] == 1, f"Order must be 1, found {data['order']}"
    assert isinstance(data["alphabet"], list), "Alphabet must be a list"
    assert len(data["alphabet"]) > 0, "Alphabet must not be empty"
    assert isinstance(data["transition_matrix"], dict), "Transition matrix must be a dict"


def test_markov_state_probabilities_sum_to_one():
    """Verify that transition probabilities sum to 1.0 for each state."""
    processed_dir = get_processed_dir()
    state_path = processed_dir / "markov_state.json"
    
    with open(state_path, 'r') as f:
        data = json.load(f)
    
    transition_matrix = data["transition_matrix"]
    alphabet = data["alphabet"]
    
    for from_state, to_probs in transition_matrix.items():
        total_prob = sum(to_probs.values())
        # Allow small floating point error
        assert abs(total_prob - 1.0) < 1e-6, \
            f"Probabilities for state '{from_state}' sum to {total_prob}, expected 1.0"
        
        # Verify all states in alphabet are present as keys
        for state in alphabet:
            assert state in to_probs, f"Missing transition to '{state}' from '{from_state}'"