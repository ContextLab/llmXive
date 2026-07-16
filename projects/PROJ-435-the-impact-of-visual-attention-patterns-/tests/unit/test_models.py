"""
Unit tests for the data models.
"""

import pytest
from code.models import Participant, Stimulus, GazeEvent


class TestParticipant:
    def test_create_participant(self):
        p = Participant(id="P001", crt_score=5.0)
        assert p.id == "P001"
        assert p.crt_score == 5.0
        assert p.random_intercept is None

    def test_create_participant_with_intercept(self):
        p = Participant(id="P002", crt_score=3.5, random_intercept=0.12)
        assert p.random_intercept == 0.12

    def test_type_coercion(self):
        p = Participant(id=123, crt_score="4.2", random_intercept="0.5")
        assert isinstance(p.id, str)
        assert isinstance(p.crt_score, float)
        assert isinstance(p.random_intercept, float)


class TestStimulus:
    def test_create_stimulus(self):
        s = Stimulus(id="H001", headline_text="Breaking News")
        assert s.id == "H001"
        assert s.headline_text == "Breaking News"
        assert s.valence is None

    def test_create_stimulus_with_valence(self):
        s = Stimulus(id="H002", headline_text="Happy Event", valence=0.8)
        assert s.valence == 0.8

    def test_type_coercion(self):
        s = Stimulus(id=999, headline_text="Test", valence="0.5", random_intercept="0.1")
        assert isinstance(s.id, str)
        assert isinstance(s.headline_text, str)
        assert isinstance(s.valence, float)
        assert isinstance(s.random_intercept, float)


class TestGazeEvent:
    def test_create_gaze_event(self):
        g = GazeEvent(timestamp=100.0, duration=200.0, roi="source", participant_id="P001")
        assert g.timestamp == 100.0
        assert g.duration == 200.0
        assert g.roi == "source"
        assert g.participant_id == "P001"

    def test_type_coercion(self):
        g = GazeEvent(
            timestamp="100.5",
            duration="200.2",
            roi=1,
            participant_id=99
        )
        assert isinstance(g.timestamp, float)
        assert isinstance(g.duration, float)
        assert isinstance(g.roi, str)
        assert isinstance(g.participant_id, str)
