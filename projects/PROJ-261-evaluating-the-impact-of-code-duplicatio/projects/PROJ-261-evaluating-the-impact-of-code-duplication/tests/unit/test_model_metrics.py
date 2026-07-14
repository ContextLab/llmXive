"""
Unit tests for the model_metrics module.

This file includes:
- A sanity test that verifies `compute_perplexity_batch` produces a valid
  output CSV when given a minimal placeholder `clone_metrics.csv`.
- An edge‑case test that simulates a failure when loading the model in
  8‑bit quantization mode. The test monkey‑patches
  `transformers.AutoModelForCausalLM.from_pretrained` to raise a
  `RuntimeError` and asserts that the exception propagates as expected.
"""

from __future__ import annotations

import csv
import pathlib

import pytest

from model_metrics import compute_perplexity_batch


def _prepare_placeholder_clone_metrics() -> pathlib.Path:
    """Create a minimal `clone_metrics.csv` required by `compute_perplexity_batch`."""
    processed_dir = pathlib.Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    placeholder = processed_dir / "clone_metrics.csv"
    placeholder.write_text(
        "total_files,clone_files,clone_density\n1,0,0.0\n", encoding="utf-8"
    )
    return placeholder


def test_compute_perplexity_batch_produces_output(tmp_path: pathlib.Path):
    """
    Basic sanity test: with a tiny placeholder `clone_metrics.csv`,
    `compute_perplexity_batch` should write `perplexity_scores.csv` containing
    a finite, positive perplexity value.
    """
    _prepare_placeholder_clone_metrics()

    # Run the function; it should write perplexity_scores.csv
    compute_perplexity_batch()

    out_path = pathlib.Path("data/processed/perplexity_scores.csv")
    assert out_path.exists(), "perplexity_scores.csv was not created"

    rows = list(csv.reader(out_path.read_text().splitlines()))
    header, values = rows
    assert header == ["file_path", "perplexity"]
    # Perplexity should be a finite positive number
    perplexity = float(values[1])
    assert perplexity > 0 and perplexity != float("inf") and perplexity != float("nan")


def test_compute_perplexity_batch_model_load_failure(monkeypatch):
    """
    Edge‑case test: simulate a failure when loading the model in 8‑bit
    quantization mode. The test patches `transformers.AutoModelForCausalLM.from_pretrained`
    to raise a RuntimeError and verifies that `compute_perplexity_batch`
    propagates the exception.
    """
    # Prepare the placeholder input file expected by the function.
    _prepare_placeholder_clone_metrics()

    # Import transformers lazily inside the test to avoid import‑time side effects.
    import transformers

    def mock_from_pretrained(*_args, **_kwargs):
        raise RuntimeError("Simulated model loading failure")

    # Monkey‑patch the class method used by `model_metrics`.
    monkeypatch.setattr(
        transformers.AutoModelForCausalLM,
        "from_pretrained",
        mock_from_pretrained,
    )

    # The function should raise the RuntimeError we injected.
    with pytest.raises(RuntimeError, match="Simulated model loading failure"):
        compute_perplexity_batch()