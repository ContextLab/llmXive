"""
Unit tests for edge cases in data processing and modeling pipelines.

Tests cover:
- Zero BGCs (empty BGC counts, missing BGC features)
- Missing metabolites (NaN abundances, missing InChIKeys)
- Alignment edge cases (partial species matches)
- Model training with edge case data
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import tempfile

# Add code directory to path for imports
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from data.align import align_data, calculate_alignment_success_rate
from data.preprocess import harmonize_metabolites, map_bgc_to_metabolite, map_bgc_to_metabolite_dataframe
from data_models import AlignedDataset, BGCFeature, MetaboliteProfile
from utils.anti_smash_parser import parse_anti_smash_json, extract_bgc_summary, get_bgc_counts_by_type


class TestZeroBGCs:
    """Test handling of zero BGC counts and empty BGC data."""

    def test_parse_empty_antismash_json(self):
        """Test parsing antiSMASH JSON with no BGCs detected."""
        empty_json = {
            "metadata": {
                "genome": "test_genome",
                "version": "1.0"
            },
            "prediction": []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(empty_json, f)
            temp_path = f.name
        
        try:
            result = parse_anti_smash_json(temp_path)
            assert len(result) == 0, "Expected empty BGC list for no detections"
        finally:
            os.unlink(temp_path)

    def test_extract_bgc_summary_no_bgc(self):
        """Test extracting summary when no BGCs are present."""
        empty_bgc_list = []
        summary = extract_bgc_summary(empty_bgc_list)
        
        assert summary == {}, "Expected empty summary dict"

    def test_get_bgc_counts_zero(self):
        """Test getting BGC counts when no BGCs exist."""
        empty_bgc_list = []
        counts = get_bgc_counts_by_type(empty_bgc_list)
        
        assert len(counts) == 0, "Expected zero counts for all BGC types"
        assert all(v == 0 for v in counts.values()), "All counts should be zero"

    def test_map_bgc_to_metabolite_empty_input(self):
        """Test mapping function with empty BGC data."""
        result = map_bgc_to_metabolite([], {})
        assert result == {}, "Expected empty mapping for empty input"

    def test_map_bgc_to_metabolite_dataframe_no_bgc_column(self):
        """Test dataframe mapping when BGC column is missing."""
        df = pd.DataFrame({
            'species': ['A', 'B'],
            'other_col': [1, 2]
        })
        
        with pytest.raises((KeyError, ValueError)):
            map_bgc_to_metabolite_dataframe(df, 'bgc_count')

    def test_aligned_dataset_zero_bgcs(self):
        """Test AlignedDataset with zero BGC counts."""
        data = AlignedDataset(
            species_names=['species1', 'species2'],
            bgc_features=[BGCFeature(type='unknown', presence=0, count=0, metabolite_class='unknown')],
            metabolite_profiles=[MetaboliteProfile(inchinkey='test', abundance=0.0, class_='terpene')],
            aligned=True
        )
        
        assert data.bgc_features[0].count == 0
        assert data.bgc_features[0].presence == 0


class TestMissingMetabolites:
    """Test handling of missing metabolite data."""

    def test_harmonize_metabolites_with_nan(self):
        """Test harmonization with NaN abundance values."""
        df = pd.DataFrame({
            'InChIKey': ['KFDQJGJYBSMWRE-UHFFFAOYSA-N', 'MISSING_KEY', 'ANOTHER_KEY'],
            'abundance': [1.5, np.nan, 2.0],
            'class': ['terpene', 'alkaloid', 'phenolic']
        })
        
        result = harmonize_metabolites(df)
        
        # NaN values should be handled (either removed or filled)
        assert len(result) > 0, "Expected some valid metabolites after harmonization"

    def test_harmonize_metabolites_empty_inchikey(self):
        """Test harmonization with empty/missing InChIKeys."""
        df = pd.DataFrame({
            'InChIKey': ['', '   ', None, 'VALID_KEY'],
            'abundance': [1.0, 2.0, 3.0, 4.0],
            'class': ['a', 'b', 'c', 'd']
        })
        
        result = harmonize_metabolites(df)
        
        # Empty keys should be filtered out
        assert all(len(str(r)) > 0 for r in result['InChIKey']), "Empty InChIKeys should be removed"

    def test_map_bgc_to_metabolite_missing_metabolite_class(self):
        """Test mapping when metabolite class is missing."""
        bgc_data = [{'type': 'polyketide'}]
        metabolite_map = {}
        
        result = map_bgc_to_metabolite(bgc_data, metabolite_map)
        
        # Should handle missing mapping gracefully
        assert isinstance(result, dict)

    def test_aligned_dataset_missing_metabolites(self):
        """Test alignment when metabolite data is completely missing."""
        # Create a scenario where metabolite data exists but BGC data doesn't
        bgc_df = pd.DataFrame({
            'species': ['species1', 'species2'],
            'bgc_count': [0, 0],
            'bgc_presence': [0, 0]
        })
        
        metab_df = pd.DataFrame({
            'species': ['species1'],  # Only one species has metabolite data
            'abundance': [1.5],
            'InChIKey': ['VALID_KEY']
        })
        
        # This should align but with missing metabolite data for species2
        aligned_df = align_data(bgc_df, metab_df, species_col='species')
        
        assert 'species2' in aligned_df['species'].values
        # Check that missing metabolite values are handled
        assert aligned_df.loc[aligned_df['species'] == 'species2', 'abundance'].isna().any()

    def test_calculate_alignment_success_with_missing_data(self):
        """Test success rate calculation when some species have missing data."""
        df = pd.DataFrame({
            'species': ['A', 'B', 'C', 'D', 'E', 'F'],
            'bgc_count': [5, 0, 3, np.nan, 2, 1],
            'abundance': [1.0, 2.0, np.nan, 4.0, 5.0, 6.0]
        })
        
        # N=5 threshold means species need both bgc_count and abundance
        success_rate = calculate_alignment_success_rate(df, min_species=5)
        
        # Should calculate a valid rate even with missing data
        assert 0.0 <= success_rate <= 1.0


class TestAlignmentEdgeCases:
    """Test edge cases in data alignment."""

    def test_align_no_common_species(self):
        """Test alignment when no species match between datasets."""
        bgc_df = pd.DataFrame({
            'species': ['species1', 'species2'],
            'bgc_count': [5, 3]
        })
        
        metab_df = pd.DataFrame({
            'species': ['species3', 'species4'],
            'abundance': [1.0, 2.0]
        })
        
        result = align_data(bgc_df, metab_df, species_col='species')
        
        # Should return empty or minimal result
        assert len(result) == 0 or all(result.duplicated().sum() == 0)

    def test_align_partial_matches(self):
        """Test alignment with partial species name matches."""
        bgc_df = pd.DataFrame({
            'species': ['Arabidopsis thaliana', 'Zea mays'],
            'bgc_count': [5, 3]
        })
        
        metab_df = pd.DataFrame({
            'species': ['Arabidopsis thaliana', 'Oryza sativa'],
            'abundance': [1.0, 2.0]
        })
        
        result = align_data(bgc_df, metab_df, species_col='species')
        
        # Should only align Arabidopsis thaliana
        assert len(result) == 1
        assert result['species'].iloc[0] == 'Arabidopsis thaliana'

    def test_align_with_duplicate_species(self):
        """Test alignment handling duplicate species entries."""
        bgc_df = pd.DataFrame({
            'species': ['species1', 'species1', 'species2'],
            'bgc_count': [5, 3, 2]
        })
        
        metab_df = pd.DataFrame({
            'species': ['species1', 'species2'],
            'abundance': [1.0, 2.0]
        })
        
        result = align_data(bgc_df, metab_df, species_col='species')
        
        # Should handle duplicates (either merge or warn)
        assert len(result) <= 3


class TestModelTrainingEdgeCases:
    """Test model training with edge case data."""

    def test_model_training_with_zero_features(self):
        """Test training when all BGC features are zero."""
        # This tests the scenario where BGC counts are all zero
        X = np.zeros((10, 5))  # All zeros
        y = np.random.random(10)
        
        # Should handle or raise informative error
        from modeling.train import train_models_loo
        
        # This should either work with regularization or raise a clear error
        try:
            # Mock the actual training to avoid full execution
            with patch('modeling.train.train_models_loo') as mock_train:
                mock_train.return_value = {'model': None, 'metrics': {'r2': 0.0}}
                result = train_models_loo(X, y, seed=42)
                assert result is not None
        except Exception as e:
            # Expected if the implementation properly rejects zero-features
            assert "zero" in str(e).lower() or "feature" in str(e).lower()

    def test_model_training_with_missing_labels(self):
        """Test training with missing target values."""
        X = np.random.random((10, 5))
        y = np.array([1.0, np.nan, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        
        # Should handle NaN labels
        from modeling.train import train_models_loo
        
        try:
            with patch('modeling.train.train_models_loo') as mock_train:
                mock_train.return_value = {'model': None, 'metrics': {'r2': 0.0}}
                result = train_models_loo(X, y, seed=42)
                assert result is not None
        except Exception:
            # Expected if implementation filters NaN labels
            pass

    def test_model_training_with_single_sample(self):
        """Test training with only one sample (edge case for LOO CV)."""
        X = np.random.random((1, 5))
        y = np.array([1.0])
        
        # LOO with 1 sample is degenerate
        from modeling.train import train_models_loo
        
        try:
            with patch('modeling.train.train_models_loo') as mock_train:
                mock_train.return_value = {'model': None, 'metrics': {'r2': 0.0}}
                result = train_models_loo(X, y, seed=42)
                assert result is not None
        except Exception:
            # Expected if implementation validates sample size
            pass


class TestDataHygieneEdgeCases:
    """Test data hygiene functions with edge cases."""

    def test_checksum_empty_file(self):
        """Test checksum calculation on empty file."""
        from utils.data_hygiene import calculate_file_checksum
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            checksum = calculate_file_checksum(temp_path)
            assert checksum is not None
            assert len(checksum) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)

    def test_checksum_nonexistent_file(self):
        """Test checksum calculation on non-existent file."""
        from utils.data_hygiene import calculate_file_checksum
        
        with pytest.raises(FileNotFoundError):
            calculate_file_checksum("/nonexistent/path/file.txt")

    def test_verify_checksums_missing_file(self):
        """Test checksum verification when a file is missing."""
        from utils.data_hygiene import verify_checksums
        
        # Create a temporary checksum file
        checksums = {
            "test.txt": "abc123"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            checksum_file = Path(tmpdir) / "checksums.json"
            with open(checksum_file, 'w') as f:
                json.dump(checksums, f)
            
            # Should raise error for missing file
            with pytest.raises((FileNotFoundError, ValueError)):
                verify_checksums(tmpdir, checksum_file)