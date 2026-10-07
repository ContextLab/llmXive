"""
Unit tests for signal_output.py (T025b)
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from src.analysis.signal_output import apply_signal_flag, generate_signals_csv

class TestSignalFlag:
    """Tests for the 2-out-of-3 signal detection rule"""
    
    def test_all_conditions_met(self):
        """Test when all 3 conditions are met -> signal"""
        row = pd.Series({
            'ror': 3.0, 'ror_ci_lower': 1.5,
            'prr': 2.0, 'prr_ci_lower': 1.5,
            'ic': 1.0, 'ic_ci_lower': 0.5
        })
        thresholds = {
            'ror_min': 2.0, 'ror_ci_min': 1.0,
            'prr_min': 1.5, 'prr_ci_min': 1.0,
            'ic_min': 0.0, 'ic_ci_min': 0.0
        }
        assert apply_signal_flag(row, thresholds) is True
    
    def test_two_conditions_met(self):
        """Test when exactly 2 conditions are met -> signal"""
        row = pd.Series({
            'ror': 3.0, 'ror_ci_lower': 1.5,  # Met
            'prr': 2.0, 'prr_ci_lower': 1.5,  # Met
            'ic': 0.5, 'ic_ci_lower': -0.5    # Not met (CI < 0)
        })
        thresholds = {
            'ror_min': 2.0, 'ror_ci_min': 1.0,
            'prr_min': 1.5, 'prr_ci_min': 1.0,
            'ic_min': 0.0, 'ic_ci_min': 0.0
        }
        assert apply_signal_flag(row, thresholds) is True
    
    def test_one_condition_met(self):
        """Test when only 1 condition is met -> no signal"""
        row = pd.Series({
            'ror': 3.0, 'ror_ci_lower': 1.5,  # Met
            'prr': 1.0, 'prr_ci_lower': 0.5,  # Not met
            'ic': 0.5, 'ic_ci_lower': -0.5    # Not met
        })
        thresholds = {
            'ror_min': 2.0, 'ror_ci_min': 1.0,
            'prr_min': 1.5, 'prr_ci_min': 1.0,
            'ic_min': 0.0, 'ic_ci_min': 0.0
        }
        assert apply_signal_flag(row, thresholds) is False
    
    def test_no_conditions_met(self):
        """Test when no conditions are met -> no signal"""
        row = pd.Series({
            'ror': 1.0, 'ror_ci_lower': 0.5,
            'prr': 1.0, 'prr_ci_lower': 0.5,
            'ic': 0.0, 'ic_ci_lower': -0.5
        })
        thresholds = {
            'ror_min': 2.0, 'ror_ci_min': 1.0,
            'prr_min': 1.5, 'prr_ci_min': 1.0,
            'ic_min': 0.0, 'ic_ci_min': 0.0
        }
        assert apply_signal_flag(row, thresholds) is False
    
    def test_boundary_values(self):
        """Test boundary values exactly at thresholds"""
        row = pd.Series({
            'ror': 2.0, 'ror_ci_lower': 1.0,  # Exactly at threshold
            'prr': 1.5, 'prr_ci_lower': 1.0,  # Exactly at threshold
            'ic': 0.0, 'ic_ci_lower': 0.0     # Exactly at threshold
        })
        thresholds = {
            'ror_min': 2.0, 'ror_ci_min': 1.0,
            'prr_min': 1.5, 'prr_ci_min': 1.0,
            'ic_min': 0.0, 'ic_ci_min': 0.0
        }
        # All 3 conditions met at boundary
        assert apply_signal_flag(row, thresholds) is True

class TestGenerateSignalsCsv:
    """Tests for generate_signals_csv function"""
    
    def test_generate_csv_creates_file(self):
        """Test that the function creates the output file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "signals.csv"
            
            # Create sample metrics DataFrame
            metrics_df = pd.DataFrame({
                'soc': ['SOC1', 'SOC2', 'SOC3'],
                'ror': [3.0, 1.0, 2.5],
                'ror_ci_lower': [1.5, 0.5, 1.2],
                'ror_ci_upper': [4.0, 2.0, 3.5],
                'prr': [2.0, 1.0, 1.8],
                'prr_ci_lower': [1.5, 0.5, 1.2],
                'prr_ci_upper': [3.0, 2.0, 2.8],
                'ic': [1.0, 0.0, 0.8],
                'ic_ci_lower': [0.5, -0.5, 0.2],
                'ic_ci_upper': [1.5, 0.5, 1.4],
                'p_adj': [0.01, 0.5, 0.05]
            })
            
            thresholds = {
                'ror_min': 2.0, 'ror_ci_min': 1.0,
                'prr_min': 1.5, 'prr_ci_min': 1.0,
                'ic_min': 0.0, 'ic_ci_min': 0.0
            }
            
            generate_signals_csv(metrics_df, thresholds, output_path)
            
            assert output_path.exists()
            
            # Load and verify
            result_df = pd.read_csv(output_path)
            
            # Check columns
            expected_cols = [
                'soc', 'ror', 'ror_ci_lower', 'ror_ci_upper',
                'prr', 'prr_ci_lower', 'prr_ci_upper',
                'ic', 'ic_ci_lower', 'ic_ci_upper',
                'p_adj', 'signal_flag', 'background_rate_status'
            ]
            assert list(result_df.columns) == expected_cols
            
            # Check signal_flag logic
            # SOC1: ROR and PRR conditions met -> signal
            # SOC2: No conditions met -> no signal
            # SOC3: ROR and PRR conditions met -> signal
            assert result_df.iloc[0]['signal_flag'] is True
            assert result_df.iloc[1]['signal_flag'] is False
            assert result_df.iloc[2]['signal_flag'] is True
            
            # Check background_rate_status
            assert all(result_df['background_rate_status'] == 'UNKNOWN')
    
    def test_empty_dataframe(self):
        """Test with empty DataFrame"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "signals.csv"
            
            metrics_df = pd.DataFrame(columns=[
                'soc', 'ror', 'ror_ci_lower', 'ror_ci_upper',
                'prr', 'prr_ci_lower', 'prr_ci_upper',
                'ic', 'ic_ci_lower', 'ic_ci_upper',
                'p_adj'
            ])
            
            thresholds = {
                'ror_min': 2.0, 'ror_ci_min': 1.0,
                'prr_min': 1.5, 'prr_ci_min': 1.0,
                'ic_min': 0.0, 'ic_ci_min': 0.0
            }
            
            generate_signals_csv(metrics_df, thresholds, output_path)
            
            assert output_path.exists()
            result_df = pd.read_csv(output_path)
            assert len(result_df) == 0