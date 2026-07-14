"""
test_main_pipeline_output.py
--------------------------------
Integration‑style test that verifies the main pipeline creates the two
required CSV files.  The test runs the ``run_pipeline`` function directly
(avoiding subprocess overhead) and checks the filesystem.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Import the pipeline entry‑point.
from main import run_pipeline


@pytest.fixture(autouse=True)
def clean_artifacts(tmp_path_factory):
    """
    Ensure a clean environment before each test run.
    The fixture removes any existing processed files and forces the
    pipeline to write fresh outputs.
    """
    # Use the repository‑relative paths defined in the implementation.
    for rel in [
        "data/processed/clone_metrics.csv",
        "data/processed/perplexity_scores.csv",
    ]:
        p = Path(rel)
        if p.is_file():
            p.unlink()
    yield
    # Clean up after the test as well.
    for rel in [
        "data/processed/clone_metrics.csv",
        "data/processed/perplexity_scores.csv",
    ]:
        p = Path(rel)
        if p.is_file():
            p.unlink()


def test_pipeline_creates_output_files():
    """
    The pipeline must exit with a zero status and produce both CSV files.
    """
    exit_code = run_pipeline()
    assert exit_code == 0, "Pipeline reported a failure"

    clone_path = Path("data/processed/clone_metrics.csv")
    perplexity_path = Path("data/processed/perplexity_scores.csv")

    assert clone_path.is_file(), "clone_metrics.csv was not created"
    assert perplexity_path.is_file(), "perplexity_scores.csv was not created"

    # Basic sanity – each file should have at least a header and one data row.
    for path in (clone_path, perplexity_path):
        with path.open() as f:
            lines = f.readlines()
            assert len(lines) >= 2, f"{path} appears empty"

# The test suite can be executed with ``pytest -q`` from the repository root.