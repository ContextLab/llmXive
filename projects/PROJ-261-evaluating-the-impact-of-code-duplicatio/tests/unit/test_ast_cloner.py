"""
Unit tests for the ``ast_cloner`` module, focusing on robust handling of
syntax errors in the input data.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

# The function under test
from code.ast_cloner import compute_clone_density_batch

def _write_dummy_raw(csv_path: Path, rows: list[dict[str, str]]) -> None:
    """
    Helper that writes a small CSV file with the given rows.  The CSV must
    contain the columns ``id`` and ``code`` as required by the pipeline.
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "code"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def test_compute_clone_density_batch_handles_syntax_error(tmp_path: Path):
    """
    Verify that ``compute_clone_density_batch`` does not raise on a syntax
    error, writes an output file, and records an empty ``clone_density`` for
    the offending row.
    """
    raw = tmp_path / "raw.csv"
    rows = [
        {"id": "0", "code": "a = 1"},                 # valid Python
        {"id": "1", "code": "def broken(: pass"},     # syntax error
        {"id": "2", "code": "b = 2"},                 # valid Python, distinct AST
    ]
    _write_dummy_raw(raw, rows)

    out = tmp_path / "clone_metrics.csv"
    result_path = compute_clone_density_batch(input_path=raw, output_path=out)

    # The function should return the exact output path we supplied.
    assert result_path == out

    # The output file must exist and be readable.
    assert out.is_file()

    # Load the output and verify the schema.
    with out.open(newline="") as f:
        reader = csv.DictReader(f)
        output_rows = list(reader)

    # There should be three rows, matching the input.
    assert len(output_rows) == 3

    # Row with the syntax error should have an empty clone_density.
    syntax_error_row = next(r for r in output_rows if r["id"] == "1")
    assert syntax_error_row["clone_density"] == ""

    # The two valid rows have distinct ASTs, therefore each should have
    # density 0 (no clones among the successfully parsed rows).
    for valid_id in ("0", "2"):
        row = next(r for r in output_rows if r["id"] == valid_id)
        assert float(row["clone_density"]) == pytest.approx(0.0)

def test_compute_clone_density_batch_correct_density_for_clones(tmp_path: Path):
    """
    Ensure that when multiple rows share the same AST, the computed density
    matches the definition (frequency‑1) / total_successful.
    """
    raw = tmp_path / "raw.csv"
    rows = [
        {"id": "0", "code": "x = 1"},
        {"id": "1", "code": "x = 1"},   # identical AST to row 0
        {"id": "2", "code": "y = 2"},
    ]
    _write_dummy_raw(raw, rows)

    out = tmp_path / "clone_metrics.csv"
    compute_clone_density_batch(input_path=raw, output_path=out)

    with out.open(newline="") as f:
        reader = csv.DictReader(f)
        output = {r["id"]: float(r["clone_density"]) for r in reader}

    # Two rows share the same AST; total successful rows = 3.
    # Density for rows 0 and 1: (2‑1)/3 = 0.333333
    # Row 2 has a unique AST: (1‑1)/3 = 0.0
    assert output["0"] == pytest.approx(1 / 3)
    assert output["1"] == pytest.approx(1 / 3)
    assert output["2"] == pytest.approx(0.0)