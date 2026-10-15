"""
Basic sanity test for ``code/train_models.py``.

The test runs the script on the tiny example dataset that is already
present in the repository. It asserts that the JSON output file is
created and that it contains a list (which may be empty if the split
produced no rows).
"""

import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

@pytest.mark.timeout(180)
def test_grid_search_results_file_exists():
    # Ensure the script has been executed – in CI the script is run
    # explicitly, but for the unit‑test we invoke it directly.
    from code.train_models import main as train_main

    # Run the training routine (it is safe on the tiny example data)
    train_main()

    results_path: Path = paths.results("grid_search_results.json")
    assert results_path.is_file(), "grid_search_results.json was not created"

    # The file must contain valid JSON representing a list
    content = results_path.read_text()
    data = json.loads(content)
    assert isinstance(data, list), "JSON root must be a list"

# The test suite for the whole project will also run the quick‑start
# commands; this unit‑test merely guarantees that the script itself does
# not raise unexpected exceptions.