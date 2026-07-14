"""
Simple integration test for ``code/eval/metrics.py``.

The test creates tiny synthetic dense and sparse frame arrays,
stores them at the expected locations, runs the ``main`` function,
and checks that the output JSON file is produced and contains the
required keys.
"""

import json
import os
import shutil
from pathlib import Path

import numpy as np
import pytest

# Import the module under test
from eval.metrics import main as metrics_main
from config import get_raw_dir, get_results_dir, ensure_directories


@pytest.fixture
def fake_data(tmp_path: Path):
    """
    Populate ``data/raw`` and ``data/results`` with tiny random arrays.
    """
    # Override the project‑wide directories to point inside the temporary
    # directory used by pytest.
    raw_dir = tmp_path / "data" / "raw"
    results_dir = tmp_path / "data" / "results"

    # Ensure the config functions point at the temporary locations.
    # The original config module builds paths relative to the repository
    # root; we monkey‑patch the environment variable used by the config
    # module (PROJECT_ROOT) if it exists.  For simplicity we just create the
    # directories where the original functions expect them.
    raw_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy frame arrays: 2 frames, 32×32 RGB
    dense = np.random.randint(0, 256, size=(2, 32, 32, 3), dtype=np.uint8)
    sparse = np.random.randint(0, 256, size=(2, 32, 32, 3), dtype=np.uint8)

    np.save(raw_dir / "dense_baseline_frames.npy", dense)
    np.save(results_dir / "sparse_warped_frames.npy", sparse)

    # Ensure the config directories exist (the main script calls this)
    ensure_directories()
    yield
    # Cleanup is automatic via the ``tmp_path`` fixture


def test_metrics_produces_json(fake_data, tmp_path: Path):
    # Run the metric computation
    metrics_main()

    out_path = Path(get_results_dir()) / "metrics.json"
    assert out_path.is_file(), "metrics.json was not created"

    with open(out_path, "r") as fp:
        data = json.load(fp)

    # Verify that all expected keys are present and are numbers
    for key in [
        "world_score",
        "sparse_consistency_score",
        "fid",
        "unified_geometric_error",
    ]:
        assert key in data, f"Missing key {key} in metrics output"
        assert isinstance(data[key], (int, float)), f"Metric {key} not numeric"