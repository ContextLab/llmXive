"""
Unit test for the dry‑run mode of the pipeline CLI.
It verifies that invoking the CLI with ``--dry-run`` creates the
expected ``sample_run.csv`` file under ``data/results`` and exits
with a zero status code.
"""

import os
from pathlib import Path

import pytest

from src.cli.run_pipeline import main, ensure_project_dirs, write_sample_result
from llmxive_toolkit import paths


@pytest.fixture(scope="function")
def clean_environment(tmp_path: Path):
    """
    Ensure a clean project directory for each test run.
    The fixture changes the working directory to a temporary location,
    runs ``ensure_project_dirs`` to create the required hierarchy,
    and restores the original cwd afterwards.
    """
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        # Re‑create the directory skeleton in the temporary location
        ensure_project_dirs()
        yield tmp_path
    finally:
        os.chdir(original_cwd)


def test_dry_run_creates_sample_file(clean_environment: Path):
    """
    Run the CLI in dry‑run mode and assert that:
    1. The exit code is ``0``.
    2. ``data/results/sample_run.csv`` exists.
    3. The CSV contains at most 10 rows (including the header).
    """
    # Invoke the CLI programmatically with the ``--dry-run`` flag.
    exit_code = main(["--dry-run"])
    assert exit_code == 0, "CLI did not exit cleanly in dry‑run mode"

    # Expected output path
    sample_path = paths.data("results", "sample_run.csv")
    assert sample_path.is_file(), f"Expected sample result file not found: {sample_path}"

    # Verify row count (header + up to 9 data rows)
    with sample_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    # First line is header; ensure total lines ≤ 11 (header + ≤10 rows)
    assert len(lines) <= 11, f"Sample CSV exceeds 10 data rows: {len(lines)-1} rows"

    # Optional sanity check: column headers are as documented
    header = lines[0].strip().split(",")
    expected_header = [
        "patch_id",
        "true_label",
        "predicted_label",
        "predicted_prob",
    ]
    assert header == expected_header, f"Unexpected CSV header: {header}"