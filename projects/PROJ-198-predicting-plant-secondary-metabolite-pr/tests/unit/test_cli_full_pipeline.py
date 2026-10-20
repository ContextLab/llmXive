"""
End‑to‑end test that runs the full CLI without specifying a step.
It should execute the download, alignment, training, and reporting stages
using mock data (CI_MODE=1) and produce the final report file.
"""

import json
from pathlib import Path

import pytest

def test_full_pipeline_creates_report(monkeypatch, tmp_path):
    # Use CI_MODE to avoid real network calls
    monkeypatch.setenv("CI_MODE", "1")
    monkeypatch.setattr("code.cli.main.PROJECT_ROOT", tmp_path)

    # Run the CLI without a step argument
    from code.cli.main import main
    import sys
    test_args = ["prog"]
    monkeypatch.setattr(sys, "argv", test_args)

    main()

    # Verify final report exists
    report_path = tmp_path / "data" / "processed" / "final_report.md"
    assert report_path.is_file()
    # Verify that the state file contains hashes for both key artefacts
    from utils.artifact import _load_state
    state = _load_state()
    aligned = tmp_path / "data" / "processed" / "aligned_matrix.csv"
    metrics = tmp_path / "data" / "processed" / "model_metrics.json"
    assert str(aligned.resolve().relative_to(tmp_path)) in state
    assert str(metrics.resolve().relative_to(tmp_path)) in state
