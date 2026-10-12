"""
Unit test for ``code/generate_graph_suite.py``.

The test runs the ``main`` function and then checks that:
1. The manifest CSV exists and contains exactly 60 rows (excluding header).
2. Every ``graph_id`` listed in the manifest corresponds to an existing JSON
   file under ``data/raw/synthetic_graphs/``.
"""

import csv
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# Import the script's main function directly (the script is in the ``code`` package)
from code.generate_graph_suite import main as generate_suite

@pytest.mark.usefixtures("tmp_path_factory")
def test_batch_generate_graph_suite(tmp_path_factory):
    # Ensure a clean temporary workspace for the test run
    # The script uses the project‑wide ``paths`` helper which writes under the
    # repository root, so we do not need to monkeypatch the location.
    generate_suite()

    manifest_path: Path = paths.data("raw", "graph_manifest.csv")
    assert manifest_path.is_file(), "Manifest CSV was not created"

    with manifest_path.open(newline="") as f:
        rows = list(csv.reader(f))

    # First row is the header
    header = rows[0]
    assert header == ["graph_id", "tier", "seed"], "Unexpected manifest header"
    data_rows = rows[1:]
    assert len(data_rows) == 60, f"Expected 60 graph entries, got {len(data_rows)}"

    # Verify each referenced JSON file exists
    for graph_id, tier_str, seed_str in data_rows:
        json_path = paths.data("raw", "synthetic_graphs", f"{graph_id}.json")
        assert json_path.is_file(), f"Graph JSON missing: {json_path}"