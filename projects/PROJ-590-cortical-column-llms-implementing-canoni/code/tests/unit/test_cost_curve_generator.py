import pytest
import json
import os
import tempfile
import pandas as pd
from pathlib import Path
import sys

# Add project root to path if not already
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.cost_curve_generator import generate_cost_curve_data

class TestCostCurveGenerator:
    def test_generate_cost_curve_data_creates_file(self):
        """Test that the function creates the output CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ablation_path = os.path.join(tmpdir, "ablation_results.json")
            output_path = os.path.join(tmpdir, "cost_curve_data.csv")
            
            # Create mock ablation data
            mock_data = [
                {
                    "variant_name": "baseline",
                    "mae": 0.05,
                    "params": 1000000
                },
                {
                    "variant_name": "full_microcircuit",
                    "mae": 0.04,
                    "params": 1050000
                },
                {
                    "variant_name": "no_recurrence",
                    "mae": 0.06,
                    "params": 1020000
                },
                {
                    "variant_name": "no_inhibition",
                    "mae": 0.07,
                    "params": 1020000
                }
            ]
            
            with open(ablation_path, 'w') as f:
                json.dump(mock_data, f)
            
            df = generate_cost_curve_data(ablation_path, output_path=output_path)
            
            assert os.path.exists(output_path), "Output CSV file was not created."
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            
            # Check required columns
            required_cols = ['variant', 'baseline_mae', 'variant_mae', 'mae_delta', 'params', 'params_delta', 'cost_metric']
            for col in required_cols:
                assert col in df.columns, f"Missing column: {col}"

    def test_cost_curve_data_values(self):
        """Test that the computed values are correct."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ablation_path = os.path.join(tmpdir, "ablation_results.json")
            output_path = os.path.join(tmpdir, "cost_curve_data.csv")
            
            baseline_mae = 0.05
            baseline_params = 1000000
            
            mock_data = [
                {
                    "variant_name": "baseline",
                    "mae": baseline_mae,
                    "params": baseline_params
                },
                {
                    "variant_name": "variant_a",
                    "mae": 0.06,
                    "params": 1000000
                }
            ]
            
            with open(ablation_path, 'w') as f:
                json.dump(mock_data, f)
            
            df = generate_cost_curve_data(ablation_path, output_path=output_path)
            
            # Find the row for variant_a
            row = df[df['variant'] == 'variant_a'].iloc[0]
            
            assert abs(row['variant_mae'] - 0.06) < 1e-6
            assert abs(row['mae_delta'] - 0.01) < 1e-6
            assert abs(row['params_delta'] - 0) < 1e-6
            assert abs(row['cost_metric'] - 0.01) < 1e-6

    def test_missing_ablation_file_raises(self):
        """Test that FileNotFoundError is raised if ablation file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "cost_curve_data.csv")
            
            with pytest.raises(FileNotFoundError):
                generate_cost_curve_data("non_existent_path.json", output_path=output_path)

    def test_empty_ablation_results_raises(self):
        """Test that ValueError is raised if ablation results are empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ablation_path = os.path.join(tmpdir, "ablation_results.json")
            output_path = os.path.join(tmpdir, "cost_curve_data.csv")
            
            with open(ablation_path, 'w') as f:
                json.dump([], f)
            
            with pytest.raises(ValueError):
                generate_cost_curve_data(ablation_path, output_path=output_path)

    def test_missing_baseline_raises(self):
        """Test that ValueError is raised if no baseline is found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ablation_path = os.path.join(tmpdir, "ablation_results.json")
            output_path = os.path.join(tmpdir, "cost_curve_data.csv")
            
            # Data without a baseline
            mock_data = [
                {
                    "variant_name": "full_microcircuit",
                    "mae": 0.04,
                    "params": 1000000
                }
            ]
            
            with open(ablation_path, 'w') as f:
                json.dump(mock_data, f)
            
            with pytest.raises(ValueError):
                generate_cost_curve_data(ablation_path, output_path=output_path)