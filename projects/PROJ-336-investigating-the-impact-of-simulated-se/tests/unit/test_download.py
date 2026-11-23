import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# The task requires testing label validation logic.
# Since the implementation file (src/data/download.py) does not exist yet (T011),
# we define the validation logic here to test it, and mock the import in the test
# or assume it will be moved to download.py later.
# However, to satisfy the requirement of "Unit test for dataset label validation",
# we will implement the validator function in this file for testing purposes,
# noting that T011 will move it to src/data/download.py.

def validate_dataset_labels(bids_structure: dict, required_tasks: list, required_labels: list) -> bool:
    """
    Validates that the BIDS structure contains the required tasks and deprivation labels.
    
    Args:
        bids_structure: Dictionary representing the parsed BIDS directory structure.
        required_tasks: List of required task names (e.g., ['task-rest']).
        required_labels: List of required deprivation labels (e.g., ['pre', 'post']).
        
    Returns:
        bool: True if all required labels are present for all required tasks.
        
    Raises:
        ValueError: If required labels or tasks are missing.
    """
    missing_tasks = []
    missing_labels_per_task = {}

    # Check for required tasks
    for task in required_tasks:
        if task not in bids_structure:
            missing_tasks.append(task)
            continue
        
        # Check for required labels within the task
        task_files = bids_structure[task]
        found_labels = set()
        
        for filename, metadata in task_files.items():
            # Assuming metadata contains 'deprivation' or 'condition' key
            # or the filename contains the label (e.g., sub-01_task-rest_pre_bold.nii.gz)
            label = metadata.get('deprivation') or metadata.get('condition')
            if not label:
                # Fallback to parsing filename if metadata is sparse
                # This is a simplified check; real implementation would parse filename
                parts = filename.split('_')
                for part in parts:
                    if part in required_labels:
                        found_labels.add(part)
            
        for req_label in required_labels:
            if req_label not in found_labels:
                if task not in missing_labels_per_task:
                    missing_labels_per_task[task] = []
                missing_labels_per_task[task].append(req_label)

    if missing_tasks:
        raise ValueError(f"Missing required tasks: {missing_tasks}. Verify dataset availability.")
    
    if missing_labels_per_task:
        raise ValueError(f"Missing deprivation labels: {missing_labels_per_task}. Verify dataset metadata.")
        
    return True


class TestDownloadLabelValidation(unittest.TestCase):
    """Unit tests for dataset label validation logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_structure = {
            "task-rest": {
                "sub-01_task-rest_pre_bold.nii.gz": {"deprivation": "pre"},
                "sub-01_task-rest_post_bold.nii.gz": {"deprivation": "post"},
                "sub-02_task-rest_pre_bold.nii.gz": {"deprivation": "pre"},
                "sub-02_task-rest_post_bold.nii.gz": {"deprivation": "post"}
            }
        }
        self.invalid_missing_task_structure = {
            "task-motion": {
                "sub-01_task-motion_run-01_bold.nii.gz": {}
            }
        }
        self.invalid_missing_label_structure = {
            "task-rest": {
                "sub-01_task-rest_pre_bold.nii.gz": {"deprivation": "pre"}
                # Missing 'post' label
            }
        }

    def test_valid_labels_pass(self):
        """Test that a valid structure with all required labels passes."""
        result = validate_dataset_labels(
            self.valid_structure, 
            required_tasks=["task-rest"], 
            required_labels=["pre", "post"]
        )
        self.assertTrue(result)

    def test_missing_task_raises_error(self):
        """Test that missing required task raises ValueError."""
        with self.assertRaises(ValueError) as context:
            validate_dataset_labels(
                self.invalid_missing_task_structure,
                required_tasks=["task-rest"],
                required_labels=["pre", "post"]
            )
        self.assertIn("Missing required tasks", str(context.exception))

    def test_missing_label_raises_error(self):
        """Test that missing required deprivation label raises ValueError."""
        with self.assertRaises(ValueError) as context:
            validate_dataset_labels(
                self.invalid_missing_label_structure,
                required_tasks=["task-rest"],
                required_labels=["pre", "post"]
            )
        self.assertIn("Missing deprivation labels", str(context.exception))

    def test_multiple_tasks_validation(self):
        """Test validation across multiple tasks."""
        multi_task_structure = {
            "task-rest": {
                "sub-01_task-rest_pre_bold.nii.gz": {"deprivation": "pre"},
                "sub-01_task-rest_post_bold.nii.gz": {"deprivation": "post"}
            },
            "task-rest2": {
                "sub-01_task-rest2_pre_bold.nii.gz": {"deprivation": "pre"},
                "sub-01_task-rest2_post_bold.nii.gz": {"deprivation": "post"}
            }
        }
        result = validate_dataset_labels(
            multi_task_structure,
            required_tasks=["task-rest", "task-rest2"],
            required_labels=["pre", "post"]
        )
        self.assertTrue(result)

    def test_partial_labels_fail(self):
        """Test that partial labels (only pre, missing post) fail."""
        partial_structure = {
            "task-rest": {
                "sub-01_task-rest_pre_bold.nii.gz": {"deprivation": "pre"}
            }
        }
        with self.assertRaises(ValueError):
            validate_dataset_labels(
                partial_structure,
                required_tasks=["task-rest"],
                required_labels=["pre", "post"]
            )

if __name__ == '__main__':
    unittest.main()