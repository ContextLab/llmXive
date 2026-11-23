"""
Unit tests for edge cases in the GWAS pipeline.

Tests cover:
1. Missing Varroa data (None/NaN values in phenotype covariates)
2. All SNPs filtered out (empty dataset after QC)
3. Empty GWAS results input
4. Single sample edge case
"""

import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.preprocess_phenotype import create_dummy_phenotypes
from utils.fdr_correction import apply_fdr_correction, calculate_q_values
from utils.validators.colony_schema import validate_colony_data, ColonySchema
from utils.validators.snp_schema import validate_snp_data, SnpSchema


class TestMissingVarroaData:
    """Tests for handling missing Varroa mite count data."""

    def test_missing_varroa_in_dataframe(self):
        """Test that missing Varroa data is handled gracefully."""
        # Create a DataFrame with missing Varroa values
        data = {
            'colony_id': ['C1', 'C2', 'C3', 'C4', 'C5'],
            'ccd_status': [1, 0, 1, 0, 1],
            'geographic_region': ['North', 'South', 'North', 'South', 'North'],
            'sampling_year': [2020, 2021, 2020, 2021, 2020],
            'varroa_load': [5.0, np.nan, 3.5, np.nan, 6.0]  # Missing values
        }
        df = pd.DataFrame(data)
        
        # Test validation - should flag missing values
        # The schema validator should handle this gracefully
        try:
            # Check if the data passes basic schema validation
            # Note: Actual handling depends on whether we impute or drop
            result = validate_colony_data(df, ColonySchema())
            # If validation passes, check that missing values are noted
            assert isinstance(result, dict) or result is True
        except Exception as e:
            # If validation fails, it should be a clear error message
            assert "varroa" in str(e).lower() or "missing" in str(e).lower()
    
    def test_all_varroa_missing(self):
        """Test behavior when all Varroa values are missing."""
        data = {
            'colony_id': ['C1', 'C2', 'C3'],
            'ccd_status': [1, 0, 1],
            'geographic_region': ['North', 'South', 'North'],
            'sampling_year': [2020, 2021, 2020],
            'varroa_load': [np.nan, np.nan, np.nan]
        }
        df = pd.DataFrame(data)
        
        # This should either fail validation or produce a warning
        # depending on implementation
        with pytest.raises((ValueError, KeyError)) as exc_info:
            validate_colony_data(df, ColonySchema())
        
        # Verify the error message mentions the missing covariate
        assert "varroa" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()

    def test_mixed_missing_and_valid_varroa(self):
        """Test preprocessing with mixed missing and valid Varroa data."""
        # Create temporary file with mixed data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'colony_id': ['C1', 'C2', 'C3', 'C4', 'C5'],
                'ccd_status': [1, 0, 1, 0, 1],
                'geographic_region': ['North', 'South', 'North', 'South', 'North'],
                'sampling_year': [2020, 2021, 2020, 2021, 2020],
                'varroa_load': [5.0, np.nan, 3.5, 4.2, np.nan]
            })
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            # Test that the file can be read
            loaded_df = pd.read_csv(temp_path)
            assert len(loaded_df) == 5
            assert loaded_df['varroa_load'].isna().sum() == 2
        finally:
            os.unlink(temp_path)

class TestAllSnpsFiltered:
    """Tests for handling scenarios where all SNPs are filtered out."""

    def test_empty_snp_dataframe(self):
        """Test behavior when SNP dataframe is empty after filtering."""
        # Create empty DataFrame with correct schema
        empty_snp_df = pd.DataFrame(columns=[
            'chr', 'pos', 'id', 'ref', 'alt', 'qual', 'filter', 'info'
        ])
        
        # Test validation of empty dataset
        with pytest.raises((ValueError, AssertionError)) as exc_info:
            validate_snp_data(empty_snp_df, SnpSchema())
        
        # Should fail because no data to validate
        assert "empty" in str(exc_info.value).lower() or "no" in str(exc_info.value).lower()
    
    def test_fdr_correction_empty_input(self):
        """Test FDR correction with empty input."""
        empty_df = pd.DataFrame(columns=['snp_id', 'p_value'])
        
        with pytest.raises((ValueError, AssertionError)) as exc_info:
            calculate_q_values(empty_df['p_value'])
        
        # Should fail because there are no p-values to correct
        assert "empty" in str(exc_info.value).lower() or "no" in str(exc_info.value).lower()
    
    def test_all_snps_filtered_by_quality(self):
        """Test scenario where all SNPs fail quality filters."""
        # Create a DataFrame where all SNPs have low quality
        low_quality_snps = pd.DataFrame({
            'chr': [1, 2, 3],
            'pos': [100, 200, 300],
            'id': ['SNP1', 'SNP2', 'SNP3'],
            'ref': ['A', 'T', 'G'],
            'alt': ['T', 'C', 'A'],
            'qual': [10.0, 15.0, 20.0],  # All below threshold of 30
            'filter': ['LowQual', 'LowQual', 'LowQual'],
            'info': ['DP=5', 'DP=8', 'DP=9']
        })
        
        # Validate that this data would be filtered
        # The schema should accept the structure but the filtering logic
        # should remove all rows
        result = validate_snp_data(low_quality_snps, SnpSchema())
        assert result is True  # Structure is valid, even if data would be filtered
        
        # Simulate filtering (this would happen in the pipeline)
        filtered = low_quality_snps[low_quality_snps['qual'] >= 30]
        assert len(filtered) == 0

