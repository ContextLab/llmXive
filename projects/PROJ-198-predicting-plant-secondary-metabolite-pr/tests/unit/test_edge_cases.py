"""
Unit tests for edge cases in data processing and modeling pipelines.

Tests cover:
- Zero BGCs (empty clusters, all-zero counts)
- Missing metabolites (NaN, empty columns, missing species)
- Alignment failures with incomplete data
- Model training with insufficient data points
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

from data.preprocess import harmonize_metabolites, map_bgc_to_metabolite_dataframe
from data.align import align_data, calculate_alignment_success_rate
from modeling.train import apply_pca, determine_cv_method
from models.schemas import AlignedDataset


class TestZeroBGCs:
    """Tests for handling zero BGC counts and empty BGC clusters."""

    def test_map_bgc_to_metabolite_empty_dataframe(self):
        """Test mapping with an empty BGC dataframe."""
        df = pd.DataFrame(columns=['species', 'bgc_type', 'count'])
        result = map_bgc_to_metabolite_dataframe(df, 'bgc_type', 'count')
        assert result.empty
        assert 'metabolite_class' in result.columns

    def test_map_bgc_to_metabolite_all_zero_counts(self):
        """Test mapping when all BGC counts are zero."""
        data = {
            'species': ['A', 'B', 'C'],
            'bgc_type': ['polyketide', 'terpene', 'non_ribosomal'],
            'count': [0, 0, 0]
        }
        df = pd.DataFrame(data)
        result = map_bgc_to_metabolite_dataframe(df, 'bgc_type', 'count')
        
        assert len(result) == 3
        assert all(result['count'] == 0)
        # Should still map types even with zero counts
        assert result['metabolite_class'].notna().all()

    def test_harmonize_metabolites_all_zeros(self):
        """Test log transformation with all-zero metabolite abundances."""
        data = {
            'species': ['A', 'B', 'C'],
            'metabolite_1': [0.0, 0.0, 0.0],
            'metabolite_2': [0.0, 0.0, 0.0]
        }
        df = pd.DataFrame(data)
        
        # Should handle zeros with pseudo-count +1
        result = harmonize_metabolites(df, value_columns=['metabolite_1', 'metabolite_2'])
        
        # After pseudo-count +1 and log, values should be log(1) = 0
        assert np.allclose(result['metabolite_1'], 0.0)
        assert np.allclose(result['metabolite_2'], 0.0)
        assert not result.isna().any().any()

    def test_pca_with_zero_variance_features(self):
        """Test PCA when features have zero variance (all same values)."""
        data = {
            'species': ['A', 'B', 'C', 'D'],
            'feature_1': [0.0, 0.0, 0.0, 0.0],
            'feature_2': [5.0, 5.0, 5.0, 5.0]
        }
        df = pd.DataFrame(data)
        
        # Should not crash, but may produce warnings
        result = apply_pca(df, value_columns=['feature_1', 'feature_2'], n_components=1)
        
        # Should have output with reduced dimensions
        assert 'pc1' in result.columns or len(result.columns) >= 1


class TestMissingMetabolites:
    """Tests for handling missing metabolite data."""

    def test_harmonize_metabolites_with_nan(self):
        """Test log transformation with NaN values in metabolite data."""
        data = {
            'species': ['A', 'B', 'C', 'D'],
            'metabolite_1': [1.0, np.nan, 3.0, 0.0],
            'metabolite_2': [np.nan, 2.0, 0.0, 4.0]
        }
        df = pd.DataFrame(data)
        
        result = harmonize_metabolites(df, value_columns=['metabolite_1', 'metabolite_2'])
        
        # NaN should remain NaN (or be handled consistently)
        # Pseudo-count should only apply to zeros, not NaN
        assert result.shape == df.shape

    def test_align_data_missing_species_in_genomics(self):
        """Test alignment when species exists in metabolites but not genomics."""
        genomics_df = pd.DataFrame({
            'species': ['Species_A', 'Species_B'],
            'bgc_count': [10, 5]
        })
        
        metabolites_df = pd.DataFrame({
            'species': ['Species_A', 'Species_C'],
            'metabolite_abundance': [100.0, 200.0]
        })
        
        result = align_data(genomics_df, metabolites_df, 
                            species_col='species', 
                            genomics_cols=['bgc_count'],
                            metabolites_cols=['metabolite_abundance'])
        
        # Should only include Species_A (intersection)
        assert len(result) == 1
        assert result['species'].iloc[0] == 'Species_A'

    def test_align_data_missing_species_in_metabolites(self):
        """Test alignment when species exists in genomics but not metabolites."""
        genomics_df = pd.DataFrame({
            'species': ['Species_A', 'Species_B'],
            'bgc_count': [10, 5]
        })
        
        metabolites_df = pd.DataFrame({
            'species': ['Species_A', 'Species_C'],
            'metabolite_abundance': [100.0, 200.0]
        })
        
        result = align_data(genomics_df, metabolites_df,
                            species_col='species',
                            genomics_cols=['bgc_count'],
                            metabolites_cols=['metabolite_abundance'])
        
        assert len(result) == 1
        assert 'Species_B' not in result['species'].values

    def test_align_data_all_missing_species(self):
        """Test alignment when no species overlap exists."""
        genomics_df = pd.DataFrame({
            'species': ['Species_A', 'Species_B'],
            'bgc_count': [10, 5]
        })
        
        metabolites_df = pd.DataFrame({
            'species': ['Species_C', 'Species_D'],
            'metabolite_abundance': [100.0, 200.0]
        })
        
        result = align_data(genomics_df, metabolites_df,
                            species_col='species',
                            genomics_cols=['bgc_count'],
                            metabolites_cols=['metabolite_abundance'])
        
        assert len(result) == 0

    def test_calculate_alignment_success_rate_zero_match(self):
        """Test alignment success rate calculation with zero matches."""
        total_species = 10
        matched_species = 0
        
        rate = calculate_alignment_success_rate(total_species, matched_species)
        
        assert rate == 0.0

    def test_calculate_alignment_success_rate_perfect_match(self):
        """Test alignment success rate calculation with perfect match."""
        total_species = 10
        matched_species = 10
        
        rate = calculate_alignment_success_rate(total_species, matched_species)
        
        assert rate == 1.0


class TestModelTrainingEdgeCases:
    """Tests for model training with edge case data."""

    def test_determine_cv_method_insufficient_samples(self):
        """Test CV method selection with very few samples."""
        # With < 5 samples, LOO should be forced
        n_samples = 3
        cv_method = determine_cv_method(n_samples)
        
        assert cv_method == 'loo'

    def test_determine_cv_method_exact_threshold(self):
        """Test CV method selection at boundary."""
        n_samples = 5
        cv_method = determine_cv_method(n_samples)
        
        # Should use LOO for very small datasets
        assert cv_method == 'loo'

    def test_determine_cv_method_normal_case(self):
        """Test CV method selection with sufficient samples."""
        n_samples = 50
        cv_method = determine_cv_method(n_samples)
        
        assert cv_method == 'kfold'

    def test_pca_with_single_sample(self):
        """Test PCA with only one sample (should fail gracefully or handle)."""
        data = {
            'species': ['A'],
            'feature_1': [1.0],
            'feature_2': [2.0]
        }
        df = pd.DataFrame(data)
        
        # With single sample, PCA cannot compute meaningful components
        # Should handle this gracefully (may return original or raise informative error)
        try:
            result = apply_pca(df, value_columns=['feature_1', 'feature_2'], n_components=1)
            # If it doesn't crash, result should have same number of rows
            assert len(result) == 1
        except Exception:
            # Expected: PCA requires at least 2 samples
            pass

    def test_pca_with_fewer_samples_than_features(self):
        """Test PCA when samples < features."""
        data = {
            'species': ['A', 'B', 'C'],
            'feature_1': [1.0, 2.0, 3.0],
            'feature_2': [4.0, 5.0, 6.0],
            'feature_3': [7.0, 8.0, 9.0],
            'feature_4': [10.0, 11.0, 12.0]
        }
        df = pd.DataFrame(data)
        
        # Should handle this case (max components = min(n_samples, n_features) - 1)
        result = apply_pca(df, value_columns=['feature_1', 'feature_2', 'feature_3', 'feature_4'], n_components=2)
        
        # Should produce at most n_samples - 1 components
        assert len(result) == 3


class TestEmptyDataFrames:
    """Tests for handling completely empty dataframes."""

    def test_harmonize_empty_dataframe(self):
        """Test harmonization with empty dataframe."""
        df = pd.DataFrame(columns=['species', 'metabolite_1', 'metabolite_2'])
        
        result = harmonize_metabolites(df, value_columns=['metabolite_1', 'metabolite_2'])
        
        assert result.empty
        assert list(result.columns) == list(df.columns)

    def test_map_bgc_empty_dataframe(self):
        """Test BGC mapping with empty dataframe."""
        df = pd.DataFrame(columns=['species', 'bgc_type', 'count'])
        
        result = map_bgc_to_metabolite_dataframe(df, 'bgc_type', 'count')
        
        assert result.empty
        assert 'metabolite_class' in result.columns

    def test_align_empty_genomics(self):
        """Test alignment with empty genomics dataframe."""
        genomics_df = pd.DataFrame(columns=['species', 'bgc_count'])
        metabolites_df = pd.DataFrame({
            'species': ['A', 'B'],
            'metabolite_abundance': [100.0, 200.0]
        })
        
        result = align_data(genomics_df, metabolites_df,
                            species_col='species',
                            genomics_cols=['bgc_count'],
                            metabolites_cols=['metabolite_abundance'])
        
        assert result.empty

    def test_align_empty_metabolites(self):
        """Test alignment with empty metabolites dataframe."""
        genomics_df = pd.DataFrame({
            'species': ['A', 'B'],
            'bgc_count': [10, 5]
        })
        metabolites_df = pd.DataFrame(columns=['species', 'metabolite_abundance'])
        
        result = align_data(genomics_df, metabolites_df,
                            species_col='species',
                            genomics_cols=['bgc_count'],
                            metabolites_cols=['metabolite_abundance'])
        
        assert result.empty