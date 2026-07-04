"""
Integration tests for the full pipeline: spatial split, training, and evaluation.
This test ensures that the components work together to produce a valid model and metrics.
"""
import os
import sys
import pytest
from pathlib import Path
import pandas as pd
import numpy as np
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import modules
from train import load_data, spatial_split, train_model, evaluate_model, save_results
from evaluate import compute_roc_auc, run_permutation_importance, apply_fdr_correction, bootstrap_stability
from features import compute_lagged_features, calculate_vif, filter_high_vif
from ingest import merge_datasets

class TestPipelineIntegration:
    """Integration tests for the end-to-end pipeline."""

    @pytest.fixture
    def sample_data(self):
        """Create a sample dataset mimicking the unified reef-species CSV."""
        # Simulate Western and Eastern Pacific reefs
        n_west = 50
        n_east = 50
        
        west_data = {
            'latitude': np.random.uniform(-20, 10, n_west),
            'longitude': np.random.uniform(120, 160, n_west),
            'SST': np.random.normal(28, 1, n_west),
            'DHW': np.random.normal(2, 1, n_west),
            'thermal_tolerance': np.random.normal(11, 1, n_west),
            'bleaching_event': np.random.choice([0, 1], n_west, p=[0.7, 0.3])
        }
        
        east_data = {
            'latitude': np.random.uniform(-20, 10, n_east),
            'longitude': np.random.uniform(-170, -130, n_east),
            'SST': np.random.normal(27, 1, n_east),
            'DHW': np.random.normal(1.5, 0.8, n_east),
            'thermal_tolerance': np.random.normal(10.5, 1, n_east),
            'bleaching_event': np.random.choice([0, 1], n_east, p=[0.8, 0.2])
        }
        
        df_west = pd.DataFrame(west_data)
        df_east = pd.DataFrame(east_data)
        
        # Add some lagged features
        df_west['SST_lag_1'] = df_west['SST'].shift(1)
        df_east['SST_lag_1'] = df_east['SST'].shift(1)
        
        # Fill NaNs for testing
        df_west = df_west.fillna(method='bfill').fillna(method='ffill')
        df_east = df_east.fillna(method='bfill').fillna(method='ffill')
        
        return pd.concat([df_west, df_east], ignore_index=True)

    def test_spatial_split_separates_regions(self, sample_data):
        """Verify spatial_split correctly separates Western and Eastern Pacific."""
        train_df, test_df = spatial_split(sample_data)
        
        # Check that train is mostly Western (long > 0) and test is mostly Eastern (long < 0)
        train_long_positive = (train_df['longitude'] > 0).sum()
        test_long_negative = (test_df['longitude'] < 0).sum()
        
        # Assert that the split is logical
        assert train_long_positive > len(train_df) * 0.8, "Train set should be mostly Western Pacific"
        assert test_long_negative > len(test_df) * 0.8, "Test set should be mostly Eastern Pacific"

    def test_train_model_produces_xgboost(self, sample_data):
        """Verify train_model produces an XGBoost model object."""
        # Split data
        train_df, test_df = spatial_split(sample_data)
        
        # Prepare features (drop non-feature columns)
        feature_cols = ['SST', 'DHW', 'thermal_tolerance', 'SST_lag_1']
        X_train = train_df[feature_cols]
        y_train = train_df['bleaching_event']
        
        model = train_model(X_train, y_train)
        
        # Verify model is an XGBoost object
        assert model is not None
        assert 'xgb' in str(type(model)).lower()

    def test_evaluate_model_returns_metrics(self, sample_data):
        """Verify evaluate_model returns a dictionary of metrics."""
        # Split data
        train_df, test_df = spatial_split(sample_data)
        
        # Prepare features
        feature_cols = ['SST', 'DHW', 'thermal_tolerance', 'SST_lag_1']
        X_train = train_df[feature_cols]
        y_train = train_df['bleaching_event']
        X_test = test_df[feature_cols]
        y_test = test_df['bleaching_event']
        
        # Train model
        model = train_model(X_train, y_train)
        
        # Evaluate
        metrics = evaluate_model(model, X_test, y_test)
        
        assert isinstance(metrics, dict)
        # Check for expected keys
        assert 'ROC_AUC' in metrics or 'roc_auc' in metrics

    def test_full_pipeline_flow(self, sample_data):
        """Test the full flow: Split -> Train -> Evaluate -> Save."""
        # 1. Spatial Split
        train_df, test_df = spatial_split(sample_data)
        
        # 2. Feature Engineering (mocked for integration test simplicity)
        # In real pipeline, this would come from features.py
        feature_cols = ['SST', 'DHW', 'thermal_tolerance', 'SST_lag_1']
        X_train = train_df[feature_cols].fillna(0)
        y_train = train_df['bleaching_event']
        X_test = test_df[feature_cols].fillna(0)
        y_test = test_df['bleaching_event']
        
        # 3. Train
        model = train_model(X_train, y_train)
        assert model is not None
        
        # 4. Evaluate
        metrics = evaluate_model(model, X_test, y_test)
        assert metrics is not None
        
        # 5. Save Results (mock path)
        save_results(metrics, "data/models/test_results.json")
        
        # Verify file was created (in a real test, we'd check disk)
        # For this unit/integration hybrid, we assume save_results works if it didn't crash
        assert os.path.exists("data/models/test_results.json")
        
        # Cleanup
        if os.path.exists("data/models/test_results.json"):
            os.remove("data/models/test_results.json")

    def test_permutation_importance_runs(self, sample_data):
        """Verify permutation importance runs without error on trained model."""
        train_df, test_df = spatial_split(sample_data)
        feature_cols = ['SST', 'DHW', 'thermal_tolerance', 'SST_lag_1']
        X_train = train_df[feature_cols].fillna(0)
        y_train = train_df['bleaching_event']
        
        model = train_model(X_train, y_train)
        
        # Run permutation importance
        # Note: This might take time, so we use a small number of permutations for the test
        importance, p_values = run_permutation_importance(model, X_train, y_train, n_permutations=10)
        
        assert importance is not None
        assert p_values is not None
        assert len(importance) == len(feature_cols)

    def test_fdr_correction_applied(self, sample_data):
        """Verify FDR correction is applied to p-values."""
        train_df, test_df = spatial_split(sample_data)
        feature_cols = ['SST', 'DHW', 'thermal_tolerance', 'SST_lag_1']
        X_train = train_df[feature_cols].fillna(0)
        y_train = train_df['bleaching_event']
        
        model = train_model(X_train, y_train)
        importance, p_values = run_permutation_importance(model, X_train, y_train, n_permutations=10)
        
        # Apply FDR
        corrected_p_values = apply_fdr_correction(p_values)
        
        assert len(corrected_p_values) == len(p_values)
        # FDR corrected p-values should be >= original p-values (monotonicity)
        # Note: This is a statistical property, but we check length at least
        assert all(np.array(corrected_p_values) >= np.array(p_values))

    def test_bootstrap_stability_runs(self, sample_data):
        """Verify bootstrap stability analysis runs."""
        train_df, test_df = spatial_split(sample_data)
        feature_cols = ['SST', 'DHW', 'thermal_tolerance', 'SST_lag_1']
        X_train = train_df[feature_cols].fillna(0)
        y_train = train_df['bleaching_event']
        
        model = train_model(X_train, y_train)
        
        # Run bootstrap stability
        stability_scores = bootstrap_stability(model, X_train, y_train, n_bootstrap=10)
        
        assert stability_scores is not None
        assert isinstance(stability_scores, dict)
        # Check that we have scores for the features
        for feat in feature_cols:
            assert feat in stability_scores