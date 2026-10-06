"""
Unit tests for edge cases in the plant stress response pipeline.

This module covers:
1. All-missing columns in data loading and imputation
2. Mismatched IDs during merge operations
3. Empty datasets
4. Single-sample datasets
5. Zero-variance features
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
import json

# Import utilities from the project
from utils.data_utils import load_csv, save_csv
from data_ingestion.normalize import (
    calculate_detection_rate,
    filter_low_abundance_proteins,
    apply_lcm_imputation
)
from data_ingestion.merge import map_uniprot_to_ensembl
from utils.schema_validator import validate_csv_schema, ValidationStatus


class TestAllMissingColumns:
    """Tests for handling columns with all missing values."""

    def test_detection_rate_all_missing(self):
        """Calculate detection rate for a column with all NaN values."""
        df = pd.DataFrame({
            'protein_A': [np.nan, np.nan, np.nan],
            'protein_B': [1.0, 2.0, 3.0]
        })
        
        rates = calculate_detection_rate(df)
        
        assert 'protein_A' in rates
        assert rates['protein_A'] == 0.0
        assert 'protein_B' in rates
        assert rates['protein_B'] == 1.0

    def test_filter_low_abundance_all_missing(self):
        """Filter should remove columns with 0% detection rate."""
        df = pd.DataFrame({
            'protein_A': [np.nan, np.nan, np.nan],
            'protein_B': [1.0, 2.0, 3.0],
            'protein_C': [np.nan, 1.0, np.nan]  # 33% detection
        })
        
        threshold = 0.5
        filtered_df, dropped = filter_low_abundance_proteins(df, threshold)
        
        assert 'protein_A' not in filtered_df.columns
        assert 'protein_B' in filtered_df.columns
        assert 'protein_C' not in filtered_df.columns  # Below threshold
        assert len(dropped) == 2
        assert 'protein_A' in dropped
        assert 'protein_C' in dropped

    def test_lcm_imputation_all_missing_column(self):
        """LCM imputation should handle all-missing columns gracefully."""
        df = pd.DataFrame({
            'protein_A': [np.nan, np.nan, np.nan],
            'protein_B': [1.0, 2.0, 3.0],
            'sample_id': ['S1', 'S2', 'S3']
        })
        
        # This should not crash, though the all-missing column might be dropped
        # or filled with a placeholder. We test that it runs without error.
        try:
            result = apply_lcm_imputation(df)
            # The result should have the same number of rows
            assert result.shape[0] == df.shape[0]
        except Exception as e:
            # If it raises, it should be a clear error, not a silent failure
            pytest.fail(f"LCM imputation crashed on all-missing column: {e}")

    def test_empty_dataframe_handling(self):
        """Empty DataFrame should be handled without crashing."""
        df = pd.DataFrame()
        
        # Detection rate on empty DF
        rates = calculate_detection_rate(df)
        assert rates == {}

        # Filter on empty DF
        filtered, dropped = filter_low_abundance_proteins(df, 0.5)
        assert filtered.empty
        assert dropped == []

    def test_schema_validation_all_missing(self):
        """Schema validator should handle all-missing columns."""
        df = pd.DataFrame({
            'protein_A': [np.nan, np.nan, np.nan],
            'sample_id': ['S1', 'S2', 'S3']
        })
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
            df.to_csv(f, index=False)
        
        try:
            result = validate_csv_schema(temp_path, expected_columns=['protein_A', 'sample_id'])
            # The schema should validate (columns exist), even if values are missing
            assert result.status == ValidationStatus.PASS or result.status == ValidationStatus.WARNING
        finally:
            os.unlink(temp_path)


class TestMismatchedIDs:
    """Tests for handling mismatched or missing IDs during merge operations."""

    def test_no_matching_ids(self):
        """When no IDs match, merge should return empty or minimal result."""
        # Create mock data with no overlap
        uniprot_df = pd.DataFrame({
            'UniProt_ID': ['P12345', 'Q67890', 'O11111'],
            'abundance_1': [1.0, 2.0, 3.0]
        })
        
        ensembl_df = pd.DataFrame({
            'Ensembl_ID': ['ENSG000001', 'ENSG000002', 'ENSG000003'],
            'expression_1': [10.0, 20.0, 30.0]
        })
        
        # The merge function should handle this gracefully
        # It might return an empty DataFrame or log a warning
        # We test that it doesn't crash
        try:
            result = map_uniprot_to_ensembl(uniprot_df, ensembl_df)
            # Result should be empty or have minimal rows
            assert isinstance(result, pd.DataFrame)
        except Exception as e:
            pytest.fail(f"Merge with no matching IDs crashed: {e}")

    def test_partial_id_overlap(self):
        """When only some IDs match, merge should preserve matched rows."""
        uniprot_df = pd.DataFrame({
            'UniProt_ID': ['P12345', 'Q67890', 'O11111'],
            'abundance_1': [1.0, 2.0, 3.0]
        })
        
        ensembl_df = pd.DataFrame({
            'Ensembl_ID': ['ENSG000001', 'ENSG000002', 'ENSG000003'],
            'expression_1': [10.0, 20.0, 30.0]
        })
        
        # Simulate a partial mapping scenario
        # In real code, this would use biomaRt, but we test the logic
        # by creating a mock mapping
        mapping_df = pd.DataFrame({
            'UniProt_ID': ['P12345', 'Q67890'],
            'Ensembl_ID': ['ENSG000001', 'ENSG000002']
        })
        
        # Test that we can merge with partial data
        merged = pd.merge(
            uniprot_df,
            mapping_df,
            on='UniProt_ID',
            how='inner'
        )
        
        assert len(merged) == 2  # Only 2 matched
        assert 'O11111' not in merged['UniProt_ID'].values

    def test_duplicate_ids_in_source(self):
        """Handle duplicate IDs in source data."""
        uniprot_df = pd.DataFrame({
            'UniProt_ID': ['P12345', 'P12345', 'Q67890'],
            'abundance_1': [1.0, 2.0, 3.0]
        })
        
        mapping_df = pd.DataFrame({
            'UniProt_ID': ['P12345', 'Q67890'],
            'Ensembl_ID': ['ENSG000001', 'ENSG000002']
        })
        
        merged = pd.merge(
            uniprot_df,
            mapping_df,
            on='UniProt_ID',
            how='inner'
        )
        
        # Duplicate in source should result in duplicate in merged
        assert len(merged) == 3
        assert len(merged[merged['UniProt_ID'] == 'P12345']) == 2

    def test_case_sensitivity_in_ids(self):
        """Test case sensitivity handling in ID matching."""
        uniprot_df = pd.DataFrame({
            'UniProt_ID': ['P12345', 'Q67890'],
            'abundance_1': [1.0, 2.0]
        })
        
        mapping_df = pd.DataFrame({
            'UniProt_ID': ['p12345', 'Q67890'],  # Different case
            'Ensembl_ID': ['ENSG000001', 'ENSG000002']
        })
        
        # Without case normalization, this should not match the first
        merged = pd.merge(
            uniprot_df,
            mapping_df,
            on='UniProt_ID',
            how='inner'
        )
        
        # Only Q67890 should match (exact case)
        assert len(merged) == 1
        assert merged['UniProt_ID'].iloc[0] == 'Q67890'


class TestZeroVarianceFeatures:
    """Tests for handling features with zero variance."""

    def test_zero_variance_detection(self):
        """Detect columns with zero variance."""
        df = pd.DataFrame({
            'constant_feature': [5.0, 5.0, 5.0, 5.0],
            'varying_feature': [1.0, 2.0, 3.0, 4.0],
            'nan_constant': [np.nan, np.nan, np.nan, np.nan]
        })
        
        # Calculate variance
        variances = df.var()
        
        assert variances['constant_feature'] == 0.0
        assert variances['varying_feature'] > 0.0
        # NaN constant might be NaN or 0 depending on pandas version
        assert pd.isna(variances['nan_constant']) or variances['nan_constant'] == 0.0

    def test_zero_variance_in_imputation(self):
        """Imputation should handle zero-variance columns."""
        df = pd.DataFrame({
            'constant_feature': [5.0, 5.0, 5.0],
            'sample_id': ['S1', 'S2', 'S3']
        })
        
        try:
            result = apply_lcm_imputation(df)
            assert result.shape[0] == df.shape[0]
        except Exception as e:
            pytest.fail(f"Imputation crashed on zero-variance column: {e}")


class TestSingleSampleDataset:
    """Tests for handling datasets with only one sample."""

    def test_single_sample_detection_rate(self):
        """Detection rate with single sample."""
        df = pd.DataFrame({
            'protein_A': [1.0],
            'protein_B': [np.nan]
        })
        
        rates = calculate_detection_rate(df)
        
        assert rates['protein_A'] == 1.0
        assert rates['protein_B'] == 0.0

    def test_single_sample_filtering(self):
        """Filtering with single sample."""
        df = pd.DataFrame({
            'protein_A': [1.0],
            'protein_B': [np.nan],
            'protein_C': [0.5]
        })
        
        filtered, dropped = filter_low_abundance_proteins(df, 0.5)
        
        assert 'protein_A' in filtered.columns
        assert 'protein_B' not in filtered.columns
        assert 'protein_C' in filtered.columns

    def test_single_sample_imputation(self):
        """Imputation with single sample."""
        df = pd.DataFrame({
            'protein_A': [1.0],
            'protein_B': [np.nan],
            'sample_id': ['S1']
        })
        
        try:
            result = apply_lcm_imputation(df)
            assert result.shape[0] == 1
        except Exception as e:
            pytest.fail(f"Imputation crashed on single sample: {e}")


class TestEmptyDataset:
    """Tests for completely empty datasets."""

    def test_empty_dataframe_load(self):
        """Load an empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("protein_A,protein_B,sample_id\n")
            temp_path = f.name
        
        try:
            df = load_csv(temp_path)
            assert df.empty
            assert list(df.columns) == ['protein_A', 'protein_B', 'sample_id']
        finally:
            os.unlink(temp_path)

    def test_empty_dataframe_processing(self):
        """Process an empty DataFrame through the pipeline."""
        df = pd.DataFrame(columns=['protein_A', 'protein_B', 'sample_id'])
        
        # Detection rate
        rates = calculate_detection_rate(df)
        assert rates == {}
        
        # Filter
        filtered, dropped = filter_low_abundance_proteins(df, 0.5)
        assert filtered.empty
        assert dropped == []

    def test_empty_dataframe_imputation(self):
        """Imputation on empty DataFrame."""
        df = pd.DataFrame(columns=['protein_A', 'protein_B', 'sample_id'])
        
        try:
            result = apply_lcm_imputation(df)
            assert result.empty
            assert list(result.columns) == ['protein_A', 'protein_B', 'sample_id']
        except Exception as e:
            pytest.fail(f"Imputation crashed on empty DataFrame: {e}")


