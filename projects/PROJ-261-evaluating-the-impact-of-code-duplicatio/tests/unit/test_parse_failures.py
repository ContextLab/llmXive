"""
Ensures that the clone‑density computation gracefully handles a dataset
with no duplicates (density should be 0 %).
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from ast_cloner import compute_clone_density_batch

RAW_SAMPLE_PATH = Path("data/raw/github-code-sample.csv")
CLONE_METRICS_PATH = Path("data/processed/clone_metrics.csv")

@pytest.fixture(autouse=True)
def prepare_unique_sample(tmp_path, monkeypatch):
    RAW_SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLONE_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Three distinct files.
    rows = [
        {"filename": "a.py", "content": "def f():\n    return 1"},
        {"filename": "b.py", "content": "def g():\n    return 2"},
        {"filename": "c.py", "content": "def h():\n    return 3"},
    ]
    with RAW_SAMPLE_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "content"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    yield

    if RAW_SAMPLE_PATH.is_file():
        RAW_SAMPLE_PATH.unlink()
    if CLONE_METRICS_PATH.is_file():
        CLONE_METRICS_PATH.unlink()

def test_zero_clone_density():
    compute_clone_density_batch()
    with CLONE_METRICS_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader)
        assert float(row["overall_density"]) == pytest.approx(0.0)
        assert float(row["type1_density"]) == pytest.approx(0.0)
        assert float(row["type2_density"]) == pytest.approx(0.0)