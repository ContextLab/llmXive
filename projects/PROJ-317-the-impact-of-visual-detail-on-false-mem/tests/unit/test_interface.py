"""
Unit tests for the simulated participant interface (code/participants/interface.py).
"""
import pytest
import time
from datetime import datetime
from pathlib import Path
import json

from code.participants.interface import SimulatedParticipantInterface, SessionConfig
from code.config import get_responses_dir, get_stimuli_dir, get_stimuli_metadata_dir
from code.data.participant import Participant, Response

# Mock dependencies for unit testing without file system I/O for stimuli
# We will test the logic of state management and response recording.

@pytest.fixture
def interface():
    """Create an interface instance with short durations for testing."""
    config = SessionConfig(
        image_display_duration_sec=0.1,
        distractor_task_duration_sec=0.1
    )
    return SimulatedParticipantInterface(config)

@pytest.fixture
def temp_response_dir(tmp_path):
    """Create a temporary directory for responses."""
    # Override the global config for this test? 
    # Since config.py uses get_project_root() which might be static,
    # we will just ensure the directory exists and use the interface's internal logic
    # by patching or simply ensuring the directory exists.
    # For simplicity in this unit test, we assume the global directories are writable
    # or we test the object state before saving.
    return tmp_path

def test_start_session(interface):
    """Test that start_session creates a valid Participant object."""
    p_id = "test_001"
    cond = "enhanced"
    
    participant = interface.start_session(p_id, cond)
    
    assert participant is not None
    assert participant.id == p_id
    assert participant.condition == cond
    assert isinstance(participant.timestamp, datetime)
    assert interface.current_session_id is not None
    assert interface.current_participant.id == p_id

def test_record_response_without_session(interface):
    """Test that recording a response fails if no session is active."""
    with pytest.raises(RuntimeError, match="No active session"):
        interface.record_response("q1", "yes")

def test_record_response_valid(interface):
    """Test recording a valid response."""
    interface.start_session("p1", "baseline")
    
    resp = interface.record_response("q1", "yes")
    
    assert isinstance(resp, Response)
    assert resp.question_id == "q1"
    assert resp.value == "yes"
    assert isinstance(resp.timestamp, datetime)
    assert len(interface.past_responses) == 1
    assert interface.past_responses[0].id == resp.id

def test_multiple_responses(interface):
    """Test recording multiple responses."""
    interface.start_session("p2", "reduced")
    
    r1 = interface.record_response("q1", "yes")
    r2 = interface.record_response("q2", "no")
    r3 = interface.record_response("q3", "maybe")
    
    assert len(interface.past_responses) == 3
    assert interface.past_responses[1].question_id == "q2"
    assert interface.past_responses[2].value == "maybe"

def test_display_stimulus_timing(interface, tmp_path):
    """Test that display_stimulus respects the configured duration."""
    # We need a fake stimulus file to test display
    # Create a dummy image
    from PIL import Image
    img_path = get_stimuli_dir() / "dummy_test.png"
    img_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a minimal valid PNG
    img = Image.new('RGB', (10, 10), color='red')
    img.save(img_path)
    
    # Create a dummy metadata file
    meta_path = get_stimuli_metadata_dir() / "dummy_test.yaml"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text("id: dummy_test\ncondition: baseline\n")
    
    # Load presentation
    presentation = interface.load_stimulus("dummy_test")
    assert presentation.stimulus_id == "dummy_test"
    
    start = time.time()
    # Override duration to be very short for test speed, but check logic
    interface.config.image_display_duration_sec = 0.2
    
    updated_pres = interface.display_stimulus(presentation)
    elapsed = time.time() - start
    
    assert updated_pres.display_end_time is not None
    assert updated_pres.display_end_time >= updated_pres.display_start_time
    # Allow some tolerance for overhead
    assert elapsed >= 0.15 

def test_save_session_responses(interface):
    """Test saving responses to disk."""
    interface.start_session("p_save", "enhanced")
    interface.record_response("q_save_1", "yes")
    interface.record_response("q_save_2", "no")
    
    output_path = interface.save_session_responses("test_save.json")
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data['participant_id'] == "p_save"
    assert data['condition'] == "enhanced"
    assert len(data['responses']) == 2
    assert data['responses'][0]['question_id'] == "q_save_1"
    assert data['responses'][1]['value'] == "no"

def test_run_distractor_task(interface):
    """Test the distractor task logic."""
    interface.start_session("p_dist", "baseline")
    
    start = time.time()
    interface.config.distractor_task_duration_sec = 0.2
    result = interface.run_distractor_task()
    elapsed = time.time() - start
    
    assert result is True
    assert elapsed >= 0.15

def test_session_isolation(interface):
    """Test that two sessions do not interfere with each other."""
    # Session 1
    interface.start_session("pA", "baseline")
    interface.record_response("qA", "valA")
    
    # Session 2
    interface.start_session("pB", "enhanced")
    interface.record_response("qB", "valB")
    
    # Check state
    assert interface.current_participant.id == "pB"
    assert len(interface.past_responses) == 1 # Only pB's response
    assert interface.past_responses[0].question_id == "qB"
    
    # pA's data is lost in this simple implementation (as expected for a single instance)
    # unless we implement a session history, which is not required by T025.
