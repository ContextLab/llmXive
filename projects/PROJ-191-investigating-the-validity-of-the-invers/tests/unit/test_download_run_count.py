"""
Unit test for the T013-DATA download script.
It checks that after executing the script, a JSON file
`data/processed/run_count.json` exists and contains the key
`run_count` with an integer value.
"""
import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# The script under test writes to `data/processed/run_count.json`.
# We invoke the script as a module to trigger its execution.
@pytest.mark.integration
def test_run_count_file_created(tmp_path, monkeypatch):
    # Ensure we are running from the project root.
    # The script uses relative paths, so we change cwd to the repository root.
    import os
    os.chdir(Path(__file__).resolve().parents[2])

    # Execute the download script.
    from code.data import download as dl
    # Run main; it will raise if anything goes wrong.
    assert dl.main() == 0

    # Verify the output JSON file.
    run_count_file = paths.data("processed", "run_count.json")
    assert run_count_file.is_file(), f"{run_count_file} does not exist"

    with open(run_count_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "run_count" in data, "run_count key missing in JSON"
    assert isinstance(data["run_count"], int), "run_count is not an integer"