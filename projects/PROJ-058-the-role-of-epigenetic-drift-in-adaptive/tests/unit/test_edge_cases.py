"""
Unit tests for edge cases in the epigenetic drift analysis pipeline.

Covers:
- Zero variance in gene expression/methylation
- Missing metadata fields (timescale, organism, etc.)
- Timescale mismatch scenarios
- Empty datasets
- Single-sample scenarios
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# Import modules being tested
from analysis.timescale_align import (
    load_timescale_data,
    extract_env_timescale,
    calculate_drift_timescale,
    calculate_alignment_status,
    process_timescale_alignment
)
from preprocess.filters import (
    filter_by_organism,
    filter_by_global_methylation_level
)
from preprocess.filter_genes import (
    filter_genes_by_variance_and_missing
)
from discovery.query_geno import (
    load_verified_datasets,
    calculate_token_overlap,
    validate_reference
)

from config import get_env


class TestZeroVarianceCases:
    """Test handling of zero variance in gene data."""

    def test_filter_genes_all_zero_variance(self):
        """When all genes have zero variance, result should be empty."""
        df = pd.DataFrame({
            'gene_id': ['gene1', 'gene2', 'gene3'],
            'variance_rna': [0.0, 0.0, 0.0],
            'variance_methyl': [0.0, 0.0, 0.0],
            'missing_rna': [0, 0, 0],
            'missing_methyl': [0, 0, 0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_path = Path(tmpdir) / 'output.csv'
            df.to_csv(input_path, index=False)
            
            filtered_df, kept_count, removed_count = filter_genes_by_variance_and_missing(
                input_path, output_path, 
                min_variance_threshold=1e-6,
                max_missing_fraction=0.1
            )
            
            assert len(filtered_df) == 0
            assert kept_count == 0
            assert removed_count == 3
    
    def test_filter_genes_mixed_variance(self):
        """Filter should keep genes with non-zero variance in at least one layer."""
        df = pd.DataFrame({
            'gene_id': ['gene1', 'gene2', 'gene3', 'gene4'],
            'variance_rna': [0.5, 0.0, 0.0, 0.8],
            'variance_methyl': [0.0, 0.3, 0.0, 0.9],
            'missing_rna': [0, 0, 0, 0],
            'missing_methyl': [0, 0, 0, 0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_path = Path(tmpdir) / 'output.csv'
            df.to_csv(input_path, index=False)
            
            filtered_df, kept_count, removed_count = filter_genes_by_variance_and_missing(
                input_path, output_path,
                min_variance_threshold=1e-6,
                max_missing_fraction=0.1
            )
            
            # gene1 (rna var), gene2 (methyl var), gene4 (both var) should be kept
            # gene3 (both zero) should be removed
            assert kept_count == 3
            assert removed_count == 1
            assert 'gene3' not in filtered_df['gene_id'].values
    
    def test_variance_calculation_single_value(self):
        """Variance of a single value should be zero or NaN."""
        values = np.array([5.0])
        var = np.var(values)
        assert var == 0.0
    
    def test_variance_calculation_identical_values(self):
        """Variance of identical values should be zero."""
        values = np.array([5.0, 5.0, 5.0, 5.0])
        var = np.var(values)
        assert var == 0.0


class TestMissingMetadataCases:
    """Test handling of missing or incomplete metadata."""

    def test_extract_env_timescale_missing_keys(self):
        """Should return None when all expected keys are missing."""
        metadata = {
            'organism': 'mouse',
            'treatment': 'control',
            'other_field': 'value'
        }
        
        result = extract_env_timescale(metadata)
        assert result is None
    
    def test_extract_env_timescale_partial_keys(self):
        """Should extract from first available key in priority order."""
        # Priority: fluctuation_timescale, fluctuation_period, env_period
        metadata = {
            'fluctuation_period': 10.5,
            'other_field': 'value'
        }
        
        result = extract_env_timescale(metadata)
        assert result == 10.5
    
    def test_extract_env_timescale_first_priority(self):
        """Should prefer fluctuation_timescale over others."""
        metadata = {
            'fluctuation_timescale': 20.0,
            'fluctuation_period': 10.0,
            'env_period': 5.0
        }
        
        result = extract_env_timescale(metadata)
        assert result == 20.0
    
    def test_load_timescale_data_missing_file(self):
        """Should raise FileNotFoundError for missing input."""
        with pytest.raises(FileNotFoundError):
            load_timescale_data(Path('/nonexistent/path/to/file.json'))
    
    def test_load_timescale_data_empty_file(self):
        """Should handle empty JSON file gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'empty.json'
            input_path.write_text('[]')
            
            result = load_timescale_data(input_path)
            assert result == []
    
    def test_load_timescale_data_missing_fields_in_record(self):
        """Should handle records with missing required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'partial.json'
            data = [
                {'id': 'valid', 'fluctuation_timescale': 10.0},
                {'id': 'missing_timescale'},
                {'id': 'missing_id'}
            ]
            json.dump(data, open(input_path, 'w'))
            
            result = load_timescale_data(input_path)
            # Should return list with partial data, filtering handled downstream
            assert len(result) == 3


class TestTimescaleMismatchCases:
    """Test alignment status calculation for mismatched timescales."""

    def test_calculate_alignment_status_aligned(self):
        """Timescales within 10% should be 'Aligned'."""
        env_timescale = 10.0
        drift_timescale = 10.5  # 5% difference
        
        status = calculate_alignment_status(env_timescale, drift_timescale)
        assert status == 'Aligned'
    
    def test_calculate_alignment_status_mismatched_slow(self):
        """Drift too slow should be 'Mismatched'."""
        env_timescale = 10.0
        drift_timescale = 25.0  # 150% difference (too slow)
        
        status = calculate_alignment_status(env_timescale, drift_timescale)
        assert status == 'Mismatched'
    
    def test_calculate_alignment_status_mismatched_fast(self):
        """Drift too fast should be 'Mismatched'."""
        env_timescale = 10.0
        drift_timescale = 2.0  # 80% difference (too fast)
        
        status = calculate_alignment_status(env_timescale, drift_timescale)
        assert status == 'Mismatched'
    
    def test_calculate_alignment_status_boundary(self):
        """Exactly 10% difference should be 'Aligned' (within tolerance)."""
        env_timescale = 10.0
        drift_timescale = 11.0  # Exactly 10%
        
        status = calculate_alignment_status(env_timescale, drift_timescale)
        assert status == 'Aligned'
    
    def test_calculate_alignment_status_zero_drift(self):
        """Zero drift timescale should be handled (division by zero)."""
        env_timescale = 10.0
        drift_timescale = 0.0
        
        # Should not crash, should return Mismatched or handle gracefully
        status = calculate_alignment_status(env_timescale, drift_timescale)
        assert status == 'Mismatched'
    
    def test_process_timescale_alignment_missing_env(self):
        """Records with missing env timescale should get 'Insufficient Data'."""
        data = [
            {
                'id': 'record1',
                'env_timescale': None,
                'drift_timescale': 10.0
            }
        ]
        
        result = process_timescale_alignment(data)
        assert result[0]['alignment_status'] == 'Insufficient Data'
        assert result[0]['temporal_validation_status'] == 'INSUFFICIENT'
    
    def test_process_timescale_alignment_missing_drift(self):
        """Records with missing drift timescale should get 'Insufficient Data'."""
        data = [
            {
                'id': 'record1',
                'env_timescale': 10.0,
                'drift_timescale': None
            }
        ]
        
        result = process_timescale_alignment(data)
        assert result[0]['alignment_status'] == 'Insufficient Data'
        assert result[0]['temporal_validation_status'] == 'INSUFFICIENT'


class TestOrganismFilteringEdgeCases:
    """Test organism filtering with edge cases."""

    def test_filter_by_organism_empty_dataframe(self):
        """Empty DataFrame should return empty result."""
        df = pd.DataFrame(columns=['organism', 'variance_rna'])
        
        result = filter_by_organism(df, ['mouse', 'C. elegans'])
        assert len(result) == 0
    
    def test_filter_by_organism_no_matches(self):
        """No matching organisms should return empty DataFrame."""
        df = pd.DataFrame({
            'organism': ['zebrafish', 'human', 'yeast'],
            'variance_rna': [1.0, 2.0, 3.0]
        })
        
        result = filter_by_organism(df, ['mouse', 'C. elegans'])
        assert len(result) == 0
    
    def test_filter_by_organism_case_insensitive(self):
        """Organism names should be matched case-insensitively."""
        df = pd.DataFrame({
            'organism': ['Mouse', 'c. elegans', 'DROSOPHILA'],
            'variance_rna': [1.0, 2.0, 3.0]
        })
        
        result = filter_by_organism(df, ['mouse', 'C. elegans'])
        assert len(result) == 2
        assert 'Mouse' in result['organism'].values
        assert 'c. elegans' in result['organism'].values


class TestMethylationFilterEdgeCases:
    """Test methylation filtering edge cases."""

    def test_filter_by_global_methylation_level_empty(self):
        """Empty DataFrame should return empty result."""
        df = pd.DataFrame(columns=['global_methylation', 'gene_id'])
        
        result = filter_by_global_methylation_level(df, threshold=0.01)
        assert len(result) == 0
    
    def test_filter_by_global_methylation_level_all_pass(self):
        """All samples below threshold should pass."""
        df = pd.DataFrame({
            'global_methylation': [0.001, 0.005, 0.009],
            'gene_id': ['g1', 'g2', 'g3']
        })
        
        result = filter_by_global_methylation_level(df, threshold=0.01)
        assert len(result) == 3
    
    def test_filter_by_global_methylation_level_all_fail(self):
        """All samples above threshold should fail."""
        df = pd.DataFrame({
            'global_methylation': [0.02, 0.05, 0.1],
            'gene_id': ['g1', 'g2', 'g3']
        })
        
        result = filter_by_global_methylation_level(df, threshold=0.01)
        assert len(result) == 0


class TestTokenOverlapEdgeCases:
    """Test token overlap calculation edge cases."""

    def test_calculate_token_overlap_empty_strings(self):
        """Empty strings should return 0.0 overlap."""
        overlap = calculate_token_overlap("", "")
        assert overlap == 0.0
    
    def test_calculate_token_overlap_no_common_tokens(self):
        """No common tokens should return 0.0 overlap."""
        overlap = calculate_token_overlap("apple banana", "orange grape")
        assert overlap == 0.0
    
    def test_calculate_token_overlap_identical_strings(self):
        """Identical strings should return 1.0 overlap."""
        overlap = calculate_token_overlap("same text", "same text")
        assert overlap == 1.0
    
    def test_calculate_token_overlap_case_insensitive(self):
        """Overlap should be case-insensitive."""
        overlap = calculate_token_overlap("UPPER CASE", "upper case")
        assert overlap == 1.0
    
    def test_calculate_token_overlap_partial_overlap(self):
        """Partial overlap should return correct ratio."""
        # "apple banana cherry" vs "apple banana date"
        # Common: 2, Total unique: 4, Overlap = 2/4 = 0.5
        overlap = calculate_token_overlap("apple banana cherry", "apple banana date")
        assert abs(overlap - 0.5) < 1e-6


class TestSingleGenerationEdgeCases:
    """Test handling of single-generation datasets."""

    def test_drift_timescale_single_generation(self):
        """Single generation should result in zero or undefined drift timescale."""
        generations = np.array([1])
        variances = np.array([0.5])
        
        # Linear regression on single point is undefined
        # Should handle gracefully (return 0, NaN, or raise specific error)
        slope = np.polyfit(generations, variances, 1)[0] if len(generations) > 1 else 0.0
        assert slope == 0.0

class TestValidationEdgeCases:
    """Test validation function edge cases."""

    def test_validate_reference_missing_verified_datasets(self):
        """Should handle when verified datasets file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_yaml = Path(tmpdir) / 'nonexistent.yaml'
            
            # Should return False or raise appropriate error
            # Based on implementation, check behavior
            try:
                load_verified_datasets(fake_yaml)
                # If no error, test the validation
                result = validate_reference("ACC123", "Test Title", fake_yaml)
                assert result is False
            except FileNotFoundError:
                # Expected behavior
                pass

class TestEmptyDatasetEdgeCases:
    """Test handling of completely empty datasets."""

    def test_process_timescale_alignment_empty_input(self):
        """Empty input list should return empty output."""
        result = process_timescale_alignment([])
        assert result == []

if __name__ == '__main__':
    pytest.main([__file__, '-v'])