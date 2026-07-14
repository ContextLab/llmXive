import csv
from pathlib import Path

import pytest

from ast_cloner import compute_clone_density_batch


@pytest.fixture
def raw_csv_two_identical(tmp_path: Path) -> Path:
    """Create a tiny raw CSV with two identical Python snippets."""
    path = tmp_path / "github-code-sample.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_path", "content"])
        writer.writeheader()
        writer.writerow(
            {"file_path": "a.py", "content": "def foo():\n    return 1"}
        )
        writer.writerow(
            {"file_path": "b.py", "content": "def foo():\n    return 1"}
        )
    return path


def test_compute_clone_density_batch_writes_file(tmp_path: Path, raw_csv_two_identical: Path):
    """Exact‑duplicate snippets should yield a density of 0.5."""
    out_path = tmp_path / "clone_metrics.csv"
    rc = compute_clone_density_batch(
        raw_path=raw_csv_two_identical,
        output_path=out_path,
    )
    assert rc == 0
    with out_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1
    density = float(rows[0]["clone_density"])
    assert pytest.approx(density, rel=1e-2) == 0.5


@pytest.fixture
def raw_csv_with_syntax_error(tmp_path: Path) -> Path:
    """CSV containing one valid snippet and one with a syntax error."""
    path = tmp_path / "github-code-sample.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_path", "content"])
        writer.writeheader()
        writer.writerow(
            {"file_path": "valid.py", "content": "def good():\n    return 42"}
        )
        # Deliberate syntax error (missing closing parenthesis)
        writer.writerow(
            {"file_path": "bad.py", "content": "def bad(:\n    pass"}
        )
    return path


def test_compute_clone_density_batch_handles_syntax_error(tmp_path: Path, raw_csv_with_syntax_error: Path):
    """Files that cannot be parsed should be skipped and logged."""
    out_path = tmp_path / "clone_metrics.csv"
    rc = compute_clone_density_batch(
        raw_path=raw_csv_with_syntax_error,
        output_path=out_path,
    )
    assert rc == 0
    with out_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1
    density = float(rows[0]["clone_density"])
    # Only the valid file remains, so no duplicates → density 0.0
    assert pytest.approx(density, rel=1e-2) == 0.0

    # Verify that a parse‑failure entry was written
    from parse_failure_logger import get_parse_failures_path

    failures_path = get_parse_failures_path()
    with failures_path.open(newline="", encoding="utf-8") as f:
        failure_reader = csv.DictReader(f)
        failures = list(failure_reader)
    # At least one failure should be recorded for the bad file
    assert any(row["file_path"] == "bad.py" for row in failures)