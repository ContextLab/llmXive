"""
Unit test for the feasibility gate script.

The test checks that the script runs without raising an exception and
that it produces a JSON file with the expected keys.
"""

import json
from pathlib import Path

from llmxive_toolkit import paths
from src.feasibility_gate import run_feasibility_gate

def test_feasibility_gate_creates_log(tmp_path: Path, monkeypatch):
    # Redirect the data directory to a temporary location for isolation.
    monkeypatch.setattr(
        "llmxive_toolkit.paths.data",
        lambda *parts: tmp_path.joinpath(*parts),
    )

    result = run_feasibility_gate()
    log_path = tmp_path / "feasibility_log.json"

    # Verify the file exists and is valid JSON.
    assert log_path.is_file()
    with log_path.open() as f:
        data = json.load(f)

    # Expected keys.
    expected_keys = {"throughput_tps", "decision", "adjusted_N"}
    assert set(data.keys()) == expected_keys

    # The function should return the same dict it wrote.
    assert data == result
    # Decision must be one of the allowed values.
    assert data["decision"] in {"proceed", "gpu_offload"}