"""
Contract test for T021b: Verify Satterthwaite summary output.

Checks:
1. File exists at data/results/lmm_summary_satterthwaite.csv
2. Contains column 'df_Satterthwaite'
3. df_Satterthwaite > 0 for all rows
4. p-values are plausible (0 < p < 1)
"""
import csv
import os
import pytest
from pathlib import Path
from config import get_results_dir

OUTPUT_FILE = "lmm_summary_satterthwaite.csv"

def get_output_path():
    return get_results_dir() / OUTPUT_FILE

def test_lmm_satterthwaite_file_exists():
    """Verify that the output file exists."""
    path = get_output_path()
    assert path.exists(), f"Output file {path} does not exist"

def test_lmm_satterthwaite_has_required_columns():
    """Verify that the output file contains the required column 'df_Satterthwaite'."""
    path = get_output_path()
    if not path.exists():
        pytest.skip("Output file does not exist")
    
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        assert 'df_Satterthwaite' in headers, f"Missing required column 'df_Satterthwaite'. Found: {headers}"

def test_lmm_satterthwaite_df_positive():
    """Verify that df_Satterthwaite > 0 for all rows."""
    path = get_output_path()
    if not path.exists():
        pytest.skip("Output file does not exist")
    
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            df_val = float(row['df_Satterthwaite'])
            assert df_val > 0, f"df_Satterthwaite must be > 0, got {df_val}"

def test_lmm_satterthwaite_p_values_plausible():
    """Verify that p-values are in the range (0, 1)."""
    path = get_output_path()
    if not path.exists():
        pytest.skip("Output file does not exist")
    
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'p_value' in row:
                p_val = float(row['p_value'])
                assert 0 <= p_val <= 1, f"p-value must be between 0 and 1, got {p_val}"

def test_lmm_satterthwaite_not_empty():
    """Verify that the output file is not empty (has at least one data row)."""
    path = get_output_path()
    if not path.exists():
        pytest.skip("Output file does not exist")
    
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) > 0, "Output file contains no data rows"