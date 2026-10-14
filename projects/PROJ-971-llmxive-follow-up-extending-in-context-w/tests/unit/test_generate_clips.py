"""Contract test for T002: 50 reproducible clips in data/raw."""
from pathlib import Path

import numpy as np

from llmxive_toolkit import paths


def test_fifty_clips_with_required_arrays():
    raw_dir = paths.data("raw")
    files = sorted(raw_dir.glob("clip_*.npz"))
    assert len(files) == 50, f"expected 50 clips, found {len(files)}"
    for f in files:
        with np.load(f) as data:
            for key in ("states", "actions", "observations"):
                assert key in data.files, f"{f} missing array {key}"
                arr = data[key]
                assert arr.ndim == 2 and arr.shape[0] > 0
                assert np.all(np.isfinite(arr))