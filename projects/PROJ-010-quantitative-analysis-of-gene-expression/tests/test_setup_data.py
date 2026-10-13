"""
Unit test for ``src/data_pipeline/setup_data.py``.

The test runs the ``setup_data`` script (via subprocess) and then checks
that the ``project_state.yaml`` file exists and contains a non‑empty
``raw_checksums`` mapping.
"""
import subprocess
import yaml
from pathlib import Path

from llmxive_toolkit import paths

def test_setup_creates_state(tmp_path):
    # Run the setup script
    result = subprocess.run(
        ["python", "src/data_pipeline/setup_data.py"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Setup script failed: {result.stderr}"

    # Verify the YAML state file
    state_file = paths.data("project_state.yaml")
    assert state_file.is_file(), "project_state.yaml was not created"

    with open(state_file) as f:
        state = yaml.safe_load(f)

    # Basic sanity checks
    assert isinstance(state, dict)
    assert "raw_checksums" in state
    assert isinstance(state["raw_checksums"], dict)
    assert len(state["raw_checksums"]) > 0, "No checksums recorded"
