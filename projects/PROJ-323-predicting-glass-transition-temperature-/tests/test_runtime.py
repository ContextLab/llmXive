"""
Test that the pipeline runtime is recorded correctly.

The test invokes ``code.run_all.main()`` which should generate
``outputs/logs/runtime.json``.  The JSON file must contain an
``elapsed_seconds`` field that is numeric and does not exceed the
six‑hour limit (21600 seconds) imposed by the specification.
"""

import json
import os

from llmxive_toolkit import paths

# Import the pipeline runner.  Importing the module is safe because it
# does not execute the pipeline on import – the ``main`` function must be
# called explicitly.
import code.run_all as run_all

def test_runtime_file_created_and_valid():
    # Run the full pipeline (which includes the runtime timer).
    run_all.main()

    runtime_path = paths.outputs("logs", "runtime.json")
    assert runtime_path.is_file(), f"{runtime_path} does not exist"

    with runtime_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # The JSON must contain the expected key.
    assert "elapsed_seconds" in data, "Key 'elapsed_seconds' missing in runtime.json"

    elapsed = data["elapsed_seconds"]
    # Must be a number (int or float).
    assert isinstance(elapsed, (int, float)), "elapsed_seconds is not numeric"

    # Must respect the six‑hour upper bound.
    assert elapsed <= 21600, f"Pipeline ran for {elapsed} seconds, exceeds 6 h limit"