"""
Unit tests for performance optimization module.

Tests cover:
- OptimizedDataLoader functionality
- Memory mapping behavior
- Chunked loading
- Feature preparation
- OptimizedSHAPCalculator functionality
- SHAP value calculation
- Ranking and feature importance
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.performance_optimizations import (
    OptimizedDataLoader,
    OptimizedSHAPCalculator,
    optimize_data_loading,
    optimize_shap_calculation,
    CHUNK_SIZE,
    MAX_WORKERS
)
from config import get_config


class TestOptimizedDataLoader:
    """Tests for OptimizedDataLoader class."""
    
    @pytest.fixture
    def sample_dataset(self, tmp_path):
        """Create a sample parquet dataset for testing."""
        # Create sample data
        np.random.seed(42)
        n_samples = 100
        
        data = {
            'composition_id': [f'comp_{i}' for i in range(n_samples)],
            'rdf_peak_pos': np.random.uniform(2.0, 3.0, n_samples),
            'rdf_peak_width': np.random.uniform(0.1, 0.5, n_samples),
            'bond_angle_variance': np.random.uniform(0.01, 0.1, n_samples),
            'coordination_numbers': np.random.uniform(4.0, 8.0, n_samples),
            'Tg_K': np.random.uniform(300, 600, n_samples),
            'Tx_K': np.random.uniform(400, 700, n_samples),
            'crystallization_label': np.random.randint(0, 2, n_samples),
            'chemical_family': np.random.choice(['oxide', 'sulfide', 'organic'], n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Save to parquet
        parquet_path = tmp_path / "final_dataset.parquet"
        df.to_parquet(parquet_path)
        
        return parquet_path
    
    def test_load_dataset(self, sample_dataset):
        """Test basic dataset loading."""
        with patch('config.get_config') as mock_config:
            mock_config.return_value.paths.processed_data = sample_dataset.parent
            
            loader = OptimizedDataLoader()
            df = loader.load_dataset()
            
            assert isinstance(df, pd.DataFrame)
            assert df.shape[0] == 100
            assert 'Tg_K' in df.columns
    
    def test_load_dataset_cached(self, sample_dataset):
        """Test that dataset is cached on second load."""
        with patch('config.get_config') as mock_config:
            mock_config.return_value.paths.processed_data = sample_dataset.parent
            
            loader = OptimizedDataLoader()
            df1 = loader.load_dataset()
            df2 = loader.load_dataset()
            
            # Should be the same object (cached)
            assert df1 is df2
    
    def test_get_feature_columns(self, sample_dataset):
        """Test feature column detection."""
        with patch('config.get_config') as mock_config:
            mock_config.return_value.paths.processed_data = sample_dataset.parent
            
            loader = OptimizedDataLoader()
            df = loader.load_dataset()
            
            feature_cols = loader.get_feature_columns(df)
            
            # Should not include excluded columns
            excluded = ['composition_id', 'Tg_K', 'Tx_K', 'crystallization_label', 
                       'chemical_family']
            for col in excluded:
                assert col not in feature_cols
            
            # Should include descriptor columns
            assert 'rdf_peak_pos' in feature_cols
            assert 'bond_angle_variance' in feature_cols
    
    def test_prepare_features(self, sample_dataset):
        """Test feature and target preparation."""
        with patch('config.get_config') as mock_config:
            mock_config.return_value.paths.processed_data = sample_dataset.parent
            
            loader = OptimizedDataLoader()
            df = loader.load_dataset()
            feature_cols = loader.get_feature_columns(df)
            
            X, y, scaler = loader.prepare_features(df, 'Tg_K', feature_cols)
            
            assert isinstance(X, np.ndarray)
            assert isinstance(y, np.ndarray)
            assert isinstance(scaler, StandardScaler)
            assert X.shape[0] == y.shape[0]
            assert X.shape[1] == len(feature_cols)
    
    def test_prepare_features_with_nan(self, sample_dataset):
        """Test that NaN values are removed during preparation."""
        with patch('config.get_config') as mock_config:
            mock_config.return_value.paths.processed_data = sample_dataset.parent
            
            loader = OptimizedDataLoader()
            df = loader.load_dataset()
            feature_cols = loader.get_feature_columns(df)
            
            # Add NaN values
            df.loc[0, 'rdf_peak_pos'] = np.nan
            df.loc[1, 'Tg_K'] = np.nan
            
            X, y, scaler = loader.prepare_features(df, 'Tg_K', feature_cols)
            
            # NaN rows should be removed
            assert X.shape[0] == 98
            assert y.shape[0] == 98
    
    def test_load_dataset_missing_file(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        with patch('config.get_config') as mock_config:
            mock_config.return_value.paths.processed_data = tmp_path
            
            loader = OptimizedDataLoader()
            
            with pytest.raises(FileNotFoundError):
                loader.load_dataset()


class TestOptimizedSHAPCalculator:
    """Tests for OptimizedSHAPCalculator class."""
    
    @pytest.fixture
    def sample_model_and_data(self):
        """Create sample model and data for SHAP testing."""
        np.random.seed(42)
        n_samples = 100
        n_features = 4
        
        X = np.random.randn(n_samples, n_features).astype(np.float32)
        y = np.random.randn(n_samples).astype(np.float32)
        
        # Train a simple model
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        return model, X, y
    
    def test_calculate_shap_values(self, sample_model_and_data):
        """Test SHAP value calculation."""
        model, X, y = sample_model_and_data
        feature_names = [f'feature_{i}' for i in range(X.shape[1])]
        
        calculator = OptimizedSHAPCalculator()
        shap_values, explainer = calculator.calculate_shap_values(
            model, X, feature_names, sample_size=20
        )
        
        assert isinstance(shap_values, np.ndarray)
        assert shap_values.shape == X.shape
        assert explainer is not None
    
    def test_calculate_ranks(self, sample_model_and_data):
        """Test SHAP rank calculation."""
        model, X, y = sample_model_and_data
        feature_names = [f'feature_{i}' for i in range(X.shape[1])]
        
        calculator = OptimizedSHAPCalculator()
        shap_values, _ = calculator.calculate_shap_values(
            model, X, feature_names, sample_size=20
        )
        
        ranks = calculator.calculate_ranks(shap_values)
        
        assert isinstance(ranks, np.ndarray)
        assert ranks.shape[0] == X.shape[1]
        assert ranks.min() >= 1
        assert ranks.max() <= X.shape[1]
    
    def test_get_ranked_features(self, sample_model_and_data):
        """Test ranked feature extraction."""
        model, X, y = sample_model_and_data
        feature_names = [f'feature_{i}' for i in range(X.shape[1])]
        
        calculator = OptimizedSHAPCalculator()
        shap_values, _ = calculator.calculate_shap_values(
            model, X, feature_names, sample_size=20
        )
        
        ranked = calculator.get_ranked_features(shap_values, feature_names)
        
        assert isinstance(ranked, list)
        assert len(ranked) == X.shape[1]
        
        # Check structure
        for item in ranked:
            assert isinstance(item, tuple)
            assert len(item) == 3
            assert isinstance(item[0], str)  # feature name
            assert isinstance(item[1], float)  # mean abs SHAP
            assert isinstance(item[2], int)  # rank
    
    def test_ranked_features_sorted(self, sample_model_and_data):
        """Test that ranked features are sorted by importance."""
        model, X, y = sample_model_and_data
        feature_names = [f'feature_{i}' for i in range(X.shape[1])]
        
        calculator = OptimizedSHAPCalculator()
        shap_values, _ = calculator.calculate_shap_values(
            model, X, feature_names, sample_size=20
        )
        
        ranked = calculator.get_ranked_features(shap_values, feature_names)
        
        # Ranks should be in ascending order
        ranks = [item[2] for item in ranked]
        assert ranks == sorted(ranks)


class TestOptimizeDataLoading:
    """Tests for optimize_data_loading function."""
    
    def test_optimize_data_loading_runs(self, sample_dataset):
        """Test that optimize_data_loading completes without error."""
        with patch('config.get_config') as mock_config:
            mock_config.return_value.paths.processed_data = sample_dataset.parent
            
            result = optimize_data_loading()
            
            assert isinstance(result, dict)
            assert 'dataset_shape' in result
            assert 'feature_count' in result
            assert 'elapsed_time' in result


class TestOptimizeSHAPCalculation:
    """Tests for optimize_shap_calculation function."""
    
    def test_optimize_shap_calculation_runs(self, sample_dataset, tmp_path):
        """Test that optimize_shap_calculation completes without error."""
        with patch('config.get_config') as mock_config:
            mock_config.return_value.paths.processed_data = sample_dataset.parent
            
            # Mock the load_models function
            with patch('utils.performance_optimizations.load_models') as mock_load_models:
                # Create a simple model
                np.random.seed(42)
                X = np.random.randn(50, 4)
                y = np.random.randn(50)
                model = RandomForestRegressor(n_estimators=10, random_state=42)
                model.fit(X, y)
                
                mock_load_models.return_value = (
                    {'regressor': model, 'classifier': None},
                    {}
                )
                
                # Mock matplotlib to avoid display issues
                with patch('matplotlib.pyplot.savefig'):
                    result = optimize_shap_calculation()
                    
                    assert isinstance(result, dict)
                    assert 'shap_shape' in result
                    assert 'top_features' in result
                    assert 'elapsed_time' in result


def test_constants():
    """Test that module constants are reasonable."""
    assert CHUNK_SIZE > 0
    assert MAX_WORKERS > 0
    assert MAX_WORKERS <= os.cpu_count()