"""
Unit tests for Participant and Response entity classes.
"""
import pytest
from datetime import datetime
from code.data.participant import Participant, Response


class TestParticipant:
    def test_participant_creation_default_id(self):
        """Test that a participant is created with a unique ID."""
        p = Participant(condition="high_detail")
        assert p.id is not None
        assert len(p.id) > 0
        assert p.condition == "high_detail"

    def test_participant_creation_custom_id(self):
        """Test creating a participant with a specific ID."""
        custom_id = "test-participant-123"
        p = Participant(id=custom_id, condition="low_detail")
        assert p.id == custom_id
        assert p.condition == "low_detail"

    def test_participant_timestamp(self):
        """Test that participant has a timestamp."""
        p = Participant()
        assert p.timestamp is not None
        # Verify it's a valid ISO format string
        datetime.fromisoformat(p.timestamp)

    def test_add_response(self):
        """Test adding a response to a participant."""
        p = Participant(condition="control")
        r = Response(
            participant_id=p.id,
            question_id="q1",
            value="yes"
        )
        p.add_response(r)
        assert len(p.responses) == 1
        assert p.responses[0] == r

    def test_to_dict(self):
        """Test participant serialization."""
        p = Participant(id="p1", condition="high_detail")
        d = p.to_dict()
        assert d["id"] == "p1"
        assert d["condition"] == "high_detail"
        assert "timestamp" in d
        assert "response_count" in d


class TestResponse:
    def test_response_creation_default_id(self):
        """Test that a response is created with a unique ID."""
        r = Response(participant_id="p1", question_id="q1", value="yes")
        assert r.id is not None
        assert len(r.id) > 0

    def test_response_creation_custom_id(self):
        """Test creating a response with a specific ID."""
        custom_id = "resp-456"
        r = Response(
            id=custom_id,
            participant_id="p1",
            question_id="q1",
            value="no"
        )
        assert r.id == custom_id
        assert r.participant_id == "p1"
        assert r.question_id == "q1"
        assert r.value == "no"

    def test_response_timestamp(self):
        """Test that response has a timestamp."""
        r = Response(participant_id="p1", question_id="q1", value="yes")
        assert r.timestamp is not None
        datetime.fromisoformat(r.timestamp)

    def test_to_dict(self):
        """Test response serialization."""
        r = Response(
            id="r1",
            participant_id="p1",
            question_id="q1",
            value="yes"
        )
        d = r.to_dict()
        assert d["id"] == "r1"
        assert d["participant_id"] == "p1"
        assert d["question_id"] == "q1"
        assert d["value"] == "yes"
        assert "timestamp" in d