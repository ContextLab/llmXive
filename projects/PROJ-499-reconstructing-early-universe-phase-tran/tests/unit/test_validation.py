"""
Unit tests for the validation module.
"""
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pytest

# Ensure code directory is in path
code_dir = Path(__file__).parent.parent.parent / "code"
import sys
sys.path.insert(0, str(code_dir))

from validation import validate_pt_synthetic, validate_inflation_synthetic


class TestValidatePtSynthetic:
    """Tests for validate_pt_synthetic function."""
    
    def test_validate_pt_synthetic_passes(self):
        """Test that validation passes when posterior is accurate."""
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create ground truth with E_PT = 1e15
            ground_truth = {
                "params": {"E_PT": 1e15}
            }
            ground_truth_path = tmpdir / "ground_truth_pt.json"
            with open(ground_truth_path, 'w') as f:
                json.dump(ground_truth, f)
            
            # Create inference results with samples centered around 1e15
            # Generate samples with mean ~1e15 and small std
            np.random.seed(42)
            samples = np.random.normal(loc=1e15, scale=1e13, size=1000)
            inference_results = {
                "samples": {"E_PT": samples.tolist()}
            }
            inference_path = tmpdir / "inference_results_pt.json"
            with open(inference_path, 'w') as f:
                json.dump(inference_results, f)
            
            # Run validation
            output_path = tmpdir / "validation_report_pt.json"
            report = validate_pt_synthetic(
                str(inference_path),
                str(ground_truth_path),
                str(output_path)
            )
            
            # Check that validation passes
            assert report["validation_passed"] is True
            assert report["covers_95_ci"] is True
            assert report["centered_within_10"] is True
            assert abs(report["posterior_mean"] - 1e15) / 1e15 < 0.10
            
            # Check that output file was created
            assert output_path.exists()
            
            # Check output file contents
            with open(output_path, 'r') as f:
                saved_report = json.load(f)
            assert saved_report["validation_passed"] is True
    
    def test_validate_pt_synthetic_fails_ci(self):
        """Test that validation fails when true value is outside 95% CI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create ground truth with E_PT = 1e15
            ground_truth = {
                "params": {"E_PT": 1e15}
            }
            ground_truth_path = tmpdir / "ground_truth_pt.json"
            with open(ground_truth_path, 'w') as f:
                json.dump(ground_truth, f)
            
            # Create inference results with samples far from true value
            # Mean at 5e14, which is 50% off
            np.random.seed(42)
            samples = np.random.normal(loc=5e14, scale=1e13, size=1000)
            inference_results = {
                "samples": {"E_PT": samples.tolist()}
            }
            inference_path = tmpdir / "inference_results_pt.json"
            with open(inference_path, 'w') as f:
                json.dump(inference_results, f)
            
            # Run validation
            output_path = tmpdir / "validation_report_pt.json"
            report = validate_pt_synthetic(
                str(inference_path),
                str(ground_truth_path),
                str(output_path)
            )
            
            # Check that validation fails
            assert report["validation_passed"] is False
            assert report["centered_within_10"] is False  # 50% error > 10%
    
    def test_validate_pt_synthetic_missing_samples(self):
        """Test that validation raises error when samples are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create ground truth
            ground_truth = {
                "params": {"E_PT": 1e15}
            }
            ground_truth_path = tmpdir / "ground_truth_pt.json"
            with open(ground_truth_path, 'w') as f:
                json.dump(ground_truth, f)
            
            # Create inference results without samples
            inference_results = {
                "other_key": "value"
            }
            inference_path = tmpdir / "inference_results_pt.json"
            with open(inference_path, 'w') as f:
                json.dump(inference_results, f)
            
            # Run validation - should raise ValueError
            output_path = tmpdir / "validation_report_pt.json"
            with pytest.raises(ValueError, match="must contain a 'samples' key"):
                validate_pt_synthetic(
                    str(inference_path),
                    str(ground_truth_path),
                    str(output_path)
                )
    
    def test_validate_pt_synthetic_missing_E_PT(self):
        """Test that validation raises error when E_PT is missing from samples."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create ground truth
            ground_truth = {
                "params": {"E_PT": 1e15}
            }
            ground_truth_path = tmpdir / "ground_truth_pt.json"
            with open(ground_truth_path, 'w') as f:
                json.dump(ground_truth, f)
            
            # Create inference results with samples but no E_PT
            inference_results = {
                "samples": {"r": [1, 2, 3]}
            }
            inference_path = tmpdir / "inference_results_pt.json"
            with open(inference_path, 'w') as f:
                json.dump(inference_results, f)
            
            # Run validation - should raise ValueError
            output_path = tmpdir / "validation_report_pt.json"
            with pytest.raises(ValueError, match="must contain 'E_PT' in samples"):
                validate_pt_synthetic(
                    str(inference_path),
                    str(ground_truth_path),
                    str(output_path)
                )


class TestValidateInflationSynthetic:
    """Tests for validate_inflation_synthetic function."""
    
    def test_validate_inflation_synthetic_passes(self):
        """Test that validation passes when posterior is accurate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create ground truth with r = 0.01
            ground_truth = {
                "params": {"r": 0.01}
            }
            ground_truth_path = tmpdir / "ground_truth_inflation.json"
            with open(ground_truth_path, 'w') as f:
                json.dump(ground_truth, f)
            
            # Create inference results with samples centered around 0.01
            np.random.seed(42)
            samples = np.random.normal(loc=0.01, scale=0.001, size=1000)
            inference_results = {
                "samples": {"r": samples.tolist()}
            }
            inference_path = tmpdir / "inference_results_inflation.json"
            with open(inference_path, 'w') as f:
                json.dump(inference_results, f)
            
            # Run validation
            output_path = tmpdir / "validation_report_inflation.json"
            report = validate_inflation_synthetic(
                str(inference_path),
                str(ground_truth_path),
                str(output_path)
            )
            
            # Check that validation passes
            assert report["validation_passed"] is True
            assert report["covers_95_ci"] is True
            assert report["centered_within_10"] is True
            assert abs(report["posterior_mean"] - 0.01) / 0.01 < 0.10
            
            # Check that output file was created
            assert output_path.exists()