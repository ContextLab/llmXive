"""
Integration test for T026: Signal Output Generation.

Verifies that the signal output script produces a valid CSV with the correct schema
and that the signal_flag logic is applied correctly.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.signal_output import apply_signal_flag, generate_signals_csv
from src.utils.config import THRESHOLDS

class TestSignalOutput:
    """Test suite for T026 signal output generation."""

    def test_apply_signal_flag_ror_only(self):
        """Test signal flag when only ROR condition is met."""
        row = pd.Series({
            'ror': 3.0, 'ror_ci_lower': 1.5,
            'prr': 1.0, 'prr_ci_lower': 0.5,
            'ic': -0.5, 'ic_ci_lower': -1.0
        })
        # ROR: 3.0 > 2.0 (True), CI > 1.0 (True) -> 1 condition
        # PRR: 1.0 > 1.5 (False) -> 0 conditions
        # IC: -0.5 > 0 (False) -> 0 conditions
        # Total: 1 -> False
        assert apply_signal_flag(row) is False

    def test_apply_signal_flag_ror_and_prr(self):
        """Test signal flag when ROR and PRR conditions are met."""
        row = pd.Series({
            'ror': 3.0, 'ror_ci_lower': 1.5,
            'prr': 2.0, 'prr_ci_lower': 1.2,
            'ic': -0.5, 'ic_ci_lower': -1.0
        })
        # ROR: True
        # PRR: 2.0 > 1.5 (True), CI > 1.0 (True) -> 1 condition
        # IC: False
        # Total: 2 -> True
        assert apply_signal_flag(row) is True

    def test_apply_signal_flag_all_three(self):
        """Test signal flag when all three conditions are met."""
        row = pd.Series({
            'ror': 3.0, 'ror_ci_lower': 1.5,
            'prr': 2.0, 'prr_ci_lower': 1.2,
            'ic': 1.0, 'ic_ci_lower': 0.5
        })
        # All True -> 3 conditions -> True
        assert apply_signal_flag(row) is True

    def test_apply_signal_flag_edge_case_ic(self):
        """Test IC condition boundary."""
        # IC > 0.0 AND IC_CI_LOWER > 0.0
        row = pd.Series({
            'ror': 1.0, 'ror_ci_lower': 0.5,
            'prr': 1.0, 'prr_ci_lower': 0.5,
            'ic': 0.1, 'ic_ci_lower': 0.1
        })
        # Only IC condition met -> 1 -> False
        assert apply_signal_flag(row) is False

        row = pd.Series({
            'ror': 3.0, 'ror_ci_lower': 1.5,
            'prr': 1.0, 'prr_ci_lower': 0.5,
            'ic': 0.1, 'ic_ci_lower': 0.1
        })
        # ROR and IC met -> 2 -> True
        assert apply_signal_flag(row) is True

    def test_generate_signals_csv_schema(self, tmp_path):
        """Test that generate_signals_csv produces a file with the correct schema."""
        # Create a mock cleaned parquet file
        # Since we can't easily mock the full run_analysis pipeline in a unit test
        # without heavy mocking, we test the function's ability to handle a scenario
        # where run_analysis returns a DataFrame.
        
        # We will mock the run_analysis function temporarily
        from unittest.mock import patch, MagicMock
        from src.analysis import signal_output

        mock_results = pd.DataFrame({
            'soc': ['SOC1', 'SOC2'],
            'ror': [3.0, 1.0],
            'ror_ci_lower': [1.5, 0.5],
            'ror_ci_upper': [5.0, 2.0],
            'prr': [2.0, 1.0],
            'prr_ci_lower': [1.2, 0.5],
            'prr_ci_upper': [3.0, 2.0],
            'ic': [1.0, -0.5],
            'ic_ci_lower': [0.5, -1.0],
            'ic_ci_upper': [2.0, 0.0],
            'p_value': [0.01, 0.5]
        })

        input_file = tmp_path / "cleaned_vaers.parquet"
        output_file = tmp_path / "signals.csv"

        # Create a dummy parquet file
        mock_results.to_parquet(input_file)

        with patch.object(signal_output, 'run_analysis', return_value=mock_results.copy()):
            with patch.object(signal_output, 'benjamini_hochberg', return_value=[0.02, 0.5]):
                generate_signals_csv(str(input_file), str(output_file))

        assert output_file.exists()
        
        df = pd.read_csv(output_file)
        
        expected_columns = [
            'soc', 'ror', 'ror_ci_lower', 'ror_ci_upper',
            'prr', 'prr_ci_lower', 'prr_ci_upper',
            'ic', 'ic_ci_lower', 'ic_ci_upper',
            'p_adj', 'signal_flag'
        ]
        
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"

        # Check signal_flag logic
        # SOC1: ROR (True), PRR (True), IC (True) -> 3 -> True
        # SOC2: ROR (False), PRR (False), IC (False) -> 0 -> False
        assert df.loc[df['soc'] == 'SOC1', 'signal_flag'].iloc[0] is True
        assert df.loc[df['soc'] == 'SOC2', 'signal_flag'].iloc[0] is False
