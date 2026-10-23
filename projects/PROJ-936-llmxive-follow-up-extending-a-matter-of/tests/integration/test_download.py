"""Integration test for the τ-bench download script.

The tests verify that ``data/raw/τc_bench/tasks.json`` exists after
the download script runs, that the file is non‑empty and contains a
non‑empty JSON list of task records, and that the README records a matching
SHA‑256 checksum.
"""

import hashlib
import json
import re

from llmxive_toolkit import paths


def test_tasks_json_exists_and_nonempty():
    tasks_path = paths.data("raw", "τc_bench", "tasks.json")
    assert tasks_path.is_file(), f"{tasks_path} does not exist."
    assert tasks_path.stat().st_size > 0, f"{tasks_path} is empty."


def test_tasks_json_is_valid_task_list():
    tasks_path = paths.data("raw", "τc_bench", "tasks.json")
    assert tasks_path.is_file(), f"{tasks_path} does not exist."
    data = json.loads(tasks_path.read_text(encoding="utf-8"))
    assert isinstance(data, list), "tasks.json must contain a JSON array."
    assert len(data) > 0, "tasks.json must contain at least one task."
    for task in data:
        assert isinstance(task, dict), "Each task record must be an object."


def test_readme_checksum_matches():
    readme_path = paths.data("raw", "τc_bench", "README.md")
    tasks_path = paths.data("raw", "τc_bench", "tasks.json")
    assert readme_path.is_file(), f"{readme_path} does not exist."
    readme = readme_path.read_text(encoding="utf-8")
    match = re.search(
        r"SHA-256 checksum of `tasks\\.json`: `([0-9a-f]{64})`", readme
    )
    assert match is not None, "README must record the tasks.json checksum."
    sha256 = hashlib.sha256(tasks_path.read_bytes()).hexdigest()
    assert match.group(1) == sha256, "Checksum in README does not match file."
