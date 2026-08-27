import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from type2_error_analysis import calculate_type2_error_delta

def test_calculate_type2_error_delta():
    """Test Type II error delta calculation with mock data."""
    # Create a temporary CSV
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("resolution,power\n")
        f.write("30m,0.95\n")
        f.write("60m,0.85\n")
        f.write("120m,0.70\n")
        f.write("240m,0.50\n")
        temp_path = f.name

    try:
        result_df = calculate_type2_error_delta(temp_path)

        # Check columns
        assert 'type2_error' in result_df.columns
        assert 'type2_error_delta' in result_df.columns

        # Check baseline (30m) delta is 0
        baseline = result_df[result_df['resolution'] == '30m']
        assert len(baseline) == 1
        assert abs(baseline['type2_error_delta'].iloc[0]) < 1e-6

        # Check 60m delta: (1-0.85) - (1-0.95) = 0.15 - 0.05 = 0.10
        row_60 = result_df[result_df['resolution'] == '60m']
        assert abs(row_60['type2_error_delta'].iloc[0] - 0.10) < 1e-6

    finally:
        os.unlink(temp_path)

def test_missing_file():
    """Test that FileNotFoundError is raised for missing input."""
    with pytest.raises(FileNotFoundError):
        calculate_type2_error_delta("/nonexistent/path.csv")

def test_missing_columns():
    """Test that ValueError is raised if columns are missing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("resolution,some_other_col\n")
        f.write("30m,0.95\n")
        temp_path = f.name

    try:
        with pytest.raises(ValueError):
            calculate_type2_error_delta(temp_path)
    finally:
        os.unlink(temp_path)