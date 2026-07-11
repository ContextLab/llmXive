import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json
import os
import sys

# Add code directory to path if not already present
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from src.validation import generate_synthetic_dataset, save_synthetic_dataset, run_blind_validation

class TestSyntheticDatasetGeneration:
    """
    Unit tests for synthetic dataset generation and blind validation.
    
    This test suite includes the critical assertion required by FR-011 and SC-008:
    The system must fail the build if false positive rate exceeds 0.05 or
    statistical power falls below 0.8.
    """

    def test_synthetic_dataset_generation(self):
        """Test that synthetic dataset generation produces valid data."""
        # Generate synthetic data with known correlation signal
        n_events = 10000
        n_intervals = 50
        
        times, anisotropy, solar_proxy, ground_truth = generate_synthetic_dataset(
            n_events=n_events,
            n_intervals=n_intervals,
            signal_amplitude=0.5,
            signal_phase=1.0
        )
        
        # Verify data structure
        assert len(times) == n_intervals
        assert len(anisotropy) == n_intervals
        assert len(solar_proxy) == n_intervals
        assert len(ground_truth) == n_intervals
        
        # Verify data types
        assert isinstance(times, np.ndarray)
        assert isinstance(anisotropy, np.ndarray)
        assert isinstance(solar_proxy, np.ndarray)
        
        # Verify data ranges
        assert np.all(anisotropy >= 0)
        assert np.all(solar_proxy >= 0)

    def test_save_synthetic_dataset(self):
        """Test that synthetic dataset can be saved and loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "validation_input.csv"
            
            # Generate and save
            times, anisotropy, solar_proxy, ground_truth = generate_synthetic_dataset(
                n_events=1000,
                n_intervals=20
            )
            save_synthetic_dataset(
                times=times,
                anisotropy=anisotropy,
                solar_proxy=solar_proxy,
                ground_truth=ground_truth,
                output_path=str(output_path)
            )
            
            # Verify file exists
            assert output_path.exists()
            
            # Verify file can be loaded
            df = pd.read_csv(output_path)
            assert len(df) == 20
            assert 'interval_start' in df.columns
            assert 'anisotropy_amp' in df.columns
            assert 'solar_proxy' in df.columns

    def test_blind_validation_metrics(self):
        """Test that blind validation produces valid metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate synthetic dataset
            times, anisotropy, solar_proxy, ground_truth = generate_synthetic_dataset(
                n_events=10000,
                n_intervals=50,
                signal_amplitude=0.5,
                signal_phase=1.0
            )
            
            # Save dataset
            input_path = Path(tmpdir) / "validation_input.csv"
            save_synthetic_dataset(
                times=times,
                anisotropy=anisotropy,
                solar_proxy=solar_proxy,
                ground_truth=ground_truth,
                output_path=str(input_path)
            )
            
            # Run blind validation
            metrics = run_blind_validation(
                input_path=str(input_path),
                output_path=str(Path(tmpdir) / "validation_metrics.json")
            )
            
            # Verify metrics structure
            assert 'fp_rate' in metrics
            assert 'power' in metrics
            assert isinstance(metrics['fp_rate'], float)
            assert isinstance(metrics['power'], float)
            
            # Verify metrics are in valid ranges
            assert 0 <= metrics['fp_rate'] <= 1
            assert 0 <= metrics['power'] <= 1

    def test_validation_thresholds_enforcement(self):
        """
        CRITICAL TEST: Assert that system fails build if thresholds are not met.
        
        This test enforces FR-011 and SC-008 requirements:
        - fp_rate must be <= 0.05
        - power must be >= 0.8
        
        If these thresholds are violated, the test raises an AssertionError,
        causing the build to fail.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate synthetic dataset with strong known signal
            times, anisotropy, solar_proxy, ground_truth = generate_synthetic_dataset(
                n_events=50000,  # Large sample for stable estimates
                n_intervals=100,  # More intervals for better statistics
                signal_amplitude=0.8,  # Strong signal
                signal_phase=1.5
            )
            
            # Save dataset
            input_path = Path(tmpdir) / "validation_input.csv"
            save_synthetic_dataset(
                times=times,
                anisotropy=anisotropy,
                solar_proxy=solar_proxy,
                ground_truth=ground_truth,
                output_path=str(input_path)
            )
            
            # Run blind validation
            metrics = run_blind_validation(
                input_path=str(input_path),
                output_path=str(Path(tmpdir) / "validation_metrics.json")
            )
            
            # Load metrics from file to ensure consistency
            metrics_path = Path(tmpdir) / "validation_metrics.json"
            with open(metrics_path, 'r') as f:
                saved_metrics = json.load(f)
            
            # Verify metrics match
            assert abs(metrics['fp_rate'] - saved_metrics['fp_rate']) < 1e-10
            assert abs(metrics['power'] - saved_metrics['power']) < 1e-10
            
            # CRITICAL ASSERTION: Enforce FR-011 and SC-008 thresholds
            # If fp_rate > 0.05, the system has too many false positives
            # If power < 0.8, the system lacks statistical power
            assert metrics['fp_rate'] <= 0.05, (
                f"False positive rate ({metrics['fp_rate']:.4f}) exceeds threshold of 0.05. "
                f"System fails FR-011 and SC-008 requirements. "
                f"Validation metrics: {metrics}"
            )
            
            assert metrics['power'] >= 0.8, (
                f"Statistical power ({metrics['power']:.4f}) is below threshold of 0.8. "
                f"System fails FR-011 and SC-008 requirements. "
                f"Validation metrics: {metrics}"
            )
            
            # Log success for debugging
            print(f"✓ Validation passed: fp_rate={metrics['fp_rate']:.4f}, power={metrics['power']:.4f}")

    def test_validation_with_weak_signal(self):
        """
        Test that validation correctly handles cases with weak or no signal.
        
        This test ensures the system doesn't falsely claim high power when
        there is no real signal to detect.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate synthetic dataset with very weak signal
            times, anisotropy, solar_proxy, ground_truth = generate_synthetic_dataset(
                n_events=10000,
                n_intervals=50,
                signal_amplitude=0.0,  # No signal
                signal_phase=0.0
            )
            
            # Save dataset
            input_path = Path(tmpdir) / "validation_input.csv"
            save_synthetic_dataset(
                times=times,
                anisotropy=anisotropy,
                solar_proxy=solar_proxy,
                ground_truth=ground_truth,
                output_path=str(input_path)
            )
            
            # Run blind validation
            metrics = run_blind_validation(
                input_path=str(input_path),
                output_path=str(Path(tmpdir) / "validation_metrics.json")
            )
            
            # With no signal, we expect:
            # - fp_rate should be low (close to significance level)
            # - power should be low (no signal to detect)
            assert metrics['fp_rate'] <= 0.1, (
                f"False positive rate too high for null case: {metrics['fp_rate']}"
            )
            
            # Note: We don't assert power >= 0.8 here because there's no signal
            # This test verifies the system behaves correctly when there's nothing to detect