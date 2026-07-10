"""
Contract test for replication output schema.

Verifies that the replication analysis output produced by code/replication.py
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
EXPECTED_OUTPUT_PATH = "data/results/replication_analysis.csv"

# Required columns as per FR-010 and US2 specification
REQUIRED_COLUMNS = [
    "gene_id",
    "te_id",
    "original_effect_size",
    "replication_effect_size",
    "direction_concordance",
    "replication_pvalue",
    "original_adj_pvalue",
    "concordance_flag"
]

def _load_replication_output() -> List[Dict[str, Any]]:
    """Load the replication output CSV file."""
    if not os.path.exists(EXPECTED_OUTPUT_PATH):
        raise FileNotFoundError(
            f"Replication output file not found at {EXPECTED_OUTPUT_PATH}. "
            "Ensure run_replication_analysis() has been executed."
        )
    
    with open(EXPECTED_OUTPUT_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def _validate_column_types(row: Dict[str, Any]) -> None:
    """Validate data types and basic constraints for a single row."""
    # gene_id and te_id must be non-empty strings
    assert isinstance(row['gene_id'], str) and len(row['gene_id']) > 0, "gene_id must be non-empty"
    assert isinstance(row['te_id'], str) and len(row['te_id']) > 0, "te_id must be non-empty"
    
    # Effect sizes and p-values must be numeric
    try:
        orig_eff = float(row['original_effect_size'])
        rep_eff = float(row['replication_effect_size'])
        rep_pval = float(row['replication_pvalue'])
        orig_adj_pval = float(row['original_adj_pvalue'])
    except ValueError as e:
        raise AssertionError(f"Numeric conversion failed for row {row}: {e}")
    
    # Effect sizes can be any float (positive or negative)
    assert not math.isnan(orig_eff), "original_effect_size cannot be NaN"
    assert not math.isnan(rep_eff), "replication_effect_size cannot be NaN"
    
    # P-values must be in [0, 1]
    assert 0.0 <= rep_pval <= 1.0, f"replication_pvalue {rep_pval} out of range [0, 1]"
    assert 0.0 <= orig_adj_pval <= 1.0, f"original_adj_pvalue {orig_adj_pval} out of range [0, 1]"
    
    # direction_concordance must be boolean-like string
    valid_concordance = ['True', 'False', 'true', 'false', '1', '0', 'yes', 'no']
    assert row['direction_concordance'] in valid_concordance, \
        f"direction_concordance '{row['direction_concordance']}' is not a valid boolean representation"
    
    # concordance_flag must be boolean-like string
    assert row['concordance_flag'] in valid_concordance, \
        f"concordance_flag '{row['concordance_flag']}' is not a valid boolean representation"

def test_replication_output_file_exists():
    """Contract Test: Verify the replication output file exists."""
    assert os.path.exists(EXPECTED_OUTPUT_PATH), \
        f"Replication output file {EXPECTED_OUTPUT_PATH} does not exist. " \
        "Run the replication pipeline (code/replication.py) to generate it."

def test_replication_output_has_required_columns():
    """Contract Test: Verify all required columns are present in the header."""
    with open(EXPECTED_OUTPUT_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
    
    missing_columns = set(REQUIRED_COLUMNS) - set(headers)
    assert not missing_columns, \
        f"Missing required columns in replication output: {missing_columns}. " \
        f"Expected columns: {REQUIRED_COLUMNS}, Found: {headers}"

def test_replication_output_column_order():
    """Contract Test: Verify columns appear in the expected order."""
    with open(EXPECTED_OUTPUT_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
    
    # Check that required columns appear in the specified order
    # (allowing for potential extra columns not in our list, but required ones must match)
    expected_order_indices = []
    for col in REQUIRED_COLUMNS:
        if col in headers:
            expected_order_indices.append(headers.index(col))
    
    # Verify the indices are strictly increasing
    for i in range(1, len(expected_order_indices)):
        assert expected_order_indices[i] > expected_order_indices[i-1], \
            f"Column '{REQUIRED_COLUMNS[i]}' appears before '{REQUIRED_COLUMNS[i-1]}' in output"

def test_replication_output_row_data_validity():
    """Contract Test: Verify data types and value constraints for all rows."""
    rows = _load_replication_output()
    
    assert len(rows) > 0, "Replication output file is empty. Expected at least one row of results."
    
    for i, row in enumerate(rows):
        try:
            _validate_column_types(row)
        except AssertionError as e:
            pytest.fail(f"Row {i} validation failed: {e}")

def test_replication_output_concordance_logic():
    """Contract Test: Verify direction_concordance logic consistency."""
    rows = _load_replication_output()
    
    for i, row in enumerate(rows):
        orig_eff = float(row['original_effect_size'])
        rep_eff = float(row['replication_effect_size'])
        
        # Calculate expected concordance
        expected_concordance = (orig_eff * rep_eff) > 0  # Same sign means concordance
        
        # Parse actual concordance
        actual_str = row['direction_concordance'].lower()
        if actual_str in ['true', '1', 'yes']:
            actual_concordance = True
        else:
            actual_concordance = False
        
        assert actual_concordance == expected_concordance, \
            f"Row {i}: direction_concordance mismatch. " \
            f"Orig: {orig_eff}, Rep: {rep_eff}, Expected: {expected_concordance}, Got: {actual_concordance}"

def test_replication_output_no_nan_values():
    """Contract Test: Ensure no NaN or Inf values in numeric columns."""
    rows = _load_replication_output()
    
    numeric_cols = [
        'original_effect_size',
        'replication_effect_size',
        'replication_pvalue',
        'original_adj_pvalue'
    ]
    
    for i, row in enumerate(rows):
        for col in numeric_cols:
            val = float(row[col])
            assert not math.isnan(val), f"Row {i}, column {col} contains NaN"
            assert not math.isinf(val), f"Row {i}, column {col} contains Inf"

if __name__ == "__main__":
    # Run tests manually if executed as script
    pytest.main([__file__, "-v"])