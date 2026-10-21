import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

def run_script(tmp_path, monkeypatch):
    """Helper to invoke the mean_wilcoxon_analysis script."""
    from src.analysis.mean_wilcoxon_analysis import main

    # Patch sys.argv for the script
    test_args = [
        "mean_wilcoxon_analysis.py",
        "--output-dir",
        str(tmp_path),
        "--metric",
        "time_to_success_ms",
    ]
    monkeypatch.setattr("sys.argv", test_args)
    return main()

def test_mean_wilcoxon_analysis_produces_output(tmp_path, monkeypatch):
    """
    End‑to‑end test that the script runs without error and writes a
    JSON‑Lines file with the expected fields.
    """
    # Ensure there is at least a minimal interaction log for the test.
    # The test creates a tiny synthetic log (real data is not required
    # for the existence check; the script will compute on it).
    log_path = paths.data("logs", "interactions_clean.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Write a minimal valid log with two participants, each having
    # one figure edited via both interfaces.
    minimal_log = [
        {
            "participant_id": "p1",
            "figure_id": "f1",
            "interface": "structured",
            "timestamp_ms": 1000,
            "iteration": 1,
        },
        {
            "participant_id": "p1",
            "figure_id": "f1",
            "interface": "structured",
            "timestamp_ms": 1500,
            "iteration": 2,
        },
        {
            "participant_id": "p1",
            "figure_id": "f1",
            "interface": "chat",
            "timestamp_ms": 2000,
            "iteration": 1,
        },
        {
            "participant_id": "p1",
            "figure_id": "f1",
            "interface": "chat",
            "timestamp_ms": 2600,
            "iteration": 2,
        },
        {
            "participant_id": "p2",
            "figure_id": "f2",
            "interface": "structured",
            "timestamp_ms": 3000,
            "iteration": 1,
        },
        {
            "participant_id": "p2",
            "figure_id": "f2",
            "interface": "structured",
            "timestamp_ms": 3500,
            "iteration": 2,
        },
        {
            "participant_id": "p2",
            "figure_id": "f2",
            "interface": "chat",
            "timestamp_ms": 4000,
            "iteration": 1,
        },
        {
            "participant_id": "p2",
            "figure_id": "f2",
            "interface": "chat",
            "timestamp_ms": 4600,
            "iteration": 2,
        },
    ]
    with log_path.open("w", encoding="utf-8") as f:
        for rec in minimal_log:
            json.dump(rec, f)
            f.write("\n")

    # Run the analysis script
    exit_code = run_script(tmp_path, monkeypatch)
    assert exit_code == 0

    # Verify output file exists and contains required fields
    result_path = Path(tmp_path) / "mean_wilcoxon_results.jsonl"
    assert result_path.is_file()

    with result_path.open("r", encoding="utf-8") as f:
        line = f.readline()
        record = json.loads(line)

    expected_fields = {
        "mean_structured",
        "mean_chat",
        "wilcoxon_stat",
        "p_value",
        "effect_size_r",
    }
    assert expected_fields.issubset(record.keys())