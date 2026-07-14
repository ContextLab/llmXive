"""
Edge‑case test where no clones are present – clone density should be 0.
"""
from __future__ import annotations

import pathlib
import csv

from ast_cloner import compute_clone_density_batch

def test_zero_clone_density(tmp_path: pathlib.Path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "a.py").write_text("x = 1", encoding="utf-8")
    (raw_dir / "b.py").write_text("y = 2", encoding="utf-8")
    output = tmp_path / "out.csv"

    compute_clone_density_batch(input_path=raw_dir, output_path=output)

    rows = list(csv.reader(output.read_text().splitlines()))
    header, values = rows
    assert header == ["total_files", "clone_files", "clone_density"]
    total, clone_files, density = map(float, values)
    assert total == 2
    assert clone_files == 0
    assert density == 0.0
