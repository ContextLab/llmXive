"""
Test that the aggregation script also writes the effective N per participant.
"""

import json
import sys
from pathlib import Path

import pytest

# Import the script's main function
from src.analysis.validation_by_session import main as agg_main

@pytest.fixture
def tmp_data(tmp_path):
    """
    Set up a temporary data tree containing:
    - interaction log (interactions_clean.jsonl)
    - ground‑truth directory (empty – not used in this test)
    - validation directory with semantic_validation.jsonl
    Returns a dict with the paths.
    """
    # Interaction log
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True)
    interactions_path = log_dir / "interactions_clean.jsonl"
    interactions = [
        {
            "participant_id": "sess_1",
            "figure_id": "0",
            "interface": "structured",
            "status": "completed",
        },
        {
            "participant_id": "sess_2",
            "figure_id": "1",
            "interface": "chat",
            # No explicit status → defaults to completed
        },
        {
            "participant_id": "sess_1",
            "figure_id": "2",
            "interface": "structured",
            "status": "aborted",
        },
    ]
    with interactions_path.open("w", encoding="utf-8") as f:
        for rec in interactions:
            f.write(json.dumps(rec) + "\n")

    # Validation records
    val_dir = tmp_path / "validation"
    val_dir.mkdir(parents=True)
    validation_path = val_dir / "semantic_validation.jsonl"
    validations = [
        {"task_id": "0", "vector_match": True, "semantic_pass": True},
        {"task_id": "1", "vector_match": False, "semantic_pass": True},
        {"task_id": "2", "vector_match": False, "semantic_pass": False},
    ]
    with validation_path.open("w", encoding="utf-8") as f:
        for rec in validations:
            f.write(json.dumps(rec) + "\n")

    # Ground‑truth (not needed for this test but required by the script).
    gt_dir = tmp_path / "ground_truth"
    gt_dir.mkdir(parents=True)

    # Output paths
    output_path = tmp_path / "semantic_validation_by_session.jsonl"
    effective_n_path = tmp_path / "effective_N_by_participant.jsonl"

    return {
        "log_dir": log_dir,
        "validation_dir": val_dir,
        "ground_truth_dir": gt_dir,
        "output_path": output_path,
        "effective_n_path": effective_n_path,
    }

def test_effective_n_is_written(tmp_data, monkeypatch):
    """
    Run the aggregation script and verify that the effective N file is created
    with the correct counts (non‑aborted tasks per session).
    """
    # Patch sys.argv for the script
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validation_by_session.py",
            "--log-dir",
            str(tmp_data["log_dir"]),
            "--validation-dir",
            str(tmp_data["validation_dir"]),
            "--ground-truth-dir",
            str(tmp_data["ground_truth_dir"]),
            "--output-path",
            str(tmp_data["output_path"]),
            "--effective-n-output",
            str(tmp_data["effective_n_path"]),
        ],
    )

    # The script calls the validation step as a subprocess; we patch
    # subprocess.run to a no‑op that pretends validation succeeded.
    def fake_subprocess_run(*args, **kwargs):
        class Result:
            returncode = 0
            stdout = ""
            stderr = ""
        return Result()
    monkeypatch.setattr("subprocess.run", fake_subprocess_run)

    exit_code = agg_main()
    assert exit_code == 0, "Aggregation script should exit with code 0"

    # Verify the effective N file exists
    eff_path = tmp_data["effective_n_path"]
    assert eff_path.is_file(), "Effective N output file was not created"

    # Load and check contents
    with eff_path.open("r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    # Expected: sess_1 has one completed task (task 0), sess_2 has one completed task (task 1)
    expected = {
        "sess_1": 1,
        "sess_2": 1,
    }
    assert {rec["session_id"]: rec["effective_N"] for rec in lines} == expected