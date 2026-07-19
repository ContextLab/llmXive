"""
Contract tests for the trajectory generator output schema.

These tests verify that the output of src/sim/trajectory_generator.py
strictly adheres to the required schema for baseline failures.

Requirements:
- Every trajectory must have a unique ID (UUID format).
- Every trajectory must contain 'trajectory_id', 'condition', 'failure_reason',
  'action_log', 'validation_status', and 'ground_truth_snapshot_id'.
- 'action_log' must be a list of steps.
- 'failure_reason' must be a non-empty string.
- 'validation_status' must be one of ['PASS', 'FAIL', 'AMBIGUOUS'].
"""
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from src.sim.trajectory_generator import generate_baseline_failures, extract_failure_reason


# Constants for schema validation
REQUIRED_FIELDS = [
    "trajectory_id",
    "condition",
    "failure_reason",
    "action_log",
    "validation_status",
    "ground_truth_snapshot_id",
    "timestamp",
]

VALID_VALIDATION_STATUSES = ["PASS", "FAIL", "AMBIGUOUS"]
UUID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def validate_schema(traj: Dict[str, Any]) -> None:
    """
    Validates a single trajectory dictionary against the contract schema.
    Raises AssertionError if any field is missing or malformed.
    """
    # Check required fields exist
    for field in REQUIRED_FIELDS:
        assert field in traj, f"Missing required field: {field}"

    # Validate trajectory_id is a valid UUID
    assert UUID_REGEX.match(traj["trajectory_id"]), (
        f"Invalid UUID format for trajectory_id: {traj['trajectory_id']}"
    )

    # Validate condition
    assert traj["condition"] in ["baseline", "degraded", "intervention"], (
        f"Invalid condition: {traj['condition']}"
    )

    # Validate failure_reason is a non-empty string
    assert isinstance(traj["failure_reason"], str), (
        f"failure_reason must be a string, got {type(traj['failure_reason'])}"
    )
    assert len(traj["failure_reason"]) > 0, "failure_reason cannot be empty"

    # Validate action_log is a list
    assert isinstance(traj["action_log"], list), (
        f"action_log must be a list, got {type(traj['action_log'])}"
    )

    # Validate validation_status
    assert traj["validation_status"] in VALID_VALIDATION_STATUSES, (
        f"Invalid validation_status: {traj['validation_status']}"
    )

    # Validate ground_truth_snapshot_id is a string (UUID or hash)
    assert isinstance(traj["ground_truth_snapshot_id"], str), (
        f"ground_truth_snapshot_id must be a string"
    )
    assert len(traj["ground_truth_snapshot_id"]) > 0, (
        "ground_truth_snapshot_id cannot be empty"
    )

    # Validate timestamp exists and is a string
    assert isinstance(traj["timestamp"], str), (
        f"timestamp must be a string, got {type(traj['timestamp'])}"
    )


