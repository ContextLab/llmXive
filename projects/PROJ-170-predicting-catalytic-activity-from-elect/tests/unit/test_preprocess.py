import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

try:
    from preprocess import (
        normalize_composition, normalize_facet, normalize_condition,
        build_stoichiometry_vocabulary, composition_to_stoich_vector,
        perform_knn_imputation, scale_features, generate_catalyst_ids,
        validate_schema_compliance, get_numeric_feature_columns
    )
    from config import get_data_path, get_output_path
except ImportError:
    from code.preprocess import (
        normalize_composition, normalize_facet, normalize_condition,
        build_stoichiometry_vocabulary, composition_to_stoich_vector,
        perform_knn_imputation, scale_features, generate_catalyst_ids,
        validate_schema_compliance, get_numeric_feature_columns
    )
    from code.config import get_data_path, get_output_path


class TestNormalization:
    """Test composition/facet/condition normalization."""
    
    def test_normalize_composition(self):
        assert normalize_composition("Fe2O3") == "fe2o3"
        assert normalize_composition("  Cu  ") == "cu"
        assert normalize_composition("CuO") == "cuo"
    
    def test_normalize_facet(self):
        assert normalize_facet("(111)") == "(111)"
        assert normalize_facet("  100  ") == "100"
    
    def test_normalize_condition(self):
        assert normalize_condition("HIGH TEMP") == "high temp"
        assert normalize_condition("  AMBIENT  ") == "ambient"


class TestStoichiometryVocabulary:
    """Test stoichiometry vocabulary building."""
    
    def test_build_vocabulary(self):
        df = pd.DataFrame({
            'composition': ['Fe2O3', 'CuO', 'Fe3O4']
        })
        vocab = build_stoichiometry_vocabulary(df)
        
        assert 'Fe' in vocab or 'fe' in vocab.keys() or any('fe' in str(k).lower() for k in vocab.keys())
        assert isinstance(vocab, dict)
        assert len(vocab) > 0
    
    def test_composition_to_vector(self):
        vocab = {'Fe': 0, 'O': 1, 'Cu': 2}
        vector = composition_to_stoich_vector('Fe2O3', vocab, 3)
        
        assert vector.shape == (3,)
        assert np.sum(vector) > 0
        assert np.isfinite(vector).all()


class TestKNNImputation:
    """Test k-NN imputation functionality."""
    
    def test_knn_imputation_no_missing(self):
        """Test imputation when no values are missing."""
        df = pd.DataFrame({
            'composition': ['Fe2O3', 'CuO', 'Fe3O4', 'Cu2O', 'FeO'],
            'd_band_center': [-2.0, -1.5, -2.2, -1.6, -1.9],
            'p_band_center': [-5.0, -4.5, -5.2, -4.6, -4.9],
            'bader_charges': [1.0, 0.9, 1.1, 0.95, 1.05],
            'activation_barrier': [1.5, 1.2, 1.6, 1.3, 1.4],
            'reaction_energy': [-0.5, -0.3, -0.6, -0.4, -0.5],
            'experimental_tof': [10.0, 20.0, 15.0, 25.0, 12.0]
        })
        
        df_imputed, stats = perform_knn_imputation(df, k=3)
        
        assert len(df_imputed) == len(df)
        assert 'is_imputed' in df_imputed.columns
        assert 'excluded_from_training' in df_imputed.columns
        assert stats['entries_with_missing'] == 0
    
    def test_knn_imputation_with_missing(self):
        """Test imputation when values are missing."""
        df = pd.DataFrame({
            'composition': ['Fe2O3', 'CuO', 'Fe3O4', 'Cu2O', 'FeO'],
            'd_band_center': [-2.0, np.nan, -2.2, -1.6, -1.9],
            'p_band_center': [-5.0, -4.5, -5.2, -4.6, -4.9],
            'bader_charges': [1.0, 0.9, 1.1, 0.95, 1.05],
            'activation_barrier': [1.5, 1.2, 1.6, 1.3, 1.4],
            'reaction_energy': [-0.5, -0.3, -0.6, -0.4, -0.5],
            'experimental_tof': [10.0, 20.0, 15.0, 25.0, 12.0]
        })
        
        df_imputed, stats = perform_knn_imputation(df, k=3)
        
        assert stats['entries_with_missing'] > 0
        # After imputation, no NaN should remain in descriptors
        descriptor_cols = ['d_band_center', 'p_band_center', 'bader_charges', 
                         'activation_barrier', 'reaction_energy']
        for col in descriptor_cols:
            assert df_imputed[col].isna().sum() == 0 or df_imputed[~df_imputed['excluded_from_training']][col].isna().sum() == 0
    
    def test_insufficient_neighbors_exclusion(self):
        """Test that entries with insufficient neighbors are excluded."""
        df = pd.DataFrame({
            'composition': ['Fe2O3', 'CuO'],
            'd_band_center': [-2.0, np.nan],
            'p_band_center': [-5.0, -4.5],
            'bader_charges': [1.0, 0.9],
            'activation_barrier': [1.5, 1.2],
            'reaction_energy': [-0.5, -0.3],
            'experimental_tof': [10.0, 20.0]
        })
        
        df_imputed, stats = perform_knn_imputation(df, k=5)
        
        # With only 2 entries, k=5 neighbors cannot be found
        assert stats['entries_excluded_insufficient_neighbors'] > 0


