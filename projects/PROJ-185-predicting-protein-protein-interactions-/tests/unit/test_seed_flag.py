"""
Unit test for the global CLI seed flag.

The test performs the following steps:
1. Removes any pre‑existing ``pipeline.log`` and the placeholder
   ``predicted_ppi_Arabidopsis.tsv`` file.
2. Executes the CLI with ``--seed 123`` twice (via ``subprocess``).
3. Verifies that the JSON‑Line log contains an entry with ``"seed": 123``.
4. Confirms that the two generated ``predicted_ppi_Arabidopsis.tsv`` files
   are byte‑wise identical, proving deterministic behaviour.
"""
import json
import subprocess
from pathlib import Path

from llmxive_toolkit import paths

LOG_PATH = paths.logs("pipeline.log")
RESULT_PATH = paths.results("predicted_ppi_Arabidopsis.tsv")


def _run_cli(seed: int) -> None:
    """Run the CLI module with the supplied seed."""
    subprocess.check_call(
        [sys.executable, "-m", "src.utils.cli", f"--seed={seed}"],
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )


def test_seed_flag_and_deterministic_output(tmp_path, monkeypatch):
    """
    Ensure that:
    * The seed is recorded in ``pipeline.log``.
    * Two consecutive runs with the same seed produce identical result files.
    """
    import os
    import sys

    # Ensure a clean environment – delete any prior artifacts.
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    if RESULT_PATH.exists():
        RESULT_PATH.unlink()

    # First run
    _run_cli(123)

    # Capture the log entry after the first run.
    with LOG_PATH.open("r", encoding="utf-8") as f:
        first_entry = json.loads(f.readline())

    assert first_entry["seed"] == 123, "Seed not recorded correctly in log"

    # Store the content of the placeholder result file.
    with RESULT_PATH.open("rb") as f:
        first_content = f.read()

    # Second run (same seed)
    _run_cli(123)

    # The log should now contain at least two entries; we only need the
    # most recent one for the seed check.
    with LOG_PATH.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    second_entry = json.loads(lines[-1])
    assert second_entry["seed"] == 123, "Second run did not record seed"

    # Verify deterministic output.
    with RESULT_PATH.open("rb") as f:
        second_content = f.read()

    assert (
        first_content == second_content
    ), "Result files differ between runs with the same seed"