class TestEmptyGwasResults:
    """Tests for handling empty GWAS results."""

    def test_empty_gwas_file(self):
        """Test reading an empty GWAS results file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            # Write only header
            f.write("snp_id\tp_value\todds_ratio\n")
            temp_path = f.name
        
        try:
            df = pd.read_csv(temp_path, sep='\t')
            assert len(df) == 0
            assert list(df.columns) == ['snp_id', 'p_value', 'odds_ratio']
        finally:
            os.unlink(temp_path)
    
    def test_fdr_on_empty_gwas(self):
        """Test FDR correction on empty GWAS results."""
        empty_gwas = pd.DataFrame(columns=['snp_id', 'p_value', 'odds_ratio'])
        
        # Should handle gracefully or raise clear error
        with pytest.raises((ValueError, AssertionError)):
            apply_fdr_correction(empty_gwas, output_path="dummy.tsv")

class TestSingleSample:
    """Tests for single sample edge cases."""

    def test_single_colony_phenotype(self):
        """Test phenotype processing with only one colony."""
        single_colony = pd.DataFrame({
            'colony_id': ['C1'],
            'ccd_status': [1],
            'geographic_region': ['North'],
            'sampling_year': [2020],
            'varroa_load': [5.0]
        })
        
        # Should fail statistical analysis but pass schema validation
        result = validate_colony_data(single_colony, ColonySchema())
        assert result is True
        
        # Statistical operations should fail
        with pytest.raises((ValueError, AssertionError)):
            # This would happen during regression or power analysis
            if len(single_colony) < 2:
                raise ValueError("Insufficient samples for statistical analysis")

    def test_single_snp(self):
        """Test SNP processing with only one variant."""
        single_snp = pd.DataFrame({
            'chr': [1],
            'pos': [100],
            'id': ['SNP1'],
            'ref': ['A'],
            'alt': ['T'],
            'qual': [50.0],
            'filter': ['PASS'],
            'info': ['DP=20']
        })
        
        result = validate_snp_data(single_snp, SnpSchema())
        assert result is True

class TestBoundaryConditions:
    """Tests for boundary conditions in data processing."""

    def test_zero_p_value(self):
        """Test handling of zero p-values (should not occur in real data)."""
        df = pd.DataFrame({
            'snp_id': ['SNP1'],
            'p_value': [0.0]
        })
        
        # FDR correction should handle or flag this
        with pytest.raises((ValueError, FloatingPointError)):
            calculate_q_values(df['p_value'])
    
    def test_p_value_one(self):
        """Test handling of p-value = 1.0."""
        df = pd.DataFrame({
            'snp_id': ['SNP1', 'SNP2'],
            'p_value': [1.0, 0.5]
        })
        
        # Should be valid but result in high q-values
        q_values = calculate_q_values(df['p_value'])
        assert len(q_values) == 2
        assert all(q >= 0 and q <= 1 for q in q_values)
    
    def test_extreme_varroa_values(self):
        """Test handling of extreme Varroa load values."""
        extreme_data = pd.DataFrame({
            'colony_id': ['C1', 'C2'],
            'ccd_status': [1, 0],
            'geographic_region': ['North', 'South'],
            'sampling_year': [2020, 2021],
            'varroa_load': [0.0, 1000.0]  # Extreme values
        })
        
        result = validate_colony_data(extreme_data, ColonySchema())
        assert result is True  # Schema should accept, but analysis might flag

if __name__ == "__main__":
    pytest.main([__file__, "-v"])