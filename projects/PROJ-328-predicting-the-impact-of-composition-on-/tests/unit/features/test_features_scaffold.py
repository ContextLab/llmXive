"""
Unit tests for the features module scaffold.
Verifies that all required components exist and are importable.
"""
import pytest
import numpy as np
from pathlib import Path
import json
import os

# Ensure we can import from the project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from features.transformer import CLRTransformer
from features.descriptor_engine import DescriptorEngine
from features.collinearity import calculate_vif, get_collinear_features, save_vif_report

class TestCLRTransformer:
    def test_init(self):
        transformer = CLRTransformer()
        assert transformer.pseudo_count == 1e-6

    def test_transform_basic(self):
        transformer = CLRTransformer()
        # Simple composition that sums to 1
        X = np.array([[0.5, 0.3, 0.2]])
        result = transformer.transform(X)
        assert result.shape == (1, 3)
        # CLR transform should result in sums close to 0
        assert np.abs(result.sum()) < 1e-6

    def test_transform_multiple_samples(self):
        transformer = CLRTransformer()
        X = np.array([
            [0.5, 0.3, 0.2],
            [0.7, 0.2, 0.1],
            [0.4, 0.4, 0.2]
        ])
        result = transformer.transform(X)
        assert result.shape == (3, 3)
        
        # Each row should sum to ~0
        row_sums = result.sum(axis=1)
        assert np.allclose(row_sums, 0, atol=1e-6)

    def test_transform_with_zeros(self):
        transformer = CLRTransformer(pseudo_count=1e-6)
        # Data with a zero that should be handled by pseudo_count
        X = np.array([[0.5, 0.5, 0.0]])
        result = transformer.transform(X)
        assert result.shape == (1, 3)
        assert not np.any(np.isnan(result))

    def test_no_nan_inf(self):
        transformer = CLRTransformer()
        X = np.random.dirichlet([1, 1, 1], size=10)
        result = transformer.transform(X)
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))

class TestDescriptorEngine:
    def test_init(self):
        engine = DescriptorEngine()
        assert engine.element_cache == {}

    def test_compute_weighted_mean_atomic_mass(self):
        engine = DescriptorEngine()
        # SAC305: Sn (118.71), Ag (107.87), Cu (63.55)
        composition = {'Sn': 0.965, 'Ag': 0.030, 'Cu': 0.005}
        result = engine.compute_weighted_mean_atomic_mass(composition)
        assert result > 0
        # Should be close to Sn's atomic mass since it dominates
        assert 110 < result < 120

    def test_compute_all_descriptors(self):
        engine = DescriptorEngine()
        composition = {'Sn': 0.965, 'Ag': 0.030, 'Cu': 0.005}
        result = engine.compute_all_descriptors(composition)
        
        assert 'weighted_mean_atomic_mass' in result
        assert 'electronegativity_variance' in result
        assert 'atomic_radius_variance' in result
        assert 'weighted_avg_melting_point' in result
        assert 'valence_electron_concentration' in result
        
        # All should be numeric
        for key, value in result.items():
            assert isinstance(value, (int, float))

class TestCollinearity:
    def test_calculate_vif_simple(self):
        import pandas as pd
        np.random.seed(42)
        n = 50
        df = pd.DataFrame({
            'x1': np.random.normal(0, 1, n),
            'x2': np.random.normal(0, 1, n),
            'x3': np.random.normal(0, 1, n)
        })
        
        vif_results = calculate_vif(df, ['x1', 'x2', 'x3'])
        
        # Independent features should have VIF close to 1
        for feature, vif in vif_results.items():
            assert 0.9 < vif < 2.0, f"VIF for {feature} should be close to 1: {vif}"

    def test_calculate_vif_collinear(self):
        import pandas as pd
        np.random.seed(42)
        n = 50
        x1 = np.random.normal(0, 1, n)
        x2 = x1 * 0.95 + np.random.normal(0, 0.05, n)  # Highly correlated
        
        df = pd.DataFrame({'x1': x1, 'x2': x2})
        
        vif_results = calculate_vif(df, ['x1', 'x2'])
        
        # Both should have high VIF
        assert vif_results['x1'] > 5.0 or vif_results['x2'] > 5.0

    def test_get_collinear_features(self):
        vif_results = {
            'x1': 1.2,
            'x2': 6.5,
            'x3': 2.1,
            'x4': 8.0
        }
        
        collinear = get_collinear_features(vif_results, threshold=5.0)
        assert set(collinear) == {'x2', 'x4'}

    def test_save_vif_report(self, tmp_path):
        import yaml
        vif_results = {
            'x1': 1.2,
            'x2': 6.5
        }
        
        output_file = tmp_path / "vif_report.yaml"
        save_vif_report(vif_results, str(output_file), threshold=5.0)
        
        assert output_file.exists()
        
        with open(output_file) as f:
            report = yaml.safe_load(f)
        
        assert 'vif_scores' in report
        assert 'collinear_features' in report
        assert report['is_collinear'] is True

class TestModuleStructure:
    def test_imports_exist(self):
        """Verify that all expected imports from __init__.py work."""
        # These should not raise ImportError
        from features import CLRTransformer, DescriptorEngine, calculate_vif, get_collinear_features
        
        # Verify they are the correct classes/functions
        assert isinstance(CLRTransformer, type)
        assert isinstance(DescriptorEngine, type)
        assert callable(calculate_vif)
        assert callable(get_collinear_features)

    def test_main_functions_exist(self):
        """Verify that main functions exist in each module."""
        from features.transformer import main as transformer_main
        from features.descriptor_engine import main as descriptor_main
        from features.collinearity import main as collinearity_main
        
        assert callable(transformer_main)
        assert callable(descriptor_main)
        assert callable(collinearity_main)