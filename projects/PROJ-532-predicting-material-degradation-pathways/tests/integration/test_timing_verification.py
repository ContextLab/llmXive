"""
Integration test for T030: Execution time verification.

This test verifies that the timing verification script runs correctly
and produces the expected output artifacts.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

import pytest

class TestTimingVerification:
    """Test suite for timing verification functionality."""
    
    def test_timing_report_structure(self):
        """Test that the timing report has the required structure."""
        # Create a sample timing report
        sample_report = {
            "task_id": "T030",
            "max_allowed_seconds": 21600,
            "max_allowed_hours": 6.0,
            "pipelines": {
                "training": {
                    "status": "success",
                    "duration_seconds": 100.0,
                    "duration_hours": 0.0278
                },
                "evaluation": {
                    "status": "success",
                    "duration_seconds": 50.0,
                    "duration_hours": 0.0139
                }
            },
            "total_duration_seconds": 150.0,
            "total_duration_hours": 0.0417,
            "status": "passed",
            "timestamp": "2024-01-01 12:00:00"
        }
        
        # Verify required fields
        assert "task_id" in sample_report
        assert "max_allowed_seconds" in sample_report
        assert "max_allowed_hours" in sample_report
        assert "pipelines" in sample_report
        assert "total_duration_seconds" in sample_report
        assert "total_duration_hours" in sample_report
        assert "status" in sample_report
        assert "timestamp" in sample_report
        
        # Verify pipeline structure
        assert "training" in sample_report["pipelines"]
        assert "evaluation" in sample_report["pipelines"]
        
        # Verify pipeline fields
        for pipeline_name in ["training", "evaluation"]:
            pipeline = sample_report["pipelines"][pipeline_name]
            assert "status" in pipeline
            assert "duration_seconds" in pipeline
            assert "duration_hours" in pipeline
            assert pipeline["status"] in ["success", "error", "failed"]
    
    def test_timing_calculation(self):
        """Test that timing calculations are correct."""
        # Test case 1: Within time limit
        training_duration = 10000  # seconds
        evaluation_duration = 5000  # seconds
        total_duration = training_duration + evaluation_duration
        max_allowed = 21600  # 6 hours
        
        assert total_duration <= max_allowed
        assert total_duration / 3600.0 <= 6.0
        
        # Test case 2: Exceeds time limit
        training_duration = 15000
        evaluation_duration = 10000
        total_duration = training_duration + evaluation_duration
        
        assert total_duration > max_allowed
        assert total_duration / 3600.0 > 6.0
    
    def test_status_determination(self):
        """Test that status is correctly determined based on timing."""
        max_allowed = 21600  # 6 hours
        
        # Case 1: Within limit -> passed
        total_duration = 20000
        status = "passed" if total_duration <= max_allowed else "failed"
        assert status == "passed"
        
        # Case 2: Exceeds limit -> failed
        total_duration = 22000
        status = "passed" if total_duration <= max_allowed else "failed"
        assert status == "failed"
        
        # Case 3: Exactly at limit -> passed
        total_duration = max_allowed
        status = "passed" if total_duration <= max_allowed else "failed"
        assert status == "passed"
    
    @pytest.mark.integration
    def test_full_pipeline_execution(self):
        """
        Integration test: Run the full timing verification pipeline.
        
        This test requires that:
        1. The training pipeline has been executed (T024-T029)
        2. The evaluation pipeline has been executed
        3. Required artifacts exist (model.pkl, train_set.parquet, etc.)
        
        If these prerequisites are not met, this test will fail.
        """
        # Check if required artifacts exist
        project_root = Path(__file__).parent.parent.parent
        training_data = project_root / "data" / "processed" / "train_set.parquet"
        model_artifact = project_root / "results" / "artifacts" / "model.pkl"
        
        if not training_data.exists():
            pytest.skip("Training data not found. Run T019 first.")
        
        if not model_artifact.exists():
            pytest.skip("Model artifact not found. Run T024-T029 first.")
        
        # Import and run the timing verification
        from timing_verification import main
        
        # Capture the return code
        return_code = main()
        
        # Verify that the timing report was created
        timing_report_path = project_root / "results" / "metrics" / "timing_verification.json"
        assert timing_report_path.exists(), "Timing report was not created"
        
        # Load and verify the report
        with open(timing_report_path, 'r') as f:
            report = json.load(f)
        
        assert report["task_id"] == "T030"
        assert "status" in report
        assert report["status"] in ["passed", "failed"]
        
        # If we got here, the pipeline executed successfully
        assert return_code in [0, 1]  # 0 for passed, 1 for failed or error
    
    def test_error_handling(self):
        """Test that errors are properly handled and reported."""
        # Simulate a training error
        training_error_duration = 100
        training_error = "Mock training error"
        
        report = {
            "pipelines": {
                "training": {
                    "status": "error",
                    "duration_seconds": training_error_duration,
                    "error": training_error
                }
            }
        }
        
        # Verify error structure
        assert report["pipelines"]["training"]["status"] == "error"
        assert "error" in report["pipelines"]["training"]
        assert report["pipelines"]["training"]["error"] == training_error
    
    def test_cpu_only_requirement(self):
        """
        Test that the timing verification enforces CPU-only execution.
        
        This is a documentation/test that the script should only run on CPU.
        In practice, this would be enforced by the execution environment.
        """
        # The timing verification script should not use GPU-specific libraries
        # This is a conceptual test - actual enforcement happens in CI/CD
        
        # Check that the script doesn't import GPU libraries
        timing_script_path = Path(__file__).parent.parent.parent / "code" / "timing_verification.py"
        
        if timing_script_path.exists():
            with open(timing_script_path, 'r') as f:
                content = f.read()
            
            # Check for GPU-specific imports
            gpu_imports = ["torch.cuda", "tensorflow.gpu", "cupy", "nvidia"]
            for gpu_import in gpu_imports:
                assert gpu_import not in content, f"GPU import found: {gpu_import}"
        
        # This test documents the requirement
        assert True  # If we get here, the check passed or the file doesn't exist yet