class TestScaling:
    """Test feature scaling."""
    
    def test_scale_features(self):
        df = pd.DataFrame({
            'feature1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'feature2': [10.0, 20.0, 30.0, 40.0, 50.0],
            'experimental_tof': [100.0, 200.0, 300.0, 400.0, 500.0]
        })
        
        feature_cols = ['feature1', 'feature2']
        df_scaled, scaler = scale_features(df, feature_cols)
        
        # Check that scaled features have zero mean and unit variance
        for col in feature_cols:
            mean = df_scaled[col].mean()
            std = df_scaled[col].std()
            assert np.isclose(mean, 0.0, atol=1e-10)
            assert np.isclose(std, 1.0, atol=1e-10)
        
        # Target should not be scaled
        assert df_scaled['experimental_tof'].mean() != 0.0


class TestCatalystIDGeneration:
    """Test catalyst ID generation."""
    
    def test_generate_catalyst_ids(self):
        df = pd.DataFrame({
            'composition': ['Fe2O3', 'CuO'],
            'surface_facet': ['111', '100'],
            'synthesis_condition': ['high_temp', 'ambient']
        })
        
        df_with_ids = generate_catalyst_ids(df)
        
        assert 'catalyst_id' in df_with_ids.columns
        assert len(df_with_ids['catalyst_id']) == 2
        assert len(df_with_ids['catalyst_id'].unique()) == 2
        assert all(isinstance(cid, str) and len(cid) == 16 for cid in df_with_ids['catalyst_id'])


class TestSchemaValidation:
    """Test schema compliance validation."""
    
    def test_schema_validation_pass(self):
        df = pd.DataFrame({
            'catalyst_id': ['abc123', 'def456'],
            'composition': ['Fe2O3', 'CuO'],
            'surface_facet': ['111', '100'],
            'synthesis_condition': ['high_temp', 'ambient'],
            'd_band_center': [-2.0, -1.5],
            'experimental_tof': [10.0, 20.0],
            'is_imputed': [False, False],
            'excluded_from_training': [False, False]
        })
        
        assert validate_schema_compliance(df) is True
    
    def test_schema_validation_missing_field(self):
        df = pd.DataFrame({
            'catalyst_id': ['abc123', 'def456'],
            'composition': ['Fe2O3', 'CuO'],
            # Missing required fields
            'experimental_tof': [10.0, 20.0],
            'is_imputed': [False, False],
            'excluded_from_training': [False, False]
        })
        
        assert validate_schema_compliance(df) is False
    
    def test_schema_validation_nan_target(self):
        df = pd.DataFrame({
            'catalyst_id': ['abc123', 'def456'],
            'composition': ['Fe2O3', 'CuO'],
            'surface_facet': ['111', '100'],
            'synthesis_condition': ['high_temp', 'ambient'],
            'd_band_center': [-2.0, -1.5],
            'experimental_tof': [10.0, np.nan],
            'is_imputed': [False, False],
            'excluded_from_training': [False, False]
        })
        
        assert validate_schema_compliance(df) is False


class TestTargetNoNaN:
    """Test that experimental_tof has no NaN values."""
    
    def test_no_nan_in_target(self):
        """Verify that after preprocessing, target has no NaN."""
        df = pd.DataFrame({
            'composition': ['Fe2O3', 'CuO', 'Fe3O4'],
            'd_band_center': [-2.0, -1.5, -2.2],
            'p_band_center': [-5.0, -4.5, -5.2],
            'bader_charges': [1.0, 0.9, 1.1],
            'activation_barrier': [1.5, 1.2, 1.6],
            'reaction_energy': [-0.5, -0.3, -0.6],
            'experimental_tof': [10.0, 20.0, 15.0]
        })
        
        df_imputed, _ = perform_knn_imputation(df, k=2)
        
        # After imputation, no NaN should remain in target
        assert df_imputed['experimental_tof'].isna().sum() == 0