"""
Contract test for the population‑structure control metrics output.

Verifies that the CSV produced by `compute_population_structure_control_metrics`
(via `code/association.py`) conforms to the expected schema.
"""
import os
import csv
import pytest
import math

EXPECTED_PATH = "data/results/population_structure_control_metrics.csv"
REQUIRED_COLUMNS = [
    "gene_id",
    "r2_with_pcs",
    "r2_without_pcs",
    "reduction_percent"
]

def _load_metrics():
    if not os.path.exists(EXPECTED_PATH):
        raise FileNotFoundError(
            f"Metrics file not found at {EXPECTED_PATH}. "
            "Run the association pipeline to generate it."
        )
    with open(EXPECTED_PATH, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def test_metrics_file_exists():
    assert os.path.exists(EXPECTED_PATH), f"Metrics file {EXPECTED_PATH} does not exist."

def test_metrics_header():
    with open(EXPECTED_PATH, newline='', encoding='utf-8') as f:
        header = csv.DictReader(f).fieldnames
    missing = set(REQUIRED_COLUMNS) - set(header)
    assert not missing, f"Missing columns in metrics file: {missing}"

def test_metrics_rows():
    rows = _load_metrics()
    assert rows, "Metrics file is empty; expected at least one gene metric."
    for i, row in enumerate(rows):
        # gene_id non‑empty
        assert row['gene_id'], f"Row {i} missing gene_id"
        # numeric fields
        for col in REQUIRED_COLUMNS[1:]:
            try:
                val = float(row[col])
            except ValueError:
                pytest.fail(f"Row {i} column {col} is not numeric")
            assert not math.isnan(val), f"Row {i} column {col} is NaN"
            assert not math.isinf(val), f"Row {i} column {col} is Inf"
        # reduction_percent handling (should be >=0)
        assert float(row['reduction_percent']) >= 0.0, "reduction_percent should be non‑negative"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])