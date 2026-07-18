"""
Integration tests for data_collection_interface.py (US1 & US2).
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We need to mock the stimulus loader and models to avoid file system dependencies
# during unit/integration testing of the logic flow.

# Add code directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models import StimulusOrigin, Stimulus
# We will mock the actual import of data_collection_interface to control dependencies
# or import it directly if we set up the environment correctly.
# For this test, we assume the module is importable.
from data_collection_interface import collect_covariates, present_stimuli, write_session_file, run_session

class TestDataCollectionInterface:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Setup: Create temp directories if needed
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.temp_dir) / "data" / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Patch OUTPUT_DIR in the module
        import data_collection_interface
        self.original_output_dir = data_collection_interface.OUTPUT_DIR
        data_collection_interface.OUTPUT_DIR = self.raw_dir

        yield

        # Teardown
        shutil.rmtree(self.temp_dir)
        data_collection_interface.OUTPUT_DIR = self.original_output_dir

    def test_collect_covariates_valid_input(self):
        """Test US2: Collecting INCOM and Usage with valid inputs."""
        mock_inputs = iter(["25", "10.5"])
        
        with patch('builtins.input', side_effect=mock_inputs):
            result = collect_covariates()
        
        assert result["INCOM_score"] == 25
        assert result["usage_frequency"] == 10.5

    def test_collect_covariates_invalid_input_retry(self):
        """Test US2: Retry logic for invalid inputs."""
        # First two are invalid, third is valid
        mock_inputs = iter(["abc", "-5", "30", "5"])
        
        with patch('builtins.input', side_effect=mock_inputs):
            result = collect_covariates()
        
        assert result["INCOM_score"] == 30
        assert result["usage_frequency"] == 5.0

    def test_present_stimuli_randomization(self):
        """Test US1: Stimuli are shuffled and responses recorded."""
        # Create mock stimuli
        stimuli = [
            Stimulus(stimulus_id="s1", origin=StimulusOrigin.AI, path="p1", metadata={}),
            Stimulus(stimulus_id="s2", origin=StimulusOrigin.HUMAN, path="p2", metadata={}),
            Stimulus(stimulus_id="s3", origin=StimulusOrigin.AI, path="p3", metadata={}),
        ]
        
        # Mock inputs for BISS scores
        mock_inputs = iter(["3", "5", "7"])
        
        with patch('builtins.input', side_effect=mock_inputs):
            responses = present_stimuli(stimuli, "test-participant")
        
        assert len(responses) == 3
        assert all(r["BISS_score"] in [3, 5, 7] for r in responses)
        assert all(r["participant_id"] == "test-participant" for r in responses)
        
        # Check that origin matches stimulus
        # Note: The order might change due to shuffle, but the set of origins should match
        response_origins = {r["origin"] for r in responses}
        expected_origins = {s.origin.value for s in stimuli}
        assert response_origins == expected_origins

    def test_write_session_file_schema(self):
        """Test that the output file matches the required flat schema."""
        covariates = {"INCOM_score": 10, "usage_frequency": 2.0}
        responses = [
            {
                "stimulus_id": "s1",
                "origin": "ai",
                "timestamp": "2023-01-01T00:00:00",
                "BISS_score": 5,
                "participant_id": "p1",
                "INCOM_score": 0, # Placeholder
                "usage_frequency": 0.0 # Placeholder
            }
        ]
        
        file_path = write_session_file("p1", covariates, responses)
        
        assert os.path.exists(file_path)
        
        with open(file_path, 'r') as f:
            line = f.readline()
            data = json.loads(line)
        
        # Verify flat schema keys
        required_keys = [
            "stimulus_id", "origin", "timestamp", "BISS_score", 
            "participant_id", "INCOM_score", "usage_frequency"
        ]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"
        
        # Verify values
        assert data["INCOM_score"] == 10
        assert data["usage_frequency"] == 2.0

    def test_partial_session_discarded(self):
        """Test that aborting a session does not write a file."""
        stimuli = [
            Stimulus(stimulus_id="s1", origin=StimulusOrigin.AI, path="p1", metadata={}),
            Stimulus(stimulus_id="s2", origin=StimulusOrigin.HUMAN, path="p2", metadata={}),
        ]
        
        # User enters BISS for first, then aborts
        mock_inputs = iter(["5", "quit"])
        
        with patch('builtins.input', side_effect=mock_inputs):
            with pytest.raises(SystemExit) as exc_info:
                present_stimuli(stimuli, "abort-test")
        
            assert str(exc_info.value) == "PARTIAL_SESSION_ABORT"
        
        # Check that no file was written for this session
        # (The write function is called after present_stimuli returns, which it won't in abort case)
        # But we must ensure the run_session flow doesn't write.
        # In the current implementation, write_session_file is called AFTER present_stimuli returns.
        # If present_stimuli raises SystemExit, write_session_file is never called.
        # So the file should not exist.
        file_path = self.raw_dir / "session_abort-test.jsonl"
        assert not file_path.exists()