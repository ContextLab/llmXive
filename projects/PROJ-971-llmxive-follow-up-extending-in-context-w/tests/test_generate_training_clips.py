"""
test_generate_training_clips.py
------------------------------

Simple verification that the ``generate_training_clips`` script creates
exactly 200 reproducible ``.npz`` files in the expected location and that
each file can be loaded successfully.

The test is deliberately lightweight – it runs the script (via subprocess)
and then inspects the filesystem.  It does not make any assumptions about
the internal implementation of ``generate_clips`` beyond the public API.
"""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from llmxive_toolkit import paths

SCRIPT_MODULE = "src.pipeline.generate_training_clips"

@pytest.fixture(scope="module")
def run_script():
    """Execute the training‑clip generation script once for the test module."""
    # Ensure a clean start: remove any pre‑existing clips.
    raw_dir = paths.data("raw")
    for f in raw_dir.glob("clip_*.npz"):
        f.unlink()
    # Run the module as a script.
    result = subprocess.run(
        [sys.executable, "-m", SCRIPT_MODULE],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    yield

def test_200_clips_created(run_script):
    """Assert that 200 ``clip_*.npz`` files exist after generation."""
    raw_dir = paths.data("raw")
    clip_files = sorted(raw_dir.glob("clip_*.npz"))
    assert len(clip_files) == 200, f"Expected 200 clips, found {len(clip_files)}"

def test_clips_loadable(run_script):
    """Each generated ``.npz`` file must contain the required arrays."""
    raw_dir = paths.data("raw")
    required_keys = {"states", "actions", "observations"}
    for clip_path in raw_dir.glob("clip_*.npz"):
        with np.load(clip_path) as data:
            assert required_keys.issubset(data.keys()), (
                f"{clip_path.name} missing required arrays"
            )
            # Basic sanity checks on shapes (non‑empty arrays)
            for key in required_keys:
                arr = data[key]
                assert isinstance(arr, np.ndarray)
                assert arr.shape[0] > 0, f"{key} in {clip_path.name} is empty"