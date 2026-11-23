"""
Unit tests for the Baseline Adapter module.
Validates parsing logic, schema compliance, and error handling.
"""
import json
import pytest
import os
import sys
import tempfile
import logging

# Ensure code/ is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from baseline_adapter import (
    parse_baseline_output,
    validate_against_masked_ground_truth,
    process_baseline_run_file,
    BaselineAdapterError,
    VALID_ACTIONS
)
from logger import get_logger

logger = get_logger(__name__)


class TestParseBaselineOutput:
    """Tests for the parse_baseline_output function."""

    def test_valid_output(self):
        """Test parsing a valid baseline output."""
        raw = json.dumps({
            "action": "move_up",
            "mental_map": json.dumps({
                "ascii_grid": "test",
                "event_log": [],
                "ground_truth_state": {},
                "masked_ground_truth": {}
            })
        })
        result = parse_baseline_output(raw, run_id="test-1")
        assert result["action"] == "move_up"
        assert isinstance(result["mental_map"], str)
        assert json.loads(result["mental_map"])["ascii_grid"] == "test"

    def test_missing_action(self):
        """Test error when 'action' is missing."""
        raw = json.dumps({"mental_map": "{}"})
        with pytest.raises(BaselineAdapterError, match="Missing required field 'action'"):
            parse_baseline_output(raw)

    def test_missing_mental_map(self):
        """Test error when 'mental_map' is missing."""
        raw = json.dumps({"action": "move_up"})
        with pytest.raises(BaselineAdapterError, match="Missing required field 'mental_map'"):
            parse_baseline_output(raw)

    def test_invalid_action(self):
        """Test error when 'action' is not in VALID_ACTIONS."""
        raw = json.dumps({"action": "teleport", "mental_map": "{}"})
        with pytest.raises(BaselineAdapterError, match="Invalid action 'teleport'"):
            parse_baseline_output(raw)

    def test_invalid_json(self):
        """Test error when raw output is not valid JSON."""
        raw = "not json at all"
        with pytest.raises(BaselineAdapterError, match="Failed to parse raw output as JSON"):
            parse_baseline_output(raw)

    def test_mental_map_not_json_string(self):
        """Test error when mental_map field is not a string or invalid JSON."""
        # mental_map is a string but not valid JSON
        raw = json.dumps({
            "action": "move_up",
            "mental_map": "this is not json"
        })
        with pytest.raises(BaselineAdapterError, match="Field 'mental_map' is not valid JSON"):
            parse_baseline_output(raw)

    def test_mental_map_not_object(self):
        """Test error when mental_map JSON is not an object."""
        raw = json.dumps({
            "action": "move_up",
            "mental_map": "[]"  # Array instead of object
        })
        with pytest.raises(BaselineAdapterError, match="Field 'mental_map' content must be a JSON object"):
            parse_baseline_output(raw)


class TestValidateAgainstMaskedGroundTruth:
    """Tests for the validation function."""

    def test_valid_structure(self):
        """Test validation passes with correct structure."""
        adapter_out = {
            "action": "move_up",
            "mental_map": json.dumps({
                "ascii_grid": "grid",
                "event_log": [],
                "ground_truth_state": {},
                "masked_ground_truth": {}
            })
        }
        mask_gt = {"dummy": "data"}
        is_valid, errors = validate_against_masked_ground_truth(adapter_out, mask_gt)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_keys_in_mental_map(self):
        """Test validation fails if mental_map missing required keys."""
        adapter_out = {
            "action": "move_up",
            "mental_map": json.dumps({"ascii_grid": "grid"})  # Missing others
        }
        mask_gt = {"dummy": "data"}
        is_valid, errors = validate_against_masked_ground_truth(adapter_out, mask_gt)
        assert is_valid is False
        assert "missing required keys" in errors[0].lower()

    def test_invalid_mental_map_json(self):
        """Test validation fails if mental_map is not JSON."""
        adapter_out = {
            "action": "move_up",
            "mental_map": "not json"
        }
        mask_gt = {"dummy": "data"}
        is_valid, errors = validate_against_masked_ground_truth(adapter_out, mask_gt)
        assert is_valid is False
        assert "not valid JSON" in errors[0]


class TestProcessBaselineRunFile:
    """Tests for file processing."""

    def test_process_and_save(self):
        """Test processing a file and saving output."""
        raw_data = json.dumps({
            "action": "wait",
            "mental_map": json.dumps({
                "ascii_grid": "test",
                "event_log": [],
                "ground_truth_state": {},
                "masked_ground_truth": {}
            })
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.json")
            output_path = os.path.join(tmpdir, "output.json")

            with open(input_path, "w") as f:
                f.write(raw_data)

            result = process_baseline_run_file(input_path, output_path)

            assert result["action"] == "wait"
            assert os.path.exists(output_path)

            with open(output_path, "r") as f:
                saved = json.load(f)
            assert saved["action"] == "wait"

    def test_process_invalid_file(self):
        """Test processing an invalid file raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "invalid.json")
            output_path = os.path.join(tmpdir, "output.json")

            with open(input_path, "w") as f:
                f.write("bad json")

            with pytest.raises(BaselineAdapterError):
                process_baseline_run_file(input_path, output_path)