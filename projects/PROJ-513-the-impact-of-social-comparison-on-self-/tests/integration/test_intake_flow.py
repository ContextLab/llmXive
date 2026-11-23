"""
Integration test for covariate locking before stimulus unlock (US2).

This test verifies that:
1. The data collection interface enforces the collection of INCOM and Usage
   covariates BEFORE any stimulus presentation begins.
2. The session flow correctly transitions from 'intake' to 'stimuli' phase
   only after valid covariate data is recorded.
3. The output schema matches the requirements (flat keys, correct field names).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path to import code modules
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data_collection_interface import collect_covariates, present_stimuli, run_session
from models import Participant, StimulusOrigin
import stimulus_loader

def test_intake_flow_locks_stimuli_until_covariates_complete():
    """
    Integration test: Verify that stimuli presentation is blocked until 
    INCOM and usage_frequency are successfully collected.
    """
    # Setup: Mock stimuli paths to avoid needing real images for this logic test
    # We mock the stimulus loader to return a minimal valid structure
    mock_stimuli = [
        {"id": "img_001", "origin": "AI", "path": "fake_ai.jpg"},
        {"id": "img_002", "origin": "Human", "path": "fake_human.jpg"},
    ]
    
    with patch('stimulus_loader.get_stimuli_paths', return_value=([], [])), \
         patch('stimulus_loader.load_stimuli', return_value=mock_stimuli), \
         patch('stimulus_loader.validate_metadata_fields', return_value=True), \
         tempfile.TemporaryDirectory() as tmp_dir:
        
        output_dir = Path(tmp_dir)
        session_id = "test_session_001"
        
        # Mock inputs to simulate the user flow:
        # 1. Enter INCOM score (e.g., 45)
        # 2. Enter Usage frequency (e.g., 10 hours)
        # 3. Enter BISS score for image 1 (e.g., 5)
        # 4. Enter BISS score for image 2 (e.g., 3)
        input_sequence = [
            "45",          # INCOM score
            "10",          # Usage frequency
            "5",           # BISS for img_001
            "3",           # BISS for img_002
            "y",           # Confirm completion
        ]
        
        input_iter = iter(input_sequence)
        
        def mock_input(prompt):
            val = next(input_iter)
            return val
        
        with patch('builtins.input', side_effect=mock_input):
            # Run the session
            # Note: run_session handles the flow: intake -> stimuli -> write
            success = run_session(
                participant_id="P001",
                output_dir=str(output_dir),
                session_id=session_id
            )
        
        # Assertions
        assert success, "Session should complete successfully"
        
        # Verify output file exists
        output_file = output_dir / f"session_{session_id}.jsonl"
        assert output_file.exists(), f"Output file {output_file} should exist"
        
        # Verify content
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        # We expect 2 lines: one for intake covariates (if recorded as a record) 
        # or one file containing all entries. 
        # Based on T013 spec: "Output data/raw/session_{id}.jsonl with flat keys"
        # The implementation typically writes a single JSON object per line per stimulus,
        # plus potentially a header or intake record. 
        # Let's verify the data structure matches the schema.
        
        records = [json.loads(line) for line in lines if line.strip()]
        
        # Find the record containing covariates (usually the first or marked by type)
        # Based on T013: schema includes INCOM_score and usage_frequency in the flat keys.
        # If the implementation writes one record per stimulus, the covariates might be 
        # repeated or stored in a separate 'intake' record. 
        # We check if ANY record has the required covariates and if the flow worked.
        
        has_incoming = False
        has_usage = False
        has_stimuli_records = 0
        
        for record in records:
            if 'INCOM_score' in record:
                has_incoming = True
                assert record['INCOM_score'] == 45, "INCOM score should be 45"
            if 'usage_frequency' in record:
                has_usage = True
                assert record['usage_frequency'] == 10, "Usage frequency should be 10"
            if 'stimulus_id' in record:
                has_stimuli_records += 1
        
        assert has_incoming, "Record must contain INCOM_score"
        assert has_usage, "Record must contain usage_frequency"
        assert has_stimuli_records == 2, "Should have 2 stimulus records"
        
        # Critical Logic Check:
        # The test passes if the session completed, meaning the intake flow
        # successfully captured data before proceeding to stimuli.
        # If the implementation had a bug where it presented stimuli first,
        # the input sequence would have been misaligned (e.g., asking for BISS first),
        # causing the mock_input to fail or the data to be wrong.
        # Since we verified the data is correct (INCOM=45, Usage=10), the lock worked.
        
        print("Test passed: Covariate locking verified.")

def test_intake_flow_rejects_invalid_covariates():
    """
    Integration test: Verify that invalid covariate inputs (e.g., non-numeric)
    are handled and the user is prompted again, preventing progression to stimuli.
    """
    mock_stimuli = [
        {"id": "img_001", "origin": "AI", "path": "fake_ai.jpg"},
    ]
    
    with patch('stimulus_loader.get_stimuli_paths', return_value=([], [])), \
         patch('stimulus_loader.load_stimuli', return_value=mock_stimuli), \
         patch('stimulus_loader.validate_metadata_fields', return_value=True), \
         tempfile.TemporaryDirectory() as tmp_dir:
        
        output_dir = Path(tmp_dir)
        session_id = "test_session_002"
        
        # Input sequence:
        # 1. Invalid INCOM (text)
        # 2. Valid INCOM (45)
        # 3. Valid Usage (10)
        # 4. Valid BISS (5)
        input_sequence = [
            "invalid",       # Should be rejected
            "45",            # Valid INCOM
            "10",            # Valid Usage
            "5",             # Valid BISS
            "y",
        ]
        
        input_iter = iter(input_sequence)
        
        def mock_input(prompt):
            val = next(input_iter)
            return val
        
        with patch('builtins.input', side_effect=mock_input):
            success = run_session(
                participant_id="P002",
                output_dir=str(output_dir),
                session_id=session_id
            )
        
        assert success, "Session should complete after valid inputs"
        
        output_file = output_dir / f"session_{session_id}.jsonl"
        with open(output_file, 'r') as f:
            content = f.read()
        
        # Verify the correct data was recorded despite the initial invalid input
        assert '"INCOM_score": 45' in content or '"INCOM_score":45' in content, "Correct INCOM should be recorded"
        assert '"usage_frequency": 10' in content or '"usage_frequency":10' in content, "Correct usage should be recorded"
        
        print("Test passed: Invalid input handling verified.")

if __name__ == "__main__":
    test_intake_flow_locks_stimuli_until_covariates_complete()
    test_intake_flow_rejects_invalid_covariates()
    print("All integration tests for T019 passed.")
