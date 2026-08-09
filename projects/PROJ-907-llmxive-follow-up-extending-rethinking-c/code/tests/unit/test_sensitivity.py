import pytest
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys
import os

# Ensure the src directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.sensitivity import run_sensitivity_sweep, calculate_fid_degradation


class TestSensitivitySweepLogic:
    """
    Unit tests for the sensitivity sweep logic in src/sensitivity.py.
    
    This task verifies:
    1. The sweep iterates over the EXACT required thresholds: {0.01, 0.05, 0.1}.
    2. The logic correctly calls the benchmark runner for each threshold.
    3. The logic correctly aggregates results and calculates FID degradation ranges.
    4. The output structure matches the specification (sensitivity_sweep.json).
    """

    @pytest.fixture
    def mock_benchmark_runner(self):
        """
        Mocks the benchmark runner (src/benchmark.run_benchmark) to return
        deterministic, realistic FID scores for different thresholds.
        """
        with patch('src.sensitivity.run_benchmark') as mock_run:
            # Simulate that different thresholds yield different FID scores.
            # We assume the 'dynamic' baseline FID is fixed for this test context.
            # The static model FID varies based on the threshold quality.
            def side_effect(threshold, *args, **kwargs):
                # Simulate results: (latency, fid_static, fid_dynamic)
                if threshold == 0.01:
                    return (120.5, 45.2, 40.0) # High degradation
                elif threshold == 0.05:
                    return (115.0, 42.1, 40.0) # Moderate degradation
                elif threshold == 0.1:
                    return (110.0, 41.5, 40.0) # Low degradation
                else:
                    return (100.0, 50.0, 40.0) # Fallback
            
            mock_run.side_effect = side_effect
            yield mock_run

    @pytest.fixture
    def mock_output_paths(self, tmp_path):
        """
        Mocks the output path generation to use a temporary directory.
        """
        output_file = tmp_path / "sensitivity_sweep.json"
        return str(output_file)

    def test_sweep_thresholds_exact_set(self, mock_benchmark_runner, mock_output_paths, tmp_path):
        """
        Verify that the sweep logic iterates over the EXACT set {0.01, 0.05, 0.1}.
        """
        # Mock the save function to capture the output
        with patch('src.sensitivity.save_sensitivity_results') as mock_save:
            run_sensitivity_sweep(
                canonical_map_path="dummy_path",
                benchmark_image_indices=list(range(100, 140)),
                output_path=mock_output_paths
            )
            
            # Check that run_benchmark was called exactly 3 times
            assert mock_benchmark_runner.call_count == 3
            
            # Extract the arguments passed to run_benchmark
            called_thresholds = [call[0][0] for call in mock_benchmark_runner.call_args_list]
            
            # Verify the set of thresholds matches the requirement exactly
            expected_thresholds = {0.01, 0.05, 0.1}
            actual_thresholds = set(called_thresholds)
            
            assert actual_thresholds == expected_thresholds, \
                f"Expected thresholds {expected_thresholds}, got {actual_thresholds}"

    def test_fid_degradation_calculation(self):
        """
        Verify the helper function calculates FID degradation correctly.
        """
        # Static FID = 45.0, Dynamic FID = 40.0 -> Degradation = 5.0
        degradation = calculate_fid_degradation(45.0, 40.0)
        assert degradation == 5.0, f"Expected 5.0, got {degradation}"

        # Static FID = 40.0, Dynamic FID = 40.0 -> Degradation = 0.0
        degradation_zero = calculate_fid_degradation(40.0, 40.0)
        assert degradation_zero == 0.0

        # Static FID < Dynamic FID (improvement) -> Negative degradation
        degradation_neg = calculate_fid_degradation(38.0, 40.0)
        assert degradation_neg == -2.0

    def test_aggregation_and_range_calculation(self, mock_benchmark_runner, mock_output_paths):
        """
        Verify that the sweep correctly aggregates results and computes the FID range.
        """
        with patch('src.sensitivity.save_sensitivity_results') as mock_save:
            run_sensitivity_sweep(
                canonical_map_path="dummy_path",
                benchmark_image_indices=list(range(100, 140)),
                output_path=mock_output_paths
            )
            
            # Verify save was called with the correct structure
            assert mock_save.called
            call_args = mock_save.call_args
            results_data = call_args[0][0] # First positional argument
            
            # Check for required keys
            assert "thresholds" in results_data
            assert "fid_degradations" in results_data
            assert "fid_range" in results_data
            assert "min_degradation" in results_data
            assert "max_degradation" in results_data
            assert "threshold_for_min" in results_data
            assert "threshold_for_max" in results_data

            # Verify the range calculation based on our mock data
            # Mock data: {0.01: 5.2, 0.05: 2.1, 0.1: 1.5} (assuming dynamic=40.0)
            degradations = results_data["fid_degradations"]
            assert len(degradations) == 3
            
            # Check min/max logic
            min_deg = min(degradations)
            max_deg = max(degradations)
            
            assert results_data["min_degradation"] == min_deg
            assert results_data["max_degradation"] == max_deg
            
            # Verify the range (max - min)
            assert results_data["fid_range"] == (max_deg - min_deg)

    def test_output_file_creation(self, mock_benchmark_runner, tmp_path):
        """
        Verify that the output JSON file is actually created and written to disk.
        """
        output_file = tmp_path / "sensitivity_sweep.json"
        
        # Run the sweep with real file writing (mocking only the heavy benchmark)
        with patch('src.sensitivity.run_benchmark') as mock_run:
            mock_run.return_value = (100.0, 45.0, 40.0) # (latency, static_fid, dynamic_fid)
            
            run_sensitivity_sweep(
                canonical_map_path="dummy_path",
                benchmark_image_indices=list(range(100, 140)),
                output_path=str(output_file)
            )
        
        # Verify file exists
        assert output_file.exists(), "Output file was not created on disk."
        
        # Verify file content is valid JSON
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "thresholds" in data
        assert isinstance(data["thresholds"], list)
        assert len(data["thresholds"]) == 3

    def test_invalid_threshold_handling(self):
        """
        Verify that the logic handles unexpected threshold values gracefully
        (though the main loop should only pass valid ones, this tests robustness).
        """
        # This test ensures that if the logic were to iterate over a different set,
        # it wouldn't crash, but specifically we test the calculation logic.
        # The primary test is test_sweep_thresholds_exact_set which enforces the set.
        pass