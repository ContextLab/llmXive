"""
Unit tests for the enhanced Type‑2 clone detection in ``ast_cloner``.
The tests construct small Python snippets that differ only in identifier
names and verify that they are counted as Type‑2 clones (but not as
Type‑1 clones).
"""
import csv
from pathlib import Path

import pytest

# Import the functions we need to test.
from ast_cloner import (
    _load_raw_samples,
    _write_clone_metric,
    compute_clone_density_batch,
    IdentifierNormalizer,
    parse_python_file,
)


@pytest.fixture
def raw_csv(tmp_path: Path):
    """Create a temporary raw CSV containing a few Python snippets."""
    csv_path = tmp_path / "github-code-sample.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["content"])
        # Exact duplicate (Type‑1)
        writer.writerow(["def foo(x):\n    return x"])
        writer.writerow(["def foo(x):\n    return x"])
        # Parameterised duplicate (Type‑2)
        writer.writerow(["def bar(y):\n    return y"])
        writer.writerow(["def baz(z):\n    return z"])
        # Unique snippet
        writer.writerow(["def qux(a, b):\n    return a + b"])
    return csv_path


def test_load_raw_samples(raw_csv: Path):
    samples = _load_raw_samples(raw_csv)
    assert len(samples) == 5
    assert samples[0].startswith("def foo")


def test_identifier_normalizer():
    src = "def my_func(arg1, arg2):\n    return arg1 + arg2"
    normalized = IdentifierNormalizer().normalize  # placeholder use
    # Directly use the internal normalisation helper via the public API.
    from ast_cloner import _normalize_source
    norm_src = _normalize_source(src)
    # After normalisation all identifiers should be replaced with __ID__
    assert "__ID__" in norm_src
    # The structure of the code should remain syntactically valid.
    parse_python_file(norm_src)  # should not raise


def test_compute_clone_density_batch(tmp_path: Path, monkeypatch):
    """
    Run ``compute_clone_density_batch`` on the temporary CSV and verify
    that the resulting metrics reflect one Type‑1 pair and one Type‑2 pair.
    """
    # Patch the paths used inside the module to point to our temp files.
    raw_path = tmp_path / "data" / "raw" / "github-code-sample.csv"
    processed_path = tmp_path / "data" / "processed" / "clone_metrics.csv"
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy the fixture CSV to the expected location.
    import shutil
    shutil.copyfile(
        tmp_path / "github-code-sample.csv",  # created by fixture
        raw_path,
    )

    monkeypatch.setattr(
        "ast_cloner.Path",  # monkeypatch the Path class used in the module
        lambda *args, **kwargs: Path(*args, **kwargs),
    )

    # Run the computation.
    compute_clone_density_batch()

    # Verify output CSV exists and contains expected values.
    assert processed_path.is_file()
    with processed_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        row = rows[0]
        # With 5 samples we have 10 total pairs.
        # Type‑1 duplicate pairs: 1 (the two identical foo functions)
        # Type‑2 duplicate pairs: 1 (bar vs baz after normalisation)
        # Hence densities = 0.1 each, overall = 0.2
        assert pytest.approx(float(row["clone_density_type1"]), rel=1e-3) == 0.1
        assert pytest.approx(float(row["clone_density_type2"]), rel=1e-3) == 0.1
        assert pytest.approx(float(row["clone_density_overall"]), rel=1e-3) == 0.2