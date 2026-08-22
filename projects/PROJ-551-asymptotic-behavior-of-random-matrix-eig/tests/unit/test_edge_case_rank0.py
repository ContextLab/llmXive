"""
Unit Tests for Edge Case Rank-0 Verification (T031)
"""

import pytest
import numpy as np
from pathlib import Path
import json
import tempfile
import os

# Import the module under test
from code.analysis.edge_case_rank0 import (
    verify_semicircle_law,
    log_verification_result,
    run_rank0_verification
)
from code.utils.config import get_project_paths

class TestVerifySemicircleLaw:
    def test_compliance_within_tolerance(self):
        """Test that eigenvalues within the theoretical edge pass."""
        # Create synthetic eigenvalues that are within [ -2, 2 ]
        eigenvalues = np.array([1.9, 1.5, 0.0, -1.5, -1.9])
        result = verify_semicircle_law(eigenvalues, n=5, expected_edge=2.0, tolerance=0.1)
        
        assert result["is_compliant"] is True
        assert result["compliance_message"] == "PASS"
        assert result["spectral_radius"] == 1.9
        assert abs(result["deviation_from_edge"]) < 0.1

    def test_non_compliance_outside_tolerance(self):
        """Test that eigenvalues exceeding the edge fail."""
        # Create synthetic eigenvalues where max > 2.0 + tolerance
        eigenvalues = np.array([2.5, 1.0, 0.0, -1.0, -2.0])
        result = verify_semicircle_law(eigenvalues, n=5, expected_edge=2.0, tolerance=0.1)
        
        assert result["is_compliant"] is False
        assert result["compliance_message"] == "FAIL"
        assert result["spectral_radius"] == 2.5
        assert result["deviation_from_edge"] == 0.5

    def test_statistical_properties(self):
        """Test that mean and variance are calculated correctly."""
        eigenvalues = np.array([1.0, 0.0, -1.0])
        result = verify_semicircle_law(eigenvalues, n=3)
        
        assert result["mean_eigenvalue"] == 0.0
        assert result["variance_eigenvalue"] == pytest.approx(0.6666, rel=1e-3)

class TestLogVerificationResult:
    def test_log_file_creation(self):
        """Test that the log file is created with correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_log.log"
            result = {
                "n": 100,
                "max_eigenvalue": 1.95,
                "is_compliant": True
            }
            
            log_verification_result(result, log_path, seed=42)
            
            assert log_path.exists()
            
            with open(log_path, 'r') as f:
                data = json.load(f)
            
            assert "timestamp" in data
            assert data["seed"] == 42
            assert data["task_id"] == "T031"
            assert data["verification_result"]["is_compliant"] is True

class TestRunRank0Verification:
    def test_full_workflow_execution(self):
        """Test the full verification workflow generates a valid log."""
        # Use a small N for speed in unit tests
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock config paths if necessary, or just pass explicit args
            # We assume the generators work as per T012
            output_path = Path(tmpdir) / "edge_case_rank0.log"
            
            # Run with small N to ensure speed
            result = run_rank0_verification(n=100, seed=42, output_path=output_path)
            
            assert output_path.exists()
            assert result["n"] == 100
            assert "max_eigenvalue" in result
            assert "is_compliant" in result
            
            # Verify the log file content matches the result
            with open(output_path, 'r') as f:
                log_data = json.load(f)
                
            assert log_data["verification_result"]["n"] == result["n"]
            assert log_data["verification_result"]["is_compliant"] == result["is_compliant"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])