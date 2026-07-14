"""Test that the parallel implementation of graph metrics finishes within the
expected time budget for a synthetic small dataset.

The test creates a minimal in‑memory dataset for 5 subjects with tiny
connectivity matrices, runs the ``main`` function of ``code/03_compute_graph_metrics.py``,
and checks that the timing log reports a duration under 1 minute (well below the
30‑minute production target). This serves as a sanity check that the parallel
code path is exercised and that the timing file is produced.
"""

import json
import os
import shutil
import time
from pathlib import Path

import pytest

# Import the script as a module
from importlib import import_module


@pytest.fixture(scope="function")
def temp_data_dir(tmp_path):
    """Create a temporary data hierarchy with required files."""
    # Directories
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    artifacts_dir = tmp_path / "data" / "artifacts"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    artifacts_dir.mkdir(parents=True)

    # Create a tiny eligible_subjects.csv
    eligible_path = processed_dir / "eligible_subjects.csv"
    with eligible_path.open("w", newline="") as f:
        f.write("subject_id\\n")
        for i in range(5):
            f.write(f"sub-{i}\\n")

    # Create tiny connectivity matrices (5x5 identity matrices)
    for i in range(5):
        mat_path = processed_dir / f"sub-{i}_connectivity.csv"
        with mat_path.open("w", newline="") as f:
            for r in range(5):
                row = [1.0 if r == c else 0.0 for c in range(5)]
                f.write(",".join(map(str, row)) + "\\n")

    # Minimal config.json to limit subjects to 5
    cfg = {"max_subjects": 5}
    cfg_path = Path(__file__).parent.parent.parent / "code" / "config.json"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    with cfg_path.open("w") as f:
        json.dump(cfg, f)

    yield tmp_path

    # Cleanup
    if cfg_path.is_file():
        cfg_path.unlink()


def test_graph_metrics_parallel_runtime(temp_data_dir):
    """Run the script and assert timing log exists and is < 1 minute."""
    # Change cwd to project root (where the script expects relative paths)
    cwd = Path.cwd()
    os.chdir(temp_data_dir)

    # Import the script fresh to pick up the temporary cwd
    module = import_module("code.03_compute_graph_metrics")

    # Execute main()
    exit_code = module.main()
    assert exit_code == 0

    # Verify output CSV exists
    out_csv = Path("data") / "processed" / "graph_metrics.csv"
    assert out_csv.is_file()

    # Verify timing log exists and contains a reasonable duration
    timing_log = Path("data") / "artifacts" / "graph_metrics_timing.log"
    assert timing_log.is_file()
    content = timing_log.read_text()
    # Extract the numeric minutes
    minutes = float(content.split(":")[1].strip().split()[0])
    assert minutes < 1.0, f"Runtime too long: {minutes} minutes"

    # Restore original cwd
    os.chdir(cwd)