"""
Integration test that runs the full US‑1 pipeline on a tiny sample and
checks that the expected CSV artefacts are produced.
"""
from __future__ import annotations

import pathlib

import pytest

from main import run_pipeline

def test_full_pipeline_small_sample(tmp_path: pathlib.Path, monkeypatch):
    # Monkey‑patch the data loader to produce only three tiny files
    class MockDataset:
        def __iter__(self):
            for i in range(3):
                yield {"content": f"# file {i}\nprint({i})"}

    monkeypatch.setattr("datasets.load_dataset", lambda *a, **k: MockDataset())

    # Run the pipeline
    exit_code = run_pipeline()
    assert exit_code == 0

    # Verify outputs
    clone_csv = pathlib.Path("data/processed/clone_metrics.csv")
    perplexity_csv = pathlib.Path("data/processed/perplexity_scores.csv")
    assert clone_csv.exists()
    assert perplexity_csv.exists()