"""
Integration test for model training pipeline (T030).
Verifies k-fold cross-validation, model training, and metrics generation.
Dependencies: T035 (training_pipeline), T037 (model_metrics).
"""
import pytest
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to path if running directly
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.training_pipeline import run_training_pipeline
from src.models.linear_regressor import run_linear_regression
from src.models.random_forest_regressor import run_random_forest_regression
from src.features.feature_engineering_pipeline import run_feature_engineering_pipeline
from src.preprocessing.scarcity_checker import run_scarcity_check

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "code" / "models"

class TestModelTrainingIntegration:
    """Integration tests for the model training pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure necessary directories exist before tests."""
        DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        yield

    def test_preprocessing_pipeline_produces_raw_data(self):
        """
        Verify that the preprocessing pipeline produces data/processed/alloys_raw.csv.
        This is a prerequisite for model training.
        """
        logger.info("Running preprocessing pipeline to ensure raw data exists...")
        # Run the preprocessing pipeline
        run_preprocessing_pipeline()

        raw_data_path = DATA_PROCESSED / "alloys_raw.csv"
        assert raw_data_path.exists(), "Preprocessing pipeline failed to produce alloys_raw.csv"
        logger.info(f"Verified {raw_data_path} exists.")

    def test_feature_engineering_pipeline_produces_features(self):
        """
        Verify that the feature engineering pipeline produces data/processed/alloys_features.csv.
        """
        logger.info("Running feature engineering pipeline...")
        # Run feature engineering
        run_feature_engineering_pipeline()

        features_path = DATA_PROCESSED / "alloys_features.csv"
        assert features_path.exists(), "Feature engineering pipeline failed to produce alloys_features.csv"
        logger.info(f"Verified {features_path} exists.")

    def test_training_pipeline_executes_k_fold_cv(self):
        """
        Verify that the training pipeline performs k-fold cross-validation
        and trains both Linear and Random Forest models.
        """
        logger.info("Running training pipeline with k-fold CV...")

        # Ensure features exist first
        features_path = DATA_PROCESSED / "alloys_features.csv"
        if not features_path.exists():
            run_feature_engineering_pipeline()

        # Run the full training pipeline
        # This function orchestrates CV, hyperparameter tuning, and model saving
        metrics = run_training_pipeline()

        # Assertions on the returned metrics dictionary
        assert metrics is not None, "Training pipeline returned None"
        assert "linear_regression" in metrics, "Missing linear_regression metrics"
        assert "random_forest" in metrics, "Missing random_forest metrics"

        # Check Linear Regression metrics structure
        lr_metrics = metrics["linear_regression"]
        assert "r2" in lr_metrics, "Linear Regression missing R²"
        assert "mae" in lr_metrics, "Linear Regression missing MAE"
        assert "rmse" in lr_metrics, "Linear Regression missing RMSE"
        assert "cv_score" in lr_metrics, "Linear Regression missing CV score"

        # Check Random Forest metrics structure
        rf_metrics = metrics["random_forest"]
        assert "r2" in rf_metrics, "Random Forest missing R²"
        assert "mae" in rf_metrics, "Random Forest missing MAE"
        assert "rmse" in rf_metrics, "Random Forest missing RMSE"
        assert "cv_score" in rf_metrics, "Random Forest missing CV score"

        # Verify models were saved to disk
        linear_model_path = MODELS_DIR / "linear_model.joblib"
        rf_model_path = MODELS_DIR / "rf_model.joblib"

        assert linear_model_path.exists(), "Linear model not saved to disk"
        assert rf_model_path.exists(), "Random Forest model not saved to disk"

        logger.info("Training pipeline successfully executed k-fold CV and saved models.")

    def test_model_metrics_json_generated(self):
        """
        Verify that model_metrics.json is generated with valid R² and MAE values
        for both models.
        """
        logger.info("Verifying model_metrics.json generation...")

        metrics_path = DATA_PROCESSED / "model_metrics.json"

        # Ensure the pipeline runs to generate the file if it doesn't exist
        if not metrics_path.exists():
            # Run training pipeline which should generate the metrics
            run_training_pipeline()

        assert metrics_path.exists(), "model_metrics.json was not generated"

        with open(metrics_path, 'r') as f:
            data = json.load(f)

        # Validate structure
        assert "linear_regression" in data, "JSON missing linear_regression key"
        assert "random_forest" in data, "JSON missing random_forest key"

        # Validate values
        lr = data["linear_regression"]
        rf = data["random_forest"]

        # Check R² exists and is a number
        assert isinstance(lr.get("r2"), (int, float)), "Linear R² must be a number"
        assert isinstance(rf.get("r2"), (int, float)), "RF R² must be a number"

        # Check MAE exists and is a number
        assert isinstance(lr.get("mae"), (int, float)), "Linear MAE must be a number"
        assert isinstance(rf.get("mae"), (int, float)), "RF MAE must be a number"

        logger.info("model_metrics.json validated successfully.")

    def test_full_integration_flow(self):
        """
        End-to-end integration test:
        1. Preprocess data -> alloys_raw.csv
        2. Engineer features -> alloys_features.csv
        3. Train models -> code/models/
        4. Generate metrics -> model_metrics.json
        """
        logger.info("Starting full integration flow...")

        # Step 1: Preprocessing
        run_preprocessing_pipeline()
        assert (DATA_PROCESSED / "alloys_raw.csv").exists()

        # Step 2: Feature Engineering
        run_feature_engineering_pipeline()
        assert (DATA_PROCESSED / "alloys_features.csv").exists()

        # Step 3: Training
        metrics = run_training_pipeline()
        assert metrics is not None
        assert (MODELS_DIR / "linear_model.joblib").exists()
        assert (MODELS_DIR / "rf_model.joblib").exists()

        # Step 4: Metrics Validation
        metrics_path = DATA_PROCESSED / "model_metrics.json"
        assert metrics_path.exists()
        with open(metrics_path, 'r') as f:
            final_metrics = json.load(f)
        
        assert "linear_regression" in final_metrics
        assert "random_forest" in final_metrics
        assert final_metrics["linear_regression"]["r2"] is not None
        assert final_metrics["random_forest"]["r2"] is not None

        logger.info("Full integration flow completed successfully.")