"""
Unit tests for the data models defined in code/models/.
"""
import pytest
from code.models import Participant, Stimulus, GazeEvent


class TestParticipant:
    def test_participant_creation(self):
        p = Participant(id="P001", crt_score=2.5, random_intercept=0.1)
        assert p.id == "P001"
        assert p.crt_score == 2.5
        assert p.random_intercept == 0.1

    def test_random_intercept_default(self):
        p = Participant(id="P002", crt_score=1.0)
        assert p.random_intercept == 0.0

    def test_random_intercept_casting(self):
        p = Participant(id="P003", crt_score=3.0, random_intercept="0.5")
        assert isinstance(p.random_intercept, float)
        assert p.random_intercept == 0.5


class TestStimulus:
    def test_stimulus_creation(self):
        s = Stimulus(id="H001", headline_text="Breaking News", valence=-0.5)
        assert s.id == "H001"
        assert s.headline_text == "Breaking News"
        assert s.valence == -0.5

    def test_random_intercept_default(self):
        s = Stimulus(id="H002", headline_text="Good News", valence=0.8)
        assert s.random_intercept == 0.0

    def test_float_casting(self):
        s = Stimulus(id="H003", headline_text="Test", valence="0.2", random_intercept="0.1")
        assert isinstance(s.valence, float)
        assert isinstance(s.random_intercept, float)


class TestGazeEvent:
    def test_gaze_event_creation(self):
        g = GazeEvent(timestamp=100.0, duration=200.0, roi="headline", participant_id="P001")
        assert g.timestamp == 100.0
        assert g.duration == 200.0
        assert g.roi == "headline"
        assert g.participant_id == "P001"

    def test_numeric_casting(self):
        g = GazeEvent(timestamp="50", duration="150", roi="source", participant_id="P002")
        assert isinstance(g.timestamp, float)
        assert isinstance(g.duration, float)
        assert g.timestamp == 50.0
        assert g.duration == 150.0