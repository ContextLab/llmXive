"""
Unit test for the ``code/main.py`` script.

The test verifies that:
* The pilot mode runs without raising an exception.
* The full experiment mode creates the expected directory structure
  and files (attempts.jsonl, evaluations.jsonl, exclusions.json,
  bes_results.json).
"""

import json
from pathlib import Path

from llmxive_toolkit import paths
from code.main import main

def test_pilot_execution(tmp_path, monkeypatch):
    """
    Run the script in pilot mode and ensure the pilot result file is created.
    """
    # Redirect the data root to a temporary directory for isolation.
    monkeypatch.setattr(paths, "data", lambda *parts: Path(tmp_path, *parts))

    # Execute pilot mode.
    exit_code = main.__wrapped__(  # access the original function without argparse parsing
        # Simulate command‑line arguments
        ["--pilot"]
    )
    assert exit_code == 0

    # Verify that the pilot result file exists and contains JSON lines.
    pilot_file = Path(tmp_path, "processed", "pilot_result.jsonl")
    assert pilot_file.is_file()
    with pilot_file.open() as f:
        lines = f.readlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert "run_id" in record and record["run_id"] == "pilot"

def test_full_experiment_execution(tmp_path, monkeypatch):
    """
    Run a tiny full experiment and check that the required artefacts are produced.
    """
    # Use a temporary data root.
    monkeypatch.setattr(paths, "data", lambda *parts: Path(tmp_path, *parts))

    # Run a short experiment (pop size 5, 2 generations) and capture the exit code.
    exit_code = main.__wrapped__(  # bypass argparse
        [
            "--method",
            "symbolic",
            "--pop-size",
            "5",
            "--generations",
            "2",
            "--output",
            str(Path(tmp_path, "processed", "symbolic_run.jsonl")),
        ]
    )
    assert exit_code == 0

    # Expected directories / files.
    bes_runs = Path(tmp_path, "processed", "bes_runs")
    assert bes_runs.is_dir()
    # There should be exactly one run sub‑directory.
    subdirs = [p for p in bes_runs.iterdir() if p.is_dir()]
    assert len(subdirs) == 1
    run_dir = subdirs[0]

    # Check attempts and evaluations logs.
    for fname in ("attempts.jsonl", "evaluations.jsonl"):
        assert (run_dir / fname).is_file()

    # Global artefacts.
    assert (Path(tmp_path, "processed", "exclusions.json")).is_file()
    assert (Path(tmp_path, "processed", "bes_results.json")).is_file()

# Helper to allow calling ``main`` with a custom argv list.
# ``argparse`` reads from ``sys.argv``; we monkey‑patch it here.
import sys
from functools import wraps

@wraps(main)
def main_wrapper(argv):
    original_argv = sys.argv
    sys.argv = ["code/main.py"] + argv
    try:
        return main()
    finally:
        sys.argv = original_argv

# Expose the wrapper for the tests.
main.__wrapped__ = main_wrapper