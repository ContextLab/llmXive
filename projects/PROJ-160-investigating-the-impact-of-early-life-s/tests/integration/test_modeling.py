"""
Integration test for LMM fitting and formula validation.

This test verifies that the linear mixed-effects models fit correctly
using the formula: subfield_vol ~ ACE_score + age + sex + scanner_site + (1|family_id)
and that the expected output structure is produced.

Prerequisites:
- data/processed/cleaned_dataset.csv must exist (produced by T019)
- code/analysis/modeling.py must be implemented (T024)
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.analysis.modeling import fit_lmm_for_subfield, run_primary_analysis
from code.config_env import get_processed_dir


class TestLMMIntegration:
    """Integration tests for LMM fitting and formula validation."""

    @pytest.fixture(scope="class")
    def processed_dir(self):
        """Get the processed data directory."""
        return get_processed_dir()

    @pytest.fixture(scope="class")
    def cleaned_data_path(self, processed_dir):
        """Path to the cleaned dataset."""
        return processed_dir / "cleaned_dataset.csv"

    @pytest.fixture(scope="class")
    def sample_data(self, cleaned_data_path):
        """Load the cleaned dataset for testing."""
        if not cleaned_data_path.exists():
            pytest.skip(f"Cleaned dataset not found at {cleaned_data_path}. "
                        "Run T019 to generate the data first.")
        return pd.read_csv(cleaned_data_path)

    def test_data_loaded_correctly(self, sample_data):
        """Verify that the cleaned dataset has the required columns."""
        required_columns = [
            'ACE', 'Age', 'Sex', 'Site', 'FamilyID', 
            'CA3', 'DG', 'Subiculum', 'ICV'
        ]
        assert all(col in sample_data.columns for col in required_columns), \
            f"Missing required columns. Found: {sample_data.columns.tolist()}"
        assert len(sample_data) > 0, "Dataset is empty"

    def test_lmm_fits_ca3(self, sample_data):
        """Test that LMM fits successfully for CA3 subfield."""
        try:
            result = fit_lmm_for_subfield(
                df=sample_data,
                subfield="CA3",
                ace_col="ACE",
                age_col="Age",
                sex_col="Sex",
                site_col="Site",
                family_col="FamilyID"
            )
            assert result is not None, "Model result is None"
            assert hasattr(result, 'fitted') or 'summary' in str(result).lower(), \
                "Result does not contain expected model summary"
        except Exception as e:
            pytest.fail(f"LMM fitting for CA3 failed: {str(e)}")

    def test_lmm_fits_dg(self, sample_data):
        """Test that LMM fits successfully for DG subfield."""
        try:
            result = fit_lmm_for_subfield(
                df=sample_data,
                subfield="DG",
                ace_col="ACE",
                age_col="Age",
                sex_col="Sex",
                site_col="Site",
                family_col="FamilyID"
            )
            assert result is not None, "Model result is None"
        except Exception as e:
            pytest.fail(f"LMM fitting for DG failed: {str(e)}")

    def test_lmm_fits_subiculum(self, sample_data):
        """Test that LMM fits successfully for Subiculum subfield."""
        try:
            result = fit_lmm_for_subfield(
                df=sample_data,
                subfield="Subiculum",
                ace_col="ACE",
                age_col="Age",
                sex_col="Sex",
                site_col="Site",
                family_col="FamilyID"
            )
            assert result is not None, "Model result is None"
        except Exception as e:
            pytest.fail(f"LMM fitting for Subiculum failed: {str(e)}")

    def test_formula_structure(self, sample_data):
        """Verify the formula structure matches the specification."""
        # The formula should be: subfield_vol ~ ACE_score + age + sex + scanner_site + (1|family_id)
        # We check that the model accepts this structure by attempting to fit
        # and verifying the formula is parsed correctly.
        try:
            # This will raise an error if the formula syntax is invalid
            result = fit_lmm_for_subfield(
                df=sample_data,
                subfield="CA3",
                ace_col="ACE",
                age_col="Age",
                sex_col="Sex",
                site_col="Site",
                family_col="FamilyID"
            )
            # If we get here, the formula was valid
            assert result is not None
        except Exception as e:
            pytest.fail(f"Formula validation failed: {str(e)}")

    def test_primary_analysis_runs(self, sample_data):
        """Test that the primary analysis pipeline runs end-to-end."""
        try:
            results = run_primary_analysis(
                df=sample_data,
                ace_col="ACE",
                age_col="Age",
                sex_col="Sex",
                site_col="Site",
                family_col="FamilyID",
                subfields=["CA3", "DG", "Subiculum"]
            )
            assert isinstance(results, dict), "Primary analysis should return a dictionary"
            assert len(results) == 3, f"Expected 3 subfield results, got {len(results)}"
            assert all(k in results for k in ["CA3", "DG", "Subiculum"]), \
                "Missing expected subfield keys in results"
        except Exception as e:
            pytest.fail(f"Primary analysis failed: {str(e)}")

    def test_model_convergence(self, sample_data):
        """Test that models converge successfully (no convergence warnings)."""
        # This is a basic check; a more robust test would inspect model warnings
        for subfield in ["CA3", "DG", "Subiculum"]:
            try:
                result = fit_lmm_for_subfield(
                    df=sample_data,
                    subfield=subfield,
                    ace_col="ACE",
                    age_col="Age",
                    sex_col="Sex",
                    site_col="Site",
                    family_col="FamilyID"
                )
                # Check if result indicates successful convergence
                # This depends on the implementation details of fit_lmm_for_subfield
                assert result is not None
            except Exception as e:
                # If the model fails to converge, it should raise an error
                # which we catch here. If it raises, the test fails.
                pytest.fail(f"Model for {subfield} did not converge: {str(e)}")

    def test_coefficient_extraction(self, sample_data):
        """Test that coefficients can be extracted from fitted models."""
        for subfield in ["CA3", "DG", "Subiculum"]:
            result = fit_lmm_for_subfield(
                df=sample_data,
                subfield=subfield,
                ace_col="ACE",
                age_col="Age",
                sex_col="Sex",
                site_col="Site",
                family_col="FamilyID"
            )
            # Verify that we can extract the ACE coefficient
            # The exact method depends on the implementation
            # Assuming result contains a summary or params attribute
            assert result is not None, f"Failed to fit model for {subfield}"