"""Integration tests for scaling law analysis."""

import pytest
import json
import os
import tempfile
from pathlib import Path
from src.experiments.scaling import create_scaling_configs, run_scaling_study
from src.utils.scaling_analyzer import calculate_scaling_exponent

class TestScalingConfigs:
    def test_scaling_config_generation(self):
        """Test that scaling configs are generated correctly."""
        configs = create_scaling_configs(base_columns=1, variants=[1, 2, 4])

        assert len(configs) == 3
        column_counts = [c.num_columns for c in configs]
        assert 1 in column_counts
        assert 2 in column_counts
        assert 4 in column_counts

    def test_scaling_config_parameter_counts(self):
        """Test that parameter counts scale as expected."""
        configs = create_scaling_configs(base_columns=1, variants=[1, 2, 4])

        param_counts = [c.num_parameters for c in configs]
        # Parameters should increase with column count
        assert param_counts[0] < param_counts[1] < param_counts[2]

class TestScalingStudyExecution:
    def test_scaling_study_runs(self):
        """Test that a full scaling study can be executed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run a minimal scaling study
            results = run_scaling_study(
                variants=[1, 2],
                output_dir=tmpdir,
                max_epochs=1
            )

            assert results is not None
            assert len(results) > 0

            # Check result schema
            for result in results:
                assert "variant" in result
                assert "mae" in result
                assert "params" in result
                assert "time" in result

    def test_scaling_exponent_calculation(self):
        """Test scaling exponent calculation from results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate some synthetic results for testing
            results = [
                {"variant": "1x", "params": 10000, "mae": 0.1, "time": 10.0},
                {"variant": "2x", "params": 20000, "mae": 0.08, "time": 20.0},
                {"variant": "4x", "params": 40000, "mae": 0.06, "time": 40.0}
            ]

            # Save to file
            output_path = Path(tmpdir) / "scaling_results.json"
            with open(output_path, 'w') as f:
                json.dump({"variants": results}, f)

            # Calculate exponent
            exponent_info = calculate_scaling_exponent(str(output_path))

            assert "exponent" in exponent_info
            assert "linear_or_sublinear" in exponent_info
            assert exponent_info["exponent"] is not None
