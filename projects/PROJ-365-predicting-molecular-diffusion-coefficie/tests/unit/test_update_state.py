"""Tests for ``code/ingestion/update_state.py``.

The test creates a minimal ``checksums.txt`` file (if it does not already
exist), runs the ``update_state`` script, and verifies that the generated
state YAML contains the expected keys and values.
"""

import datetime
import json
import os
from pathlib import Path

import yaml
import pytest

from llmxive_toolkit import paths

# Import the script to test its ``main`` function.
from code.ingestion.update_state import main as update_state_main

@pytest.fixture
def ensure_raw_data(tmp_path_factory):
    """Create a minimal raw data environment for the test."""
    # Use the project's real paths (they point under the repo root).
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Ensure a dummy dataset.csv exists.
    dataset_path = raw_dir / "dataset.csv"
    if not dataset_path.is_file():
        dataset_path.write_text("smiles,solvent_type,diffusion_coefficient,viscosity,dielectric_constant\n", encoding="utf-8")

    # Create a simple checksums.txt with the hash of dataset.csv.
    checksums_path = paths.data("checksums.txt")
    import hashlib

    def _hash(p: Path) -> str:
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    checksum_line = f"{_hash(dataset_path)}  data/raw/dataset.csv\n"
    checksums_path.write_text(checksum_line, encoding="utf-8")

    return {
        "raw_dir": raw_dir,
        "dataset_path": dataset_path,
        "checksums_path": checksums_path,
    }

def test_update_state_writes_yaml(ensure_raw_data):
    """Run the script and verify the produced state file."""
    # Run the update_state script.
    update_state_main()

    state_path = paths.state("ingestion", "state.yaml")
    assert state_path.is_file(), "State YAML file was not created"

    # Load and inspect the YAML content.
    with state_path.open("r", encoding="utf-8") as f:
        state_data = yaml.safe_load(f)

    # Basic structure checks.
    assert isinstance(state_data, dict), "State file must contain a mapping"
    assert "artifact_hashes" in state_data, "Missing 'artifact_hashes' key"
    assert "updated_at" in state_data, "Missing 'updated_at' key"

    # Verify that the dataset.csv entry exists.
    artifact_hashes = state_data["artifact_hashes"]
    assert "data/raw/dataset.csv" in artifact_hashes, "dataset.csv hash missing"

    # Verify that the checksums.txt entry exists (added by the script).
    rel_checksums = str(paths.data("checksums.txt").relative_to(paths.root))
    assert rel_checksums in artifact_hashes, "checksums.txt hash missing"

    # Verify that the timestamp is a valid ISO‑8601 string.
    try:
        parsed = datetime.datetime.fromisoformat(state_data["updated_at"])
    except Exception as exc:
        pytest.fail(f"'updated_at' is not a valid ISO‑8601 timestamp: {exc}")

    # The timestamp should be recent (within the last minute).
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = now - parsed
    assert delta.total_seconds() < 60, "Timestamp is not recent"