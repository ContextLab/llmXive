"""Unit tests for the surface‑entity extraction script (T007).

The test creates a tiny synthetic ``commit_pairs.csv`` with two rows,
runs the extraction function, and checks that the expected JSON files
are produced and contain the correct entities.  Verification against a
real repository is not required for the test – all ``verified`` flags
are expected to be ``false`` because no repository clones exist in the
test environment.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the function under test
from code.entity_extraction_surface import run_extraction, paths

@pytest.fixture
def synthetic_csv(tmp_path: Path) -> Path:
    """Create a minimal ``commit_pairs.csv`` with known patterns."""
    csv_path = tmp_path / "commit_pairs.csv"
    rows = [
        {
            "commit_hash": "abc123",
            "commit_message": "Fix bug in utils",
            "repository_name": "dummy_repo",
            "doc_diff": "Added file src/main.py\\n+def foo(bar):\\n+Version 1.2.3 released",
            "timestamp": "2023-01-01T12:00:00Z",
        },
        {
            "commit_hash": "def456",
            "commit_message": "Update docs",
            "repository_name": "dummy_repo",
            "doc_diff": "Modified README.md\\n+def bar()\\n+Version 0.9.0",
            "timestamp": "2023-01-02T12:00:00Z",
        },
    ]
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    return csv_path

def test_surface_extraction_creates_json(synthetic_csv: Path, tmp_path: Path):
    """Run the extraction on the synthetic CSV and verify JSON output."""
    out_dir = tmp_path / "surface_entities"
    # Run the extraction (repos_root points to a non‑existent directory;
    # verification will therefore produce ``verified: false``)
    exit_code = run_extraction(csv_path=synthetic_csv, output_dir=out_dir, repos_root=tmp_path / "repos")
    assert exit_code == 0

    # Two JSON files should have been created
    json_files = sorted(out_dir.glob("*.json"))
    assert len(json_files) == 2
    expected_hashes = {"abc123", "def456"}
    found_hashes = {p.stem for p in json_files}
    assert found_hashes == expected_hashes

    # Verify the content of one file
    with json_files[0].open(encoding="utf-8") as f:
        data = json.load(f)

    assert data["sample_id"] in expected_hashes
    assert data["type"] == "surface"
    # Collect the extracted entities
    extracted = {e["entity"] for e in data["entities"]}
    # Expected entities based on the regexes
    expected_entities = {
        "src/main.py",
        "def foo(",
        "1.2.3",
        "README.md",
        "def bar(",
        "0.9.0",
    }
    # Because each JSON file only contains the entities for its own row,
    # we check that the union of both files matches the expectation.
    # The test will read both files and compare the combined set.
    # (The first file may contain a subset; the second file contains the rest.)
    # We'll compute the union across all files.
    all_entities = set()
    for jf in json_files:
        with jf.open(encoding="utf-8") as f:
            d = json.load(f)
            all_entities.update(e["entity"] for e in d["entities"])
    assert all_entities == expected_entities

    # All verification flags should be False (no repo clones)
    for jf in json_files:
        with jf.open(encoding="utf-8") as f:
            d = json.load(f)
            assert all(not e["verified"] for e in d["entities"])