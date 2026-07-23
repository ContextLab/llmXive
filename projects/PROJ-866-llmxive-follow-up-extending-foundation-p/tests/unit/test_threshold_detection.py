import pytest
import numpy as np
import json
import os
import tempfile
from pathlib import Path

# Import the module to test
from analysis.threshold_detection import bootstrap_threshold, detect_threshold_with_correction

class TestBootstrapThreshold:
    """Unit tests for bootstrap_threshold function."""
    
    def test_bootstrap_threshold_basic(self):
        """Test basic bootstrap threshold calculation."""
        # Create synthetic data with known properties
        np.random.seed(42)
        reductions = np.linspace(0, 90, 20)
        errors = np.array([0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0,
                          3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0])
        
        threshold, ci_lower, ci_upper = bootstrap_threshold(
            reductions, errors, 
            threshold_pct=1.0,
            n_resamples=100,  # Small number for speed
            rng=np.random.default_rng(42)
        )
        
        # Threshold should be between 0 and 90
        assert 0 <= threshold <= 90
        # CI should be ordered
        assert ci_lower <= threshold <= ci_upper
        # CI should be reasonable width
        assert ci_upper - ci_lower > 0
        
    def test_bootstrap_threshold_all_valid(self):
        """Test when all errors are below threshold."""
        reductions = np.array([10, 20, 30, 40, 50])
        errors = np.array([0.1, 0.2, 0.3, 0.4, 0.5])  # All below 1%
        
        threshold, ci_lower, ci_upper = bootstrap_threshold(
            reductions, errors,
            threshold_pct=1.0,
            n_resamples=50,
            rng=np.random.default_rng(42)
        )
        
        # Should return the maximum reduction
        assert threshold == 50.0
        assert ci_lower == 50.0
        assert ci_upper == 50.0
        
    def test_bootstrap_threshold_no_valid(self):
        """Test when no errors are below threshold."""
        reductions = np.array([10, 20, 30])
        errors = np.array([5.0, 6.0, 7.0])  # All above 1%
        
        threshold, ci_lower, ci_upper = bootstrap_threshold(
            reductions, errors,
            threshold_pct=1.0,
            n_resamples=50,
            rng=np.random.default_rng(42)
        )
        
        # Should return the minimum reduction
        assert threshold == 10.0

