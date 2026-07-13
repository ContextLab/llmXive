import pytest
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.scheduler.state_coverage import (
    initialize_coverage_vector,
    detect_state_transitions,
    aggregate_coverage_vectors,
    merge_coverage_vectors_threadsafe
)
from code.utils.constants import is_valid_coverage_vector


class MockStateHandler:
    """
    Mock class simulating the state tracking behavior of MobileGym environments.
    Used to generate deterministic state transitions for testing bit-flipping logic.
    """
    def __init__(self, schema_variables: List[str]):
        self.schema_variables = schema_variables
        self.current_state = {var: False for var in schema_variables}
        self.transition_log = []

    def update_state(self, variable_name: str, new_value: bool) -> bool:
        """
        Updates a state variable. Returns True if the value changed (transition occurred).
        """
        if variable_name not in self.current_state:
            raise ValueError(f"Unknown variable: {variable_name}")
        
        old_value = self.current_state[variable_name]
        if old_value != new_value:
            self.current_state[variable_name] = new_value
            self.transition_log.append({
                "variable": variable_name,
                "old_value": old_value,
                "new_value": new_value,
                "timestamp": len(self.transition_log)
            })
            return True
        return False

    def get_current_state_dict(self) -> Dict[str, bool]:
        return self.current_state.copy()


@pytest.fixture
def sample_schema():
    """Provides a standard list of state variables for testing."""
    return [
        "dark_mode",
        "night_mode",
        "high_contrast",
        "font_size_large",
        "auto_play_videos",
        "location_services_enabled",
        "notifications_enabled"
    ]


def test_initialize_coverage_vector_zeros(sample_schema):
    """
    Test that a new coverage vector is initialized to all zeros (False).
    """
    vector = initialize_coverage_vector(sample_schema)
    assert len(vector) == len(sample_schema)
    assert all(v is False for v in vector)
    assert is_valid_coverage_vector(vector, sample_schema)


def test_detect_state_transitions_no_change(sample_schema):
    """
    Test that detect_state_transitions returns empty list if no state changes.
    """
    handler = MockStateHandler(sample_schema)
    # No updates made
    transitions = detect_state_transitions(handler.get_current_state_dict(), sample_schema)
    assert transitions == []


def test_detect_state_transitions_single_flip(sample_schema):
    """
    Test that a single state change is detected as a bit flip.
    """
    handler = MockStateHandler(sample_schema)
    
    # Simulate a change: dark_mode goes from False to True
    handler.update_state("dark_mode", True)
    
    current_state = handler.get_current_state_dict()
    transitions = detect_state_transitions(current_state, sample_schema)
    
    assert len(transitions) == 1
    assert transitions[0]["variable"] == "dark_mode"
    assert transitions[0]["old_value"] is False
    assert transitions[0]["new_value"] is True


def test_detect_state_transitions_multiple_flips(sample_schema):
    """
    Test detection of multiple simultaneous bit flips.
    """
    handler = MockStateHandler(sample_schema)
    
    # Simulate changes in multiple variables
    handler.update_state("dark_mode", True)
    handler.update_state("night_mode", True)
    handler.update_state("auto_play_videos", False) # Change from default False? 
    # Wait, default is False. Let's change auto_play_videos to True then back to False to ensure detection logic works on any change
    # Actually, let's just set them to specific values different from init
    handler.update_state("auto_play_videos", True)
    handler.update_state("font_size_large", True)
    
    current_state = handler.get_current_state_dict()
    transitions = detect_state_transitions(current_state, sample_schema)
    
    # We expect 4 transitions: dark_mode, night_mode, auto_play_videos, font_size_large
    assert len(transitions) == 4
    
    # Verify specific flips
    flipped_vars = {t["variable"] for t in transitions}
    assert "dark_mode" in flipped_vars
    assert "night_mode" in flipped_vars
    assert "auto_play_videos" in flipped_vars
    assert "font_size_large" in flipped_vars


def test_aggregate_coverage_vectors_bit_flipping(sample_schema):
    """
    Integration test: Verify that aggregate_coverage_vectors correctly flips bits
    in the base vector based on detected transitions.
    
    This is the core test for the "binary vector bit-flipping on state change" requirement.
    """
    base_vector = initialize_coverage_vector(sample_schema)
    assert all(v is False for v in base_vector)
    
    handler = MockStateHandler(sample_schema)
    
    # Trigger a specific state change
    handler.update_state("dark_mode", True)
    
    transitions = detect_state_transitions(handler.get_current_state_dict(), sample_schema)
    
    # Aggregate the transitions into the vector
    updated_vector = aggregate_coverage_vectors(base_vector, transitions)
    
    # Verify bit flipping logic
    # dark_mode is at index 0
    assert updated_vector[0] is True, "Bit for 'dark_mode' should have flipped to 1"
    
    # Other bits should remain 0
    for i, val in enumerate(updated_vector):
        if i != 0:
            assert val is False, f"Bit at index {i} should remain 0"


def test_aggregate_coverage_vectors_multiple_flips(sample_schema):
    """
    Test that multiple bit flips are correctly reflected in the aggregated vector.
    """
    base_vector = initialize_coverage_vector(sample_schema)
    handler = MockStateHandler(sample_schema)
    
    # Flip 3 bits
    handler.update_state("dark_mode", True)
    handler.update_state("night_mode", True)
    handler.update_state("location_services_enabled", True)
    
    transitions = detect_state_transitions(handler.get_current_state_dict(), sample_schema)
    updated_vector = aggregate_coverage_vectors(base_vector, transitions)
    
    # Check specific indices
    # dark_mode -> 0
    # night_mode -> 1
    # location_services_enabled -> 5
    assert updated_vector[0] is True
    assert updated_vector[1] is True
    assert updated_vector[5] is True
    
    # Check others are False
    for i, val in enumerate(updated_vector):
        if i not in [0, 1, 5]:
            assert val is False


def test_merge_coverage_vectors_threadsafe(sample_schema):
    """
    Test thread-safe merging of two vectors with different bits set.
    """
    vec1 = initialize_coverage_vector(sample_schema)
    vec2 = initialize_coverage_vector(sample_schema)
    
    # Manually set bits to simulate parallel rollouts
    # vec1 has dark_mode
    vec1[0] = True
    # vec2 has night_mode
    vec2[1] = True
    
    merged = merge_coverage_vectors_threadsafe(vec1, vec2)
    
    assert merged[0] is True
    assert merged[1] is True
    assert all(v is False for i, v in enumerate(merged) if i not in [0, 1])


def test_aggregate_coverage_vectors_no_transitions(sample_schema):
    """
    Test that vector remains unchanged if no transitions are provided.
    """
    base_vector = initialize_coverage_vector(sample_schema)
    base_vector[0] = True # Set one bit initially
    
    transitions = []
    updated_vector = aggregate_coverage_vectors(base_vector, transitions)
    
    assert updated_vector == base_vector
    assert updated_vector[0] is True