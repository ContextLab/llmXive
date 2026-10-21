import json
import pytest
from pathlib import Path
from src.analysis.validation_by_session import main

def test_validation_by_session_mapping(tmp_path, monkeypatch):
    # Setup temporary directories
    log_dir = tmp_path / "logs"
    val_dir = tmp_path / "validation"
    gt_dir = tmp_path / "gt"
    log_dir.mkdir()
    val_dir.mkdir()
    gt_dir.mkdir()
    out_path = tmp_path / "results_session.jsonl"

    # Create mock interaction log
    # figure_0 belongs to user_A, figure_1 belongs to user_B
    interactions = [
        {"participant_id": "user_A", "figure_id": "0", "iteration": 1},
        {"participant_id": "user_B", "figure_id": "1", "iteration": 1},
    ]
    with (log_dir / "interactions_clean.jsonl").open("w") as f:
        for rec in interactions:
            f.write(json.dumps(rec) + "\n")

    # Create mock semantic validation log
    # task_0 succeeded, task_1 failed
    validations = [
        {"task_id": "0", "vector_match": True, "semantic_pass": False, "overall_success": True},
        {"task_id": "1", "vector_match": False, "semantic_pass": False, "overall_success": False},
    ]
    with (val_dir / "semantic_validation.jsonl").open("w") as f:
        for rec in validations:
            f.write(json.dumps(rec) + "\n")

    # Mock subprocess.run to avoid calling the real run_validation
    import subprocess
    def mock_run(*args, **kwargs):
        class Result:
            def __init__(self):
                self.returncode = 0
                self.stdout = ""
                self.stderr = ""
        return Result()
    monkeypatch.setattr(subprocess, "run", mock_run)

    # Mock sys.argv for main()
    import sys
    monkeypatch.setattr(sys, "argv", [
        "validation_by_session.py",
        "--log-dir", str(log_dir),
        "--validation-dir", str(val_dir),
        "--ground-truth-dir", str(gt_dir),
        "--output-path", str(out_path)
    ])

    # Execute
    exit_code = main()
    assert exit_code == 0

    # Verify results
    results = []
    with out_path.open("r") as f:
        for line in f:
            results.append(json.loads(line))

    assert len(results) == 2
    # Check mapping for user_A
    res_0 = next(r for r in results if r["task_id"] == "0")
    assert res_0["session_id"] == "user_A"
    assert res_0["overall_success"] is True

    # Check mapping for user_B
    res_1 = next(r for r in results if r["task_id"] == "1")
    assert res_1["session_id"] == "user_B"
    assert res_1["overall_success"] is False