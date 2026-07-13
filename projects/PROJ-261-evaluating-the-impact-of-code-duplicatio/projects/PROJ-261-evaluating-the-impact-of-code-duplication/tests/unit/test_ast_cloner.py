"""
Unit tests for the ast_cloner module.

This file contains:
1. A basic sanity test that checks the clone density computation writes the expected
   output CSV and produces the correct density values for identical code snippets.
2. A syntax‑error handling test that ensures the pipeline does not crash when a
   Python fragment cannot be parsed and that the failure is recorded in the
   `data/parse_failures.csv` log.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from code.ast_cloner import compute_clone_density_batch

def _write_dummy_raw(csv_path: Path, rows: list[tuple[int, str]]) -> None:
    """Write a CSV with ``id`` and ``code`` columns."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "code"])
        writer.writeheader()
        for idx, code in rows:
            writer.writerow({"id": idx, "code": code})

def test_compute_clone_density_batch_writes_output(tmp_path: Path):
    """Basic sanity check – output file is created and densities are correct."""
    raw = tmp_path / "raw.csv"
    _write_dummy_raw(raw, [(0, "a = 1"), (1, "a = 1"), (2, "a = 1")])
    out = tmp_path / "clone_metrics.csv"
    result_path = compute_clone_density_batch(input_path=raw, output_path=out)
    assert result_path == out
    with out.open(newline="") as f:
        rows = list(csv.DictReader(f))
    # three rows should be present
    assert len(rows) == 3
    # All rows share identical AST, so density should be (3‑1)/3 = 0.666666…
    for r in rows:
        assert float(r["clone_density"]) == pytest.approx(2 / 3)

def test_compute_clone_density_batch_handles_syntax_error(tmp_path: Path):
    """
    Ensure that a file containing a syntax error does not cause the whole
    pipeline to raise and that the offending row is logged in
    ``data/parse_failures.csv``.
    """
    # Row 0 – valid Python; Row 1 – invalid syntax
    raw = tmp_path / "raw_syntax.csv"
    _write_dummy_raw(raw, [(0, "a = 1"), (1, "def broken(:")])
    out = tmp_path / "clone_metrics_syntax.csv"

    # The function should complete without raising.
    result_path = compute_clone_density_batch(input_path=raw, output_path=out)
    assert result_path == out
    assert out.is_file()

    # The valid row should appear in the output CSV.
    with out.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert any(row["id"] == "0" for row in rows)

    # The parse‑failure log must contain an entry for the offending id.
    parse_log = Path("data/parse_failures.csv")
    assert parse_log.is_file(), "Parse‑failure log was not created"
    with parse_log.open(newline="") as f:
        failures = list(csv.DictReader(f))
    # The failure entry should reference the id of the bad row.
    assert any(failure["id"] == "1" for failure in failures)