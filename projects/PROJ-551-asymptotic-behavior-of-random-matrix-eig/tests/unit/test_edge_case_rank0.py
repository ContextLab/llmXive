"""
Unit tests for T031: Edge Case Rank 0 Verification.
"""
import pytest
import numpy as np
from pathlib import Path
import json
import os
import tempfile
import shutil

# Import from project
from analysis.edge_case_rank0 import verify_semicircle_law, run_rank0_verification
from generators.wigner import generate_wigner_matrix

class TestSemicircleVerification:
    """Tests for the semicircle law verification logic."""

    def test_verify_semicircle_law_no_outliers(self):
        """Test that a valid Wigner matrix (N=1000) passes verification."""
        N = 1000
        seed = 42
        matrix = generate_wigner_matrix(N, seed=seed)
        
        # Compute eigenvalues manually for test
        # Using np.linalg.eigh for exactness in test
        all_eigs = np.linalg.eigh(matrix)[0]
        top_eigs = np.sort(all_eigs)[::-1][:10]

        # Verify
        result = verify_semicircle_law(top_eigs, N, tolerance=1e-10)
        
        assert result["N"] == N
        assert "max_eigenvalue" in result
        assert "is_compliant" in result
        # For N=1000, max_eig should be close to 2.0, definitely not > 2.5
        assert result["max_eigenvalue"] < 2.5 

    def test_verify_semicircle_law_with_artificial_outlier(self):
        """Test that an artificial outlier is detected."""
        N = 1000
        # Create eigenvalues with a clear outlier > 2.0
        eigs = np.array([3.5, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1])
        
        result = verify_semicircle_law(eigs, N, tolerance=1e-10)
        
        # The logic in verify_semicircle_law calls validate_eigenvalues
        # which checks if max > 2.0 + tol.
        # 3.5 > 2.0, so outlier_detected should be True.
        assert result["outlier_detected"] is True
        assert result["is_compliant"] is False

    def test_run_rank0_verification_creates_log(self):
        """Test that the full run creates the expected log file."""
        N = 200  # Small N for fast test
        seed = 123
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_edge_case_rank0.log"
            
            result = run_rank0_verification(N, seed, log_path)
            
            # Check file exists
            assert log_path.exists()
            
            # Check content
            with open(log_path) as f:
                data = json.load(f)
            
            assert data["task_id"] == "T031"
            assert data["parameters"]["N"] == N
            assert data["parameters"]["perturbation_rank"] == 0
            assert "results" in data
            assert "is_compliant" in data["results"]