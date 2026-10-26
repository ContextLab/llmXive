"""
Unit tests for the full‑context execution engine.

The tests verify that:
1. The script produces a JSON file at the expected location.
2. The file contains the requested number of logs when ``--n`` is used.
3. Each log conforms to the minimal required schema fields.
"""

import json
from pathlib import Path

from llmxive_toolkit import paths

# Import the entry‑point so we can invoke it programmatically.
from code.services.executor_full import run_full_context

def test_full_context_creates_file(tmp_path: Path):
    # Prepare a tiny synthetic workflow list.
    workflow = {
        "id": "wf-001",
        "metadata": {"depth": 3, "complexity": 7},
        "policy_graph": {"nodes": [], "edges": []},
    }
    input_file = tmp_path / "workflows.json"
    with input_file.open("w", encoding="utf-8") as f:
        json.dump([workflow], f)

    output_file = tmp_path / "full_context_logs.json"

    # Run the engine on the single workflow.
    run_full_context(input_file, output_file, limit=None)

    assert output_file.is_file()

    with output_file.open("r", encoding="utf-8") as f:
        logs = json.load(f)

    assert isinstance(logs, list) and len(logs) == 1
    log_entry = logs[0]

    # Minimal schema validation – required fields only.
    for field in ("workflow_id", "compression_depth", "token_count", "policy_violations"):
        assert field in log_entry

    # Verify that the engine recorded a full‑context run.
    assert log_entry["compression_depth"] == 0
    assert log_entry["context_reduction_pct"] == 0
    assert log_entry["status"] == "full_context"

def test_limit_argument_respects_n(tmp_path: Path):
    # Create three dummy workflows.
    workflows = [
        {"id": f"wf-{i:03d}", "metadata": {}, "policy_graph": {}}
        for i in range(3)
    ]
    input_file = tmp_path / "workflows.json"
    with input_file.open("w", encoding="utf-8") as f:
        json.dump(workflows, f)

    output_file = tmp_path / "full_context_logs.json"

    # Request only two logs via the ``limit`` argument.
    run_full_context(input_file, output_file, limit=2)

    with output_file.open("r", encoding="utf-8") as f:
        logs = json.load(f)

    assert len(logs) == 2