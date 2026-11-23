import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.evaluate import calculate_stability_and_flip_rate
from src.utils import write_csv


class TestSensitivityStability:
    """Unit tests for T027: Stability calculation and flip rate."""

    def test_flip_rate_calculation(self):
        """Test that flip rate is calculated correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "input.csv"
            output_path = Path(tmp_dir) / "output.csv"

            # Create test data:
            # Dim A: status changes twice (0 -> 1 -> 0) -> 2 flips / 2 transitions = 1.0
            # Dim B: status constant (0 -> 0 -> 0) -> 0 flips / 2 transitions = 0.0
            data = {
                'dimension': ['A', 'A', 'A', 'B', 'B', 'B'],
                'threshold': [0.80, 0.85, 0.90, 0.80, 0.85, 0.90],
                'status': ['feature-sufficient', 'VLM-required', 'feature-sufficient',
                           'feature-sufficient', 'feature-sufficient', 'feature-sufficient']
            }
            df = pd.DataFrame(data)
            write_csv(df, input_path)

            calculate_stability_and_flip_rate(input_path, output_path)

            result_df = pd.read_csv(output_path)

            # Check dimensions
            assert 'flip_rate' in result_df.columns
            assert 'threshold_sensitive' in result_df.columns

            # Check Dim A
            dim_a = result_df[result_df['dimension'] == 'A']
            assert dim_a['flip_rate'].iloc[0] == 1.0  # 2 flips / 2 transitions
            assert dim_a['threshold_sensitive'].iloc[0] == True

            # Check Dim B
            dim_b = result_df[result_df['dimension'] == 'B']
            assert dim_b['flip_rate'].iloc[0] == 0.0
            assert dim_b['threshold_sensitive'].iloc[0] == False

    def test_single_threshold_no_flips(self):
        """Test behavior when only one threshold exists (no transitions)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "input.csv"
            output_path = Path(tmp_dir) / "output.csv"

            data = {
                'dimension': ['A'],
                'threshold': [0.85],
                'status': ['feature-sufficient']
            }
            df = pd.DataFrame(data)
            write_csv(df, input_path)

            calculate_stability_and_flip_rate(input_path, output_path)

            result_df = pd.read_csv(output_path)
            # Should not crash, flip rate should be 0.0
            assert result_df['flip_rate'].iloc[0] == 0.0
            assert result_df['threshold_sensitive'].iloc[0] == False

    def test_missing_input_file(self):
        """Test that FileNotFoundError is raised if input is missing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "nonexistent.csv"
            output_path = Path(tmp_dir) / "output.csv"

            with pytest.raises(FileNotFoundError):
                calculate_stability_and_flip_rate(input_path, output_path)

    def test_output_columns(self):
        """Test that output CSV contains required columns."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "input.csv"
            output_path = Path(tmp_dir) / "output.csv"

            data = {
                'dimension': ['A', 'A'],
                'threshold': [0.80, 0.85],
                'status': ['feature-sufficient', 'feature-sufficient']
            }
            df = pd.DataFrame(data)
            write_csv(df, input_path)

            calculate_stability_and_flip_rate(input_path, output_path)

            result_df = pd.read_csv(output_path)
            required_cols = ['dimension', 'threshold', 'status', 'flip_rate']
            for col in required_cols:
                assert col in result_df.columns