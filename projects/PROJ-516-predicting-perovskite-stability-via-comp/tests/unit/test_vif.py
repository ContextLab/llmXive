"""
Unit tests for the VIF Calculator (T016a).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.utils.vif_calculator import calculate_vif, run_vif_diagnostic

class TestVIFCalculator:
    """Tests for VIF calculation logic."""

    def test_calculate_vif_perfect_collinearity(self):
        """Test VIF calculation when features are perfectly collinear."""
        # Create a dataset where x2 = 2 * x1
        data = {
            'x1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'x2': [2.0, 4.0, 6.0, 8.0, 10.0],
            'x3': [1.0, 2.0, 3.0, 4.0, 5.0]  # independent
        }
        df = pd.DataFrame(data)
        features = ['x1', 'x2', 'x3']

        vif_series = calculate_vif(df, features)

        # x1 and x2 should have very high VIF (or inf) due to collinearity
        # x3 should have VIF = 1.0 (no correlation with others)
        assert vif_series['x3'] == 1.0
        # Check that at least one of the collinear pairs has high VIF
        assert vif_series['x1'] > 10 or vif_series['x2'] > 10

    def test_calculate_vif_independent_features(self):
        """Test VIF calculation for independent features."""
        # Create a dataset with independent features
        np.random.seed(42)
        data = {
            'x1': np.random.randn(100),
            'x2': np.random.randn(100),
            'x3': np.random.randn(100)
        }
        df = pd.DataFrame(data)
        features = ['x1', 'x2', 'x3']

        vif_series = calculate_vif(df, features)

        # All VIFs should be close to 1.0
        for vif in vif_series:
            assert 0.9 <= vif <= 2.0, f"VIF {vif} is unexpectedly high for independent features"

    def test_run_vif_diagnostic_writes_file(self):
        """Test that run_vif_diagnostic writes the output file."""
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            # Create dummy input data
            data = {
                'formula': ['CsPbI3', 'MAPbBr3'],
                'T_d': [500.0, 600.0],
                'atomic_fraction_A': [0.2, 0.2],
                'atomic_fraction_B': [0.2, 0.2],
                'atomic_fraction_X': [0.6, 0.6],
                'weighted_ionic_radius': [1.5, 1.6],
                'weighted_electronegativity': [2.0, 2.1],
                'weighted_formation_enthalpy': [-0.5, -0.6],
                'variance_ionic_radius': [0.1, 0.1],
                'variance_electronegativity': [0.05, 0.05]
            }
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)

            # Run the diagnostic
            result_df = run_vif_diagnostic(input_path, output_path, threshold=5.0)

            # Verify file exists
            assert output_path.exists()

            # Verify content
            loaded_df = pd.read_csv(output_path)
            assert 'descriptor' in loaded_df.columns
            assert 'vif_value' in loaded_df.columns
            assert 'flagged' in loaded_df.columns
            assert len(loaded_df) == 6  # 6 numeric descriptors (excluding formula, T_d)

    def test_vif_flagging_threshold(self):
        """Test that features are correctly flagged based on threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            # Create data with known collinearity to force high VIF
            np.random.seed(42)
            x1 = np.random.randn(50)
            x2 = x1 * 2 + np.random.randn(50) * 0.1  # Highly correlated
            x3 = np.random.randn(50)  # Independent

            data = {
                'formula': ['CsPbI3'] * 50,
                'T_d': [500.0] * 50,
                'f1': x1,
                'f2': x2,
                'f3': x3
            }
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)

            # Run with threshold 5
            result_df = run_vif_diagnostic(input_path, output_path, threshold=5.0)

            # Check that f1 or f2 (the correlated ones) are flagged
            # Since they are highly correlated, at least one should have VIF > 5
            flagged_descriptors = result_df[result_df['flagged']]['descriptor'].tolist()
            assert any(d in flagged_descriptors for d in ['f1', 'f2']), \
                "Correlated features should be flagged"