"""
Integration test for the full batch simulation pipeline.

The test runs the batch runner in ``dry‑run`` mode (which still writes the
HDF5 files and the summary CSV) and checks that the expected number of
output files is produced and that the summary CSV contains the correct
number of rows.
"""

import csv
from pathlib import Path

import pytest

from code.run_batch import main as run_batch_main

@pytest.fixture
def temp_output(tmp_path):
    # Use a temporary directory for the simulation outputs
    return tmp_path

def test_batch_execution(temp_output):
    # Locate a small subset of networks for a quick test – we use the first
    # two networks found under ``data/raw/networks``.
    networks_root = Path("data/raw/networks")
    edgelist_files = list(networks_root.rglob("*.edgelist"))[:2]
    assert edgelist_files, "No network files available for the test."

    # Run the batch on this subset by passing the parent directory of the
    # selected files. The batch script will discover the two files.
    args = [
        "--networks", str(networks_root),
        "--output", str(temp_output),
        "--epsilon-start", "0.05",
        "--epsilon-end", "0.10",
        "--epsilon-step", "0.05",
        "--seeds", "2",
        "--max-iter", "500",
        "--tol", "1e-4",
    ]
    # Invoke the batch runner directly (no CLI wrapper)
    run_batch_main(args)

    # Verify that the expected number of HDF5 files were created:
    # 2 networks * 2 epsilon values * 2 seeds = 8 files
    h5_files = list(Path(temp_output).glob("run_*.h5"))
    assert len(h5_files) == 8, f"Expected 8 HDF5 files, found {len(h5_files)}"

    # Verify the summary CSV exists and has the correct number of rows
    summary_path = Path(temp_output) / "summary.csv"
    assert summary_path.is_file(), "summary.csv was not created"

    with summary_path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 8, f"Summary CSV should contain 8 rows, got {len(rows)}"

        # Basic sanity checks on column presence
        for row in rows:
            for col in ["run_id", "network_id", "epsilon", "seed", "convergence_time", "status", "final_clusters"]:
                assert col in row, f"Missing column {col} in summary CSV"