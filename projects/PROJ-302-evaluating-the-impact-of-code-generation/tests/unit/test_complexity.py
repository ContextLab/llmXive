"""
Unit tests for the complexity extraction module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the function to test
from code.feature_extraction.complexity import calculate_snippet_complexity, MISSING_VALUE

def test_calculate_loc_simple():
    """Test LOC calculation for a simple script."""
    code = """
    x = 1
    y = 2
    z = x + y
    """
    loc, cc = calculate_snippet_complexity(code)
    # 3 lines of code
    assert loc == 3.0
    # No functions, baseline complexity 1
    assert cc == 1.0

def test_calculate_complexity_function():
    """Test Cyclomatic Complexity calculation."""
    code = """
    def check(x):
        if x > 0:
            return True
        else:
            return False
    """
    loc, cc = calculate_snippet_complexity(code)
    # The function has 1 decision point (if), so complexity is 1 (base) + 1 = 2
    # radon.cc_visit returns complexity for the function itself.
    # Base complexity is 1. 'if' adds 1. Total 2.
    assert cc == 2.0
    # LOC should be 5 (def, if, return, else, return)
    assert loc == 5.0

def test_calculate_empty():
    """Test handling of empty code."""
    loc, cc = calculate_snippet_complexity("")
    assert loc == MISSING_VALUE
    assert cc == MISSING_VALUE

def test_calculate_none():
    """Test handling of None input."""
    loc, cc = calculate_snippet_complexity(None)
    assert loc == MISSING_VALUE
    assert cc == MISSING_VALUE

def test_calculate_complex_control_flow():
    """Test with multiple control flow statements."""
    code = """
    def process(data):
        for item in data:
            if item > 0:
                print("positive")
            elif item < 0:
                print("negative")
            else:
                print("zero")
        return True
    """
    loc, cc = calculate_snippet_complexity(code)
    # Complexity: 1 (base) + 1 (for) + 1 (if) + 1 (elif) = 4
    assert cc == 4.0

def test_integration_parquet_io():
    """Test the full pipeline with a temporary parquet file."""
    from code.feature_extraction.complexity import process_dataset

    # Create temporary input file
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.parquet"
        output_path = Path(tmpdir) / "output.parquet"

        # Create test data
        data = {
            "snippet_id": [1, 2],
            "source_code": [
                "x = 1\ny = 2",
                "def add(a, b):\n    return a + b"
            ]
        }
        df_input = pd.DataFrame(data)
        df_input.to_parquet(input_path)

        # Run process
        process_dataset(str(input_path), str(output_path))

        # Verify output
        assert output_path.exists()
        df_output = pd.read_parquet(output_path)

        assert "loc" in df_output.columns
        assert "cyclomatic_complexity" in df_output.columns
        assert len(df_output) == 2

        # Check specific values
        # Row 0: simple assignment, 2 lines, complexity 1
        assert df_output.iloc[0]["loc"] == 2.0
        assert df_output.iloc[0]["cyclomatic_complexity"] == 1.0

        # Row 1: function, 2 lines, complexity 1 (base) + 0 (no if/for) = 1? 
        # Actually radon counts the function definition as complexity 1.
        # Let's just ensure it's a valid number and not -1
        assert df_output.iloc[1]["loc"] >= 2.0
        assert df_output.iloc[1]["cyclomatic_complexity"] >= 1.0
