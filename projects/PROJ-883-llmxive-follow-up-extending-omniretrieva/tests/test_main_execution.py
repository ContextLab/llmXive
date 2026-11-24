"""Integration test for the end‑to‑end pipeline."""

import json
from pathlib import Path

from llmxive_toolkit import paths, get_logger
from code.main import main as run_main

log = get_logger(__name__)

def test_end_to_end(tmp_path, monkeypatch):
    """
    Run the full pipeline and verify that the required output files exist
    and contain plausible data.
    """
    # Ensure the project directories point to a temporary location to avoid
    # polluting the real repository state.
    monkeypatch.setattr(paths, "data", lambda *parts: Path(tmp_path, *parts))
    monkeypatch.setattr(paths, "results", lambda *parts: Path(tmp_path, *parts))

    # Execute the pipeline.
    run_main()

    # Verify CSV exists and has at least the header + one data row.
    csv_path = Path(tmp_path, "processed", "execution_logs.csv")
    assert csv_path.is_file(), f"Missing CSV: {csv_path}"
    with open(csv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) >= 2, "CSV should contain header and at least one metric row"

    # Verify JSONL exists and contains the same number of entries.
    jsonl_path = Path(tmp_path, "processed", "execution_metrics.jsonl")
    assert jsonl_path.is_file(), f"Missing JSONL: {jsonl_path}"
    with open(jsonl_path, "r", encoding="utf-8") as f:
        jsonl_lines = [json.loads(l) for l in f if l.strip()]
    assert len(jsonl_lines) == len(lines) - 1, "JSONL should have one entry per CSV row"

    # Spot‑check that required fields are present in the first metric.
    first_metric = jsonl_lines[0]
    for key in ["query_id", "source_type", "complexity_level", "latency_ms",
                "translation_error", "success_flag", "timeout_flag"]:
        assert key in first_metric, f"Missing field {key} in metric"