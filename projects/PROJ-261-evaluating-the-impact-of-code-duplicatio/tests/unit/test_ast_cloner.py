import pathlib
import csv
import pytest

from ast_cloner import compute_clone_density_batch, parse_python_file

def create_dummy_raw_csv(tmp_path):
    raw_path = tmp_path / "github-code-sample.csv"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_path", "code"])
        writer.writeheader()
        writer.writerow({"file_path": "a.py", "code": "x = 1"})
        writer.writerow({"file_path": "b.py", "code": "x = 1"})  # duplicate
    return raw_path

def test_compute_clone_density_writes_output(tmp_path):
    raw_csv = create_dummy_raw_csv(tmp_path)
    # Call with explicit keyword to hit the flexible signature
    compute_clone_density_batch(input_path=raw_csv)

    out_csv = pathlib.Path("data/processed/clone_metrics.csv")
    assert out_csv.is_file()
    with out_csv.open() as f:
        rows = list(csv.DictReader(f))
        assert len(rows) == 2
        # Both rows should have a non‑zero clone density
        assert float(rows[0]["clone_density"]) > 0

@pytest.mark.parametrize(
    "source,expected",
    [
        ("def foo():\n    return 1", True),
        ("def foo(\n    return 1", False),  # syntax error
    ],
)
def test_parse_python_file(source, expected):
    tree = parse_python_file(source)
    if expected:
        assert isinstance(tree, type(ast.parse(source)))
    else:
        assert tree is None