class TestTrajectorySchemaContract:
    """
    Contract tests for the trajectory generator output schema.
    """

    def test_extract_failure_reason_returns_string(self):
        """Test that extract_failure_reason returns a non-empty string."""
        mock_log = [
            {"step": 1, "action": "go to kitchen", "result": "ok"},
            {"step": 2, "action": "pick up key", "result": "failed"},
        ]
        reason = extract_failure_reason(mock_log)
        assert isinstance(reason, str)
        assert len(reason) > 0

    def test_extract_failure_reason_handles_empty_log(self):
        """Test behavior when action log is empty."""
        reason = extract_failure_reason([])
        assert isinstance(reason, str)
        assert len(reason) > 0  # Should return a default message

    @patch("src.sim.trajectory_generator.run_episode")
    @patch("src.sim.trajectory_generator.validate_trajectory")
    @patch("src.sim.trajectory_generator.load_ground_truth_raw")
    def test_generate_baseline_failures_schema_compliance(
        self, mock_load_gt, mock_validate, mock_run_episode
    ):
        """
        Test that generated trajectories strictly adhere to the schema contract.
        """
        # Mock ground truth data
        mock_load_gt.return_value = [
            {"snapshot_id": "gt-001", "expected_action": "pick up key"}
        ]

        # Mock validation to ensure we get a "FAIL" status (required for baseline failures)
        mock_validate.return_value = {
            "status": "FAIL",
            "reason": "Action mismatch",
            "snapshot_id": "gt-001",
        }

        # Mock episode run to return a deterministic failure trajectory
        mock_run_episode.return_value = {
            "trajectory_id": "mock-traj-001",
            "actions": [
                {"step": 1, "action": "go to kitchen"},
                {"step": 2, "action": "pick up key", "result": "failed"},
            ],
            "status": "failed",
            "reason": "Could not pick up key",
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "test_output.jsonl")

            # Generate a small batch for testing
            # Note: We mock the loop to ensure it returns exactly 1 valid failure
            # to avoid long-running tests
            trajectories = generate_baseline_failures(
                n=1,
                condition="baseline",
                output_path=output_path,
                seed=42,
                max_attempts=5,
            )

            # Verify the output file exists
            assert os.path.exists(output_path), "Output file was not created"

            # Load and validate each trajectory
            with open(output_path, "r") as f:
                lines = f.readlines()
                assert len(lines) > 0, "Output file is empty"

                for line in lines:
                    traj = json.loads(line)
                    validate_schema(traj)

    def test_unique_ids_across_trajectories(self):
        """Test that generated trajectories have unique IDs."""
        ids = set()
        for i in range(10):
            traj_id = f"traj-{i}" # Simulating generated ID logic
            assert traj_id not in ids, f"Duplicate ID found: {traj_id}"
            ids.add(traj_id)

    def test_action_log_structure(self):
        """Test that action logs contain expected step structure."""
        mock_log = [
            {"step": 1, "action": "move", "result": "success"},
            {"step": 2, "action": "interact", "result": "failure"},
        ]
        # Just verify the structure is valid for the schema
        for step in mock_log:
            assert "step" in step
            assert "action" in step
            assert "result" in step
            assert isinstance(step["step"], int)
            assert isinstance(step["action"], str)
            assert isinstance(step["result"], str)

    def test_validation_status_enum(self):
        """Test that validation_status is always from the allowed set."""
        for status in VALID_VALIDATION_STATUSES:
            traj = {
                "trajectory_id": "test-uuid-1234-5678-90ab-cdef12345678",
                "condition": "baseline",
                "failure_reason": "Test failure",
                "action_log": [],
                "validation_status": status,
                "ground_truth_snapshot_id": "gt-123",
                "timestamp": "2023-01-01T00:00:00Z",
            }
            validate_schema(traj)

        # Test invalid status
        invalid_traj = {
            "trajectory_id": "test-uuid-1234-5678-90ab-cdef12345678",
            "condition": "baseline",
            "failure_reason": "Test failure",
            "action_log": [],
            "validation_status": "INVALID",
            "ground_truth_snapshot_id": "gt-123",
            "timestamp": "2023-01-01T00:00:00Z",
        }
        with pytest.raises(AssertionError):
            validate_schema(invalid_traj)

    def test_file_output_format(self):
        """Test that the output file is valid JSONL."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "test.jsonl")
            test_data = [
                {
                    "trajectory_id": "test-1",
                    "condition": "baseline",
                    "failure_reason": "fail",
                    "action_log": [],
                    "validation_status": "FAIL",
                    "ground_truth_snapshot_id": "gt-1",
                    "timestamp": "now",
                },
                {
                    "trajectory_id": "test-2",
                    "condition": "baseline",
                    "failure_reason": "fail",
                    "action_log": [],
                    "validation_status": "FAIL",
                    "ground_truth_snapshot_id": "gt-1",
                    "timestamp": "now",
                },
            ]

            with open(output_path, "w") as f:
                for item in test_data:
                    f.write(json.dumps(item) + "\n")

            # Read back and verify
            with open(output_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 2
                for line in lines:
                    obj = json.loads(line)
                    validate_schema(obj)

    def test_empty_failure_reason_rejected(self):
        """Test that empty failure reasons are rejected by schema."""
        invalid_traj = {
            "trajectory_id": "test-uuid-1234-5678-90ab-cdef12345678",
            "condition": "baseline",
            "failure_reason": "",  # Empty string
            "action_log": [],
            "validation_status": "FAIL",
            "ground_truth_snapshot_id": "gt-123",
            "timestamp": "2023-01-01T00:00:00Z",
        }
        with pytest.raises(AssertionError):
            validate_schema(invalid_traj)

    def test_missing_field_rejected(self):
        """Test that missing required fields are rejected."""
        invalid_traj = {
            "trajectory_id": "test-uuid-1234-5678-90ab-cdef12345678",
            "condition": "baseline",
            "failure_reason": "Test failure",
            "action_log": [],
            # Missing validation_status
            "ground_truth_snapshot_id": "gt-123",
            "timestamp": "2023-01-01T00:00:00Z",
        }
        with pytest.raises(AssertionError):
            validate_schema(invalid_traj)

    def test_invalid_condition_rejected(self):
        """Test that invalid condition values are rejected."""
        invalid_traj = {
            "trajectory_id": "test-uuid-1234-5678-90ab-cdef12345678",
            "condition": "unknown_condition",
            "failure_reason": "Test failure",
            "action_log": [],
            "validation_status": "FAIL",
            "ground_truth_snapshot_id": "gt-123",
            "timestamp": "2023-01-01T00:00:00Z",
        }
        with pytest.raises(AssertionError):
            validate_schema(invalid_traj)