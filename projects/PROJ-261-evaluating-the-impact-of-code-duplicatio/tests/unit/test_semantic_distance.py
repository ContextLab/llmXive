import csv
import tempfile
from pathlib import Path

import pytest

# Import the function under test
from model_metrics import compute_semantic_distance_batch

@pytest.fixture
def temporary_python_files():
    """Create a temporary directory with a couple of simple .py files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        (base_path / "a.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
        (base_path / "b.py").write_text("def bar(x):\n    return x * 2\n", encoding="utf-8")
        yield base_path

def test_compute_semantic_distance_creates_csv(temporary_python_files):
    """Ensure the semantic distance CSV is created and contains valid numeric entries."""
    input_dir = temporary_python_files
    # Run the computation
    compute_semantic_distance_batch(input_path=input_dir)

    output_path = Path("data/processed/semantic_distance.csv")
    assert output_path.is_file(), "Semantic distance CSV was not created."

    # Read the CSV and verify contents
    with output_path.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    # Expect two rows (one per .py file)
    assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"

    for row in rows:
        # file_path should be a relative path ending with .py
        assert row["file_path"].endswith(".py")
        # semantic_distance should be a parsable float
        try:
            val = float(row["semantic_distance"])
        except ValueError:
            pytest.fail(f"Semantic distance value is not a float: {row['semantic_distance']}")
        # Distance should be finite (not NaN or inf)
        assert math.isfinite(val), "Semantic distance is not finite"

    # Clean up the generated file to avoid side‑effects for other tests
    output_path.unlink()