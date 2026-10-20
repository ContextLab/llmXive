"""
Integration test that verifies the ``run`` sub‑command executes without error
and produces the expected artefacts.

The test invokes the CLI using the same argument names that were present in
the original run‑book (``--node-count`` and ``--injected-latency``) to ensure
backward compatibility, as well as the canonical ``--nodes``/``--latency``
flags.  It asserts that the process exits with status 0 and that the three
core output files exist.
"""

import subprocess
import sys
from pathlib import Path

import pytest

@pytest.mark.parametrize(
    "args",
    [
        # Canonical flag names
        ["run", "--config", "config.yaml", "--granularity", "fine", "--nodes", "2", "--latency", "0"],
        # Legacy aliases used by an older run‑book
        ["run", "--config", "config.yaml", "--granularity", "fine", "--node-count", "2", "--injected-latency", "0"],
    ],
)
def test_cli_run_subcommand_success(args):
    """Execute the CLI run sub‑command and verify artefacts."""
    # Build the command line: ``python -m code.orchestrator.cli <args>``.
    cmd = [sys.executable, "-m", "code.orchestrator.cli"] + args

    # Run the process; capture output for debugging if needed.
    result = subprocess.run(cmd, capture_output=True, text=True)

    # The CLI must exit with status 0.
    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    # Expected artefacts (they are written into the project data folder).
    expected_paths = [
        Path("data/raw/run_001.csv"),
        Path("data/raw/dropout_events.json"),
        Path("data/raw/validation_status.json"),
    ]

    for p in expected_paths:
        assert p.is_file(), f"Expected artefact not found: {p}"
