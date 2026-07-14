"""
test_main_pipeline.py
---------------------
Basic integration test that the main pipeline runs without raising
exceptions and produces the two required CSV files.
"""
from __future__ import annotations

import pathlib

import pytest

from code.main import run_pipeline

@pytest.mark.integration
def test_pipeline_generates_outputs(tmp_path: pathlib.Path, monkeypatch):
    """
    Run the pipeline in a temporary directory and verify that the expected
    CSV artefacts are created.
    """
    # Redirect the project‑wide data directory to a temporary location
    project_root = pathlib.Path(__file__).parents[2]  # projects/PROJ-...
    data_dir = tmp_path / "data"
    monkeypatch.chdir(project_root)  # ensure relative paths resolve correctly
    # Ensure the data directories exist under the temporary root
    (project_root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "processed").mkdir(parents=True, exist_ok=True)

    exit_code = run_pipeline()
    assert exit_code == 0, "Pipeline should exit with code 0"

    clone_metrics = project_root / "data" / "processed" / "clone_metrics.csv"
    perplexity_scores = project_root / "data" / "processed" / "perplexity_scores.csv"

    assert clone_metrics.is_file(), "clone_metrics.csv must exist after pipeline"
    assert perplexity_scores.is_file(), "perplexity_scores.csv must exist after pipeline"