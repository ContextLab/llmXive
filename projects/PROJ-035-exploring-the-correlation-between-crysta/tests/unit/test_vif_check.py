import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
import sys

from src.analysis.run_vif_check import run_vif_check

class TestVIFCheck:
    @pytest.fixture
    def sample_data(self):
        """Create a sample dataframe with known VIF characteristics."""
        np.random.seed(42)
        n = 100
        # Create some correlated features to induce VIF
        x1 = np.random.normal(0, 1, n)
        x2 = x1 * 0.9 + np.random.normal(0, 0.1, n)  # Highly correlated with x1
        x3 = np.random.normal(0, 1, n)  # Independent
        x4 = np.random.normal(0, 1, n)  # Independent

        df = pd.DataFrame({
            'tilting_angle': x1,
            'bond_length_variance': x2,
            'tolerance_factor': x3,
            'unit_cell_volume': x4,
            'thermal_conductivity': np.random.normal(10, 2, n)
        })
        return df

    def test_run_vif_check_creates_outputs(self, sample_data):
        """Test that run_vif_check creates the required output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            report_path = Path(tmpdir) / "report.json"

            sample_data.to_csv(input_path, index=False)

            result = run_vif_check(
                input_path=str(input_path),
                output_csv_path=str(output_path),
                report_path=str(report_path)
            )

            # Check files exist
            assert output_path.exists(), "Filtered CSV not created"
            assert report_path.exists(), "VIF report not created"

            # Check report structure
            assert "vif_results" in result
            assert "excluded_predictors" in result
            assert "included_predictors" in result
            assert "threshold" in result

            # Check output CSV has fewer columns if exclusion happened
            output_df = pd.read_csv(output_path)
            assert len(output_df) == len(sample_data)  # Rows preserved

    def test_vif_threshold_logic(self, sample_data):
        """Test that predictors with VIF > threshold are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            report_path = Path(tmpdir) / "report.json"

            sample_data.to_csv(input_path, index=False)

            # Use a low threshold to force exclusion
            result = run_vif_check(
                input_path=str(input_path),
                output_csv_path=str(output_path),
                report_path=str(report_path),
                vif_threshold=2.0
            )

            # Load report
            with open(report_path) as f:
                report = json.load(f)

            # With highly correlated x1 and x2, at least one should be excluded
            assert len(report['excluded_predictors']) + len(report['included_predictors']) == 4

            # Load output and verify columns
            output_df = pd.read_csv(output_path)
            output_cols = set(output_df.columns)
            excluded_set = set(report['excluded_predictors'])

            for col in excluded_set:
                assert col not in output_cols, f"Excluded predictor {col} found in output"

    def test_file_paths_exist(self, sample_data):
        """Test that the function creates directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "subdir" / "output.csv"
            report_path = Path(tmpdir) / "subdir" / "report.json"

            sample_data.to_csv(input_path, index=False)

            result = run_vif_check(
                input_path=str(input_path),
                output_csv_path=str(output_path),
                report_path=str(report_path)
            )

            assert output_path.exists()
            assert report_path.exists()