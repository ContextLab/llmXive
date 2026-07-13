import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

from seed import init_reproducibility, get_seed_env_vars
from config import get_data_processed_dir, get_models_dir, get_cv_folds, get_log_level, get_log_format
from utils.logging_config import setup_logging, get_logger
from utils.error_handlers import ModelTrainingError

# Configure logging
logger = get_logger(__name__)

class LinearRegressionTrainer:
    """
    Trainer for Linear Regression baseline model.
    
    This class handles loading validated data, training a Linear Regression model,
    performing cross-validation, and saving model artifacts and metrics.
    """

    def __init__(self, seed: int = 42):
        """
        Initialize the Linear Regression trainer.
        
        Args:
            seed: Random seed for reproducibility.
        """
        self.seed = seed
        init_reproducibility(seed)
        self.model = LinearRegression()
        self.metrics: Dict[str, Any] = {}
        self.cv_scores: Optional[np.ndarray] = None
        self.feature_names: Optional[List[str]] = None
        self.target_name = "hardness_hv"

    def load_data(self, data_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Load the validated dataset.
        
        Args:
            data_path: Optional path to the validated CSV. If None, uses config default.
        
        Returns:
            Loaded DataFrame.
        
        Raises:
            ModelTrainingError: If data file is not found or is invalid.
        """
        if data_path is None:
            processed_dir = get_data_processed_dir()
            data_path = Path(processed_dir) / "solder_hardness_validated.csv"
        
        if not data_path.exists():
            raise ModelTrainingError(f"Validated data file not found: {data_path}")
        
        logger.info(f"Loading validated data from {data_path}")
        df = pd.read_csv(data_path)
        
        if self.target_name not in df.columns:
            raise ModelTrainingError(f"Target column '{self.target_name}' not found in data. Columns: {df.columns.tolist()}")
        
        # Identify feature columns (exclude target and metadata columns)
        exclude_cols = [self.target_name, "source", "citation", "alloy_name", "composition_string"]
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        if not feature_cols:
            raise ModelTrainingError("No feature columns found in the dataset.")
        
        self.feature_names = feature_cols
        logger.info(f"Using {len(feature_cols)} features: {feature_cols}")
        
        return df

    def train(self, df: pd.DataFrame) -> None:
        """
        Train the Linear Regression model.
        
        Args:
            df: DataFrame containing features and target.
        """
        X = df[self.feature_names].values
        y = df[self.target_name].values

        logger.info(f"Training Linear Regression model on {len(df)} samples with {len(self.feature_names)} features")
        
        try:
            self.model.fit(X, y)
            logger.info("Linear Regression model trained successfully")
        except Exception as e:
            raise ModelTrainingError(f"Failed to train Linear Regression model: {str(e)}")

    def evaluate_cv(self, df: pd.DataFrame, cv_folds: Optional[int] = None) -> Dict[str, float]:
        """
        Perform k-fold cross-validation.
        
        Args:
            df: DataFrame containing features and target.
            cv_folds: Number of CV folds. If None, uses config default.
        
        Returns:
            Dictionary with CV metrics.
        """
        if cv_folds is None:
            cv_folds = get_cv_folds()
        
        X = df[self.feature_names].values
        y = df[self.target_name].values

        logger.info(f"Performing {cv_folds}-fold cross-validation")
        
        # Calculate R2 scores
        r2_scores = cross_val_score(self.model, X, y, cv=cv_folds, scoring='r2')
        
        # Calculate negative MSE scores (sklearn returns negative MSE for cross_val_score)
        mse_scores = cross_val_score(self.model, X, y, cv=cv_folds, scoring='neg_mean_squared_error')
        rmse_scores = np.sqrt(-mse_scores)
        
        self.cv_scores = r2_scores

        metrics = {
            "cv_r2_mean": float(np.mean(r2_scores)),
            "cv_r2_std": float(np.std(r2_scores)),
            "cv_rmse_mean": float(np.mean(rmse_scores)),
            "cv_rmse_std": float(np.std(rmse_scores)),
            "cv_folds": cv_folds,
            "r2_scores": r2_scores.tolist()
        }

        logger.info(f"CV R²: {metrics['cv_r2_mean']:.4f} ± {metrics['cv_r2_std']:.4f}")
        logger.info(f"CV RMSE: {metrics['cv_rmse_mean']:.4f} ± {metrics['cv_rmse_std']:.4f}")
        
        return metrics

    def evaluate_test(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Evaluate model on the full dataset (as a simple test, since we don't have a separate split here).
        
        Args:
            df: DataFrame containing features and target.
        
        Returns:
            Dictionary with test metrics.
        """
        X = df[self.feature_names].values
        y = df[self.target_name].values

        y_pred = self.model.predict(X)
        
        r2 = r2_score(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        mae = mean_absolute_error(y, y_pred)

        metrics = {
            "test_r2": float(r2),
            "test_rmse": float(rmse),
            "test_mae": float(mae),
            "n_samples": len(df)
        }

        logger.info(f"Test R²: {metrics['test_r2']:.4f}")
        logger.info(f"Test RMSE: {metrics['test_rmse']:.4f}")
        logger.info(f"Test MAE: {metrics['test_mae']:.4f}")
        
        return metrics

    def get_coefficients(self) -> Dict[str, float]:
        """
        Get model coefficients.
        
        Returns:
            Dictionary mapping feature names to coefficients.
        """
        if self.feature_names is None or self.model.coef_ is None:
            raise ModelTrainingError("Model not trained yet. Call train() first.")
        
        return dict(zip(self.feature_names, self.model.coef_.tolist()))

    def get_intercept(self) -> float:
        """
        Get model intercept.
        
        Returns:
            Intercept value.
        """
        if self.model.intercept_ is None:
            raise ModelTrainingError("Model not trained yet. Call train() first.")
        
        return float(self.model.intercept_)

    def save_artifacts(self, output_dir: Optional[Path] = None) -> Path:
        """
        Save model artifacts, metrics, and diagnostics.
        
        Args:
            output_dir: Optional directory to save artifacts. If None, uses config default.
        
        Returns:
            Path to the output directory.
        """
        if output_dir is None:
            models_dir = get_models_dir()
            output_dir = Path(models_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model coefficients and intercept
        coefficients = self.get_coefficients()
        intercept = self.get_intercept()
        
        model_info = {
            "model_type": "LinearRegression",
            "seed": self.seed,
            "feature_names": self.feature_names,
            "coefficients": coefficients,
            "intercept": intercept,
            "metrics": self.metrics,
            "cv_scores": self.cv_scores.tolist() if self.cv_scores is not None else None
        }
        
        model_path = output_dir / "linear_regression_model.json"
        with open(model_path, 'w') as f:
            json.dump(model_info, f, indent=2)
        
        logger.info(f"Saved model artifacts to {model_path}")
        
        return output_dir

    def run_full_pipeline(self, data_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Run the complete training pipeline.
        
        Args:
            data_path: Optional path to validated data.
        
        Returns:
            Dictionary containing all metrics and paths.
        """
        # Load data
        df = self.load_data(data_path)
        
        # Train model
        self.train(df)
        
        # Evaluate with CV
        cv_metrics = self.evaluate_cv(df)
        
        # Evaluate on full dataset
        test_metrics = self.evaluate_test(df)
        
        # Combine metrics
        self.metrics = {
            **cv_metrics,
            **test_metrics,
            "coefficients": self.get_coefficients(),
            "intercept": self.get_intercept()
        }
        
        # Save artifacts
        output_dir = self.save_artifacts()
        
        return {
            "metrics": self.metrics,
            "output_dir": str(output_dir),
            "model_path": str(output_dir / "linear_regression_model.json")
        }


def main():
    """Main entry point for Linear Regression training."""
    # Setup logging
    setup_logging(get_log_level(), get_log_format())
    
    logger.info("=" * 60)
    logger.info("Starting Linear Regression Training (T024)")
    logger.info("=" * 60)
    
    try:
        trainer = LinearRegressionTrainer(seed=42)
        results = trainer.run_full_pipeline()
        
        logger.info("=" * 60)
        logger.info("Linear Regression Training Complete")
        logger.info(f"R² (CV): {results['metrics']['cv_r2_mean']:.4f} ± {results['metrics']['cv_r2_std']:.4f}")
        logger.info(f"R² (Test): {results['metrics']['test_r2']:.4f}")
        logger.info(f"Model saved to: {results['model_path']}")
        logger.info("=" * 60)
        
        return results
        
    except ModelTrainingError as e:
        logger.error(f"Model training failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during training: {str(e)}")
        raise ModelTrainingError(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
