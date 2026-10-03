import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.analysis.signal_output import apply_signal_flag, generate_signals_csv

class TestSignalOutput:
    """
    Integration tests for T026: Signal Output Generation
    """

    @pytest.fixture
    def sample_metrics_df(self):
        """Create a sample dataframe with all required metrics."""
        return pd.DataFrame({
            'soc': ['SOC_001', 'SOC_002', 'SOC_003', 'SOC_004', 'SOC_005'],
            'ror': [3.0, 1.0, 2.5, 1.5, 0.5],
            'ror_ci_lower': [1.5, 0.5, 1.2, 0.8, 0.2],
            'ror_ci_upper': [5.0, 2.0, 4.0, 3.0, 1.0],
            'prr': [2.0, 1.0, 1.8, 1.2, 0.5],
            'prr_ci_lower': [1.2, 0.5, 1.0, 0.6, 0.2],
            'prr_ci_upper': [3.0, 2.0, 3.0, 2.0, 1.0],
            'ic': [1.5, -0.5, 0.8, 0.2, -1.0],
            'ic_ci_lower': [0.5, -1.0, 0.2, -0.2, -2.0],
            'ic_ci_upper': [2.5, 0.0, 1.5, 0.8, 0.0],
            'p_adj': [0.01, 0.50, 0.03, 0.20, 0.90]
        })

    @pytest.fixture
    def temp_input_file(self, sample_metrics_df):
        """Create a temporary input CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_metrics_df.to_csv(f, index=False)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def temp_output_file(self):
        """Create a temporary output file path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
        os.unlink(temp_path)  # Delete so generate_signals_csv can create it
        yield temp_path

    def test_apply_signal_flag_ror_condition(self):
        """Test ROR condition: ROR > 2.0 and ROR_CI_LOWER > 1.0"""
        row = pd.Series({
            'ror': 3.0, 'ror_ci_lower': 1.5,
            'prr': 1.0, 'prr_ci_lower': 0.5,
            'ic': -0.5, 'ic_ci_lower': -1.0
        })
        # Only ROR condition met -> 1 condition -> False
        assert apply_signal_flag(row) is False

    def test_apply_signal_flag_two_conditions(self):
        """Test 2-out-of-3 rule: exactly 2 conditions met -> True"""
        row = pd.Series({
            'ror': 3.0, 'ror_ci_lower': 1.5,  # ROR met
            'prr': 2.0, 'prr_ci_lower': 1.2,  # PRR met
            'ic': -0.5, 'ic_ci_lower': -1.0   # IC not met
        })
        assert apply_signal_flag(row) is True

    def test_apply_signal_flag_all_conditions(self):
        """Test all 3 conditions met -> True"""
        row = pd.Series({
            'ror': 3.0, 'ror_ci_lower': 1.5,
            'prr': 2.0, 'prr_ci_lower': 1.2,
            'ic': 1.5, 'ic_ci_lower': 0.5
        })
        assert apply_signal_flag(row) is True

    def test_apply_signal_flag_no_conditions(self):
        """Test no conditions met -> False"""
        row = pd.Series({
            'ror': 1.0, 'ror_ci_lower': 0.5,
            'prr': 1.0, 'prr_ci_lower': 0.5,
            'ic': -0.5, 'ic_ci_lower': -1.0
        })
        assert apply_signal_flag(row) is False

    def test_generate_signals_csv_creates_file(self, temp_input_file, temp_output_file):
        """Test that generate_signals_csv creates the output file."""
        generate_signals_csv(temp_input_file, temp_output_file)
        assert os.path.exists(temp_output_file)

    def test_generate_signals_csv_correct_columns(self, temp_input_file, temp_output_file):
        """Test that output CSV has all required columns."""
        generate_signals_csv(temp_input_file, temp_output_file)
        df = pd.read_csv(temp_output_file)
        
        required_columns = [
            'soc', 'ror', 'ror_ci_lower', 'ror_ci_upper',
            'prr', 'prr_ci_lower', 'prr_ci_upper',
            'ic', 'ic_ci_lower', 'ic_ci_upper',
            'p_adj', 'signal_flag'
        ]
        
        assert all(col in df.columns for col in required_columns)
        assert len(df.columns) == len(required_columns)

    def test_generate_signals_csv_signal_flag_values(self, temp_input_file, temp_output_file):
        """Test that signal_flag is boolean and correctly calculated."""
        generate_signals_csv(temp_input_file, temp_output_file)
        df = pd.read_csv(temp_output_file)
        
        # Check signal_flag column exists and is boolean
        assert 'signal_flag' in df.columns
        assert df['signal_flag'].dtype == bool

    def test_generate_signals_csv_with_thresholds(self, temp_input_file, temp_output_file):
        """Test signal detection against known thresholds."""
        # Create data where we know the expected outcome
        data = pd.DataFrame({
            'soc': ['StrongSignal', 'WeakSignal', 'NoSignal'],
            'ror': [5.0, 2.5, 1.0],
            'ror_ci_lower': [3.0, 1.2, 0.5],
            'ror_ci_upper': [7.0, 4.0, 2.0],
            'prr': [4.0, 1.8, 1.0],
            'prr_ci_lower': [2.5, 1.0, 0.5],
            'prr_ci_upper': [5.5, 3.0, 2.0],
            'ic': [2.0, 0.8, -0.5],
            'ic_ci_lower': [1.0, 0.2, -1.5],
            'ic_ci_upper': [3.0, 1.5, 0.5],
            'p_adj': [0.001, 0.05, 0.9]
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            data.to_csv(f, index=False)
            input_path = f.name
        
        try:
            generate_signals_csv(input_path, temp_output_file)
            df = pd.read_csv(temp_output_file)
            
            # StrongSignal: ROR>2/CI>1 (Yes), PRR>1.5/CI>1 (Yes), IC>0/CI>0 (Yes) -> 3 -> True
            # WeakSignal: ROR>2/CI>1 (Yes), PRR>1.5/CI>1 (No, CI<1), IC>0/CI>0 (Yes) -> 2 -> True
            # NoSignal: ROR>2/CI>1 (No), PRR>1.5/CI>1 (No), IC>0/CI>0 (No) -> 0 -> False
            
            assert df.loc[df['soc'] == 'StrongSignal', 'signal_flag'].iloc[0] is True
            assert df.loc[df['soc'] == 'WeakSignal', 'signal_flag'].iloc[0] is True
            assert df.loc[df['soc'] == 'NoSignal', 'signal_flag'].iloc[0] is False
        finally:
            os.unlink(input_path)
