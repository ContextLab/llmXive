"""
test_memory_usage.py
--------------------
Ensures that the pipeline records peak memory usage in the expected
``outputs/logs/memory.json`` file and that the recorded value is a
non‑negative number.
"""

import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# Import the run_all module and invoke its main entry point.
from code.run_all import main as run_all_main


@pytest.mark.timeout(300)
def test_memory_json_is_created_and_valid():
    """
    Run the full pipeline and verify that ``memory.json`` exists and
    contains a ``peak_rss_mb`` field with a numeric (int or float) value.
    """
    # Execute the pipeline.
    run_all_main()

    # Resolve the expected output path.
    memory_path: Path = paths.outputs("logs", "memory.json")

    # The file must exist after the run.
    assert memory_path.is_file(), f"{memory_path} was not created"

    # Load and validate JSON contents.
    with memory_path.open() as f:
        data = json.load(f)

    assert "peak_rss_mb" in data, "'peak_rss_mb' key missing in memory.json"
    peak = data["peak_rss_mb"]
    # The value should be a number (int or float) and non‑negative.
    assert isinstance(peak, (int, float)), "peak_rss_mb is not numeric"
    assert peak >= 0, "peak_rss_mb should be non‑negative"

    # Optional sanity check: ensure the recorded memory is within the
    # allowed CI limit (7 GB).  This mirrors the verification step.
    assert peak <= 7000, f"Recorded peak memory {peak} MB exceeds CI limit"