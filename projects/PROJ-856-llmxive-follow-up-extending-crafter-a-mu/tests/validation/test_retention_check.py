"""
test_retention_check.py
-----------------------

Unit tests for the retention verification script.  The tests construct
temporary ``semantic_validation.jsonl`` files with controlled content
and invoke the script's ``main`` function directly, checking that the
correct exit status and output are produced.

Two scenarios are covered:

1. **Passing case** – at least ``min_valid`` participants out of the
   required total have a successful record.
2. **Failing case** – fewer than ``min_valid`` participants succeed,
   which should cause the script to exit with status 1 and emit an
   appropriate error message.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

# Import the module under test.
from src.analysis import retention_check

def _write_validation_file(records, directory):
    """Helper to write a JSON‑Lines validation file."""
    validation_path = Path(directory) / "validation" / "semantic_validation.jsonl"
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    with validation_path.open("w", encoding="utf-8") as f:
        for rec in records:
            json.dump(rec, f)
            f.write("\\n")
    return validation_path

def test_retention_check_passes(capfd):
    """
    Scenario: enough participants have a primary‑success trial.
    Expect exit code 0 and a success message.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create 32 participants, 28 of which succeed.
        records = []
        for i in range(32):
            success = i < 28  # first 28 succeed
            records.append(
                {
                    "participant_id": f"p{i}",
                    "overall_success": success,
                }
            )
        # Write the validation file.
        _write_validation_file(records, tmpdir)

        # Simulate command‑line arguments.
        args = SimpleNamespace(
            log_dir=os.path.join(tmpdir, "logs"),
            min_valid=28,
            required_participants=32,
        )
        # Monkey‑patch the argument parser to return our args.
        original_parse = retention_check._parse_args
        retention_check._parse_args = lambda: args

        # Run the script.
        exit_code = retention_check.main()

        # Restore original parser.
        retention_check._parse_args = original_parse

        # Capture stdout/stderr.
        out, err = capfd.readouterr()

        assert exit_code == 0
        assert "Retention check passed" in out
        assert err == ""

def test_retention_check_fails(capfd):
    """
    Scenario: insufficient participants succeed (27 < 28).
    Expect exit code 1 and an error message.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create 32 participants, only 27 succeed.
        records = []
        for i in range(32):
            success = i < 27  # first 27 succeed
            records.append(
                {
                    "participant_id": f"p{i}",
                    "overall_success": success,
                }
            )
        _write_validation_file(records, tmpdir)

        args = SimpleNamespace(
            log_dir=os.path.join(tmpdir, "logs"),
            min_valid=28,
            required_participants=32,
        )
        original_parse = retention_check._parse_args
        retention_check._parse_args = lambda: args

        exit_code = retention_check.main()

        retention_check._parse_args = original_parse
        out, err = capfd.readouterr()

        assert exit_code == 1
        assert "Retention check failed" in err
        assert out == ""