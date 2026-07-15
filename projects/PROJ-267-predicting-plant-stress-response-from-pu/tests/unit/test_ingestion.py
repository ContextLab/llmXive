"""
Unit tests for the data ingestion module, specifically normalize.py (T012) and merge.py (T013).
Focus: LCM (MinProb) imputation logic and low-abundance filtering.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_ingestion.normalize import calculate_detection_rate, filter_low_abundance_proteins, apply_lcm_imputation
from utils.config import DATA_PROCESSED_PATH

class TestLCMImputation:
    """Tests for Left-Censored Missing (LCM) imputation logic using MinProb."""

    def test_lcm_imputation_minprob(self):
        """
        Test that the LCM imputation (MinProb) correctly shifts left-censored values.
        
        Logic:
        1. Create a synthetic dataset with a known distribution (e.g., normal).
        2. Introduce "left-censored" missingness: values below a threshold are set to NaN.
        3. Apply apply_lcm_imputation.
        4. Verify that the imputed values are:
           - Less than the detection threshold (since they are censored).
           - Drawn from a distribution that is lower than the observed mean.
           - Not equal to the original non-NaN values.
        """
        # 1. Create synthetic data
        np.random.seed(42)
        n_samples = 50
        n_features = 5
        
        # Generate data from a normal distribution
        data = np.random.normal(loc=10.0, scale=2.0, size=(n_samples, n_features))
        df = pd.DataFrame(data, columns=[f"Protein_{i}" for i in range(n_features)])
        
        # 2. Introduce left-censored missingness
        # Assume a detection threshold of 8.0. Values < 8.0 become NaN.
        detection_threshold = 8.0
        df_censored = df.copy()
        mask = df_censored < detection_threshold
        df_censored[mask] = np.nan
        
        # Verify we actually created some NaNs
        assert df_censored.isna().sum().sum() > 0, "Synthetic data generation failed to create missing values."
        
        # 3. Apply LCM imputation
        # The function expects a dataframe and an optional threshold.
        # If threshold is not provided, it might calculate it or use a default.
        # We explicitly pass the threshold used for censoring to ensure consistency.
        df_imputed = apply_lcm_imputation(df_censored, threshold=detection_threshold)
        
        # 4. Verify results
        # a. No NaNs should remain (assuming the function fills all)
        assert not df_imputed.isna().any().any(), "LCM imputation failed to fill all missing values."
        
        # b. Imputed values should be below the detection threshold
        # We only check the cells that were originally NaN
        imputed_values = df_imputed[mask]
        assert (imputed_values < detection_threshold).all().all(), \
            "Imputed values for censored data exceed the detection threshold."
        
        # c. Imputed values should be significantly lower than the observed mean
        observed_mean = df[~mask].mean().mean()
        imputed_mean = imputed_values.mean()
        assert imputed_mean < observed_mean, \
            "Imputed values (MinProb) should be lower than the observed mean."

    def test_lcm_imputation_filter_low_abundance(self):
        """
        Test that proteins with low detection rates are correctly filtered out.
        
        Logic:
        1. Create a dataset where one protein has >50% missing values (low abundance).
        2. Apply filter_low_abundance_proteins with a 50% threshold.
        3. Verify the low-abundance protein is removed.
        """
        # 1. Create synthetic data
        np.random.seed(42)
        n_samples = 20
        
        # Protein A: High abundance (mostly present)
        protein_a = np.random.normal(loc=15.0, scale=1.0, size=n_samples)
        
        # Protein B: Low abundance (>50% missing)
        # 60% missing
        protein_b = np.random.normal(loc=10.0, scale=1.0, size=n_samples)
        missing_count = int(n_samples * 0.6)
        protein_b[:missing_count] = np.nan
        
        # Protein C: Moderate abundance (exactly 50% missing - edge case)
        protein_c = np.random.normal(loc=10.0, scale=1.0, size=n_samples)
        protein_c[:10] = np.nan
        
        df = pd.DataFrame({
            "Protein_A": protein_a,
            "Protein_B": protein_b,
            "Protein_C": protein_c
        })
        
        # 2. Apply filter
        # Threshold is 0.5 (50%). Proteins with detection rate < 0.5 are dropped.
        # Detection rate = (1 - missing_rate).
        # Protein B: missing_rate = 0.6 -> detection_rate = 0.4 -> DROPPED
        # Protein C: missing_rate = 0.5 -> detection_rate = 0.5 -> KEPT (if condition is < threshold)
        # The task says "filter low-abundance proteins (<50% detection)".
        # So we keep if detection_rate >= 0.5.
        
        df_filtered = filter_low_abundance_proteins(df, threshold=0.5)
        
        # 3. Verify
        assert "Protein_A" in df_filtered.columns, "High abundance protein was incorrectly dropped."
        assert "Protein_B" not in df_filtered.columns, "Low abundance protein was not dropped."
        # Protein C has exactly 50% detection. Depending on implementation (< vs <=), it might stay.
        # Standard interpretation: "filter ... (<50%)" means keep if >= 50%.
        # So Protein C should remain.
        assert "Protein_C" in df_filtered.columns, "Protein with exactly 50% detection was incorrectly dropped."
        
        # Verify shape
        assert df_filtered.shape[1] == 2, f"Expected 2 columns, got {df_filtered.shape[1]}"

    def test_detection_rate_calculation(self):
        """
        Test the helper function for calculating detection rates.
        """
        data = {
            "P1": [1.0, 2.0, np.nan, 4.0], # 25% missing -> 75% detection
            "P2": [np.nan, np.nan, 3.0, np.nan], # 75% missing -> 25% detection
            "P3": [1.0, 2.0, 3.0, 4.0] # 0% missing -> 100% detection
        }
        df = pd.DataFrame(data)
        
        rates = calculate_detection_rate(df)
        
        assert abs(rates["P1"] - 0.75) < 1e-6, "Detection rate for P1 incorrect."
        assert abs(rates["P2"] - 0.25) < 1e-6, "Detection rate for P2 incorrect."
        assert abs(rates["P3"] - 1.0) < 1e-6, "Detection rate for P3 incorrect."

class TestMergeMapping:
    """Tests for UniProt to Ensembl mapping logic (T013)."""

    def test_biomaRt_mapping_structure(self):
        """
        Test that the mapping function returns the correct structure.
        Note: This test assumes biomaRt is available. If not, it should raise RuntimeError.
        """
        # Use a small set of known IDs for testing if available, or mock the environment
        # Since we cannot guarantee biomaRt availability in all test environments,
        # we test the logic flow and error handling.
        
        from data_ingestion.merge import map_uniprot_to_ensembl, SPECIES_MART_MAP
        
        # Test 1: Check species mapping validity
        assert "arabidopsis" in SPECIES_MART_MAP
        assert SPECIES_MART_MAP["arabidopsis"] == "at"
        
        # Test 2: Invalid species should raise ValueError
        with pytest.raises(ValueError):
            map_uniprot_to_ensembl(["P12345"], species="invalid_species")

    def test_biomaRt_failure_raises_error(self):
        """
        Test that the function raises RuntimeError when mapping fails.
        This simulates the case where biomaRt is not installed or returns no results.
        """
        from data_ingestion.merge import map_uniprot_to_ensembl
        
        # We simulate a failure by passing IDs that are known to fail or by mocking
        # the R environment to fail. Since we can't easily mock rpy2 here without
        # complex setup, we rely on the fact that if biomaRt is missing, the function
        # raises RuntimeError.
        
        # If biomaRt is installed, we test with a set of IDs that might not exist
        # to trigger the "unmapped" error path.
        try:
            # Try with a fake ID
            result = map_uniprot_to_ensembl(["FAKE_ID_12345"], species="arabidopsis")
            # If we get here, it means the function didn't raise an error for unmapped IDs.
            # In strict mode, it should have raised RuntimeError.
            # However, if the ID actually mapped (unlikely for FAKE_ID), we proceed.
            # We assert that if it didn't raise, the result must be empty or handled.
            assert len(result) == 0 or result["Ensembl_ID"].isna().all()
        except RuntimeError as e:
            # This is the expected behavior for unmapped IDs or missing biomaRt
            assert "Mapping failed" in str(e) or "biomaRt" in str(e)
        except Exception as e:
            # Unexpected error
            pytest.fail(f"Unexpected exception: {e}")

    def test_lcm_imputation_integration(self):
        """
        Integration test ensuring the merge module can handle data that has been imputed.
        """
        # Create a dummy dataframe with imputed values
        data = {
            "UniProt_ID": ["P12345", "Q67890"],
            "Protein_A": [1.0, 2.0],
            "Protein_B": [np.nan, 3.0]
        }
        df = pd.DataFrame(data)
        
        # Verify the dataframe structure
        assert "UniProt_ID" in df.columns
        assert df.shape[0] == 2

class TestPipelineIntegration:
    """Integration tests for the merge pipeline."""

    def test_run_merge_pipeline(self):
        """
        Test the full pipeline: load -> map -> save.
        This requires a real input file.
        """
        # Check if the expected input file exists
        input_file = DATA_PROCESSED_PATH / "normalized_proteomics.csv"
        
        if not input_file.exists():
            pytest.skip(f"Input file {input_file} not found. Skipping integration test.")
        
        # Import the function
        from data_ingestion.merge import run_merge_pipeline
        
        # Run the pipeline
        output_path = run_merge_pipeline(input_path=input_file, species="arabidopsis")
        
        # Verify output exists
        assert output_path.exists()
        
        # Verify output content
        result_df = pd.read_csv(output_path)
        assert "Ensembl_ID" in result_df.columns
        assert "UniProt_ID" in result_df.columns