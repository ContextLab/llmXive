"""
Contract tests for CAQ availability validation (Task T101).

These tests verify:
1. Successful validation when the CAQ field is present.
2. Proper handling (exception raising and process exit) when the CAQ field is missing.
"""

import json
import sys

import pytest

from data.loader import validate_caq_availability
from errors import DataMissingCreativityError
from main import run_validation

from llmxive_toolkit import paths

def test_validate_caq_availability_success():
    """validate_caq_availability should return True when CAQ is present."""
    behavioral = {"CAQ": 4.2, "age": 30}
    assert validate_caq_availability(behavioral) is True

def test_validate_caq_availability_missing_raises():
    """When CAQ is missing, validate_caq_availability must raise DataMissingCreativityError."""
    behavioral = {"age": 30}
    with pytest.raises(DataMissingCreativityError) as exc:
        validate_caq_availability(behavioral)
    # The error message must be the required error code.
    assert str(exc.value) == "DATA_MISSING_CREATIVITY"

def test_run_validation_exits_on_missing_caq(tmp_path, caplog):
    """
    run_validation should exit with code 1 and log the DATA_MISSING_CREATIVITY
    reason when the behavioral JSON lacks a CAQ field.
    """
    # Prepare a minimal behavioral JSON without CAQ.
    behav_path = paths.data("raw", "behavioral.json")
    behav_path.parent.mkdir(parents=True, exist_ok=True)
    behav_path.write_text(json.dumps({}))

    # Capture logs and the SystemExit.
    with pytest.raises(SystemExit) as exit_exc:
        run_validation()

    # Verify exit code.
    assert exit_exc.value.code == 1

    # Ensure the logged message contains the required error code.
    # caplog captures logging output; we also check stdout via captured output.
    logged_messages = caplog.text
    assert "DATA_MISSING_CREATIVITY" in logged_messages

    # Clean up the temporary file for isolation.
    behav_path.unlink(missing_ok=True)