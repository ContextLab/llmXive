"""
Integration test that runs the full pipeline on a tiny synthetic sample.
The test ensures that the expected CSV artefacts are created.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

# Import the pipeline entry point.
from main import run_pipeline

@pytest.fixture(scope="module")
def run_full_pipeline(tmp_path_factory):
    """Execute the pipeline once; subsequent tests can read the artefacts."""
    # Ensure a clean data directory.
    data_dir = Path("data")
    if data_dir.is_dir():
        import shutil
        shutil.rmtree(data_dir)
    # Run the pipeline – this will invoke the real implementations.
    run_pipeline()
    yield

def test_clone_metrics_created(run_full_pipeline):
    clone_path = Path("data/processed/clone_metrics.csv")
    assert clone_path.is_file()
    with clone_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    # At least one row should be present.
    assert len(rows) > 0

def test_perplexity_scores_created(run_full_pipeline):
    perplex_path = Path("data/processed/perplexity_scores.csv")
    assert perplex_path.is_file()
    with perplex_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) > 0