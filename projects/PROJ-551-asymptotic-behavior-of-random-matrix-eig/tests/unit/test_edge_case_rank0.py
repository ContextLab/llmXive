"""
Unit Tests for Edge Case Rank 0 Verification (T031)
===================================================

Tests the logic that verifies the semicircle law for an unperturbed Wigner matrix.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import logging
import json
import os
from pathlib import Path

# Import the module under test
# Adjust import path based on project structure
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.edge_case_rank0 import (
    verify_semicircle_law,
    run_rank0_verification
)


class TestVerifySemicircleLaw:
    """Tests for the verify_semicircle_law function."""

    def test_empty_eigenvalues(self):
        """Should return failed status if no eigenvalues are provided."""
        result = verify_semicircle_law([], N=1000)
        assert result["status"] == "failed"
        assert result["reason"] == "No eigenvalues computed"
        assert result["within_tolerance"] is False

    def test_within_tolerance(self):
        """Should pass if max eigenvalue is close to 2.0."""
        # Typical max eigenvalue for large N is slightly above 2.0 but within tolerance
        eigenvalues = [2.01, 1.95, 1.90]
        result = verify_semicircle_law(eigenvalues, N=1000, tolerance=0.1)
        assert result["status"] == "passed"
        assert result["within_tolerance"] is True
        assert abs(result["max_eigenvalue"] - 2.01) < 1e-6

    def test_exceeds_tolerance(self):
        """Should fail if max eigenvalue significantly exceeds 2.0."""
        # A perturbed matrix might have an outlier > 2.0 + tolerance
        eigenvalues = [2.5, 1.9, 1.8]
        result = verify_semicircle_law(eigenvalues, N=1000, tolerance=0.1)
        assert result["status"] == "failed"
        assert result["within_tolerance"] is False
        assert result["max_eigenvalue"] == 2.5

    def test_exact_edge(self):
        """Should pass if max eigenvalue is exactly 2.0."""
        eigenvalues = [2.0, 1.9, 1.8]
        result = verify_semicircle_law(eigenvalues, N=1000, tolerance=0.1)
        assert result["status"] == "passed"
        assert result["within_tolerance"] is True


class TestRunRank0Verification:
    """Tests for the full verification workflow."""

    @patch("analysis.edge_case_rank0.generate_wigner_matrix")
    @patch("analysis.edge_case_rank0.compute_top_eigenvalues")
    @patch("analysis.edge_case_rank0.setup_simulation_logger")
    @patch("analysis.edge_case_rank0.get_project_paths")
    @patch("analysis.edge_case_rank0.ensure_directories")
    @patch("analysis.edge_case_rank0.get_matrix_size", return_value=100)
    @patch("analysis.edge_case_rank0.get_seed", return_value=42)
    @patch("analysis.edge_case_rank0.get_num_eigenvalues", return_value=5)
    def test_verification_passes(
        self,
        mock_get_num_eigs,
        mock_get_seed,
        mock_get_size,
        mock_ensure_dirs,
        mock_get_paths,
        mock_setup_logger,
        mock_compute_eigs,
        mock_gen_wigner
    ):
        """Test that the workflow runs and returns a passed status for unperturbed data."""
        # Setup mocks
        mock_paths = MagicMock()
        mock_paths.__getitem__ = lambda self, key: Path("data/logs")
        mock_get_paths.return_value = mock_paths

        mock_logger = MagicMock()
        mock_setup_logger.return_value = mock_logger

        # Mock Wigner matrix generation
        mock_wigner = np.random.randn(100, 100)
        mock_wigner = (mock_wigner + mock_wigner.T) / 2
        mock_gen_wigner.return_value = mock_wigner

        # Mock eigenvalues: slightly above 2.0 but within tolerance (1e-2)
        # For N=100, the fluctuation is larger, so we simulate a realistic value
        # that is still compliant with the logic (e.g., 2.005)
        mock_eigenvalues = [2.005, 1.99, 1.98, 1.95, 1.90]
        mock_compute_eigs.return_value = mock_eigenvalues

        # Run the function
        result = run_rank0_verification()

        # Assertions
        assert result["status"] == "passed"
        assert result["within_tolerance"] is True
        assert mock_gen_wigner.called
        assert mock_compute_eigs.called
        assert mock_logger.info.called

    @patch("analysis.edge_case_rank0.generate_wigner_matrix")
    @patch("analysis.edge_case_rank0.compute_top_eigenvalues")
    @patch("analysis.edge_case_rank0.setup_simulation_logger")
    @patch("analysis.edge_case_rank0.get_project_paths")
    @patch("analysis.edge_case_rank0.ensure_directories")
    @patch("analysis.edge_case_rank0.get_matrix_size", return_value=100)
    @patch("analysis.edge_case_rank0.get_seed", return_value=42)
    @patch("analysis.edge_case_rank0.get_num_eigenvalues", return_value=5)
    def test_verification_fails_on_outlier(
        self,
        mock_get_num_eigs,
        mock_get_seed,
        mock_get_size,
        mock_ensure_dirs,
        mock_get_paths,
        mock_setup_logger,
        mock_compute_eigs,
        mock_gen_wigner
    ):
        """Test that the workflow returns a failed status if an outlier is detected."""
        # Setup mocks
        mock_paths = MagicMock()
        mock_paths.__getitem__ = lambda self, key: Path("data/logs")
        mock_get_paths.return_value = mock_paths

        mock_logger = MagicMock()
        mock_setup_logger.return_value = mock_logger

        mock_gen_wigner.return_value = np.random.randn(100, 100)

        # Mock eigenvalues with a clear outlier (e.g., 2.5)
        mock_eigenvalues = [2.5, 1.9, 1.8, 1.7, 1.6]
        mock_compute_eigs.return_value = mock_eigenvalues

        # Run the function
        result = run_rank0_verification()

        # Assertions
        assert result["status"] == "failed"
        assert result["within_tolerance"] is False
        assert result["max_eigenvalue"] == 2.5
        assert mock_logger.error.called is False # Should not error, just fail validation
        # But it should log the result
        assert mock_logger.info.called

    def test_exception_handling(self):
        """Test that exceptions are caught and logged."""
        # We can't easily mock the entire chain to throw an exception without
        # patching many things, so we test the logic inside run_rank0_verification
        # by patching the critical compute step to raise.
        
        with patch("analysis.edge_case_rank0.get_project_paths") as mock_paths, \
             patch("analysis.edge_case_rank0.ensure_directories"), \
             patch("analysis.edge_case_rank0.setup_simulation_logger") as mock_logger_setup, \
             patch("analysis.edge_case_rank0.get_matrix_size", return_value=100), \
             patch("analysis.edge_case_rank0.get_seed", return_value=42), \
             patch("analysis.edge_case_rank0.get_num_eigenvalues", return_value=5), \
             patch("analysis.edge_case_rank0.generate_wigner_matrix") as mock_gen, \
             patch("analysis.edge_case_rank0.compute_top_eigenvalues") as mock_comp:

            mock_paths.return_value = {"data_logs": Path("data/logs")}
            mock_logger = MagicMock()
            mock_logger_setup.return_value = mock_logger
            mock_gen.return_value = np.random.randn(100, 100)
            mock_comp.side_effect = RuntimeError("Solver failed")

            result = run_rank0_verification()

            assert result["status"] == "error"
            assert "Solver failed" in result["reason"]
            assert mock_logger.error.called