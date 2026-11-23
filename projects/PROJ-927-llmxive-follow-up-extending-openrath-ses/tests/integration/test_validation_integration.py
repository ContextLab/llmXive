"""
Integration test for workflow validation against generated ground truth files.
This ensures that the generator (T012/T013) produces files that satisfy SC-005.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path

# Import generator to create test data
from generators.workflow_generator import generate_workflow, calculate_sha256
# Import validator
from generators.workflow_validator import validate_workflow, validate_workflow_file, ValidationError

class TestValidationIntegration:
    def test_generated_workflow_passes_validation(self, tmp_path):
        """
        Generate a workflow using the generator, save it, and verify it passes
        the SC-005 validation logic.
        """
        # Generate a workflow
        workflow = generate_workflow(workflow_id="int-test-001")
        
        # Save to temp file
        file_path = tmp_path / "int_test_workflow.json"
        with open(file_path, 'w') as f:
            json.dump(workflow, f)
        
        # Validate using the file validator
        assert validate_workflow_file(str(file_path)) is True

    def test_generated_batch_passes_validation(self, tmp_path):
        """
        Generate a batch of workflows and validate them all.
        """
        # Generate a batch (using a small count for speed)
        # Note: generate_ground_truth_batch writes to disk, we'll simulate the check
        # by generating individual workflows in a loop to ensure they pass validation
        ids = ["batch-001", "batch-002", "batch-003"]
        
        for wf_id in ids:
            workflow = generate_workflow(workflow_id=wf_id)
            file_path = tmp_path / f"{wf_id}.json"
            with open(file_path, 'w') as f:
                json.dump(workflow, f)
            
            # Validate
            assert validate_workflow_file(str(file_path)) is True, f"Failed validation for {wf_id}"

    def test_validation_catches_corrupted_file(self, tmp_path):
        """
        Create a file that mimics a corrupted workflow (missing key) and ensure
        validation catches it.
        """
        # Create a valid workflow first
        workflow = generate_workflow(workflow_id="corrupt-test")
        
        # Corrupt it by removing a required key
        del workflow["state_snapshots"]
        
        file_path = tmp_path / "corrupt_workflow.json"
        with open(file_path, 'w') as f:
            json.dump(workflow, f)
        
        # Validation should fail
        with pytest.raises(ValidationError) as exc_info:
            validate_workflow_file(str(file_path))
        
        assert "state_snapshots" in str(exc_info.value)
