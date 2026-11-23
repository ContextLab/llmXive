"""
Unit tests for JSON event log generation (T015).

Verifies that `generate_event_log` produces valid JSON strings
with the correct structure as defined in FR-001.
"""
import json
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from renderer import generate_event_log

def test_basic_step_event():
    """Test generation of a basic step event."""
    log_str = generate_event_log(
        time_step=5,
        player_pos=(10, 20),
        action="move_right"
    )
    
    assert isinstance(log_str, str)
    data = json.loads(log_str)
    
    assert data["t"] == 5
    assert data["event"] == "step"
    assert data["player_pos"]["x"] == 10
    assert data["player_pos"]["y"] == 20
    assert data["action"] == "move_right"
    assert "details" not in data

def test_event_with_details():
    """Test generation of an event with additional details."""
    log_str = generate_event_log(
        time_step=10,
        player_pos=(0, 0),
        action="pick_up",
        event_type="item_acquired",
        details={"item_id": "key_01", "color": "gold"}
    )
    
    data = json.loads(log_str)
    
    assert data["t"] == 10
    assert data["event"] == "item_acquired"
    assert data["details"]["item_id"] == "key_01"
    assert data["details"]["color"] == "gold"

def test_invalid_json_structure():
    """Verify the output is strictly valid JSON."""
    log_str = generate_event_log(
        time_step=99,
        player_pos=(1, 1),
        action="move_up"
    )
    
    # Should not raise an exception
    try:
        parsed = json.loads(log_str)
        assert "t" in parsed
        assert "event" in parsed
    except json.JSONDecodeError:
        assert False, "Generated log string is not valid JSON"

def test_coordinate_types():
    """Test that coordinates can be integers."""
    log_str = generate_event_log(
        time_step=1,
        player_pos=(100, 200),
        action="move_down"
    )
    data = json.loads(log_str)
    assert data["player_pos"]["x"] == 100
    assert data["player_pos"]["y"] == 200