"""Unit tests for data models."""
import pytest
from code.models import Participant, Stimulus, GazeEvent

class TestParticipant:
    def test_participant_creation(self):
        p = Participant(id="P001", crt_score=2.5)
        assert p.id == "P001"
        assert p.crt_score == 2.5
        assert p.random_intercept == 0.0

    def test_participant_with_intercept(self):
        p = Participant(id="P002", crt_score=1.0, random_intercept=0.5)
        assert p.random_intercept == 0.5

    def test_generate_random_intercept(self):
        intercept = Participant.generate_random_intercept()
        assert isinstance(intercept, float)

class TestStimulus:
    def test_stimulus_creation(self):
        s = Stimulus(id="H001", headline_text="Test Headline")
        assert s.id == "H001"
        assert s.headline_text == "Test Headline"
        assert s.valence == 0.0
        assert s.random_intercept == 0.0

    def test_stimulus_with_valence(self):
        s = Stimulus(id="H002", headline_text="Another Headline", valence=0.8)
        assert s.valence == 0.8

    def test_generate_random_intercept(self):
        intercept = Stimulus.generate_random_intercept()
        assert isinstance(intercept, float)

class TestGazeEvent:
    def test_gaze_event_creation(self):
        g = GazeEvent(timestamp=100.0, duration=250.0, roi="source", participant_id="P001")
        assert g.timestamp == 100.0
        assert g.duration == 250.0
        assert g.roi == "source"
        assert g.participant_id == "P001"

    def test_gaze_event_zero_duration(self):
        g = GazeEvent(timestamp=0.0, duration=0.0, roi="headline", participant_id="P002")
        assert g.duration == 0.0