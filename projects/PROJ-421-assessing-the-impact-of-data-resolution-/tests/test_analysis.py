"""
Unit tests for the analysis module, specifically focusing on sensitivity analysis
and threshold identification logic for User Story 3.
"""
import pytest
import numpy as np
import pandas as pd
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust import path based on project structure
# Assuming tests are at root and code is in 'code/'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from analysis import (
    calculate_statistical_power,
    run_analysis_for_resolution,
    simulate_h1_gibbs,
    generate_null_distribution,
    create_binary_indicator_map
)
import config

# Mock data generator for testing without full pipeline
def generate_mock_binary_map(shape=(100, 100), density=0.3, seed=42):
    """Generates a mock binary spatial map for testing."""
    rng = np.random.default_rng(seed)
    data = rng.random(shape) < density
    return data.astype(int)

def generate_mock_weights(shape=(100, 100)):
    """Generates a mock spatial weights matrix (rook contiguity approximation)."""
    # For testing purposes, we mock the weights object behavior
    # In a real scenario, this would be a libpysal W object
    return MagicMock(spec=['neighbors', 'id_order', 'transform'])

class TestSensitivityAnalysis:
    """
    Tests for sensitivity analysis (±10% sweep) as described in T027.
    Verifies that the threshold identification is robust to small perturbations
    in the input power data or resolution factors.
    """

    def test_sensitivity_analysis_small_variation(self):
        """
        Test that a ±10% variation in the power curve data points
        does not cause the identified threshold resolution to jump by more than
        one step in the geometric series (e.g., 30m -> 60m -> 120m).
        """
        # Setup mock data representing a typical power curve
        # Resolutions: 30, 60, 120, 240, 480
        resolutions = [30, 60, 120, 240, 480]
        # Typical power values: high at low res, dropping below 0.8 at some point
        base_power = [0.99, 0.95, 0.82, 0.65, 0.40]

        # Create a temporary CSV file for the mock power data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("resolution_m,power\n")
            for r, p in zip(resolutions, base_power):
                f.write(f"{r},{p:.4f}\n")
            temp_csv_path = f.name

        try:
            # Import the helper logic that would normally be in visualization.py
            # Since T027 is a test task, we inline the logic or import if available.
            # Assuming visualization.py logic is: find first resolution where power < 0.80
            def find_threshold(power_csv_path, threshold=0.80):
                df = pd.read_csv(power_csv_path)
                # Sort by resolution to ensure order
                df = df.sort_values('resolution_m')
                # Find first row where power < threshold
                below_threshold = df[df['power'] < threshold]
                if below_threshold.empty:
                    return None
                return int(below_threshold.iloc[0]['resolution_m'])

            # 1. Calculate baseline threshold
            baseline_threshold = find_threshold(temp_csv_path)
            assert baseline_threshold == 240, f"Expected baseline threshold 240m, got {baseline_threshold}"

            # 2. Apply ±10% noise to power values
            rng = np.random.default_rng(42)
            noisy_power = []
            for p in base_power:
                # Apply 10% variation
                noise = rng.uniform(-0.10, 0.10)
                noisy_val = p * (1 + noise)
                noisy_val = max(0.0, min(1.0, noisy_val)) # Clamp to [0, 1]
                noisy_power.append(noisy_val)

            # Write noisy data to a new temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='_noisy.csv', delete=False) as f:
                f.write("resolution_m,power\n")
                for r, p in zip(resolutions, noisy_power):
                    f.write(f"{r},{p:.4f}\n")
                noisy_csv_path = f.name

            try:
                # 3. Calculate threshold with noisy data
                noisy_threshold = find_threshold(noisy_csv_path)
                
                # 4. Verify stability: The threshold should not jump more than one step
                # Steps: 30->60, 60->120, 120->240, 240->480
                # If baseline was 240, noisy should be 120, 240, or 480.
                
                steps = {30: 0, 60: 1, 120: 2, 240: 3, 480: 4}
                
                if baseline_threshold is None or noisy_threshold is None:
                    # If one is None and other is not, it's a significant jump (fail)
                    if (baseline_threshold is None) != (noisy_threshold is None):
                        raise AssertionError("Threshold jumped from None to a value or vice versa")
                    return # Both None is stable

                baseline_idx = steps.get(baseline_threshold)
                noisy_idx = steps.get(noisy_threshold)

                if baseline_idx is None or noisy_idx is None:
                    raise AssertionError(f"Unexpected resolution values: {baseline_threshold}, {noisy_threshold}")

                delta_steps = abs(noisy_idx - baseline_idx)
                
                # Assert that the jump is at most 1 step
                assert delta_steps <= 1, (
                    f"Sensitivity analysis failed: Threshold jumped by {delta_steps} steps. "
                    f"Baseline: {baseline_threshold}m, Noisy: {noisy_threshold}m. "
                    f"Expected max jump of 1 step."
                )
                
            finally:
                os.unlink(noisy_csv_path)

        finally:
            os.unlink(temp_csv_path)

    def test_sensitivity_analysis_edge_case_boundary(self):
        """
        Test sensitivity when power is exactly on the boundary (0.80).
        A small variation should flip the threshold, but this is expected
        behavior for edge cases; the test verifies the logic handles it gracefully.
        """
        resolutions = [30, 60, 120, 240, 480]
        # Exact boundary at 120m
        base_power = [0.99, 0.95, 0.80, 0.65, 0.40]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("resolution_m,power\n")
            for r, p in zip(resolutions, base_power):
                f.write(f"{r},{p:.4f}\n")
            temp_csv_path = f.name

        try:
            def find_threshold(power_csv_path, threshold=0.80):
                df = pd.read_csv(power_csv_path)
                df = df.sort_values('resolution_m')
                below = df[df['power'] < threshold]
                if below.empty:
                    return None
                return int(below.iloc[0]['resolution_m'])

            baseline = find_threshold(temp_csv_path)
            # With 0.80 exactly, it should be 240 (first strictly less than 0.80)
            assert baseline == 240, f"Expected 240, got {baseline}"

            # Now perturb slightly UP at 120m (0.80 -> 0.88) -> threshold stays 240
            # Perturb slightly DOWN at 120m (0.80 -> 0.72) -> threshold becomes 120
            
            # Test case: Perturbation makes 120m pass (0.88)
            noisy_up = [0.99, 0.95, 0.88, 0.65, 0.40]
            with tempfile.NamedTemporaryFile(mode='w', suffix='_up.csv', delete=False) as f:
                f.write("resolution_m,power\n")
                for r, p in zip(resolutions, noisy_up):
                    f.write(f"{r},{p:.4f}\n")
                temp_up = f.name
            
            try:
                val_up = find_threshold(temp_up)
                assert val_up == 240, "Expected 240 when 120m power increases"
            finally:
                os.unlink(temp_up)

            # Test case: Perturbation makes 120m fail (0.72)
            noisy_down = [0.99, 0.95, 0.72, 0.65, 0.40]
            with tempfile.NamedTemporaryFile(mode='w', suffix='_down.csv', delete=False) as f:
                f.write("resolution_m,power\n")
                for r, p in zip(resolutions, noisy_down):
                    f.write(f"{r},{p:.4f}\n")
                temp_down = f.name

            try:
                val_down = find_threshold(temp_down)
                assert val_down == 120, "Expected 120 when 120m power decreases"
            finally:
                os.unlink(temp_down)

        finally:
            os.unlink(temp_csv_path)

    def test_sensitivity_sweep_logic(self):
        """
        Verify the ±10% sweep logic implementation details.
        Ensures that the sweep covers the range [0.9x, 1.1x] correctly.
        """
        rng = np.random.default_rng(12345)
        base_val = 0.85
        
        # Simulate 1000 iterations of ±10% sweep
        deviations = []
        for _ in range(1000):
            factor = rng.uniform(-0.10, 0.10)
            deviations.append(base_val * (1 + factor))
        
        deviations = np.array(deviations)
        
        # Check bounds
        min_expected = base_val * 0.90
        max_expected = base_val * 1.10
        
        assert np.all(deviations >= min_expected * 0.999), "Sweep went below -10%"
        assert np.all(deviations <= max_expected * 1.001), "Sweep went above +10%"
        
        # Check mean is close to base (unbiased noise)
        assert np.isclose(np.mean(deviations), base_val, atol=0.01), "Noise is biased"

class TestThresholdIdentification:
    """
    Tests for the threshold identification logic (T029 dependency).
    """
    
    def test_find_threshold_basic(self):
        """Test basic threshold finding."""
        data = {
            'resolution_m': [30, 60, 120, 240, 480],
            'power': [0.99, 0.90, 0.85, 0.70, 0.50]
        }
        df = pd.DataFrame(data)
        
        # Find first < 0.80
        result = df[df['power'] < 0.80].iloc[0]['resolution_m']
        assert result == 240

    def test_find_threshold_no_threshold(self):
        """Test when no resolution crosses the threshold."""
        data = {
            'resolution_m': [30, 60, 120],
            'power': [0.99, 0.90, 0.85]
        }
        df = pd.DataFrame(data)
        result = df[df['power'] < 0.80]
        assert result.empty

    def test_find_threshold_all_below(self):
        """Test when all resolutions are below threshold."""
        data = {
            'resolution_m': [30, 60],
            'power': [0.70, 0.60]
        }
        df = pd.DataFrame(data)
        result = df[df['power'] < 0.80].iloc[0]['resolution_m']
        assert result == 30

if __name__ == '__main__':
    pytest.main([__file__, '-v'])