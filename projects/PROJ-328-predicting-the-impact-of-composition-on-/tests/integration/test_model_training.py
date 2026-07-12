"""
Integration test for the model training pipeline (User Story 2).

This test verifies the end-to-end flow of:
1. Loading the validated dataset from data/processed/solder_hardness_validated.csv
2. Performing CLR transformation on compositional data
3. Computing compositional descriptors
4. Calculating VIF scores
5. Training XGBoost and Linear Regression models
6. Running cross-validation
7. Saving model artifacts and metrics

Prerequisites:
- T016 must be complete (validated dataset exists)
- T018 must be complete (model output schema contract test exists)
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import yaml

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from seed import init_reproducibility
from config import (
    get_data_processed_dir, 
    get_models_dir, 
    get_vif_threshold,
    get_cv_folds,
    get_bootstrap_iterations
)
from features.transformer import CLRTransformer
from features.descriptor_engine import DescriptorEngine
from features.collinearity import calculate_vif, get_collinear_features
from models.xgboost_trainer import XGBoostTrainer
from models.linear_trainer import LinearRegressionTrainer
from evaluation.cv import run_cross_validation
from utils.error_handlers import ModelTrainingError, DataValidationError


class TestModelTrainingPipeline:
    """Integration tests for the full model training pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize reproducibility and validate test preconditions."""
        # Initialize random seeds
        init_reproducibility()
        
        # Verify validated dataset exists
        data_dir = get_data_processed_dir()
        self.validated_data_path = data_dir / "solder_hardness_validated.csv"
        
        if not self.validated_data_path.exists():
            pytest.skip(
                f"Validated dataset not found at {self.validated_data_path}. "
                "Run T016 first."
            )
        
        # Ensure models directory exists
        models_dir = get_models_dir()
        models_dir.mkdir(parents=True, exist_ok=True)

    def test_pipeline_loads_and_transforms_data(self):
        """Test that the pipeline successfully loads and transforms data."""
        # Load data
        df = pd.read_csv(self.validated_data_path)
        
        assert len(df) > 0, "Dataset is empty"
        assert "hardness_hv" in df.columns, "Missing hardness column"
        
        # Identify composition columns (all numeric columns except hardness)
        composition_cols = [col for col in df.columns if col != "hardness_hv"]
        
        # Apply CLR transformation
        transformer = CLRTransformer()
        clr_df, weights = transformer.fit_transform(df, composition_cols)
        
        assert clr_df is not None, "CLR transformation failed"
        assert len(clr_df) == len(df), "Data length changed after transformation"
        
        # Verify no NaN values in transformed data
        assert not clr_df.isnull().any().any(), "Transformed data contains NaN values"

    def test_descriptor_engine_computes_features(self):
        """Test that descriptors are computed correctly."""
        df = pd.read_csv(self.validated_data_path)
        
        composition_cols = [col for col in df.columns if col != "hardness_hv"]
        
        # Transform data
        transformer = CLRTransformer()
        clr_df, weights = transformer.fit_transform(df, composition_cols)
        
        # Compute descriptors
        engine = DescriptorEngine()
        descriptors = engine.compute_descriptors(df, clr_df, composition_cols)
        
        assert descriptors is not None, "Descriptor computation failed"
        assert len(descriptors) == len(df), "Descriptor count mismatch"
        
        # Check expected descriptor columns exist
        expected_cols = [
            "weighted_mean_atomic_mass",
            "electronegativity_variance",
            "atomic_radius_variance",
            "weighted_avg_melting_point",
            "valence_electron_concentration"
        ]
        
        for col in expected_cols:
            assert col in descriptors.columns, f"Missing descriptor: {col}"
            assert not descriptors[col].isnull().any(), f"Descriptor {col} contains NaN"

    def test_vif_calculation_and_collinearity_detection(self):
        """Test VIF calculation and collinearity detection."""
        df = pd.read_csv(self.validated_data_path)
        
        composition_cols = [col for col in df.columns if col != "hardness_hv"]
        
        # Transform and compute descriptors
        transformer = CLRTransformer()
        clr_df, weights = transformer.fit_transform(df, composition_cols)
        
        engine = DescriptorEngine()
        descriptors = engine.compute_descriptors(df, clr_df, composition_cols)
        
        # Calculate VIF
        vif_scores = calculate_vif(descriptors)
        
        assert isinstance(vif_scores, dict), "VIF calculation did not return a dict"
        assert len(vif_scores) > 0, "No VIF scores calculated"
        
        # Check that VIF values are numeric and positive
        for feature, vif in vif_scores.items():
            assert isinstance(vif, (int, float)), f"VIF for {feature} is not numeric"
            assert vif >= 0, f"VIF for {feature} is negative"

    def test_xgboost_training_and_cv(self):
        """Test XGBoost model training and cross-validation."""
        df = pd.read_csv(self.validated_data_path)
        
        composition_cols = [col for col in df.columns if col != "hardness_hv"]
        
        # Transform and compute descriptors
        transformer = CLRTransformer()
        clr_df, weights = transformer.fit_transform(df, composition_cols)
        
        engine = DescriptorEngine()
        descriptors = engine.compute_descriptors(df, clr_df, composition_cols)
        
        target = df["hardness_hv"]
        
        # Initialize trainer
        trainer = XGBoostTrainer(
            cv_folds=get_cv_folds(),
            vif_threshold=get_vif_threshold()
        )
        
        # Train model
        model, metrics, best_params = trainer.train(descriptors, target)
        
        assert model is not None, "XGBoost model training failed"
        assert metrics is not None, "Metrics not returned"
        
        # Verify metrics contain expected keys
        assert "r2_mean" in metrics, "Missing R² mean in metrics"
        assert "rmse_mean" in metrics, "Missing RMSE mean in metrics"
        
        # Verify model can predict
        predictions = model.predict(descriptors.head(5))
        assert len(predictions) == 5, "Prediction count mismatch"

    def test_linear_regression_training_and_cv(self):
        """Test Linear Regression model training and cross-validation."""
        df = pd.read_csv(self.validated_data_path)
        
        composition_cols = [col for col in df.columns if col != "hardness_hv"]
        
        # Transform and compute descriptors
        transformer = CLRTransformer()
        clr_df, weights = transformer.fit_transform(df, composition_cols)
        
        engine = DescriptorEngine()
        descriptors = engine.compute_descriptors(df, clr_df, composition_cols)
        
        target = df["hardness_hv"]
        
        # Initialize trainer
        trainer = LinearRegressionTrainer(
            cv_folds=get_cv_folds()
        )
        
        # Train model
        model, metrics = trainer.train(descriptors, target)
        
        assert model is not None, "Linear Regression model training failed"
        assert metrics is not None, "Metrics not returned"
        
        # Verify metrics contain expected keys
        assert "r2_mean" in metrics, "Missing R² mean in metrics"
        assert "rmse_mean" in metrics, "Missing RMSE mean in metrics"

    def test_model_artifacts_saved(self):
        """Test that model artifacts are saved to the correct location."""
        df = pd.read_csv(self.validated_data_path)
        
        composition_cols = [col for col in df.columns if col != "hardness_hv"]
        
        # Transform and compute descriptors
        transformer = CLRTransformer()
        clr_df, weights = transformer.fit_transform(df, composition_cols)
        
        engine = DescriptorEngine()
        descriptors = engine.compute_descriptors(df, clr_df, composition_cols)
        
        target = df["hardness_hv"]
        
        # Train XGBoost model
        xgb_trainer = XGBoostTrainer(
            cv_folds=get_cv_folds(),
            vif_threshold=get_vif_threshold()
        )
        xgb_model, xgb_metrics, xgb_params = xgb_trainer.train(descriptors, target)
        
        # Train Linear Regression model
        lr_trainer = LinearRegressionTrainer(cv_folds=get_cv_folds())
        lr_model, lr_metrics = lr_trainer.train(descriptors, target)
        
        # Save models
        models_dir = get_models_dir()
        
        xgb_path = models_dir / "xgboost_hardness_model.pkl"
        lr_path = models_dir / "linear_hardness_model.pkl"
        
        xgb_trainer.save_model(xgb_model, str(xgb_path))
        lr_trainer.save_model(lr_model, str(lr_path))
        
        # Verify files exist
        assert xgb_path.exists(), "XGBoost model not saved"
        assert lr_path.exists(), "Linear Regression model not saved"
        
        # Verify metrics saved
        metrics_path = models_dir / "training_metrics.yaml"
        assert metrics_path.exists(), "Metrics file not saved"
        
        # Load and verify metrics content
        with open(metrics_path, "r") as f:
            saved_metrics = yaml.safe_load(f)
        
        assert "xgboost" in saved_metrics, "XGBoost metrics not saved"
        assert "linear_regression" in saved_metrics, "Linear metrics not saved"

    def test_full_pipeline_integration(self):
        """
        Full integration test: run the entire pipeline from data loading
        to model saving and verify all outputs are correct.
        """
        # 1. Load data
        df = pd.read_csv(self.validated_data_path)
        assert len(df) >= 100, "Dataset size below threshold (T016 requirement)"
        
        composition_cols = [col for col in df.columns if col != "hardness_hv"]
        
        # 2. Transform
        transformer = CLRTransformer()
        clr_df, weights = transformer.fit_transform(df, composition_cols)
        
        # 3. Compute descriptors
        engine = DescriptorEngine()
        descriptors = engine.compute_descriptors(df, clr_df, composition_cols)
        
        # 4. Check collinearity
        vif_scores = calculate_vif(descriptors)
        collinear = get_collinear_features(vif_scores, get_vif_threshold())
        
        # 5. Train both models
        target = df["hardness_hv"]
        
        xgb_trainer = XGBoostTrainer(
            cv_folds=get_cv_folds(),
            vif_threshold=get_vif_threshold()
        )
        xgb_model, xgb_metrics, xgb_params = xgb_trainer.train(descriptors, target)
        
        lr_trainer = LinearRegressionTrainer(cv_folds=get_cv_folds())
        lr_model, lr_metrics = lr_trainer.train(descriptors, target)
        
        # 6. Verify metrics
        assert xgb_metrics["r2_mean"] >= 0, "XGBoost R² cannot be negative"
        assert lr_metrics["r2_mean"] >= 0, "Linear R² cannot be negative"
        
        # 7. Save artifacts
        models_dir = get_models_dir()
        xgb_path = models_dir / "xgboost_hardness_model.pkl"
        lr_path = models_dir / "linear_hardness_model.pkl"
        metrics_path = models_dir / "training_metrics.yaml"
        
        xgb_trainer.save_model(xgb_model, str(xgb_path))
        lr_trainer.save_model(lr_model, str(lr_path))
        
        # Compile metrics
        all_metrics = {
            "xgboost": {
                "r2_mean": float(xgb_metrics["r2_mean"]),
                "r2_std": float(xgb_metrics.get("r2_std", 0)),
                "rmse_mean": float(xgb_metrics["rmse_mean"]),
                "rmse_std": float(xgb_metrics.get("rmse_std", 0)),
                "best_params": xgb_params
            },
            "linear_regression": {
                "r2_mean": float(lr_metrics["r2_mean"]),
                "r2_std": float(lr_metrics.get("r2_std", 0)),
                "rmse_mean": float(lr_metrics["rmse_mean"]),
                "rmse_std": float(lr_metrics.get("rmse_std", 0))
            },
            "vif_scores": {k: float(v) for k, v in vif_scores.items()},
            "collinear_features": collinear
        }
        
        with open(metrics_path, "w") as f:
            yaml.dump(all_metrics, f, default_flow_style=False)
        
        # 8. Verify all outputs
        assert xgb_path.exists(), "XGBoost model artifact missing"
        assert lr_path.exists(), "Linear model artifact missing"
        assert metrics_path.exists(), "Metrics artifact missing"
        
        # 9. Verify model can load and predict
        from utils.error_handlers import ModelTrainingError
        try:
            xgb_loaded = xgb_trainer.load_model(str(xgb_path))
            _ = xgb_loaded.predict(descriptors.head(1))
        except Exception as e:
            raise ModelTrainingError(f"Failed to load XGBoost model: {e}")
        
        try:
            lr_loaded = lr_trainer.load_model(str(lr_path))
            _ = lr_loaded.predict(descriptors.head(1))
        except Exception as e:
            raise ModelTrainingError(f"Failed to load Linear model: {e}")