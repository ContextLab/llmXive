"""
Unit tests for the AST cloner utilities, including syntax‑error handling.
"""
from __future__ import annotations

import csv
import pathlib
import pytest
import ast

from ast_cloner import compute_clone_density_batch, parse_python_file, IdentifierNormalizer


def test_parse_python_file_reads_content(tmp_path: pathlib.Path):
    file = tmp_path / "example.py"
    file.write_text("a = 1", encoding="utf-8")
    content = parse_python_file(file)
    assert content == "a = 1"


def test_identifier_normalizer_changes_names():
    source = "def foo(x):\n    return x + 1"
    tree = ast.parse(source)
    normaliser = IdentifierNormalizer()
    new_tree = normaliser.visit(tree)
    normalized = ast.unparse(new_tree)
    # The function name and argument should be replaced by generic placeholders
    assert "def var_0(var_1):" in normalized


def test_compute_clone_density_batch_writes_csv(tmp_path: pathlib.Path):
    # Create two identical files (Type‑1 clone) and one distinct file
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "a.py").write_text("x = 1", encoding="utf-8")
    (raw_dir / "b.py").write_text("x = 1", encoding="utf-8")
    (raw_dir / "c.py").write_text("y = 2", encoding="utf-8")

    output_csv = tmp_path / "clone_metrics.csv"

    # Call with explicit paths
    compute_clone_density_batch(input_path=raw_dir, output_path=output_csv)

    # Verify CSV exists and contains plausible numbers
    assert output_csv.exists()
    rows = list(csv.reader(output_csv.read_text().splitlines()))
    header, values = rows
    assert header == ["total_files", "clone_files", "clone_density"]
    total, clone_files, density = map(float, values)
    assert total == 3
    assert clone_files == 2  # two files belong to a clone group
    assert 0.0 < density <= 1.0


def test_parse_python_file_syntax_error(tmp_path: pathlib.Path):
    """
    Ensure that parsing a file with invalid Python syntax raises a SyntaxError.
    """
    bad_file = tmp_path / "bad.py"
    # Deliberately malformed Python code
    bad_file.write_text("def foo(:\n    pass", encoding="utf-8")

    with pytest.raises(SyntaxError):
        parse_python_file(bad_file)