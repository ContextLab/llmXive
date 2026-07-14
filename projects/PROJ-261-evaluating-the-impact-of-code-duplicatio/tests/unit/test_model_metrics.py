"""
Unit tests for the ``model_metrics`` module.

The first test verifies that a tiny placeholder ``clone_metrics.csv`` leads to a
valid ``perplexity_scores.csv`` with a finite, positive perplexity value.

The second test checks the edge‑case where model loading fails (e.g. missing
``bitsandbytes`` or any runtime error). In this situation ``compute_perplexity_batch``
must raise ``ModelLoadingError`` rather than bubbling up an unexpected exception.
"""

from __future__ import annotations

import csv
import pathlib

import pytest

# Import the symbols we need from the implementation.
from model_metrics import compute_perplexity_batch, ModelLoadingError

def test_compute_perplexity_batch_produces_output(tmp_path: pathlib.Path):
    """
    Ensure that ``compute_perplexity_batch`` creates a CSV with a finite,
    positive perplexity value when given a minimal ``clone_metrics.csv``.
    """
    processed_dir = pathlib.Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    placeholder = processed_dir / "clone_metrics.csv"
    placeholder.write_text(
        "total_files,clone_files,clone_density\n1,0,0.0\n",
        encoding="utf-8",
    )

    # Run the function; it should write ``perplexity_scores.csv``.
    compute_perplexity_batch()

    out_path = pathlib.Path("data/processed/perplexity_scores.csv")
    assert out_path.exists(), "Output CSV was not created"

    rows = list(csv.reader(out_path.read_text().splitlines()))
    header, values = rows
    assert header == ["file_path", "perplexity"]
    perplexity = float(values[1])
    assert perplexity > 0 and perplexity != float("inf") and not (perplexity != perplexity)  # NaN check

def test_compute_perplexity_batch_model_loading_failure(monkeypatch):
    """
    Simulate a failure while loading the 8‑bit model and verify that the
    ``ModelLoadingError`` exception is raised.
    """
    # Replace the ``load_model`` function with one that always raises.
    def fake_load_model():
        raise RuntimeError("simulated model loading failure")

    import model_metrics

    monkeypatch.setattr(model_metrics, "load_model", fake_load_model)

    with pytest.raises(ModelLoadingError):
        compute_perplexity_batch()
