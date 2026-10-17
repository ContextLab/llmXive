"""
Contract test for association output schema.

Verifies that the association analysis output produced by code/association.py
conforms to the expected schema defined in the project specification.

This test ensures:
1. The output file exists at the expected path.
2. The CSV header contains all required columns.
3. Data types and value constraints for each column are valid.
"""
import os
import csv
import pytest
import math
from typing import List, Dict, Any

# Expected output path relative to project root
EXPECTED_OUTPUT_PATH = "data/results/association_results_bh.csv"

# Required columns as per FR‑004 and FR‑005
REQUIRED_COLUMNS = [
    "te_id",
    "gene_id",
    "effect_size",
    "p_value",
    "adj_p_value",
    "r_squared",
    "t_statistic"
]

def _load_association_output() -> List[Dict[str, Any]]:
    """Load the association output CSV file."""
    if not os.path.exists(EXPECTED_OUTPUT_PATH):
        raise FileNotFoundError(
            f"Association output file not found at {EXPECTED_OUTPUT_PATH}. "
            "Ensure run_association_analysis() has been executed."
        )

    with open(EXPECTED_OUTPUT_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def test_association_output_file_exists():
    """Contract Test: Verify the association output file exists."""
    assert os.path.exists(EXPECTED_OUTPUT_PATH), (
        f"Association output file {EXPECTED_OUTPUT_PATH} does not exist. "
        "Run the association pipeline (code/association.py) to generate it."
    )

def test_association_output_has_required_columns():
    """Contract Test: Verify all required columns are present in the header."""
    with open(EXPECTED_OUTPUT_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

    missing = set(REQUIRED_COLUMNS) - set(headers)
    assert not missing, (
        f"Missing required columns in association output: {missing}. "
        f"Expected columns: {REQUIRED_COLUMNS}, Found: {headers}"
    )

def test_association_output_column_order():
    """Contract Test: Verify required columns appear in the expected order."""
    with open(EXPECTED_OUTPUT_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

    # Ensure required columns are in the specified order (allowing extra columns)
    indices = [headers.index(col) for col in REQUIRED_COLUMNS if col in headers]
    assert indices == sorted(indices), "Required columns are not in the expected order."

def test_association_output_row_data_validity():
    """Contract Test: Verify data types and basic constraints for all rows."""
    rows = _load_association_output()
    assert len(rows) > 0, "Association output file is empty; expected at least one row."

    for i, row in enumerate(rows):
        try:
            # te_id and gene_id must be non‑empty strings
            assert row['te_id'] and isinstance(row['te_id'], str)
            assert row['gene_id'] and isinstance(row['gene_id'], str)

            # Numeric fields
            effect = float(row['effect_size'])
            p_val = float(row['p_value'])
            adj_p = float(row['adj_p_value'])
            r2 = float(row['r_squared'])
            t_stat = float(row['t_statistic'])
        except (ValueError, KeyError) as e:
            pytest.fail(f"Row {i} validation failed: {e}")

        # P‑values must be within [0, 1]
        assert 0.0 <= p_val <= 1.0, f"p_value {p_val} out of range"
        assert 0.0 <= adj_p <= 1.0, f"adj_p_value {adj_p} out of range"
        # R² must be within [0, 1]
        assert 0.0 <= r2 <= 1.0, f"r_squared {r2} out of range"

def test_association_output_no_nan_or_inf():
    """Contract Test: Ensure no NaN or infinite values in numeric columns."""
    rows = _load_association_output()
    numeric_cols = ['effect_size', 'p_value', 'adj_p_value', 'r_squared', 't_statistic']
    for i, row in enumerate(rows):
        for col in numeric_cols:
            val = float(row[col])
            assert not math.isnan(val), f"Row {i} column {col} contains NaN"
            assert not math.isinf(val), f"Row {i} column {col} contains Inf"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])