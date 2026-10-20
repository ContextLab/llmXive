"""
Minimal test that the ``--step train_and_evaluate`` CLI step runs without error
when the required aligned matrix and a dummy model metrics file exist.
"""

import json
from pathlib import Path

import pytest

def test_train_and_evaluate_runs(monkeypatch, tmp_path):
    # Setup dummy aligned matrix
    aligned = tmp_path / "data" / "processed" / "aligned_matrix.csv"
    aligned.parent.mkdir(parents=True, exist_ok=True)
    aligned.write_text("species,target,feat1,feat2")

    # Setup dummy model metrics file (will be overwritten)
    metrics = tmp_path / "data" / "processed" / "model_metrics.json"
    metrics.parent.mkdir(parents=True, exist_ok=True)
    metrics.write_text("{}")

    # Patch project root inside CLI
    monkeypatch.setattr("code.cli.main.PROJECT_ROOT", tmp_path)

    # Run CLI step
    from code.cli.main import main
    import sys
    test_args = ["prog", "--step", "train_and_evaluate"]
    monkeypatch.setattr(sys, "argv", test_args)

    # Execute
    main()

    # Verify that metrics file was (re)written and hash recorded
    assert metrics.is_file()
    from utils.artifact import _load_state
    state = _load_state()
    rel = metrics.resolve().relative_to(tmp_path)
    assert str(rel) in state
