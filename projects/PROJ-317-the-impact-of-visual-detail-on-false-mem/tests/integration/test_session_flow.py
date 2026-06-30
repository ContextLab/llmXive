"""
Integration test for simulated session flow (User Story 2).

This test verifies the end-to-end flow of a simulated participant session:
1. Session initialization with a participant and image stimulus.
2. Presentation of the baseline image.
3. Execution of the distractor task.
4. Presentation of recognition questions (true and false details).
5. Capture and logging of responses.
6. Verification that all responses are recorded correctly in the expected output file.
"""
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path to allow imports of sibling modules
# Assuming this test is run from the project root or the path is configured correctly
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_project_root, get_responses_dir, get_stimuli_metadata_dir
from code.data.participant import Participant, Response
from code.participants.interface import run_simulated_session
from code.participants.session import SessionManager


@pytest.fixture
def temp_response_dir():
    """Create a temporary directory for response files during the test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the config to return our temp directory
        original_get_responses_dir = get_responses_dir
        get_responses_dir.__globals__['get_config'] = lambda: MagicMock(
            get_data_dir=lambda: Path(tmpdir),
            get_responses_dir=lambda: Path(tmpdir) / "responses"
        )
        # Ensure the directory exists
        resp_dir = Path(tmpdir) / "responses"
        resp_dir.mkdir(parents=True, exist_ok=True)
        yield resp_dir
        # Restore original function if needed (though in this scope it's local)
        get_responses_dir.__globals__['get_config'] = lambda: original_get_responses_dir()


@pytest.fixture
def mock_stimuli_metadata():
    """Create mock stimuli metadata for the test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        meta_dir = Path(tmpdir)
        # Create a mock metadata file
        mock_meta = {
            "image_id": "test_img_001",
            "condition": "enhanced",
            "true_details": [
                {"id": "d1", "description": "red car", "category": "vehicle"},
                {"id": "d2", "description": "blue sky", "category": "background"}
            ],
            "false_details_pool": [
                {"id": "f1", "description": "green truck", "category": "vehicle"},
                {"id": "f2", "description": "cloudy sky", "category": "background"}
            ]
        }
        meta_file = meta_dir / "test_img_001.yaml"
        # Using JSON for simplicity in mock, assuming loader handles YAML/JSON interchangeably or we mock the loader
        import json
        with open(meta_file, 'w') as f:
            json.dump(mock_meta, f)

        # Mock the config to return our temp metadata dir
        original_get_stimuli_metadata_dir = get_stimuli_metadata_dir
        get_stimuli_metadata_dir.__globals__['get_config'] = lambda: MagicMock(
            get_stimuli_metadata_dir=lambda: meta_dir
        )

        yield meta_dir, mock_meta

        # Restore
        get_stimuli_metadata_dir.__globals__['get_config'] = lambda: original_get_stimuli_metadata_dir()


def test_session_flow_end_to_end(temp_response_dir, mock_stimuli_metadata):
    """
    Integration test for simulated session flow.

    Asserts that:
    - A session can be initialized.
    - The distractor task runs.
    - Recognition questions are generated and answered.
    - All responses are recorded in a JSON file in the responses directory.
    - The response file contains the expected structure and data.
    """
    meta_dir, mock_meta = mock_stimuli_metadata
    image_id = mock_meta["image_id"]
    participant_id = "sim_participant_001"

    # Prepare arguments for run_simulated_session
    # We need to mock the image loading and display since we don't have real images
    with patch('code.participants.interface.load_image') as mock_load_image, \
         patch('code.participants.interface.display_image') as mock_display_image, \
         patch('code.participants.interface.get_user_input') as mock_get_input:

        # Setup mocks
        mock_load_image.return_value = MagicMock() # Mock PIL Image
        mock_display_image.return_value = True # Simulate successful display

        # Simulate user inputs for the session:
        # 1. Distractor task answers (e.g., 2 + 3 = 5)
        # 2. Recognition answers (True/False)
        # We'll use a queue of inputs to simulate a sequence of questions
        mock_inputs = [
            "5", # Answer to distractor 1
            "8", # Answer to distractor 2
            "yes", # Answer to recognition 1 (True detail)
            "no", # Answer to recognition 2 (False detail)
        ]
        mock_get_input.side_effect = lambda q: mock_inputs.pop(0) if mock_inputs else ""

        # Run the session
        # The function signature might vary, adjust based on actual implementation
        # Assuming it takes participant_id, image_id, and maybe output_dir
        session_manager = SessionManager(
            participant_id=participant_id,
            image_id=image_id,
            output_dir=temp_response_dir
        )

        # Call the main interface function
        # Assuming run_simulated_session uses SessionManager internally or is the entry point
        # For this test, we'll directly call the logic that would be triggered by the CLI
        # or the main entry point of the interface module.
        # Let's assume run_simulated_session is the function that orchestrates the flow.
        run_simulated_session(participant_id, image_id, temp_response_dir)

        # Verify output file exists
        expected_output_file = temp_response_dir / f"{participant_id}_{image_id}_responses.json"
        assert expected_output_file.exists(), f"Response file {expected_output_file} was not created."

        # Load and verify content
        with open(expected_output_file, 'r') as f:
            responses_data = json.load(f)

        # Check structure
        assert "participant_id" in responses_data
        assert "image_id" in responses_data
        assert "responses" in responses_data
        assert "timestamp" in responses_data

        # Check data integrity
        assert responses_data["participant_id"] == participant_id
        assert responses_data["image_id"] == image_id

        # Verify number of responses (2 distractor + 2 recognition = 4)
        assert len(responses_data["responses"]) == 4, f"Expected 4 responses, got {len(responses_data['responses'])}"

        # Verify specific response types (optional, depends on implementation details)
        # For now, just check that we have responses recorded
        for resp in responses_data["responses"]:
            assert "question_id" in resp
            assert "value" in resp
            assert "timestamp" in resp
            assert "question_type" in resp # e.g., 'distractor', 'recognition'

    print(f"Session flow test passed. Responses saved to {expected_output_file}")