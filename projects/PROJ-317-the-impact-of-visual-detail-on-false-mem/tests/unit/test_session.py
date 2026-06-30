"""
Unit tests for session state management in code/participants/session.py.

Tests verify that the Session class correctly manages state transitions,
records responses, and handles timeouts/dropouts as defined in the
participant interface specification.
"""

import pytest
from datetime import datetime
from pathlib import Path
import sys
import os

# Ensure the code directory is in the path for imports
code_root = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from data.participant import Participant, Response
from participants.session import Session, SessionState, SessionError


class TestSessionInitialization:
    """Tests for Session object creation and initial state."""

    def test_session_creates_with_expected_initial_state(self):
        """Verify a new session starts in the 'idle' state."""
        participant = Participant(
            id="P001",
            condition="enhanced",
            timestamp=datetime.now()
        )
        session = Session(participant=participant)

        assert session.state == SessionState.IDLE
        assert session.current_image_id is None
        assert len(session.responses) == 0
        assert session.start_time is not None
        assert session.end_time is None

    def test_session_raises_if_participant_is_none(self):
        """Verify Session cannot be created without a Participant."""
        with pytest.raises(ValueError, match="Participant cannot be None"):
            Session(participant=None)


class TestStateTransitions:
    """Tests for session state machine transitions."""

    def test_transition_to_image_viewing(self):
        """Verify transition from IDLE to VIEWING_IMAGE."""
        participant = Participant(id="P002", condition="reduced", timestamp=datetime.now())
        session = Session(participant=participant)

        session.transition_to_image_viewing(image_id="IMG_001")

        assert session.state == SessionState.VIEWING_IMAGE
        assert session.current_image_id == "IMG_001"

    def test_transition_to_distractor_task(self):
        """Verify transition from VIEWING_IMAGE to DISTRACTOR_TASK."""
        participant = Participant(id="P003", condition="baseline", timestamp=datetime.now())
        session = Session(participant=participant)

        # First move to viewing
        session.transition_to_image_viewing(image_id="IMG_002")
        assert session.state == SessionState.VIEWING_IMAGE

        # Then move to distractor
        session.transition_to_distractor_task()

        assert session.state == SessionState.DISTRACTOR_TASK
        assert session.current_image_id == "IMG_002" # Should retain context

    def test_transition_to_recognition(self):
        """Verify transition from DISTRACTOR_TASK to RECOGNITION."""
        participant = Participant(id="P004", condition="enhanced", timestamp=datetime.now())
        session = Session(participant=participant)

        session.transition_to_image_viewing(image_id="IMG_003")
        session.transition_to_distractor_task()
        session.transition_to_recognition()

        assert session.state == SessionState.RECOGNITION

    def test_transition_to_completed(self):
        """Verify transition from RECOGNITION to COMPLETED."""
        participant = Participant(id="P005", condition="reduced", timestamp=datetime.now())
        session = Session(participant=participant)

        session.transition_to_image_viewing(image_id="IMG_004")
        session.transition_to_distractor_task()
        session.transition_to_recognition()
        session.transition_to_completed()

        assert session.state == SessionState.COMPLETED
        assert session.end_time is not None

    def test_invalid_transition_raises_error(self):
        """Verify that skipping states raises a SessionError."""
        participant = Participant(id="P006", condition="baseline", timestamp=datetime.now())
        session = Session(participant=participant)

        # Attempt to jump from IDLE directly to RECOGNITION
        with pytest.raises(SessionError, match="Invalid state transition"):
            session.transition_to_recognition()


class TestResponseRecording:
    """Tests for recording responses within a session."""

    def test_record_response_in_valid_state(self):
        """Verify responses can be recorded during RECOGNITION state."""
        participant = Participant(id="P007", condition="enhanced", timestamp=datetime.now())
        session = Session(participant=participant)

        session.transition_to_image_viewing("IMG_005")
        session.transition_to_distractor_task()
        session.transition_to_recognition()

        response = Response(
            id="R001",
            question_id="Q_TRUE_1",
            value=1, # True
            timestamp=datetime.now()
        )

        session.record_response(response)

        assert len(session.responses) == 1
        assert session.responses[0].question_id == "Q_TRUE_1"

    def test_record_response_in_invalid_state_raises_error(self):
        """Verify recording a response in IDLE state raises an error."""
        participant = Participant(id="P008", condition="reduced", timestamp=datetime.now())
        session = Session(participant=participant)

        response = Response(id="R002", question_id="Q_1", value=0, timestamp=datetime.now())

        with pytest.raises(SessionError, match="Cannot record response in state IDLE"):
            session.record_response(response)

    def test_multiple_responses_are_accumulated(self):
        """Verify that multiple responses are stored in order."""
        participant = Participant(id="P009", condition="baseline", timestamp=datetime.now())
        session = Session(participant=participant)

        session.transition_to_image_viewing("IMG_006")
        session.transition_to_distractor_task()
        session.transition_to_recognition()

        resp1 = Response(id="R1", question_id="Q1", value=1, timestamp=datetime.now())
        resp2 = Response(id="R2", question_id="Q2", value=0, timestamp=datetime.now())

        session.record_response(resp1)
        session.record_response(resp2)

        assert len(session.responses) == 2
        assert session.responses[0].question_id == "Q1"
        assert session.responses[1].question_id == "Q2"


class TestSessionTimeoutAndDropout:
    """Tests for handling timeouts and partial sessions."""

    def test_mark_as_dropped_out(self):
        """Verify session can be marked as dropped out."""
        participant = Participant(id="P010", condition="enhanced", timestamp=datetime.now())
        session = Session(participant=participant)

        session.transition_to_image_viewing("IMG_007")

        # Simulate dropout
        session.mark_as_dropped_out()

        assert session.state == SessionState.DROPPED_OUT
        assert session.end_time is not None
        assert len(session.responses) == 0 # No responses recorded if dropped early

    def test_get_session_summary_for_completed_session(self):
        """Verify summary generation for a completed session."""
        participant = Participant(id="P011", condition="reduced", timestamp=datetime.now())
        session = Session(participant=participant)

        session.transition_to_image_viewing("IMG_008")
        session.transition_to_distractor_task()
        session.transition_to_recognition()

        session.record_response(Response(id="R1", question_id="Q1", value=1, timestamp=datetime.now()))
        session.transition_to_completed()

        summary = session.get_session_summary()

        assert summary["participant_id"] == "P011"
        assert summary["condition"] == "reduced"
        assert summary["state"] == "COMPLETED"
        assert summary["total_responses"] == 1
        assert "start_time" in summary
        assert "end_time" in summary

    def test_get_session_summary_for_dropped_session(self):
        """Verify summary generation for a dropped session."""
        participant = Participant(id="P012", condition="baseline", timestamp=datetime.now())
        session = Session(participant=participant)

        session.transition_to_image_viewing("IMG_009")
        session.mark_as_dropped_out()

        summary = session.get_session_summary()

        assert summary["state"] == "DROPPED_OUT"
        assert summary["is_complete"] is False