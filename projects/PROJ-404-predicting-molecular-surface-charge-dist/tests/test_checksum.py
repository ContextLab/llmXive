"""
Test that the checksum of the downloaded QM9 parquet file is recorded
in the project state YAML.
"""
import os
import yaml

from llmxive_toolkit import paths
from code.data.loader import download_qm9_parquet, update_state_checksum

def test_checksum_record(tmp_path, monkeypatch):
    # Ensure we write to a temporary state file to avoid polluting the repo
    state_file = tmp_path / "state.yaml"
    parquet_path = download_qm9_parquet(force_download=False)

    # Record checksum to the temporary state file
    update_state_checksum(str(state_file), parquet_path)

    # Load the YAML and verify the hash entry exists
    with open(state_file, "r") as f:
        data = yaml.safe_load(f)

    assert "artifact_hashes" in data, "artifact_hashes section missing"
    artifact_hashes = data["artifact_hashes"]
    filename = os.path.basename(parquet_path)
    assert filename in artifact_hashes, f"{filename} not recorded in artifact_hashes"
    # The hash should be a 64‑character hex string
    assert isinstance(artifact_hashes[filename], str) and len(artifact_hashes[filename]) == 64
