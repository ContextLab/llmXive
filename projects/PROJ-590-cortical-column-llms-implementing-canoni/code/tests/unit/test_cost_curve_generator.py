"""
Unit tests for the cost_curve_generator module.
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
import sys
import pandas as pd

# Add code to path if not already
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils.cost_curve_generator import (
    load_baseline_metrics,
    load_microcircuit_metrics,
    load_ablation_results,
    calculate_relative_increase,
    calculate_metabolic_cost,
    generate_cost_curve_data
)


class TestCostCurveGenerator:
    """Tests for cost curve generation logic."""

    def test_calculate_relative_increase(self):
        """Test relative increase calculation."""
        assert calculate_relative_increase(10.0, 15.0) == 0.5
        assert calculate_relative_increase(10.0, 10.0) == 0.0
        assert calculate_relative_increase(10.0, 5.0) == -0.5
        # Edge case: base is zero
        assert calculate_relative_increase(0.0, 5.0) == float('inf')
        assert calculate_relative_increase(0.0, 0.0) == 0.0

    def test_calculate_metabolic_cost(self):
        """Test metabolic cost calculation."""
        assert calculate_metabolic_cost(100.0, 0.1) == 1000.0
        assert calculate_metabolic_cost(50.0, 0.5) == 100.0
        # Edge case: MAE is zero
        assert calculate_metabolic_cost(100.0, 0.0) == float('inf')

    def test_load_baseline_metrics_missing_file(self, tmp_path):
        """Test loading baseline metrics when file is missing."""
        # Create a temporary path that doesn't exist
        with pytest.raises(FileNotFoundError):
            # Temporarily override the path for testing
            import src.utils.cost_curve_generator as mod
            original_path = mod.BASELINE_METRICS_PATH
            mod.BASELINE_METRICS_PATH = tmp_path / "nonexistent.json"
            try:
                load_baseline_metrics()
            finally:
                mod.BASELINE_METRICS_PATH = original_path

    def test_load_ablation_results_empty(self, tmp_path):
        """Test loading ablation results with empty list."""
        ablation_file = tmp_path / "ablation.json"
        with open(ablation_file, 'w') as f:
            json.dump([], f)

        import src.utils.cost_curve_generator as mod
        original_path = mod.ABLATION_RESULTS_PATH
        mod.ABLATION_RESULTS_PATH = ablation_file
        try:
            results = load_ablation_results()
            assert results == []
        finally:
            mod.ABLATION_RESULTS_PATH = original_path

    def test_generate_cost_curve_data_integration(self, tmp_path):
        """Test full cost curve generation with mock data."""
        # Create temporary files for inputs
        baseline_file = tmp_path / "baseline_run.json"
        microcircuit_file = tmp_path / "microcircuit_run.json"
        ablation_file = tmp_path / "ablation_study_results.json"
        output_file = tmp_path / "cost_curve_data.csv"

        # Write mock data
        with open(baseline_file, 'w') as f:
            json.dump({
                'mae': 0.05,
                'training_time_sec': 100.0,
                'params': 1000000
            }, f)

        with open(microcircuit_file, 'w') as f:
            json.dump({
                'mae': 0.04,
                'training_time_sec': 150.0,
                'params': 1000000
            }, f)

        with open(ablation_file, 'w') as f:
            json.dump({
                'results': [
                    {'variant': 'ablation_recurrence', 'mae': 0.06, 'training_time_sec': 120.0, 'params': 950000},
                    {'variant': 'ablation_inhibition', 'mae': 0.07, 'training_time_sec': 130.0, 'params': 980000}
                ]
            }, f)

        # Patch the paths
        import src.utils.cost_curve_generator as mod
        original_baseline = mod.BASELINE_METRICS_PATH
        original_micro = mod.MICROCIRCUIT_METRICS_PATH
        original_ablation = mod.ABLATION_RESULTS_PATH
        original_output = mod.OUTPUT_PATH

        try:
            mod.BASELINE_METRICS_PATH = baseline_file
            mod.MICROCIRCUIT_METRICS_PATH = microcircuit_file
            mod.ABLATION_RESULTS_PATH = ablation_file
            mod.OUTPUT_PATH = output_file

            # Run the generator
            df = generate_cost_curve_data()

            # Verify output exists
            assert output_file.exists()

            # Verify content
            assert len(df) == 4  # baseline, full, 2 ablations
            assert 'variant' in df.columns
            assert 'metabolic_cost' in df.columns
            assert 'rel_mae_increase' in df.columns

            # Check baseline row
            baseline_row = df[df['variant'] == 'baseline'].iloc[0]
            assert baseline_row['rel_mae_increase'] == 0.0
            assert baseline_row['rel_time_increase'] == 0.0

            # Check ablation row
            ablation_row = df[df['variant'] == 'ablation_recurrence'].iloc[0]
            # MAE increased from 0.05 to 0.06 -> (0.06-0.05)/0.05 = 0.2
            assert abs(ablation_row['rel_mae_increase'] - 0.2) < 1e-6

        finally:
            # Restore original paths
            mod.BASELINE_METRICS_PATH = original_baseline
            mod.MICROCIRCUIT_METRICS_PATH = original_micro
            mod.ABLATION_RESULTS_PATH = original_ablation
            mod.OUTPUT_PATH = original_output
