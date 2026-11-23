"""
Integration test to verify that the simulation logs the specific
'Out of Bounds' reason when a resource limit is exceeded.

The test runs the CLI entry point ``src.cli.run_simulation`` with a deliberately
low memory limit (0 MiB) so that the internal memory‑check logic triggers a
termination.  After execution it inspects the JSON status file
``simulation_status.json`` that the CLI writes via ``log_status`` and asserts
that the recorded reason contains the expected phrase.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "memory_limit",
    [
        "0",   # Zero MiB – guaranteed to exceed any realistic usage
    ],
)
def test_out_of_bounds_reason_logged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, memory_limit: str):
    """
    Run the simulation with an impossible memory limit and verify that the
    generated log contains the phrase ``Out of Bounds``.
    """
    # Switch the working directory to a temporary folder so that any
    # files produced by the CLI are isolated from the repository.
    monkeypatch.chdir(tmp_path)

    # Build the command line arguments.  We ask for only a single step
    # because the purpose of the test is to trigger the limit, not to
    # perform a full simulation.
    cmd = [
        sys.executable,
        "-m",
        "src.cli.run_simulation",
        "--steps",
        "1",
        "--memory-limit",
        memory_limit,
    ]

    # Execute the CLI.  ``stdout``/``stderr`` are captured for debugging
    # but are not required for the assertion.
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # The CLI may exit with a non‑zero status if it aborts after logging
    # the termination reason.  The test is interested only in the side‑effect
    # (the log file), so we do not enforce a specific return code.
    assert result.returncode in (0, 1, 2), f"Unexpected return code {result.returncode}"

    # The CLI writes its status to ``simulation_status.json`` by default.
    log_path = tmp_path / "simulation_status.json"
    assert log_path.is_file(), f"Log file {log_path} was not created by the CLI."

    # Load the JSON log and verify the presence of the expected reason.
    with log_path.open("r", encoding="utf-8") as f:
        log_data = json.load(f)

    # The log schema used by ``log_status`` includes a ``reason`` key when
    # a termination condition is hit.  Some implementations may embed the
    # message under a generic ``status`` field; we check both.
    reason = log_data.get("reason") or log_data.get("status")
    assert reason is not None, "Log does not contain a 'reason' or 'status' field."

    # The exact wording is defined by the termination handler; the test
    # requires that the phrase ``Out of Bounds`` appears anywhere in the
    # recorded reason.
    assert "Out of Bounds" in str(reason), f"Expected 'Out of Bounds' in reason, got: {reason}"