"""Integration test for the τⁿ‑Bench download script.

The test verifies that ``data/raw/τc_bench/tasks.json`` exists after the
download script runs and that the file is non‑empty.
"""

import os

from llmxive_toolkit import paths

def test_tasks_json_exists_and_nonempty():
    tasks_path = paths.data("raw", "τc_bench", "tasks.json")
    assert tasks_path.is_file(), f"{tasks_path} does not exist."
    assert tasks_path.stat().st_size > 0, f"{tasks_path} is empty."
