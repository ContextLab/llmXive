"""Unit test for ``code/ingestion/update_state.py``.

The test creates (or overwrites) a minimal ``checksums.txt`` file,
runs the ``main`` function, and verifies that a state YAML file is
written under ``data/state`` containing the expected keys and a
recent ``updated_at`` timestamp.
"""

import datetime
import yaml
from pathlib import Path

from llmxive_toolkit import paths

def test_update_state_writes_yaml(tmp_path):
    # Ensure the checksums file exists with a deterministic entry.
    checksums_path = paths.data("checksums.txt")
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    checksums_path.write_text("dummyhash  data/raw/dataset.csv\n", encoding="utf-8")

    # Import and run the script's main function.
    from ingestion.update_state import main
    main()

    # Verify that the state file was created in the project‑owned location.
    state_path = paths.data("state", "ingestion_state.yaml")
    assert state_path.is_file(), f"State file not found at {state_path}"

    # Load and inspect the YAML content.
    content = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    assert isinstance(content, dict), "State file does not contain a YAML mapping"
    assert "artifact_hashes" in content, "Missing 'artifact_hashes' section"
    assert "updated_at" in content, "Missing 'updated_at' timestamp"

    # The dummy entry should be present.
    artifact_hashes = content["artifact_hashes"]
    assert "data/raw/dataset.csv" in artifact_hashes, "Checksum entry missing for dataset.csv"

    # Verify the timestamp is recent (within the last 30 seconds).
    ts = datetime.datetime.fromisoformat(content["updated_at"])
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = (now - ts).total_seconds()
    assert delta < 30, f"Timestamp is too old: {delta} seconds ago"