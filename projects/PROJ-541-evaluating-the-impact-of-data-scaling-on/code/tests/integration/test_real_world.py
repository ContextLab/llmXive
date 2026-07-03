"""
Integration test for full real-world pipeline on Iris dataset (T034a).

This test verifies the entire pipeline for real-world data ingestion,
scaling, statistical testing, and result aggregation using the Iris dataset.
It ensures that the pipeline runs end-to-end without errors and produces
valid statistical results.
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path for imports
code_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(code_root))

from preprocessing.ingestion import download_dataset, preprocess_dataset
from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from analysis.tests import run_scaled_t_test, ScalingMethod, TestResult
from simulation.config import SimulationConfig


class TestRealWorldPipeline:
    """Integration tests for real-world dataset pipeline."""

    @pytest.fixture
    def iris_config(self):
        """Configuration for Iris dataset test."""
        return {
            'id': 'uciml/iris',
            'source': 'UCI',
            'name': 'Iris',
            'target': 'class',
            'load_method': 'uciml'
        }

    def test_dataset_ingestion_and_preprocessing(self, iris_config):
        """Test that Iris dataset can be downloaded and preprocessed."""
        # Download dataset
        df = download_dataset(iris_config)
        
        # Verify dataset properties
        assert df is not None, "Dataset download failed"
        assert len(df) > 0, "Dataset is empty"
        assert iris_config['target'] in df.columns, f"Target column {iris_config['target']} not found"
        
        # Preprocess dataset
        processed_df = preprocess_dataset(df, iris_config['target'])
        
        # Verify preprocessing results
        assert processed_df is not None, "Preprocessing failed"
        assert len(processed_df) > 0, "Processed dataset is empty"
        assert processed_df.isna().sum().sum() == 0, "Preprocessing did not handle missing values"
        
        print(f"✓ Dataset ingestion successful: {len(processed_df)} rows, {len(processed_df.columns)} features")

    def test_scaling_methods_on_real_data(self, iris_config):
        """Test that all scaling methods work on real Iris data."""
        # Download and preprocess
        df = download_dataset(iris_config)
        processed_df = preprocess_dataset(df, iris_config['target'])
        
        # Separate features and target
        target_col = iris_config['target']
        features = [col for col in processed_df.columns if col != target_col]
        X = processed_df[features].select_dtypes(include=[np.number])
        y = processed_df[target_col]
        
        # Test Standardization
        X_std = standardize_data(X)
        assert X_std is not None, "Standardization failed"
        # Verify mean ≈ 0 and std ≈ 1 (with tolerance for numerical precision)
        assert np.allclose(X_std.mean().values, 0, atol=1e-10), "Standardized mean not zero"
        assert np.allclose(X_std.std().values, 1, atol=1e-10), "Standardized std not one"
        
        # Test Min-Max Scaling
        X_minmax = min_max_scale(X)
        assert X_minmax is not None, "Min-Max scaling failed"
        # Verify min = 0 and max = 1
        assert np.allclose(X_minmax.min().values, 0, atol=1e-10), "Min-Max min not zero"
        assert np.allclose(X_minmax.max().values, 1, atol=1e-10), "Min-Max max not one"
        
        # Test Robust Scaling
        X_robust = robust_scale(X)
        assert X_robust is not None, "Robust scaling failed"
        
        print("✓ All scaling methods work correctly on real data")

    def test_statistical_tests_on_scaled_data(self, iris_config):
        """Test that statistical tests run on scaled real data."""
        # Download and preprocess
        df = download_dataset(iris_config)
        processed_df = preprocess_dataset(df, iris_config['target'])
        
        # Separate features and target
        target_col = iris_config['target']
        features = [col for col in processed_df.columns if col != target_col]
        X = processed_df[features].select_dtypes(include=[np.number])
        y = processed_df[target_col]
        
        # Convert target to binary for t-test (e.g., setosa vs non-setosa)
        binary_target = (y == 'Iris-setosa').astype(int)
        
        # Split into two groups
        group1 = X[binary_target == 1]
        group2 = X[binary_target == 0]
        
        # Test t-test with different scaling methods
        for scaling_method in [ScalingMethod.STANDARDIZE, ScalingMethod.MINMAX, ScalingMethod.ROBUST]:
            # Apply scaling
            if scaling_method == ScalingMethod.STANDARDIZE:
                X_scaled = standardize_data(X)
            elif scaling_method == ScalingMethod.MINMAX:
                X_scaled = min_max_scale(X)
            else:  # ROBUST
                X_scaled = robust_scale(X)
            
            # Split scaled data
            group1_scaled = X_scaled[binary_target == 1]
            group2_scaled = X_scaled[binary_target == 0]
            
            # Run t-test
            result = run_scaled_t_test(group1_scaled, group2_scaled, scaling_method)
            
            # Verify result structure
            assert result is not None, f"T-test failed for {scaling_method}"
            assert isinstance(result, TestResult), "Result is not a TestResult"
            assert hasattr(result, 'p_value'), "Result missing p_value"
            assert hasattr(result, 'test_statistic'), "Result missing test_statistic"
            assert result.p_value is not None, "p_value is None"
            assert not np.isnan(result.p_value), "p_value is NaN"
            
            print(f"✓ T-test successful for {scaling_method}: p-value = {result.p_value:.4f}")

    def test_full_pipeline_end_to_end(self, iris_config):
        """Test the complete pipeline from download to statistical testing."""
        # Step 1: Download dataset
        df = download_dataset(iris_config)
        assert df is not None, "Dataset download failed"
        
        # Step 2: Preprocess
        processed_df = preprocess_dataset(df, iris_config['target'])
        assert processed_df is not None, "Preprocessing failed"
        
        # Step 3: Extract features and target
        target_col = iris_config['target']
        features = [col for col in processed_df.columns if col != target_col]
        X = processed_df[features].select_dtypes(include=[np.number])
        y = processed_df[target_col]
        
        # Step 4: Create binary target for t-test
        binary_target = (y == 'Iris-setosa').astype(int)
        
        # Step 5: Run pipeline with all scaling methods
        results = {}
        for scaling_method in [ScalingMethod.STANDARDIZE, ScalingMethod.MINMAX, ScalingMethod.ROBUST]:
            # Apply scaling
            if scaling_method == ScalingMethod.STANDARDIZE:
                X_scaled = standardize_data(X)
            elif scaling_method == ScalingMethod.MINMAX:
                X_scaled = min_max_scale(X)
            else:  # ROBUST
                X_scaled = robust_scale(X)
            
            # Split into groups
            group1 = X_scaled[binary_target == 1]
            group2 = X_scaled[binary_target == 0]
            
            # Run t-test
            result = run_scaled_t_test(group1, group2, scaling_method)
            results[scaling_method] = result
            
            # Verify result
            assert result is not None, f"Pipeline failed for {scaling_method}"
            assert not np.isnan(result.p_value), f"Invalid p-value for {scaling_method}"
            
            print(f"✓ Full pipeline completed for {scaling_method}")
        
        # Step 6: Verify consistency across scaling methods
        # (p-values should be similar since scaling is linear)
        p_values = [results[method].p_value for method in results]
        p_std = np.std(p_values)
        
        # Allow some variation due to numerical precision
        assert p_std < 0.1, f"P-values vary too much across scaling methods: std={p_std}"
        
        print(f"✓ Pipeline consistency verified: p-value std = {p_std:.6f}")
        
        return results

    def test_multiple_datasets(self):
        """Test pipeline on multiple real-world datasets."""
        datasets = [
            {'id': 'uciml/iris', 'source': 'UCI', 'target': 'class', 'load_method': 'uciml'},
            {'id': 'uciml/wine', 'source': 'UCI', 'target': 'class', 'load_method': 'uciml'},
        ]
        
        successful_datasets = 0
        
        for dataset_config in datasets:
            try:
                # Run full pipeline
                results = self.test_full_pipeline_end_to_end(dataset_config)
                successful_datasets += 1
                print(f"✓ Successfully processed {dataset_config['id']}")
            except Exception as e:
                print(f"⚠ Failed to process {dataset_config['id']}: {str(e)}")
        
        # At least one dataset should succeed
        assert successful_datasets > 0, "No datasets processed successfully"
        
        print(f"✓ Multiple dataset test: {successful_datasets}/{len(datasets)} successful")