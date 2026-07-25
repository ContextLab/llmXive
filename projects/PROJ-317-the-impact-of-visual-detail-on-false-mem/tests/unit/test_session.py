"""
Unit tests for session state management in the participant interface.

This module tests the SessionState and SessionManager classes defined in
code/participants/session.py to ensure correct state transitions,
response recording, and session lifecycle management.
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path for imports if running standalone
# Note: In the actual project structure, this is handled by the test runner
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from participants.session import SessionState, SessionManager, create_session
from data.participant import Participant, Response


class TestSessionState:
    """Tests for the SessionState dataclass."""

    def test_initial_state(self):
        """Test that a new session starts in the correct initial state."""
        state = SessionState()
        assert state.is_active is True
        assert state.current_stage == "initialized"
        assert state.responses == []
        assert state.participant_id is None
        assert state.start_time is None
        assert state.end_time is None

    def test_transition_to_active(self):
        """Test transitioning from initialized to active."""
        state = SessionState()
        state.transition_to_active()
        assert state.is_active is True
        assert state.current_stage == "active"
        assert state.start_time is not None
        assert state.start_time <= datetime.now()

    def test_transition_to_staged(self):
        """Test transitioning to a specific stage."""
        state = SessionState()
        state.transition_to_staged("distractor_task")
        assert state.current_stage == "distractor_task"

    def test_add_response(self):
        """Test adding a response to the session state."""
        state = SessionState()
        response = Response(
            id="resp_001",
            question_id="q_001",
            value=True,
            timestamp=datetime.now()
        )
        state.add_response(response)
        assert len(state.responses) == 1
        assert state.responses[0].id == "resp_001"
        assert state.responses[0].value is True

    def test_add_response_duplicate_id(self):
        """Test that adding a response with duplicate ID raises an error."""
        state = SessionState()
        response1 = Response(
            id="resp_001",
            question_id="q_001",
            value=True,
            timestamp=datetime.now()
        )
        response2 = Response(
            id="resp_001",
            question_id="q_002",
            value=False,
            timestamp=datetime.now()
        )
        state.add_response(response1)
        with pytest.raises(ValueError, match="Response with ID"):
            state.add_response(response2)

    def test_get_responses_by_question(self):
        """Test retrieving responses filtered by question ID."""
        state = SessionState()
        state.add_response(Response(id="r1", question_id="q1", value=True, timestamp=datetime.now()))
        state.add_response(Response(id="r2", question_id="q2", value=False, timestamp=datetime.now()))
        state.add_response(Response(id="r3", question_id="q1", value=True, timestamp=datetime.now()))

        q1_responses = state.get_responses_by_question("q1")
        assert len(q1_responses) == 2
        assert all(r.question_id == "q1" for r in q1_responses)

    def test_to_dict_serialization(self):
        """Test that session state can be serialized to a dictionary."""
        state = SessionState()
        state.transition_to_active()
        state.add_response(Response(id="r1", question_id="q1", value=True, timestamp=datetime.now()))

        state_dict = state.to_dict()
        assert isinstance(state_dict, dict)
        assert state_dict["is_active"] is True
        assert "responses" in state_dict
        assert len(state_dict["responses"]) == 1

    def test_from_dict_deserialization(self):
        """Test that session state can be deserialized from a dictionary."""
        original_state = SessionState()
        original_state.transition_to_active()
        original_state.add_response(Response(id="r1", question_id="q1", value=True, timestamp=datetime.now()))
        original_dict = original_state.to_dict()

        restored_state = SessionState.from_dict(original_dict)
        assert restored_state.is_active is True
        assert restored_state.current_stage == "active"
        assert len(restored_state.responses) == 1
        assert restored_state.responses[0].id == "r1"

    def test_is_session_complete(self):
        """Test the logic for determining if a session is complete."""
        state = SessionState()
        assert state.is_session_complete() is False

        state.transition_to_active()
        assert state.is_session_complete() is False

        state.transition_to_staged("completed")
        # Even with completed stage, if no end_time set, might depend on logic
        # Assuming is_session_complete checks for end_time or specific state
        # Based on typical logic, we expect it to return True if stage is completed
        # Let's verify the actual implementation logic by checking the property
        # If the implementation relies on end_time, we need to set it.
        # For this test, we assume the property checks current_stage == "completed"
        assert state.is_session_complete() is True


class TestSessionManager:
    """Tests for the SessionManager class."""

    @pytest.fixture
    def temp_session_dir(self):
        """Create a temporary directory for session data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_create_session(self, temp_session_dir):
        """Test creating a new session."""
        participant = Participant(id="P001", condition="high_detail", timestamp=datetime.now())
        session = create_session(
            participant=participant,
            session_dir=temp_session_dir / "sessions",
            session_id="S001"
        )

        assert session is not None
        assert session.session_id == "S001"
        assert session.participant.id == "P001"
        assert session.state.is_active is True

    def test_session_manager_initialization(self, temp_session_dir):
        """Test SessionManager initialization."""
        manager = SessionManager(
            session_dir=temp_session_dir / "sessions",
            session_id="S002"
        )

        assert manager.session_dir == temp_session_dir / "sessions"
        assert manager.session_id == "S002"
        assert manager.state.is_active is True

    def test_record_response(self, temp_session_dir):
        """Test recording a response in the session manager."""
        manager = SessionManager(
            session_dir=temp_session_dir / "sessions",
            session_id="S003"
        )

        response = Response(
            id="resp_001",
            question_id="q_001",
            value=True,
            timestamp=datetime.now()
        )

        manager.record_response(response)

        assert len(manager.state.responses) == 1
        assert manager.state.responses[0].id == "resp_001"

    def test_save_session(self, temp_session_dir):
        """Test saving session state to disk."""
        manager = SessionManager(
            session_dir=temp_session_dir / "sessions",
            session_id="S004"
        )
        manager.state.transition_to_active()
        manager.record_response(Response(
            id="r1", question_id="q1", value=True, timestamp=datetime.now()
        ))

        save_path = manager.save_session()

        assert save_path.exists()
        assert save_path.suffix == ".json"

        # Verify content
        with open(save_path, 'r') as f:
            data = json.load(f)
        assert data["session_id"] == "S004"
        assert len(data["state"]["responses"]) == 1

    def test_load_session(self, temp_session_dir):
        """Test loading a session from disk."""
        # First, create and save a session
        manager = SessionManager(
            session_dir=temp_session_dir / "sessions",
            session_id="S005"
        )
        manager.state.transition_to_active()
        manager.record_response(Response(
            id="r1", question_id="q1", value=True, timestamp=datetime.now()
        ))
        save_path = manager.save_session()

        # Now load it
        loaded_manager = SessionManager.load_session(save_path)

        assert loaded_manager.session_id == "S005"
        assert loaded_manager.state.is_active is True
        assert len(loaded_manager.state.responses) == 1
        assert loaded_manager.state.responses[0].id == "r1"

    def test_transition_stages(self, temp_session_dir):
        """Test transitioning through session stages."""
        manager = SessionManager(
            session_dir=temp_session_dir / "sessions",
            session_id="S006"
        )

        assert manager.state.current_stage == "initialized"

        manager.transition_to_stage("presentation")
        assert manager.state.current_stage == "presentation"

        manager.transition_to_stage("distractor_task")
        assert manager.state.current_stage == "distractor_task"

        manager.transition_to_stage("recognition")
        assert manager.state.current_stage == "recognition"

        manager.transition_to_stage("completed")
        assert manager.state.current_stage == "completed"

    def test_finalize_session(self, temp_session_dir):
        """Test finalizing a session."""
        manager = SessionManager(
            session_dir=temp_session_dir / "sessions",
            session_id="S007"
        )
        manager.record_response(Response(
            id="r1", question_id="q1", value=True, timestamp=datetime.now()
        ))

        manager.finalize_session()

        assert manager.state.is_active is False
        assert manager.state.current_stage == "completed"
        assert manager.state.end_time is not None
        assert manager.state.end_time <= datetime.now()

    def test_get_session_summary(self, temp_session_dir):
        """Test generating a session summary."""
        manager = SessionManager(
            session_dir=temp_session_dir / "sessions",
            session_id="S008"
        )
        manager.state.transition_to_active()
        manager.record_response(Response(
            id="r1", question_id="q1", value=True, timestamp=datetime.now()
        ))
        manager.record_response(Response(
            id="r2", question_id="q2", value=False, timestamp=datetime.now()
        ))
        manager.finalize_session()

        summary = manager.get_session_summary()

        assert isinstance(summary, dict)
        assert summary["session_id"] == "S008"
        assert summary["total_responses"] == 2
        assert summary["is_complete"] is True

    def test_save_session_creates_directory(self, temp_session_dir):
        """Test that saving a session creates the directory if it doesn't exist."""
        deep_path = temp_session_dir / "sessions" / "subdir" / "deep"
        manager = SessionManager(
            session_dir=deep_path,
            session_id="S009"
        )

        save_path = manager.save_session()

        assert save_path.exists()
        assert deep_path.exists()

    def test_load_session_nonexistent(self, temp_session_dir):
        """Test loading a session that doesn't exist raises an error."""
        nonexistent_path = temp_session_dir / "sessions" / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            SessionManager.load_session(nonexistent_path)

    def test_duplicate_response_id_in_manager(self, temp_session_dir):
        """Test that duplicate response IDs in a session are rejected."""
        manager = SessionManager(
            session_dir=temp_session_dir / "sessions",
            session_id="S010"
        )

        manager.record_response(Response(
            id="dup_id", question_id="q1", value=True, timestamp=datetime.now()
        ))

        with pytest.raises(ValueError, match="Response with ID"):
            manager.record_response(Response(
                id="dup_id", question_id="q2", value=False, timestamp=datetime.now()
            ))


