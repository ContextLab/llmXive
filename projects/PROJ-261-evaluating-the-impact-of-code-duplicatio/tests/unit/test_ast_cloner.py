"""
Unit tests for the ast_cloner module.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from code.ast_cloner import compute_clone_density_batch


def _write_dummy_raw(csv_path: Path, rows: int):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "code"])
        writer.writeheader()
        for i in range(rows):
            writer.writerow({"id": i, "code": "a = 1"})


def test_compute_clone_density_batch_writes_output(tmp_path: Path):
    raw = tmp_path / "raw.csv"
    _write_dummy_raw(raw, 3)
    out = tmp_path / "clone_metrics.csv"
    result_path = compute_clone_density_batch(input_path=raw, output_path=out)
    assert result_path == out
    with out.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    # All rows share identical AST, so density should be (3-1)/3 = 0.666667
    for r in rows:
        assert float(r["clone_density"]) == pytest.approx(2 / 3)