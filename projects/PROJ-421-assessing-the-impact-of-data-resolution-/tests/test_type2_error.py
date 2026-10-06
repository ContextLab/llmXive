"""
Unit tests for Type II Error Delta Analysis (T030).
"""

import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path

# Import the function under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from type2_error_analysis import calculate_type2_error_delta

def test_calculate_type2_error_delta_basic():
    """
    Test basic calculation of Type II error delta.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "results.csv"
        output_path = Path(tmpdir) / "results_output.csv"

        # Create a mock results dataframe
        # 30m baseline: Power = 0.90 -> Error = 0.10
        # 60m: Power = 0.80 -> Error = 0.20 -> Delta = 0.10 (10%)
        # 120m: Power = 0.70 -> Error = 0.30 -> Delta = 0.20 (20%)
        mock_data = {
            'resolution': ['30m', '60m', '120m'],
            'power': [0.90, 0.80, 0.70]
        }
        df = pd.DataFrame(mock_data)
        df.to_csv(input_path, index=False)

        result_df = calculate_type2_error_delta(str(input_path), str(output_path))

        # Expected Deltas (percentage points)
        # Baseline Error = 0.10
        # 60m Error = 0.20 -> Delta = 0.10 * 100 = 10.0
        # 120m Error = 0.30 -> Delta = 0.20 * 100 = 20.0
        expected_deltas = [0.0, 10.0, 20.0]

        assert 'type_ii_error_delta' in result_df.columns
        assert pytest.approx(result_df.iloc[0]['type_ii_error_delta'], 0.01) == 0.0
        assert pytest.approx(result_df.iloc[1]['type_ii_error_delta'], 0.01) == 10.0
        assert pytest.approx(result_df.iloc[2]['type_ii_error_delta'], 0.01) == 20.0

        # Verify file was written
        assert output_path.exists()
        loaded_df = pd.read_csv(output_path)
        assert 'type_ii_error_delta' in loaded_df.columns

def test_calculate_type2_error_delta_missing_file():
    """
    Test that FileNotFoundError is raised if input file is missing.
    """
    with pytest.raises(FileNotFoundError):
        calculate_type2_error_delta("/nonexistent/path/results.csv")

def test_calculate_type2_error_delta_missing_power():
    """
    Test that ValueError is raised if 'power' column is missing.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "results.csv"
        mock_data = {
            'resolution': ['30m', '60m'],
            'moran_i': [0.5, 0.4]
        }
        pd.DataFrame(mock_data).to_csv(input_path, index=False)

        with pytest.raises(ValueError) as exc_info:
            calculate_type2_error_delta(str(input_path))
        
        assert "'power' column" in str(exc_info.value)

def test_calculate_type2_error_delta_missing_baseline():
    """
    Test that ValueError is raised if 30m baseline is missing.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "results.csv"
        mock_data = {
            'resolution': ['60m', '120m'],
            'power': [0.80, 0.70]
        }
        pd.DataFrame(mock_data).to_csv(input_path, index=False)

        with pytest.raises(ValueError) as exc_info:
            calculate_type2_error_delta(str(input_path))
        
        assert "30m baseline" in str(exc_info.value)