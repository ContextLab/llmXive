"""
Unit test for ``code/update_metadata_checksums.py``.
The test creates a temporary file hierarchy, runs the update script,
and verifies that the ``derived_artifacts`` section of ``metadata.yaml``
contains an entry for each temporary artifact with a valid SHA‑256 hash.
"""
import hashlib
import json
from pathlib import Path
import yaml

import pytest

# Import the script's functions directly
from code.update_metadata_checksums import (
    compute_sha256,
    load_metadata,
    save_metadata,
    collect_artifact_paths,
    update_derived_section,
)


@pytest.fixture
def temp_project(tmp_path: Path):
    """
    Set up a minimal project layout inside the temporary directory.
    The fixture mirrors the real project structure required by the script.
    """
    # Create required directories
    (tmp_path / "data" / "processed" / "networks").mkdir(parents=True)
    (tmp_path / "results").mkdir(parents=True)

    # Create a dummy artifact file
    dummy_file = tmp_path / "data" / "processed" / "networks" / "dummy.pkl"
    dummy_file.write_bytes(b"dummy content")

    # Create a dummy metrics CSV
    metrics_file = tmp_path / "data" / "processed" / "metrics.csv"
    metrics_file.write_text("material_id,avg_degree\nmp-1,3.0\n")

    # Create a dummy result JSON
    result_file = tmp_path / "results" / "correlations.json"
    result_file.write_text(json.dumps([]))

    # Create an empty metadata.yaml (the script will populate it)
    metadata_file = tmp_path / "data" / "metadata.yaml"
    metadata_file.write_text("")

    # Patch the llmxive_toolkit.paths functions to point to the temp root
    from llmxive_toolkit import paths

    original_root = paths.root

    # Monkey‑patch the root attribute
    paths.root = tmp_path

    yield {
        "root": tmp_path,
        "metadata_file": metadata_file,
        "artifact_paths": [dummy_file, metrics_file, result_file],
    }

    # Restore original root after test
    paths.root = original_root


def test_compute_sha256(tmp_path: Path):
    file_path = tmp_path / "test.bin"
    data = b"hello world"
    file_path.write_bytes(data)
    expected = hashlib.sha256(data).hexdigest()
    assert compute_sha256(file_path) == expected


def test_metadata_update(temp_project):
    meta_path = temp_project["metadata_file"]

    # Load (creates skeleton)
    metadata = load_metadata(meta_path)
    assert "derived_artifacts" in metadata

    # Collect artifacts (the function uses the patched paths.root)
    artifacts = collect_artifact_paths()
    assert set(artifacts) == set(temp_project["artifact_paths"])

    # Update the derived section
    update_derived_section(metadata, artifacts)
    save_metadata(meta_path, metadata)

    # Reload and verify contents
    with meta_path.open("r", encoding="utf-8") as f:
        reloaded = yaml.safe_load(f)

    derived = reloaded.get("derived_artifacts", [])
    assert len(derived) == len(artifacts)

    # Each entry must contain a valid SHA‑256 hash (64 hex chars)
    for entry in derived:
        assert "artifact_path" in entry
        assert "sha256" in entry
        assert len(entry["sha256"]) == 64
        # Verify that the hash matches the actual file content
        actual_path = Path(entry["artifact_path"])
        assert actual_path.is_file()
        assert entry["sha256"] == compute_sha256(actual_path)