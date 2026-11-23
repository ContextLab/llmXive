"""Test that VIF diagnostics are produced and contain valid values."""

from __future__ import annotations

import json

from llmxive_toolkit import paths
from src.pipeline.run_all import main as run_all_main

def test_vif_diagnostics_created(tmp_path):
    """
    Execute the end‑to‑end pipeline (ingestion + VIF) and verify that
    ``data/results/vif_diagnostics.json`` exists and contains a non‑empty
    mapping of predictor names to VIF values.
    """
    # Run the pipeline; this will also trigger dataset download.
    exit_code = run_all_main([])
    assert exit_code == 0, "Pipeline run_all failed"

    vif_path = paths.results("vif_diagnostics.json")
    assert vif_path.is_file(), f"VIF file not found at {vif_path}"

    with open(vif_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    assert isinstance(data, dict), "VIF JSON should be a dict"
    assert data, "VIF JSON is empty"
    # Each VIF should be a positive number.
    for name, value in data.items():
        assert isinstance(value, (int, float)), f"VIF for {name} is not numeric"
        assert value >= 0, f"VIF for {name} is negative"