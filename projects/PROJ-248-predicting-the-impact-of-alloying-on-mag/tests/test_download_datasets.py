"""
test_download_datasets.py

Integration test for the Phase 0 data‑acquisition script.  The test runs the
``download_datasets.py`` script (which writes its outputs to the ``data/``
directory) and then checks that the three expected artefacts exist and are
non‑empty.

The test is deliberately lightweight – it does not assert specific record
counts because the upstream datasets may evolve – but it guarantees that
the download step succeeded without raising an exception.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from llmxive_toolkit import paths

SCRIPT = Path(__file__).parents[1] / "code" / "download_datasets.py"


@pytest.mark.timeout(600)
def test_download_datasets_runs_successfully():
    """Execute the download script and verify output files."""
    # Run the script as a subprocess to mimic the CI execution environment.
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    # Expected output files
    raw_mp = paths.data("raw_mp.jsonl")
    raw_oqmd = paths.data("raw_oqmd.csv")
    manifest = paths.data("data_sources.yaml")

    for p in (raw_mp, raw_oqmd, manifest):
        assert p.is_file(), f"Expected file {p} does not exist."
        assert p.stat().st_size > 0, f"File {p} is empty."
