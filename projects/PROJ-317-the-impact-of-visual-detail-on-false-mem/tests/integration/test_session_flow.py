"""
Integration test for simulated session flow (T024).

This test verifies the end-to-end flow of a simulated participant session:
1. Session creation and initialization
2. Stimulus presentation (baseline image)
3. Distractor task execution
4. Recognition question generation and response
5. Session state persistence and response recording

Dependencies:
- T025 (Simulated participant interface)
- T026 (Distractor task)
- T027.2 (Recognition question generator)
- T027.3 (Response capture)
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from participants.session import SessionManager, SessionState, create_session
from participants.interface import SimulatedParticipantInterface, SessionConfig
from data.participant import Participant, Response
from config import get_project_root, get_data_dir, get_responses_dir


class TestSessionFlow:
    """Integration tests for the full simulated session flow."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_stimulus_metadata(self, temp_output_dir):
        """Create mock stimulus metadata for testing."""
        metadata_dir = temp_output_dir / "stimuli_metadata"
        metadata_dir.mkdir(parents=True)

        metadata_file = metadata_dir / "test_img_001.yaml"
        metadata_content = """
        image_id: test_img_001
        baseline_path: test_img_001_baseline.png
        enhanced_path: test_img_001_enhanced.png
        reduced_path: test_img_001_reduced.png
        complexity_score: 0.5
        objects:
          - object_name: red car
            category: vehicle
            visual_features: [color, shape]
          - object_name: blue house
            category: building
            visual_features: [color, size]
          - object_name: green tree
            category: nature
            visual_features: [color, texture]
        """
        metadata_file.write_text(metadata_content)
        return metadata_dir

    @pytest.fixture
    def mock_mock_objects(self, temp_output_dir):
        """Create mock object pool for false detail generation."""
        assets_dir = temp_output_dir / "assets"
        assets_dir.mkdir(parents=True)

        mock_objects_file = assets_dir / "mock_objects.json"
        mock_objects_data = [
            {"object_name": "red car", "category": "vehicle", "visual_features": ["color", "shape"]},
            {"object_name": "blue house", "category": "building", "visual_features": ["color", "size"]},
            {"object_name": "green tree", "category": "nature", "visual_features": ["color", "texture"]},
            {"object_name": "yellow sun", "category": "nature", "visual_features": ["color", "shape"]},
            {"object_name": "black cat", "category": "animal", "visual_features": ["color", "shape"]},
            {"object_name": "white dog", "category": "animal", "visual_features": ["color", "size"]},
            {"object_name": "purple flower", "category": "nature", "visual_features": ["color", "texture"]},
            {"object_name": "orange ball", "category": "toy", "visual_features": ["color", "shape"]},
            {"object_name": "pink balloon", "category": "toy", "visual_features": ["color", "size"]},
            {"object_name": "brown chair", "category": "furniture", "visual_features": ["color", "shape"]},
            {"object_name": "gray table", "category": "furniture", "visual_features": ["color", "size"]},
            {"object_name": "silver clock", "category": "object", "visual_features": ["color", "shape"]},
            {"object_name": "gold ring", "category": "jewelry", "visual_features": ["color", "texture"]},
            {"object_name": "silver spoon", "category": "utensil", "visual_features": ["color", "shape"]},
            {"object_name": "blue cup", "category": "utensil", "visual_features": ["color", "size"]},
            {"object_name": "red apple", "category": "food", "visual_features": ["color", "shape"]},
            {"object_name": "green leaf", "category": "nature", "visual_features": ["color", "texture"]},
            {"object_name": "yellow banana", "category": "food", "visual_features": ["color", "shape"]},
            {"object_name": "purple grape", "category": "food", "visual_features": ["color", "size"]},
            {"object_name": "orange juice", "category": "food", "visual_features": ["color", "texture"]},
        ]
        mock_objects_file.write_text(json.dumps(mock_objects_data, indent=2))
        return mock_objects_file

    def test_full_session_flow(self, temp_output_dir, mock_stimulus_metadata, mock_mock_objects):
        """Test the complete simulated participant session flow."""
        # Setup paths
        responses_dir = temp_output_dir / "responses"
        responses_dir.mkdir(parents=True)

        # Create a mock config that points to our temp directories
        config = SessionConfig(
            stimulus_metadata_dir=str(mock_stimulus_metadata),
            mock_objects_path=str(mock_mock_objects),
            responses_dir=str(responses_dir),
            image_display_duration=2.0,  # Shortened for testing
            distractor_duration=3.0,     # Shortened for testing
            num_questions=4              # Reduced for testing
        )

        # Create session manager
        session_manager = SessionManager(config)

        # Create a new session
        session_id = session_manager.create_session()
        assert session_id is not None
        assert isinstance(session_id, str)

        # Verify session state exists
        session_state = session_manager.get_session_state(session_id)
        assert session_state is not None
        assert session_state.session_id == session_id
        assert session_state.status == "initialized"

        # Step 1: Present stimulus (baseline image)
        # In a real scenario, this would display an image for a set duration
        # Here we simulate the state transition
        session_manager.present_stimulus(session_id, "test_img_001")
        session_state = session_manager.get_session_state(session_id)
        assert session_state.status == "stimulus_presented"
        assert session_state.current_stimulus_id == "test_img_001"

        # Step 2: Execute distractor task
        # In a real scenario, this would present arithmetic questions for 2 minutes
        # Here we simulate the state transition and result
        distractor_result = session_manager.execute_distractor_task(session_id)
        assert distractor_result is not None
        assert distractor_result.completed is True
        assert distractor_result.duration > 0

        session_state = session_manager.get_session_state(session_id)
        assert session_state.status == "distractor_completed"

        # Step 3: Generate and answer recognition questions
        # This should generate both true and false questions
        recognition_results = session_manager.generate_and_answer_questions(session_id)
        assert recognition_results is not None
        assert len(recognition_results) > 0

        # Verify we have a mix of true and false questions
        true_count = sum(1 for r in recognition_results if r.is_true_detail)
        false_count = sum(1 for r in recognition_results if not r.is_true_detail)
        assert true_count > 0, "Should have at least one true detail question"
        assert false_count > 0, "Should have at least one false detail question"

        session_state = session_manager.get_session_state(session_id)
        assert session_state.status == "session_completed"

        # Step 4: Verify response recording
        # Check that response files were created
        response_files = list(responses_dir.glob(f"{session_id}_*.json"))
        assert len(response_files) > 0, "Response files should be created"

        # Load and verify response content
        response_data = json.loads(response_files[0].read_text())
        assert "session_id" in response_data
        assert response_data["session_id"] == session_id
        assert "participant_id" in response_data
        assert "stimulus_id" in response_data
        assert response_data["stimulus_id"] == "test_img_001"
        assert "responses" in response_data
        assert len(response_data["responses"]) == len(recognition_results)

        # Verify each response has required fields
        for resp in response_data["responses"]:
            assert "question_id" in resp
            assert "question_text" in resp
            assert "is_true_detail" in resp
            assert "response_value" in resp
            assert "timestamp" in resp

        # Step 5: Verify session integrity
        # The session should be properly finalized and all data consistent
        final_state = session_manager.get_session_state(session_id)
        assert final_state.status == "session_completed"
        assert final_state.completed_at is not None
        assert final_state.started_at is not None
        assert final_state.total_duration > 0

    def test_session_with_dropout(self, temp_output_dir, mock_stimulus_metadata, mock_mock_objects):
        """Test session handling when a participant drops out."""
        responses_dir = temp_output_dir / "responses"
        responses_dir.mkdir(parents=True)

        config = SessionConfig(
            stimulus_metadata_dir=str(mock_stimulus_metadata),
            mock_objects_path=str(mock_mock_objects),
            responses_dir=str(responses_dir),
            image_display_duration=2.0,
            distractor_duration=3.0,
            num_questions=4
        )

        session_manager = SessionManager(config)
        session_id = session_manager.create_session()

        # Present stimulus
        session_manager.present_stimulus(session_id, "test_img_001")

        # Simulate dropout before completing distractor task
        session_manager.mark_dropout(session_id, reason="participant_left")

        session_state = session_manager.get_session_state(session_id)
        assert session_state.status == "dropped_out"
        assert session_state.dropout_reason == "participant_left"

        # Verify partial session recording
        response_files = list(responses_dir.glob(f"{session_id}_*.json"))
        # Even dropped sessions should have a partial record
        assert len(response_files) > 0

        response_data = json.loads(response_files[0].read_text())
        assert response_data["status"] == "dropped_out"
        assert response_data["dropout_reason"] == "participant_left"

    def test_session_error_handling(self, temp_output_dir, mock_stimulus_metadata, mock_mock_objects):
        """Test session error handling for invalid inputs."""
        responses_dir = temp_output_dir / "responses"
        responses_dir.mkdir(parents=True)

        config = SessionConfig(
            stimulus_metadata_dir=str(mock_stimulus_metadata),
            mock_objects_path=str(mock_mock_objects),
            responses_dir=str(responses_dir),
            image_display_duration=2.0,
            distractor_duration=3.0,
            num_questions=4
        )

        session_manager = SessionManager(config)
        session_id = session_manager.create_session()

        # Try to present a non-existent stimulus
        with pytest.raises(ValueError) as exc_info:
            session_manager.present_stimulus(session_id, "non_existent_img")

        assert "not found" in str(exc_info.value).lower()

        # Session should still be in initialized state
        session_state = session_manager.get_session_state(session_id)
        assert session_state.status == "initialized"

    def test_response_data_integrity(self, temp_output_dir, mock_stimulus_metadata, mock_mock_objects):
        """Test that response data maintains integrity across the session."""
        responses_dir = temp_output_dir / "responses"
        responses_dir.mkdir(parents=True)

        config = SessionConfig(
            stimulus_metadata_dir=str(mock_stimulus_metadata),
            mock_objects_path=str(mock_mock_objects),
            responses_dir=str(responses_dir),
            image_display_duration=2.0,
            distractor_duration=3.0,
            num_questions=4
        )

        session_manager = SessionManager(config)
        session_id = session_manager.create_session()

        # Complete the full session
        session_manager.present_stimulus(session_id, "test_img_001")
        session_manager.execute_distractor_task(session_id)
        recognition_results = session_manager.generate_and_answer_questions(session_id)

        # Load the response file
        response_files = list(responses_dir.glob(f"{session_id}_*.json"))
        response_data = json.loads(response_files[0].read_text())

        # Verify data consistency
        assert len(response_data["responses"]) == len(recognition_results)

        # Check that all question IDs match
        response_question_ids = {r["question_id"] for r in response_data["responses"]}
        expected_question_ids = {r.question_id for r in recognition_results}
        assert response_question_ids == expected_question_ids

        # Check that true/false labels match
        for resp in response_data["responses"]:
            matching_result = next(r for r in recognition_results if r.question_id == resp["question_id"])
            assert resp["is_true_detail"] == matching_result.is_true_detail

        # Verify timestamps are in order
        timestamps = [datetime.fromisoformat(r["timestamp"]) for r in response_data["responses"]]
        assert timestamps == sorted(timestamps), "Timestamps should be in chronological order"

    def test_session_concurrent_access(self, temp_output_dir, mock_stimulus_metadata, mock_mock_objects):
        """Test that multiple sessions can be managed concurrently."""
        responses_dir = temp_output_dir / "responses"
        responses_dir.mkdir(parents=True)

        config = SessionConfig(
            stimulus_metadata_dir=str(mock_stimulus_metadata),
            mock_objects_path=str(mock_mock_objects),
            responses_dir=str(responses_dir),
            image_display_duration=2.0,
            distractor_duration=3.0,
            num_questions=4
        )

        session_manager = SessionManager(config)

        # Create multiple sessions
        session_ids = [session_manager.create_session() for _ in range(3)]
        assert len(set(session_ids)) == 3, "Session IDs should be unique"

        # Run each session partially
        for sid in session_ids:
            session_manager.present_stimulus(sid, "test_img_001")

        # Verify all sessions are in correct state
        for sid in session_ids:
            state = session_manager.get_session_state(sid)
            assert state.status == "stimulus_presented"
            assert state.current_stimulus_id == "test_img_001"

        # Complete one session
        session_manager.execute_distractor_task(session_ids[0])
        session_manager.generate_and_answer_questions(session_ids[0])

        # Verify the completed session
        state = session_manager.get_session_state(session_ids[0])
        assert state.status == "session_completed"

        # Other sessions should remain in their previous state
        for sid in session_ids[1:]:
            state = session_manager.get_session_state(sid)
            assert state.status == "stimulus_presented"