import csv
import os
from pathlib import Path

import pytest

# Import the function from the module under test
from ast_cloner import compute_clone_density_batch

@pytest.fixture
def sample_python_files(tmp_path: Path):
    """Create a small set of Python files for testing."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    # File 1: simple function
    (src_dir / "a.py").write_text(
        "def foo(x):\n    return x + 1\n"
    )
    # File 2: identical to a.py (type‑1 clone)
    (src_dir / "b.py").write_text(
        "def foo(x):\n    return x + 1\n"
    )
    # File 3: same logic but different variable name (type‑2 clone)
    (src_dir / "c.py").write_text(
        "def foo(y):\n    return y + 1\n"
    )
    # File 4: unrelated code
    (src_dir / "d.py").write_text(
        "def bar(z):\n    return z * 2\n"
    )
    return src_dir

def test_compute_clone_density_batch_writes_csv(tmp_path: Path, sample_python_files):
    """Ensure the function creates the CSV with expected columns."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    # Override the default path by passing the temporary source directory
    compute_clone_density_batch(input_path=sample_python_files)

    csv_path = Path("data/processed/clone_metrics.csv")
    assert csv_path.is_file(), "clone_metrics.csv was not created"

    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Verify that each source file produced a row
    expected_files = {str(p) for p in sample_python_files.rglob("*.py")}
    result_files = {row["file_path"] for row in rows}
    assert expected_files == result_files

    # Check that clone_density column exists and is a float string
    for row in rows:
        try:
            float(row["clone_density"])
        except ValueError:
            pytest.fail(f"clone_density not convertible to float: {row['clone_density']}")

def test_compute_clone_density_batch_default_path(tmp_path: Path, monkeypatch):
    """When called without arguments it should use data/raw."""
    # Create a dummy data/raw hierarchy
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "example.py").write_text("x = 1\n")

    # Run without specifying a path
    compute_clone_density_batch()

    csv_path = Path("data/processed/clone_metrics.csv")
    assert csv_path.is_file()
    # Clean up created files to avoid side effects for other tests
    csv_path.unlink()
    (raw_dir / "example.py").unlink()
    raw_dir.rmdir()
    # Remove processed directory if empty
    processed_dir = Path("data/processed")
    if not any(processed_dir.iterdir()):
        processed_dir.rmdir()