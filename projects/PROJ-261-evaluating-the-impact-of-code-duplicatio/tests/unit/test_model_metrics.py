"""
Minimal sanity test for the model_metrics module to ensure it does not
produce NaN or infinite perplexity values on a tiny sample.
"""
from __future__ import annotations

import csv
import pathlib

import pytest

from model_metrics import compute_perplexity_batch

def test_compute_perplexity_batch_produces_output(tmp_path: pathlib.Path):
    # The compute_perplexity_batch implementation reads from
    # data/processed/clone_metrics.csv – we create a tiny placeholder that
    # satisfies the expected schema.
    processed_dir = pathlib.Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    placeholder = processed_dir / "clone_metrics.csv"
    placeholder.write_text("total_files,clone_files,clone_density\n1,0,0.0\n", encoding="utf-8")

    # Run the function; it should write perplexity_scores.csv
    compute_perplexity_batch()

    out_path = pathlib.Path("data/processed/perplexity_scores.csv")
    assert out_path.exists()
    rows = list(csv.reader(out_path.read_text().splitlines()))
    header, values = rows
    assert header == ["file_path", "perplexity"]
    # Perplexity should be a finite positive number
    perplexity = float(values[1])
    assert perplexity > 0 and perplexity != float("inf") and perplexity != float("nan")
