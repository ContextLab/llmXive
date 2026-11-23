"""
Contract test for robustness_model_results.json schema
"""

import os
import sys
import json
import pytest
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import get_path


def load_robustness_results() -> Dict[str, Any]:
    """Load robustness model results."""
    results_path = get_path('data/processed/robustness_model_results.json')
    
    if not os.path.exists(results_path):
        pytest.skip(f"Results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)


class TestRobustnessModelSchema:
    """Test schema compliance of robustness_model_results.json"""
    
    @pytest.fixture
    def results(self):
        return load_robustness_results()
    
    def test_required_top_level_keys(self, results):
        """Test that all required top-level keys are present."""
        required_keys = ['linear_regression', 'lasso', 'model_comparison', 'metadata']
        
        for key in required_keys:
            assert key in results, f"Missing required key: {key}"
    
    def test_linear_regression_structure(self, results):
        """Test linear_regression section structure."""
        lr = results['linear_regression']
        
        required_fields = ['r2_cv_mean', 'r2_cv_std', 'r2_full', 'adj_r2_full', 
                         'rmse_full', 'coefficients', 'intercept']
        
        for field in required_fields:
            assert field in lr, f"Missing field in linear_regression: {field}"
        
        # Type checks
        assert isinstance(lr['r2_cv_mean'], (int, float))
        assert isinstance(lr['r2_cv_std'], (int, float))
        assert isinstance(lr['coefficients'], list)
        assert isinstance(lr['intercept'], (int, float))
    
    def test_lasso_structure(self, results):
        """Test lasso section structure."""
        lasso = results['lasso']
        
        required_fields = ['optimal_alpha', 'r2_cv_mean', 'r2_full', 'adj_r2_full',
                         'rmse_full', 'coefficients', 'intercept']
        
        for field in required_fields:
            assert field in lasso, f"Missing field in lasso: {field}"
        
        # Type checks
        assert isinstance(lasso['optimal_alpha'], (int, float))
        assert isinstance(lasso['r2_cv_mean'], (int, float))
        assert isinstance(lasso['coefficients'], list)
    
    def test_model_comparison_structure(self, results):
        """Test model_comparison section structure."""
        comparison = results['model_comparison']
        
        required_fields = ['best_model', 'r2_difference']
        
        for field in required_fields:
            assert field in comparison, f"Missing field in model_comparison: {field}"
        
        # Value checks
        assert comparison['best_model'] in ['linear_regression', 'lasso']
        assert isinstance(comparison['r2_difference'], (int, float))
    
    def test_metadata_structure(self, results):
        """Test metadata section structure."""
        metadata = results['metadata']
        
        required_fields = ['n_samples', 'n_features', 'n_folds', 'feature_names']
        
        for field in required_fields:
            assert field in metadata, f"Missing field in metadata: {field}"
        
        # Type checks
        assert isinstance(metadata['n_samples'], int)
        assert isinstance(metadata['n_features'], int)
        assert isinstance(metadata['n_folds'], int)
        assert isinstance(metadata['feature_names'], list)
    
    def test_r2_range(self, results):
        """Test that R² values are in valid range."""
        lr_r2 = results['linear_regression']['r2_full']
        lasso_r2 = results['lasso']['r2_full']
        
        # R² can be negative for poor models, but typically > -1
        assert lr_r2 > -2, f"Linear R² out of reasonable range: {lr_r2}"
        assert lasso_r2 > -2, f"Lasso R² out of reasonable range: {lasso_r2}"
    
    def test_coefficient_count(self, results):
        """Test that coefficient count matches number of features."""
        n_features = results['metadata']['n_features']
        
        lr_n_coef = len(results['linear_regression']['coefficients'])
        lasso_n_coef = len(results['lasso']['coefficients'])
        
        assert lr_n_coef == n_features, f"Linear coefficients count mismatch: {lr_n_coef} vs {n_features}"
        assert lasso_n_coef == n_features, f"Lasso coefficients count mismatch: {lasso_n_coef} vs {n_features}"
    
    def test_analysis_metadata(self, results):
        """Test that analysis metadata is present."""
        assert 'analysis_type' in results
        assert results['analysis_type'] == 'robustness_modeling'
        
        assert 'input_file' in results
        assert 'parameter_variant' in results
        assert 'timestamp' in results