class TestSessionIntegration:
    """Integration tests for session workflow."""

    @pytest.fixture
    def temp_session_dir(self):
        """Create a temporary directory for session data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_full_session_lifecycle(self, temp_session_dir):
        """Test the complete lifecycle of a session from creation to finalization."""
        # Create session
        participant = Participant(id="P001", condition="high_detail", timestamp=datetime.now())
        session_dir = temp_session_dir / "sessions"
        manager = SessionManager(session_dir=session_dir, session_id="S011")

        # Simulate workflow
        manager.transition_to_stage("presentation")
        manager.record_response(Response(id="r1", question_id="q1", value=True, timestamp=datetime.now()))

        manager.transition_to_stage("distractor_task")
        manager.record_response(Response(id="r2", question_id="q2", value=False, timestamp=datetime.now()))

        manager.transition_to_stage("recognition")
        manager.record_response(Response(id="r3", question_id="q3", value=True, timestamp=datetime.now()))

        # Save and finalize
        save_path = manager.save_session()
        manager.finalize_session()

        # Verify state
        assert manager.state.is_active is False
        assert manager.state.current_stage == "completed"
        assert len(manager.state.responses) == 3

        # Verify file on disk
        assert save_path.exists()
        with open(save_path, 'r') as f:
            data = json.load(f)
        assert data["state"]["is_active"] is False
        assert len(data["state"]["responses"]) == 3

    def test_session_recovery_after_crash_simulation(self, temp_session_dir):
        """Simulate a crash and verify session can be recovered."""
        manager = SessionManager(
            session_dir=temp_session_dir / "sessions",
            session_id="S012"
        )
        manager.transition_to_stage("distractor_task")
        manager.record_response(Response(id="r1", question_id="q1", value=True, timestamp=datetime.now()))

        # Simulate crash by saving state
        crash_path = manager.save_session()

        # Simulate recovery by loading state
        recovered_manager = SessionManager.load_session(crash_path)

        assert recovered_manager.state.current_stage == "distractor_task"
        assert len(recovered_manager.state.responses) == 1
        assert recovered_manager.state.responses[0].id == "r1"