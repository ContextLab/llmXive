"""
Contract tests for T017b: Markov Artifacts.

Verifies that the saved artifacts meet the schema requirements:
- markov_state.json contains keys: transition_matrix, alphabet, order
- order is exactly 1
- transition_matrix is a dict of dicts with float values
- alphabet is a list of strings
"""
import json
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_processed_dir

@pytest.fixture
def processed_dir():
    return get_processed_dir()

@pytest.fixture
def markov_state_path(processed_dir):
    return processed_dir / "markov_state.json"

@pytest.fixture
def transition_probs_path(processed_dir):
    return processed_dir / "transition_probs.json"

def test_markov_state_file_exists(markov_state_path):
    """Test that markov_state.json exists."""
    assert markov_state_path.exists(), "markov_state.json does not exist"

def test_markov_state_is_valid_json(markov_state_path):
    """Test that markov_state.json contains valid JSON."""
    try:
        with open(markov_state_path, 'r') as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"markov_state.json is not valid JSON: {e}")

def test_markov_state_has_required_keys(markov_state_path):
    """Test that markov_state.json has the required keys."""
    with open(markov_state_path, 'r') as f:
        state = json.load(f)
    
    required_keys = {'transition_matrix', 'alphabet', 'order'}
    missing_keys = required_keys - set(state.keys())
    
    assert not missing_keys, f"markov_state.json is missing required keys: {missing_keys}"

def test_markov_state_order_is_one(markov_state_path):
    """Test that the Markov model order is exactly 1."""
    with open(markov_state_path, 'r') as f:
        state = json.load(f)
    
    assert state['order'] == 1, f"Markov model order must be 1, got {state['order']}"

def test_transition_matrix_structure(markov_state_path):
    """Test that transition_matrix is a dict of dicts with float values."""
    with open(markov_state_path, 'r') as f:
        state = json.load(f)
    
    transition_matrix = state['transition_matrix']
    
    assert isinstance(transition_matrix, dict), "transition_matrix must be a dict"
    
    for source, destinations in transition_matrix.items():
        assert isinstance(source, str), f"Source state '{source}' must be a string"
        assert isinstance(destinations, dict), f"Destinations for '{source}' must be a dict"
        
        for dest, prob in destinations.items():
            assert isinstance(dest, str), f"Destination state '{dest}' must be a string"
            assert isinstance(prob, float), f"Probability for {source}->{dest} must be a float, got {type(prob)}"
            assert 0.0 <= prob <= 1.0, f"Probability must be between 0 and 1, got {prob}"

def test_alphabet_structure(markov_state_path):
    """Test that alphabet is a list of strings."""
    with open(markov_state_path, 'r') as f:
        state = json.load(f)
    
    alphabet = state['alphabet']
    
    assert isinstance(alphabet, list), "alphabet must be a list"
    assert len(alphabet) > 0, "alphabet must not be empty"
    
    for item in alphabet:
        assert isinstance(item, str), f"Alphabet item '{item}' must be a string"

def test_transition_probs_file_exists(transition_probs_path):
    """Test that transition_probs.json exists."""
    assert transition_probs_path.exists(), "transition_probs.json does not exist"

def test_transition_probs_matches_state(markov_state_path, transition_probs_path):
    """Test that transition_probs.json matches the transition_matrix in markov_state.json."""
    with open(markov_state_path, 'r') as f:
        state = json.load(f)
    
    with open(transition_probs_path, 'r') as f:
        probs = json.load(f)
    
    assert state['transition_matrix'] == probs, "transition_probs.json does not match transition_matrix in markov_state.json"
