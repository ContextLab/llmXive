"""
Unit tests for the step‑expander utility (code.utils.step_expander).

The tests verify that the script correctly reads the two log files,
creates step‑level records, and respects the exclusion rule for
``[deferred]`` context reduction percentages.
"""

import json
from pathlib import Path

from llmxive_toolkit import paths

# Import the public function directly for testing.
from code.utils.step_expander import _log_to_step, expand_logs

def _write_log(file_path: Path, records):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

def test_log_to_step_binary_outcome():
    # No violations -> outcome 0
    log_entry = {
        "workflow_id": "wf-001",
        "policy_violations": [],
        "context_reduction_pct": 20,
        "complexity": 5,
        "depth": 3,
    }
    step = _log_to_step(log_entry)
    assert step["outcome"] == 0
    assert step["exclude_from_regression"] is False

    # With violations -> outcome 1
    log_entry["policy_violations"] = [{"rule_id": "budget_exceeded"}]
    step = _log_to_step(log_entry)
    assert step["outcome"] == 1

def test_expand_logs_combines_full_and_compressed(tmp_path: Path):
    # Prepare minimal full‑context log
    full_log = [
        {
            "workflow_id": "wf-full-1",
            "policy_violations": [],
            "context_reduction_pct": 0,
            "complexity": 2,
            "depth": 1,
        }
    ]

    # Prepare compressed log with a deferred reduction
    compressed_log = [
        {
            "workflow_id": "wf-comp-1",
            "policy_violations": [{"rule_id": "audit_logging"}],
            "context_reduction_pct": "[deferred]",
            "complexity": 3,
            "depth": 2,
        }
    ]

    full_path = tmp_path / "full.json"
    comp_path = tmp_path / "comp.json"
    out_path = tmp_path / "step_outcomes.json"

    _write_log(full_path, full_log)
    _write_log(comp_path, compressed_log)

    # Run the expansion
    expand_logs(full_path, comp_path, out_path)

    # Verify output file exists and contains two records
    assert out_path.is_file()
    with out_path.open("r", encoding="utf-8") as f:
        results = json.load(f)

    assert isinstance(results, list) and len(results) == 2

    # Check that the deferred row is flagged for exclusion
    deferred = next(r for r in results if r["workflow_id"] == "wf-comp-1")
    assert deferred["exclude_from_regression"] is True
    assert deferred["outcome"] == 1  # because it had a violation

    # Check numeric row
    numeric = next(r for r in results if r["workflow_id"] == "wf-full-1")
    assert numeric["exclude_from_regression"] is False
    assert numeric["outcome"] == 0
    assert numeric["context_reduction_pct"] == 0
    assert numeric["policy_complexity"] == 2
    assert numeric["delegation_depth"] == 1