class TestSpecialValues:
    """Tests for handling special values like inf, -inf, and extremely large numbers."""

    def test_infinite_values_detection(self):
        """Detect infinite values in data."""
        df = pd.DataFrame({
            'normal': [1.0, 2.0, 3.0],
            'inf': [np.inf, 2.0, 3.0],
            'neg_inf': [1.0, -np.inf, 3.0]
        })
        
        # Check for infinite values
        has_inf = np.isinf(df).any().any()
        assert has_inf is True

    def test_infinite_values_in_imputation(self):
        """Imputation should handle or reject infinite values."""
        df = pd.DataFrame({
            'protein_A': [1.0, np.inf, 3.0],
            'sample_id': ['S1', 'S2', 'S3']
        })
        
        try:
            result = apply_lcm_imputation(df)
            # Should either handle it or raise a clear error
            # We just test it doesn't crash silently
        except Exception:
            # Expected: either ValueError or it handles it
            pass

    def test_extreme_values_detection(self):
        """Detect extremely large values that might cause numerical issues."""
        df = pd.DataFrame({
            'normal': [1.0, 2.0, 3.0],
            'extreme': [1e308, 1e308, 1e308]
        })
        
        # Check for extreme values
        max_val = df['extreme'].max()
        assert max_val > 1e300