class TestDetectThresholdWithCorrection:
    """Integration tests for detect_threshold_with_correction."""
    
    def test_detect_threshold_basic(self):
        """Test basic threshold detection with mock data."""
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            processed_dir = os.path.join(temp_dir, "processed")
            results_dir = os.path.join(temp_dir, "results")
            os.makedirs(processed_dir)
            os.makedirs(results_dir)
            
            # Create mock processed logs
            mock_logs = [
                {
                    "workflow_id": "wf_001",
                    "context_reduction_pct": 10.0,
                    "total_steps": 100,
                    "policy_violations": 1
                },
                {
                    "workflow_id": "wf_002",
                    "context_reduction_pct": 20.0,
                    "total_steps": 100,
                    "policy_violations": 2
                },
                {
                    "workflow_id": "wf_003",
                    "context_reduction_pct": 30.0,
                    "total_steps": 100,
                    "policy_violations": 5
                },
                {
                    "workflow_id": "wf_004",
                    "context_reduction_pct": 40.0,
                    "total_steps": 100,
                    "policy_violations": 8
                },
                {
                    "workflow_id": "wf_005",
                    "context_reduction_pct": 50.0,
                    "total_steps": 100,
                    "policy_violations": 12
                }
            ]
            
            # Save mock logs
            for i, log in enumerate(mock_logs):
                with open(os.path.join(processed_dir, f"log_{i}.json"), 'w') as f:
                    json.dump(log, f)
            
            # Run threshold detection
            results = detect_threshold_with_correction(
                logs_path=processed_dir,
                output_dir=results_dir,
                target_error_pct=1.0,
                n_resamples=50,  # Small for speed
                correction_method="benjamini_hochberg"
            )
            
            # Verify results structure
            assert "threshold_detection" in results
            assert "max_context_reduction_pct" in results["threshold_detection"]
            assert "confidence_interval_95" in results["threshold_detection"]
            assert "lower_bound" in results["threshold_detection"]["confidence_interval_95"]
            assert "upper_bound" in results["threshold_detection"]["confidence_interval_95"]
            
            # Verify CI file was created
            ci_file = os.path.join(results_dir, "threshold_ci.json")
            assert os.path.exists(ci_file)
            
            # Verify CI file contents
            with open(ci_file, 'r') as f:
                ci_data = json.load(f)
            
            assert ci_data == results
            
            # Threshold should be reasonable (between 0 and 50)
            threshold = results["threshold_detection"]["max_context_reduction_pct"]
            assert 0 <= threshold <= 50
            
    def test_detect_threshold_with_bonferroni(self):
        """Test threshold detection with Bonferroni correction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            processed_dir = os.path.join(temp_dir, "processed")
            results_dir = os.path.join(temp_dir, "results")
            os.makedirs(processed_dir)
            os.makedirs(results_dir)
            
            # Create simple mock logs
            mock_logs = [
                {
                    "workflow_id": "wf_001",
                    "context_reduction_pct": 10.0,
                    "total_steps": 100,
                    "policy_violations": 1
                },
                {
                    "workflow_id": "wf_002",
                    "context_reduction_pct": 20.0,
                    "total_steps": 100,
                    "policy_violations": 2
                }
            ]
            
            for i, log in enumerate(mock_logs):
                with open(os.path.join(processed_dir, f"log_{i}.json"), 'w') as f:
                    json.dump(log, f)
            
            results = detect_threshold_with_correction(
                logs_path=processed_dir,
                output_dir=results_dir,
                target_error_pct=1.0,
                n_resamples=50,
                correction_method="bonferroni"
            )
            
            assert results["threshold_detection"]["correction_method"] == "bonferroni"
            assert "max_context_reduction_pct" in results["threshold_detection"]
            
    def test_rounding_to_two_decimals(self):
        """Test that threshold is rounded to exactly 2 decimal places."""
        with tempfile.TemporaryDirectory() as temp_dir:
            processed_dir = os.path.join(temp_dir, "processed")
            results_dir = os.path.join(temp_dir, "results")
            os.makedirs(processed_dir)
            os.makedirs(results_dir)
            
            # Create mock logs
            mock_logs = [
                {
                    "workflow_id": "wf_001",
                    "context_reduction_pct": 10.123456,
                    "total_steps": 100,
                    "policy_violations": 1
                },
                {
                    "workflow_id": "wf_002",
                    "context_reduction_pct": 20.654321,
                    "total_steps": 100,
                    "policy_violations": 2
                }
            ]
            
            for i, log in enumerate(mock_logs):
                with open(os.path.join(processed_dir, f"log_{i}.json"), 'w') as f:
                    json.dump(log, f)
            
            results = detect_threshold_with_correction(
                logs_path=processed_dir,
                output_dir=results_dir,
                target_error_pct=1.0,
                n_resamples=50
            )
            
            threshold = results["threshold_detection"]["max_context_reduction_pct"]
            ci_lower = results["threshold_detection"]["confidence_interval_95"]["lower_bound"]
            ci_upper = results["threshold_detection"]["confidence_interval_95"]["upper_bound"]
            
            # Verify rounding to 2 decimal places
            assert round(threshold, 2) == threshold
            assert round(ci_lower, 2) == ci_lower
            assert round(ci_upper, 2) == ci_upper
            
    def test_empty_logs_handling(self):
        """Test that empty logs directory raises appropriate error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            processed_dir = os.path.join(temp_dir, "processed")
            results_dir = os.path.join(temp_dir, "results")
            os.makedirs(processed_dir)
            os.makedirs(results_dir)
            
            # Don't create any log files
            
            with pytest.raises(ValueError, match="No processed logs found"):
                detect_threshold_with_correction(
                    logs_path=processed_dir,
                    output_dir=results_dir
                )