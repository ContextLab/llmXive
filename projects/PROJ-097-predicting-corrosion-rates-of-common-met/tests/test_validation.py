"""Test that the ingestion‑validation script produces a sensible pass‑rate."""

from __future__ import annotations

import json
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def test_ingestion_validation_pass_rate():
    """Run the validation script and assert that the JSON exists and the rate is high."""
    from src.pipeline.validation import main as validation_main

    rc = validation_main([])
    assert rc == 0, "validation_main exited with non‑zero status"

    metrics_path = paths.results("ingestion_validation_metrics.json")
    assert metrics_path.is_file(), f"Metrics file not found at {metrics_path}"

    with open(metrics_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    assert "pass_rate" in data, "pass_rate field missing in metrics JSON"
    # The script itself enforces the 0.95 threshold, but we double‑check here.
    assert isinstance(data["pass_rate"], float), "pass_rate should be a float"
    assert data["pass_rate"] >= 0.95, f"Pass rate too low: {data['pass_rate']}"