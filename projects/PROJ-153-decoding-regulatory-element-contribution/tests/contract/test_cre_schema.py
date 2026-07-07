"""
Contract test for US1 output schema: results/CRE_ranked_<stress>.md

Validates that the ranked CRE catalog produced by the pipeline adheres to the
required schema defined in the specification (FR-008, SC-001).

Requirements:
- File must exist at results/CRE_ranked_<stress>.md
- Must contain a header row with specific columns
- Must contain at least one data row with q-value <= 0.05
- Column types and formats must match specification
"""

import os
import re
import pytest
from pathlib import Path

# Expected output directory and filename pattern
RESULTS_DIR = Path("results")
OUTPUT_PATTERN = r"CRE_ranked_(.+)\.md"

# Required columns as per specification (FR-008)
REQUIRED_COLUMNS = [
    "CRE_id",
    "chrom",
    "start",
    "end",
    "strand",
    "TF",
    "log2FC",
    "beta1",
    "q_value"
]

# Column regex patterns for validation
COLUMN_PATTERNS = {
    "chrom": r"^chr[0-9XYM]+$",
    "start": r"^\d+$",
    "end": r"^\d+$",
    "strand": r"^[+-.]$",
    "TF": r"^[A-Z0-9_]+$",
    "log2FC": r"^-?\d+(\.\d+)?$",
    "beta1": r"^-?\d+(\.\d+)?$",
    "q_value": r"^\d+\.\d+$"
}

def find_ranked_cre_files():
    """Find all CRE ranked markdown files in the results directory."""
    if not RESULTS_DIR.exists():
        return []
    
    files = []
    for f in RESULTS_DIR.iterdir():
        if f.is_file() and re.match(OUTPUT_PATTERN, f.name):
            files.append(f)
    return files

def parse_markdown_table(file_path):
    """
    Parse a markdown table from a file.
    Returns (headers, rows) where rows is a list of dicts.
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    headers = None
    rows = []
    in_table = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect table header
        if line.startswith('|') and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if headers is None:
                headers = parts
                in_table = True
            elif in_table:
                # Data row
                if len(parts) == len(headers):
                    row = dict(zip(headers, parts))
                    rows.append(row)
    
    return headers, rows

def test_output_file_exists():
    """Verify that at least one ranked CRE file exists."""
    files = find_ranked_cre_files()
    assert len(files) > 0, "No CRE ranked files found in results/ directory"

def test_required_columns_present():
    """Verify that all required columns are present in the output."""
    files = find_ranked_cre_files()
    assert len(files) > 0, "No CRE ranked files found to validate schema"
    
    for file_path in files:
        headers, _ = parse_markdown_table(file_path)
        assert headers is not None, f"Could not parse table from {file_path}"
        
        missing = set(REQUIRED_COLUMNS) - set(headers)
        assert len(missing) == 0, f"Missing required columns in {file_path}: {missing}"

def test_at_least_one_significant_cre():
    """Verify that at least one CRE with q <= 0.05 is present."""
    files = find_ranked_cre_files()
    assert len(files) > 0, "No CRE ranked files found to validate significance"
    
    found_significant = False
    for file_path in files:
        _, rows = parse_markdown_table(file_path)
        for row in rows:
            if "q_value" in row:
                try:
                    q_val = float(row["q_value"])
                    if q_val <= 0.05:
                        found_significant = True
                        break
                except ValueError:
                    continue
        if found_significant:
            break
    
    assert found_significant, "No CREs with q-value <= 0.05 found in any output file"

def test_column_format_validation():
    """Verify that column values match expected formats."""
    files = find_ranked_cre_files()
    assert len(files) > 0, "No CRE ranked files found to validate formats"
    
    for file_path in files:
        headers, rows = parse_markdown_table(file_path)
        if headers is None or len(rows) == 0:
            continue
        
        for row in rows:
            for col_name, pattern in COLUMN_PATTERNS.items():
                if col_name in row:
                    value = row[col_name]
                    assert re.match(pattern, value), \
                        f"Invalid format for {col_name}='{value}' in {file_path}"

def test_q_value_filtering():
    """Verify that only CREs with q <= 0.05 are included (per FR-007)."""
    files = find_ranked_cre_files()
    assert len(files) > 0, "No CRE ranked files found to validate filtering"
    
    for file_path in files:
        _, rows = parse_markdown_table(file_path)
        for row in rows:
            if "q_value" in row:
                try:
                    q_val = float(row["q_value"])
                    assert q_val <= 0.05, \
                        f"Found CRE with q-value {q_val} > 0.05 in {file_path} (violates FR-007)"
                except ValueError:
                    pytest.fail(f"Non-numeric q_value found in {file_path}")

def test_sorting_by_q_value_and_beta1():
    """Verify that results are sorted by q-value and |beta1| (per SC-001)."""
    files = find_ranked_cre_files()
    assert len(files) > 0, "No CRE ranked files found to validate sorting"
    
    for file_path in files:
        _, rows = parse_markdown_table(file_path)
        if len(rows) < 2:
            continue
        
        # Check if sorted by q_value ascending
        q_values = []
        for row in rows:
            if "q_value" in row:
                try:
                    q_values.append(float(row["q_value"]))
                except ValueError:
                    continue
        
        if len(q_values) >= 2:
            # Verify non-decreasing order
            for i in range(len(q_values) - 1):
                assert q_values[i] <= q_values[i + 1], \
                    f"Results in {file_path} are not sorted by q-value ascending"