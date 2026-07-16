"""
Unit tests for the base data models.
"""
import pytest
from code.models.participant import Participant
from code.models.stimulus import Stimulus
from code.models.gaze_event import GazeEvent

def test_participant_creation():
    """Test that Participant is created with correct attributes."""
    p = Participant(id="P001", crt_score=5.0)
    assert p.id == "P001"
    assert p.crt_score == 5.0
    assert p.random_intercept == 0.0  # Default initialization

def test_participant_with_intercept():
    """Test Participant creation with explicit random_intercept."""
    p = Participant(id="P002", crt_score=3.5, random_intercept=0.15)
    assert p.id == "P002"
    assert p.crt_score == 3.5
    assert p.random_intercept == 0.15

def test_stimulus_creation():
    """Test that Stimulus is created with correct attributes."""
    s = Stimulus(id="H001", headline_text="Breaking News: Event Happens", valence=0.8)
    assert s.id == "H001"
    assert s.headline_text == "Breaking News: Event Happens"
    assert s.valence == 0.8
    assert s.random_intercept == 0.0

def test_stimulus_with_intercept():
    """Test Stimulus creation with explicit random_intercept."""
    s = Stimulus(id="H002", headline_text="Another Headline", valence=-0.2, random_intercept=-0.05)
    assert s.id == "H002"
    assert s.headline_text == "Another Headline"
    assert s.valence == -0.2
    assert s.random_intercept == -0.05

def test_gaze_event_creation():
    """Test that GazeEvent is created with correct attributes."""
    g = GazeEvent(timestamp=100.0, duration=200.0, roi="headline", participant_id="P001")
    assert g.timestamp == 100.0
    assert g.duration == 200.0
    assert g.roi == "headline"
    assert g.participant_id == "P001"

def test_gaze_event_types():
    """Test that GazeEvent handles numeric types correctly."""
    g = GazeEvent(timestamp=0, duration=0, roi="source", participant_id="P099")
    assert g.timestamp == 0
    assert g.duration == 0
    assert g.roi == "source"
    assert g.participant_id == "P099"
