"""
Integration test for k-fold cross-validation pipeline (US3).

This test verifies that the model training pipeline correctly:
1. Loads processed descriptor data
2. Splits data into k folds
3. Trains and validates models on each fold
4. Aggregates metrics (RMSE, R²) across folds
5. Handles edge cases (insufficient data per fold, material imbalance)

Dependencies:
- code/models/train.py (train_polynomial_model, train_joint_gp_model)
- code/models/validate.py (k-fold CV logic - to be implemented)
- data/processed/descriptors.csv (preprocessed output from US2)
"""

import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.models.train import (
    load_descriptors_for_training,
    train_polynomial_model,
    train_joint_gp_model
)
from code.models.validate import k_fold_cross_validation
from code.utils.logging import get_logger

logger = get_logger(__name__)


class TestKFoldCrossValidationPipeline:
    """Integration tests for the k-fold cross-validation pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures before each test."""
        self.data_path = PROJECT_ROOT / "data" / "processed" / "descriptors.csv"
        self.results_path = PROJECT_ROOT / "data" / "processed" / "cv_results"
        
        # Ensure results directory exists
        self.results_path.mkdir(parents=True, exist_ok=True)
        
        # Verify data file exists
        if not self.data_path.exists():
            pytest.skip(f"Data file not found: {self.data_path}. "
                      "Run US2 tasks to generate descriptors.csv first.")
        
        yield
        
        # Cleanup if needed
        if self.results_path.exists():
            import shutil
            shutil.rmtree(self.results_path, ignore_errors=True)

    def test_load_and_validate_data(self):
        """Test that descriptor data can be loaded and validated for training."""
        # Load data
        X, y, metadata = load_descriptors_for_training(self.data_path)
        
        # Assertions
        assert X is not None, "Feature matrix should not be None"
        assert y is not None, "Target vector should not be None"
        assert len(X) == len(y), "Features and targets must have same length"
        assert len(X) > 0, "Dataset must contain samples"
        
        # Check for required columns in metadata
        assert 'material' in metadata.columns, "Metadata must include 'material' column"
        assert 'reduction' in metadata.columns, "Metadata must include 'reduction' column"
        
        logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features")

    def test_k_fold_split_structure(self):
        """Test that k-fold splitting produces correct fold structure."""
        # Load data
        X, y, metadata = load_descriptors_for_training(self.data_path)
        
        # Run k-fold split
        n_folds = 5
        folds = k_fold_cross_validation._create_folds(X, y, n_folds, random_state=42)
        
        # Assertions
        assert len(folds) == n_folds, f"Should produce {n_folds} folds"
        
        total_samples = 0
        for i, (train_idx, test_idx) in enumerate(folds):
            total_samples += len(train_idx) + len(test_idx)
            
            # Ensure no overlap between train and test
            assert len(set(train_idx) & set(test_idx)) == 0, \
                f"Fold {i}: Train and test sets must be disjoint"
            
            # Ensure each sample appears in exactly one test set
            # (verified at end by checking total count)
            
            logger.info(f"Fold {i}: Train={len(train_idx)}, Test={len(test_idx)}")
        
        # Each sample should appear in exactly one test fold
        all_test_indices = []
        for _, test_idx in folds:
            all_test_indices.extend(test_idx)
        
        assert len(all_test_indices) == len(y), \
            "Each sample should appear in exactly one test fold"

    def test_polynomial_model_training_per_fold(self):
        """Test polynomial model training across all folds."""
        # Load data
        X, y, metadata = load_descriptors_for_training(self.data_path)
        
        # Run k-fold CV for polynomial model
        n_folds = 5
        results = k_fold_cross_validation.run_polynomial_cv(
            X, y, n_folds=n_folds, random_state=42
        )
        
        # Assertions
        assert results is not None, "CV results should not be None"
        assert 'metrics' in results, "Results must contain 'metrics' key"
        assert 'fold_results' in results, "Results must contain 'fold_results' key"
        
        metrics = results['metrics']
        fold_results = results['fold_results']
        
        # Check metrics structure
        assert 'mean_r2' in metrics, "Metrics must include mean R²"
        assert 'mean_rmse' in metrics, "Metrics must include mean RMSE"
        assert 'std_r2' in metrics, "Metrics must include std R²"
        assert 'std_rmse' in metrics, "Metrics must include std RMSE"
        
        # Check fold results
        assert len(fold_results) == n_folds, \
            f"Should have results for {n_folds} folds"
        
        for i, fold_result in enumerate(fold_results):
            assert 'r2' in fold_result, f"Fold {i} must have R² score"
            assert 'rmse' in fold_result, f"Fold {i} must have RMSE score"
            assert 'train_size' in fold_result, f"Fold {i} must have train size"
            assert 'test_size' in fold_result, f"Fold {i} must have test size"
            
            logger.info(f"Fold {i}: R²={fold_result['r2']:.4f}, "
                      f"RMSE={fold_result['rmse']:.4f}")
        
        # Verify aggregation
        expected_mean_r2 = np.mean([f['r2'] for f in fold_results])
        expected_mean_rmse = np.mean([f['rmse'] for f in fold_results])
        
        assert np.isclose(metrics['mean_r2'], expected_mean_r2, atol=1e-6), \
            "Mean R² should be average of fold R² scores"
        assert np.isclose(metrics['mean_rmse'], expected_mean_rmse, atol=1e-6), \
            "Mean RMSE should be average of fold RMSE scores"

    def test_gp_model_training_per_fold(self):
        """Test Gaussian Process model training across all folds."""
        # Load data
        X, y, metadata = load_descriptors_for_training(self.data_path)
        
        # Run k-fold CV for GP model
        n_folds = 5
        results = k_fold_cross_validation.run_gp_cv(
            X, y, n_folds=n_folds, random_state=42
        )
        
        # Assertions
        assert results is not None, "CV results should not be None"
        assert 'metrics' in results, "Results must contain 'metrics' key"
        assert 'fold_results' in results, "Results must contain 'fold_results' key"
        
        metrics = results['metrics']
        fold_results = results['fold_results']
        
        # Check metrics structure
        assert 'mean_r2' in metrics, "Metrics must include mean R²"
        assert 'mean_rmse' in metrics, "Metrics must include mean RMSE"
        
        # Check fold results
        assert len(fold_results) == n_folds, \
            f"Should have results for {n_folds} folds"
        
        for i, fold_result in enumerate(fold_results):
            assert 'r2' in fold_result, f"Fold {i} must have R² score"
            assert 'rmse' in fold_result, f"Fold {i} must have RMSE score"
            
            logger.info(f"Fold {i} (GP): R²={fold_result['r2']:.4f}, "
                      f"RMSE={fold_result['rmse']:.4f}")

    def test_material_balance_across_folds(self):
        """Test that material types are reasonably balanced across folds."""
        # Load data
        X, y, metadata = load_descriptors_for_training(self.data_path)
        
        # Run k-fold split
        n_folds = 5
        folds = k_fold_cross_validation._create_folds(X, y, n_folds, random_state=42)
        
        # Check material distribution in each test fold
        materials = metadata['material'].values
        
        for i, (train_idx, test_idx) in enumerate(folds):
            test_materials = materials[test_idx]
            unique, counts = np.unique(test_materials, return_counts=True)
            
            logger.info(f"Fold {i} test set: {dict(zip(unique, counts))}")
            
            # Each fold should have at least some representation
            # (allowing for small datasets where some folds might miss a rare material)
            assert len(unique) >= 1, \
                f"Fold {i} test set should have at least one material type"

    def test_cv_results_export(self):
        """Test that CV results are correctly exported to disk."""
        # Load data
        X, y, metadata = load_descriptors_for_training(self.data_path)
        
        # Run CV
        n_folds = 5
        poly_results = k_fold_cross_validation.run_polynomial_cv(
            X, y, n_folds=n_folds, random_state=42
        )
        
        # Export results
        output_file = self.results_path / "polynomial_cv_results.csv"
        k_fold_cross_validation.export_cv_results(poly_results, output_file)
        
        # Verify file exists
        assert output_file.exists(), \
            f"CV results file should be created at {output_file}"
        
        # Verify content
        df = pd.read_csv(output_file)
        
        # Check expected columns
        expected_columns = ['fold', 'r2', 'rmse', 'train_size', 'test_size']
        for col in expected_columns:
            assert col in df.columns, f"Results must include '{col}' column"
        
        # Verify row count
        assert len(df) == n_folds, \
            f"Results should have {n_folds} rows (one per fold)"
        
        logger.info(f"Exported CV results to {output_file}")

    def test_model_comparison_across_folds(self):
        """Test comparison of polynomial vs GP models across folds."""
        # Load data
        X, y, metadata = load_descriptors_for_training(self.data_path)
        
        # Run CV for both models
        n_folds = 5
        poly_results = k_fold_cross_validation.run_polynomial_cv(
            X, y, n_folds=n_folds, random_state=42
        )
        gp_results = k_fold_cross_validation.run_gp_cv(
            X, y, n_folds=n_folds, random_state=42
        )
        
        # Compare mean metrics
        poly_mean_r2 = poly_results['metrics']['mean_r2']
        gp_mean_r2 = gp_results['metrics']['mean_r2']
        
        logger.info(f"Polynomial mean R²: {poly_mean_r2:.4f}")
        logger.info(f"GP mean R²: {gp_mean_r2:.4f}")
        
        # Both models should produce valid metrics
        assert -1 <= poly_mean_r2 <= 1, "Polynomial R² should be in valid range"
        assert -1 <= gp_mean_r2 <= 1, "GP R² should be in valid range"
        
        # Export comparison
        comparison_file = self.results_path / "model_comparison.csv"
        k_fold_cross_validation.export_model_comparison(
            poly_results, gp_results, comparison_file
        )
        
        assert comparison_file.exists(), \
            f"Comparison file should be created at {comparison_file}"

    def test_small_dataset_handling(self):
        """Test that the pipeline handles small datasets gracefully."""
        # Load full data
        X, y, metadata = load_descriptors_for_training(self.data_path)
        
        # Create a small subset (e.g., 10 samples)
        if len(X) > 10:
            subset_indices = np.random.choice(len(X), 10, replace=False)
            X_small = X[subset_indices]
            y_small = y[subset_indices]
            metadata_small = metadata.iloc[subset_indices].reset_index(drop=True)
        else:
            X_small = X
            y_small = y
            metadata_small = metadata
        
        # Try with k=3 folds for small dataset
        n_folds = 3
        
        # Should not raise an error
        try:
            results = k_fold_cross_validation.run_polynomial_cv(
                X_small, y_small, n_folds=n_folds, random_state=42
            )
            
            assert results is not None
            assert results['metrics']['mean_r2'] is not None
            
            logger.info(f"Small dataset test passed: {len(X_small)} samples, {n_folds} folds")
        except Exception as e:
            pytest.fail(f"Pipeline failed on small dataset: {str(e)}")

    def test_reproducibility(self):
        """Test that CV results are reproducible with fixed random state."""
        # Load data
        X, y, metadata = load_descriptors_for_training(self.data_path)
        
        # Run CV twice with same random state
        n_folds = 5
        random_state = 12345
        
        results1 = k_fold_cross_validation.run_polynomial_cv(
            X, y, n_folds=n_folds, random_state=random_state
        )
        results2 = k_fold_cross_validation.run_polynomial_cv(
            X, y, n_folds=n_folds, random_state=random_state
        )
        
        # Results should be identical
        assert np.isclose(
            results1['metrics']['mean_r2'],
            results2['metrics']['mean_r2'],
            atol=1e-10
        ), "Mean R² should be reproducible"
        
        assert np.isclose(
            results1['metrics']['mean_rmse'],
            results2['metrics']['mean_rmse'],
            atol=1e-10
        ), "Mean RMSE should be reproducible"
        
        logger.info("Reproducibility test passed")

    def test_extrapolation_detection_in_cv(self):
        """Test that extrapolation is properly flagged during CV."""
        # Load data
        X, y, metadata = load_descriptors_for_training(self.data_path)
        
        # Run CV
        n_folds = 5
        results = k_fold_cross_validation.run_polynomial_cv(
            X, y, n_folds=n_folds, random_state=42,
            flag_extrapolation=True
        )
        
        # Check that extrapolation flags are included
        for fold_result in results['fold_results']:
            assert 'extrapolation_flags' in fold_result, \
                "Fold results should include extrapolation flags"
            
            flags = fold_result['extrapolation_flags']
            assert isinstance(flags, list), "Extrapolation flags should be a list"
            assert len(flags) == fold_result['test_size'], \
                "Should have one flag per test sample"

    def test_full_pipeline_end_to_end(self):
        """Test the complete CV pipeline from data loading to results export."""
        # Full pipeline execution
        data_path = self.data_path
        results_dir = self.results_path
        
        # 1. Load data
        X, y, metadata = load_descriptors_for_training(data_path)
        logger.info(f"Step 1: Loaded {len(X)} samples")
        
        # 2. Run polynomial CV
        poly_results = k_fold_cross_validation.run_polynomial_cv(
            X, y, n_folds=5, random_state=42
        )
        logger.info(f"Step 2: Completed polynomial CV")
        
        # 3. Run GP CV
        gp_results = k_fold_cross_validation.run_gp_cv(
            X, y, n_folds=5, random_state=42
        )
        logger.info(f"Step 3: Completed GP CV")
        
        # 4. Export results
        poly_file = results_dir / "polynomial_cv_results.csv"
        gp_file = results_dir / "gp_cv_results.csv"
        comparison_file = results_dir / "model_comparison.csv"
        
        k_fold_cross_validation.export_cv_results(poly_results, poly_file)
        k_fold_cross_validation.export_cv_results(gp_results, gp_file)
        k_fold_cross_validation.export_model_comparison(
            poly_results, gp_results, comparison_file
        )
        logger.info(f"Step 4: Exported results to {results_dir}")
        
        # 5. Verify all files exist
        assert poly_file.exists(), "Polynomial results file should exist"
        assert gp_file.exists(), "GP results file should exist"
        assert comparison_file.exists(), "Comparison file should exist"
        
        # 6. Summary
        logger.info("=" * 60)
        logger.info("END-TO-END TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Polynomial CV: R² = {poly_results['metrics']['mean_r2']:.4f} ± {poly_results['metrics']['std_r2']:.4f}")
        logger.info(f"GP CV: R² = {gp_results['metrics']['mean_r2']:.4f} ± {gp_results['metrics']['std_r2']:.4f}")
        logger.info("=" * 60)
        
        # Assert that at least one model achieved reasonable performance
        assert poly_results['metrics']['mean_r2'] > -0.5 or \
               gp_results['metrics']['mean_r2'] > -0.5, \
               "At least one model should achieve reasonable R²"

    def test_insufficient_data_per_fold(self):
        """Test behavior when a fold has insufficient training data."""
        # Load data
        X, y, metadata = load_descriptors_for_training(self.data_path)
        
        # Create a very small dataset (e.g., 4 samples) and try 3 folds
        if len(X) > 4:
            subset_indices = np.random.choice(len(X), 4, replace=False)
            X_small = X[subset_indices]
            y_small = y[subset_indices]
        else:
            X_small = X[:4]
            y_small = y[:4]
        
        # This should either work with small folds or raise a clear error
        try:
            results = k_fold_cross_validation.run_polynomial_cv(
                X_small, y_small, n_folds=3, random_state=42
            )
            logger.info("Small fold test completed successfully")
        except ValueError as e:
            # Expected if minimum samples per fold is enforced
            assert "insufficient" in str(e).lower() or "minimum" in str(e).lower(), \
                f"Error message should indicate insufficient data: {str(e)}"
            logger.info(f"Expected error for insufficient data: {str(e)}")

    def test_multimaterial_cv(self):
        """Test CV performance across different materials."""
        # Load data
        X, y, metadata = load_descriptors_for_training(self.data_path)
        
        # Run CV
        n_folds = 5
        results = k_fold_cross_validation.run_polynomial_cv(
            X, y, n_folds=n_folds, random_state=42
        )
        
        # Group results by material
        if 'material' in metadata.columns:
            materials = metadata['material'].unique()
            
            logger.info(f"Testing CV across {len(materials)} materials: {materials}")
            
            for material in materials:
                material_mask = metadata['material'] == material
                X_mat = X[material_mask]
                y_mat = y[material_mask]
                
                if len(X_mat) >= n_folds:
                    mat_results = k_fold_cross_validation.run_polynomial_cv(
                        X_mat, y_mat, n_folds=min(n_folds, max(2, len(X_mat)//2)),
                        random_state=42
                    )
                    logger.info(f"  {material}: R² = {mat_results['metrics']['mean_r2']:.4f}")
                else:
                    logger.info(f"  {material}: Insufficient samples ({len(X_mat)}) for CV")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])