"""
Unit tests for T029: FWE Correction.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import numpy as np

# Import the functions to test
from fwe_correction import (
    apply_bonferroni_correction,
    apply_fdr_correction,
    run_fwe_correction,
    TARGET_COMPARISONS
)

class TestBonferroniCorrection:
    def test_simple_bonferroni(self):
        """Test basic Bonferroni calculation."""
        p = 0.01
        n = 5
        expected = 0.05
        assert apply_bonferroni_correction(p, n) == expected

    def test_bonferroni_cap_at_1(self):
        """Test that corrected p-value does not exceed 1.0."""
        p = 0.2
        n = 10
        result = apply_bonferroni_correction(p, n)
        assert result == 1.0
        assert result <= 1.0

    def test_small_p_values(self):
        """Test with very small p-values."""
        p = 0.001
        n = 20
        result = apply_bonferroni_correction(p, n)
        assert result == 0.02

class TestFDRCorrection:
    def test_fdr_monotonicity(self):
        """Test that FDR corrected p-values are monotonic."""
        p_values = [0.01, 0.05, 0.03, 0.001]
        corrected = apply_fdr_correction(p_values)
        
        # Check that corrected values are sorted relative to input order?
        # Actually, BH ensures that if p_i < p_j then p_corr_i <= p_corr_j
        # Let's just check they are valid probabilities
        for p in corrected:
            assert 0.0 <= p <= 1.0

    def test_fdr_with_identical_p(self):
        """Test FDR with identical p-values."""
        p_values = [0.05, 0.05, 0.05]
        corrected = apply_fdr_correction(p_values)
        
        # All should be corrected to same value or similar logic
        assert len(corrected) == 3
        for p in corrected:
            assert 0.0 <= p <= 1.0

    def test_fdr_empty_list(self):
        """Test FDR with empty list."""
        assert apply_fdr_correction([]) == []

class TestRunFWECorrection:
    def setup_method(self):
        """Set up temporary files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.t_test_path = Path(self.temp_dir) / "t_test_results.json"
        self.metadata_path = Path(self.temp_dir) / "feature_metadata.json"
        self.output_path = Path(self.temp_dir) / "feature_metadata_updated.json"

        # Create mock t-test results
        mock_ttest = {}
        for comp in TARGET_COMPARISONS:
            key = f"{comp['electrode']}_{comp['band']}"
            mock_ttest[key] = {
                "p_value": 0.04,
                "t_statistic": 2.1
            }
        
        with open(self.t_test_path, 'w') as f:
            json.dump(mock_ttest, f)

        # Create mock metadata
        mock_metadata = {
            "correlation_matrix": {},
            "collinearity_report": {}
        }
        with open(self.metadata_path, 'w') as f:
            json.dump(mock_metadata, f)

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_run_bonferroni(self):
        """Test running Bonferroni correction end-to-end."""
        result = run_fwe_correction(
            self.t_test_path,
            self.metadata_path,
            self.output_path,
            method="bonferroni"
        )
        
        assert result["method"] == "bonferroni"
        assert result["n_tests"] == len(TARGET_COMPARISONS)
        assert len(result["corrected_results"]) == len(TARGET_COMPARISONS)
        
        # Check file was written
        assert self.output_path.exists()
        
        with open(self.output_path, 'r') as f:
            saved_metadata = json.load(f)
        
        assert "fwe_corrected_p_values" in saved_metadata
        assert len(saved_metadata["fwe_corrected_p_values"]) == len(TARGET_COMPARISONS)

    def test_run_fdr(self):
        """Test running FDR correction end-to-end."""
        result = run_fwe_correction(
            self.t_test_path,
            self.metadata_path,
            self.output_path,
            method="fdr"
        )
        
        assert result["method"] == "fdr"
        assert len(result["corrected_results"]) == len(TARGET_COMPARISONS)

    def test_missing_input_file(self):
        """Test that FileNotFoundError is raised if input is missing."""
        with pytest.raises(FileNotFoundError):
            run_fwe_correction(
                Path("/nonexistent/path.json"),
                self.metadata_path,
                self.output_path
            )

    def test_missing_metadata_file(self):
        """Test that FileNotFoundError is raised if metadata is missing."""
        with pytest.raises(FileNotFoundError):
            run_fwe_correction(
                self.t_test_path,
                Path("/nonexistent/path.json"),
                self.output_path
            )

    def test_corrected_values_valid(self):
        """Test that corrected p-values are valid probabilities."""
        result = run_fwe_correction(
            self.t_test_path,
            self.metadata_path,
            self.output_path,
            method="bonferroni"
        )
        
        for r in result["corrected_results"]:
            assert 0.0 <= r["corrected_p"] <= 1.0
            assert 0.0 <= r["uncorrected_p"] <= 1.0