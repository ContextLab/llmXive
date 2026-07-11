import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.validation import generate_synthetic_dataset, run_blind_validation

class TestSyntheticDatasetGeneration:
    def test_generate_synthetic_dataset_with_signal(self):
        """Test that synthetic dataset is generated with correct parameters."""
        df, gt = generate_synthetic_dataset(
            n_points=50,
            true_amplitude=0.05,
            true_phase_days=100,
            seed=42
        )
        
        assert len(df) == 50
        assert 'interval_start' in df.columns
        assert 'dipole_amp' in df.columns
        assert 'solar_proxy' in df.columns
        
        assert gt['true_amplitude'] == 0.05
        assert gt['true_phase_days'] == 100
        assert gt['n_points'] == 50

    def test_run_blind_validation_creates_output(self):
        """Test that run_blind_validation creates the output JSON file with required keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Generate synthetic data
            df, gt = generate_synthetic_dataset(n_points=100, seed=42)
            input_path = tmpdir / "input.csv"
            gt_path = tmpdir / "gt.json"
            output_path = tmpdir / "metrics.json"
            
            df.to_csv(input_path, index=False)
            with open(gt_path, 'w') as f:
                json.dump(gt, f)
            
            # Run validation
            run_blind_validation(
                input_path=str(input_path),
                ground_truth_path=str(gt_path),
                output_metrics_path=str(output_path),
                n_permutations=100 # Small number for speed
            )
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                metrics = json.load(f)
            
            assert 'fp_rate' in metrics
            assert 'power' in metrics
            assert isinstance(metrics['fp_rate'], float)
            assert isinstance(metrics['power'], float)

    def test_validation_thresholds(self):
        """
        Test that the system fails if thresholds are not met.
        This simulates the assertion required by T029.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Generate a dataset with a VERY strong signal to ensure Power=1
            df, gt = generate_synthetic_dataset(n_points=200, true_amplitude=0.5, seed=42)
            input_path = tmpdir / "input.csv"
            gt_path = tmpdir / "gt.json"
            output_path = tmpdir / "metrics.json"
            
            df.to_csv(input_path, index=False)
            with open(gt_path, 'w') as f:
                json.dump(gt, f)
            
            run_blind_validation(
                input_path=str(input_path),
                ground_truth_path=str(gt_path),
                output_metrics_path=str(output_path),
                n_permutations=500
            )
            
            with open(output_path, 'r') as f:
                metrics = json.load(f)
            
            # Assertion from T029
            if metrics['fp_rate'] > 0.05:
                raise AssertionError(f"False positive rate {metrics['fp_rate']} exceeds threshold 0.05")
            if metrics['power'] < 0.8:
                raise AssertionError(f"Power {metrics['power']} is below threshold 0.8")