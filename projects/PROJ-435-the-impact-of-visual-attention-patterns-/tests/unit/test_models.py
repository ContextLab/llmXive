"""
Unit tests for data models.
"""
import pytest
from code.models import Participant, Stimulus, GazeEvent


class TestParticipant:
    def test_create_participant(self):
        p = Participant(id="P001", crt_score=0.75)
        assert p.id == "P001"
        assert p.crt_score == 0.75
        assert p.random_intercept == 0.0

    def test_participant_with_intercept(self):
        p = Participant(id="P002", crt_score=0.5, random_intercept=0.1)
        assert p.random_intercept == 0.1


class TestStimulus:
    def test_create_stimulus(self):
        s = Stimulus(id="H001", headline_text="Test Headline")
        assert s.id == "H001"
        assert s.headline_text == "Test Headline"
        assert s.valence is None
        assert s.random_intercept == 0.0

    def test_stimulus_with_valence(self):
        s = Stimulus(id="H002", headline_text="Another Headline", valence=0.8)
        assert s.valence == 0.8


class TestGazeEvent:
    def test_create_gaze_event(self):
        g = GazeEvent(
            timestamp=100.0,
            duration=200.0,
            roi="headline_body",
            participant_id="P001"
        )
        assert g.timestamp == 100.0
        assert g.duration == 200.0
        assert g.roi == "headline_body"
        assert g.participant_id == "P001"
