import sys
import json
from pathlib import Path

import pytest

# Import the module under test
from src.analysis import validation_by_session

def test_validation_by_session_aggregation(tmp_path, monkeypatch):
    """
    Create minimal interaction logs and validation records, run the aggregation
    script, and verify that the output contains the correct session mapping
    and overall_success flag.
    """
    # ------------------------------------------------------------------
    # Prepare fake interaction logs
    # ------------------------------------------------------------------
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True)
    interactions_path = log_dir / "interactions_clean.jsonl"
    interactions = [
        {"participant_id": "sess1", "figure_id": "0"},
        {"participant_id": "sess2", "figure_id": "1"},
    ]
    interactions_path.write_text("\n".join(json.dumps(r) for r in interactions) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------
    # Prepare fake validation records
    # ------------------------------------------------------------------
    val_dir = tmp_path / "validation"
    val_dir.mkdir(parents=True)
    validation_path = val_dir / "semantic_validation.jsonl"
    validations = [
        {"figure_id": "0", "vector_match": True, "semantic_pass": False},
        {"figure_id": "1", "vector_match": False, "semantic_pass": True},
    ]
    validation_path.write_text("\n".join(json.dumps(r) for r in validations) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------
    # Define output path
    # ------------------------------------------------------------------
    output_path = tmp_path / "results" / "validation_by_session.jsonl"

    # ------------------------------------------------------------------
    # Run the script via its CLI entry point
    # ------------------------------------------------------------------
    args = [
        "prog",
        "--log-dir",
        str(log_dir),
        "--validation-dir",
        str(val_dir),
        "--output-path",
        str(output_path),
    ]
    monkeypatch.setattr(sys, "argv", args)

    # The script returns an exit code; we assert success (0)
    exit_code = validation_by_session.main()
    assert exit_code == 0

    # ------------------------------------------------------------------
    # Verify the aggregated output
    # ------------------------------------------------------------------
    assert output_path.is_file()
    lines = [json.loads(l) for l in output_path.read_text().splitlines() if l.strip()]
    assert len(lines) == 2

    # Build a lookup for easier assertions
    lookup = {rec["task_id"]: rec for rec in lines}

    # Session mapping should match the interaction logs
    assert lookup["0"]["session_id"] == "sess1"
    assert lookup["1"]["session_id"] == "sess2"

    # overall_success should be True for both because each record has at
    # least one of the success conditions satisfied.
    assert lookup["0"]["overall_success"] is True
    assert lookup["1"]["overall_success"] is True