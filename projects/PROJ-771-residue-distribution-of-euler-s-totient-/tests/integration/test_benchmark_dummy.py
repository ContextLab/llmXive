"""
Integration test for the dummy benchmark script.

This test ensures that executing ``scripts/run_dummy.py`` creates the
``benchmark_dummy.json`` report with the required numeric fields.
"""

import json
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def test_benchmark_dummy_creates_file(tmp_path):
    """
    Run the dummy benchmark script and verify the output JSON.

    The test removes any pre‑existing benchmark file, invokes the script
    via a subprocess (so the real ``benchmark`` context manager is exercised),
    and then checks that the resulting JSON file exists and contains numeric
    ``wall_time_sec`` and ``peak_memory_mb`` entries.
    """
    # Ensure a clean start
    out_path = paths.results("reports", "benchmark_dummy.json")
    if out_path.is_file():
        out_path.unlink()

    # Execute the dummy script
    subprocess.check_call([sys.executable, "scripts/run_dummy.py"])

    # Verify the file was created
    assert out_path.is_file(), f"Benchmark report not found at {out_path}"

    # Load and validate JSON contents
    with open(out_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Required numeric fields
    assert isinstance(data.get("wall_time_sec"), (int, float)), "wall_time_sec must be numeric"
    assert isinstance(data.get("peak_memory_mb"), (int, float)), "peak_memory_mb must be numeric"
    # Basic sanity checks (non‑negative)
    assert data["wall_time_sec"] >= 0, "wall_time_sec should be non‑negative"
    assert data["peak_memory_mb"] >= 0, "peak_memory_mb should be non‑negative"