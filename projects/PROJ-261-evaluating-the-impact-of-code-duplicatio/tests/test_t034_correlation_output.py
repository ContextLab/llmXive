import csv
from pathlib import Path

def test_correlation_results_exists():
    """
    Simple integration test for task T034 – verifies that the correlation
    results CSV is produced by the pipeline and contains the expected columns.
    """
    path = Path("data/analysis/correlation_results.csv")
    assert path.is_file(), f"{path} does not exist"

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        expected = {"spearman_coefficient", "p_value", "n"}
        assert expected.issubset(set(header)), f"Missing columns: {expected - set(header)}"

# The test can be executed via ``pytest -q tests/test_t034_correlation_output.py``.