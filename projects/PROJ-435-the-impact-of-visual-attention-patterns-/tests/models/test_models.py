"""
Unit tests for the data models (Participant, Stimulus, GazeEvent).
"""
import pytest
import numpy as np
from code.models import Participant, Stimulus, GazeEvent


class TestParticipant:
    def test_create_participant(self):
        """Test basic creation of a Participant."""
        p = Participant(id=1, crt_score=2.5)
        assert p.id == 1
        assert p.crt_score == 2.5
        assert isinstance(p.random_intercept, float)

    def test_invalid_crt_score(self):
        """Test that non-numeric CRT score raises error."""
        with pytest.raises(TypeError):
            Participant(id=1, crt_score="high")


class TestStimulus:
    def test_create_stimulus(self):
        """Test basic creation of a Stimulus."""
        s = Stimulus(id=101, headline_text="Breaking News")
        assert s.id == 101
        assert s.headline_text == "Breaking News"
        assert s.valence == 0.0
        assert isinstance(s.random_intercept, float)

    def test_invalid_text(self):
        """Test that non-string text raises error."""
        with pytest.raises(TypeError):
            Stimulus(id=101, headline_text=12345)


class TestGazeEvent:
    def test_create_gaze_event(self):
        """Test basic creation of a GazeEvent."""
        g = GazeEvent(timestamp=100.0, duration=200.0, roi="headline", participant_id=1)
        assert g.timestamp == 100.0
        assert g.duration == 200.0
        assert g.roi == "headline"
        assert g.participant_id == 1

    def test_invalid_timestamp(self):
        """Test that non-numeric timestamp raises error."""
        with pytest.raises(TypeError):
            GazeEvent(timestamp="now", duration=200.0, roi="headline", participant_id=1)

    def test_invalid_duration(self):
        """Test that non-numeric duration raises error."""
        with pytest.raises(TypeError):
            GazeEvent(timestamp=100.0, duration="long", roi="headline", participant_id=1)

    def test_invalid_participant_id(self):
        """Test that non-integer participant_id raises error."""
        with pytest.raises(TypeError):
            GazeEvent(timestamp=100.0, duration=200.0, roi="headline", participant_id="one")