import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

def test_aggregated_validation_has_real_sessions(tmp_path, monkeypatch):
    """
    Run the ``validation_by_session`` script on the existing dataset and
    ensure that at least one output line contains a session_id other than
    ``unknown``. This proves that the interaction log is being used to map
    tasks to real participant identifiers.
    """
    # Use the project's default data locations.
    output_path = Path("data/results/validation_by_session.jsonl")
    # Ensure a clean run of the script.
    import importlib
    mod = importlib.import_module("src.analysis.validation_by_session")
    # Run with default arguments (the script reads from the real data dirs).
    ret = mod.main()
    assert ret == 0, "validation_by_session script failed"

    assert output_path.is_file(), f"Expected output file at {output_path}"
    with output_path.open("r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    # There should be at least one line where session_id is not "unknown".
    assert any(rec["session_id"] != "unknown" for rec in lines), (
        "All session_id values are 'unknown'; interaction log mapping failed."
    )