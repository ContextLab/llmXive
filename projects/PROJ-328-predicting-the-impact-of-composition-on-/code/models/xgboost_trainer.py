"""
XGBoost Trainer Module for Solder Hardness Prediction.

Implements XGBoost regression training with grid search (<=10 combinations),
cross-validation, and model persistence.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import GridSearchCV, cross_val_score, KFold
from sklearn.metrics import r2_score, mean_squared_error, make_scorer
from sklearn.preprocessing import StandardScaler

# Project imports
from seed import init_reproducibility
from config import (
    get_data_processed_dir,
    get_models_dir,
    get_cv_folds,
    get_bootstrap_iterations,
)
from utils.error_handlers import ModelTrainingError, DataValidationError
from utils.logging_config import get_logger
from features.collinearity import calculate_vif, get_collinear_features
from features.descriptor_engine import DescriptorEngine

logger = get_logger(__name__)


class XGBoostTrainer:
    """
    Trainer class for XGBoost models with hyperparameter tuning.
    """

    def __init__(self, seed: int = 42, cv_folds: Optional[int] = None):
        """
        Initialize the trainer.

        Args:
            seed: Random seed for reproducibility.
            cv_folds: Number of cross-validation folds.
        """
        init_reproducibility(seed)
        self.seed = seed
        self.cv_folds = cv_folds or get_cv_folds()
        self.model: Optional[xgb.XGBRegressor] = None
        self.best_params: Dict[str, Any] = {}
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []
        self.metrics_history: List[Dict[str, Any]] = []

    def load_data(self, data_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Load the validated dataset.

        Args:
            data_path: Path to the CSV file. If None, uses config default.

        Returns:
            DataFrame with composition and hardness data.
        """
        if data_path is None:
            processed_dir = get_data_processed_dir()
            data_path = processed_dir / "solder_hardness_validated.csv"

        if not data_path.exists():
            raise DataValidationError(
                f"Validated data file not found: {data_path}. "
                "Run ingestion pipeline first."
            )

        logger.info(f"Loading data from {data_path}")
        df = pd.read_csv(data_path)

        # Identify target column
        target_col = "hardness_hv"
        if target_col not in df.columns:
            # Try to find a column that looks like hardness
            hardness_cols = [c for c in df.columns if "hardness" in c.lower()]
            if not hardness_cols:
                raise DataValidationError(
                    f"Target column '{target_col}' not found in dataset. "
                    f"Available columns: {list(df.columns)}"
                )
            target_col = hardness_cols[0]
            logger.warning(f"Using '{target_col}' as target column.")

        self.target_col = target_col
        logger.info(f"Loaded {len(df)} samples. Target: {target_col}")
        return df

    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features and target for training.

        Args:
            df: DataFrame with composition and target.

        Returns:
            Tuple of (X_features, y_target).
        """
        # Identify feature columns (exclude target and metadata)
        exclude_cols = {self.target_col, "alloy_id", "source", "citation"}
        feature_cols = [c for c in df.columns if c not in exclude_cols]

        if not feature_cols:
            raise DataValidationError("No feature columns found in dataset.")

        self.feature_names = feature_cols
        logger.info(f"Using {len(feature_cols)} features: {feature_cols}")

        X = df[feature_cols].values
        y = df[self.target_col].values

        # Handle missing values
        if np.any(np.isnan(X)):
            logger.warning("NaN values found in features. Imputing with mean.")
            from sklearn.impute import SimpleImputer
            imputer = SimpleImputer(strategy='mean')
            X = imputer.fit_transform(X)

        if np.any(np.isnan(y)):
            logger.warning("NaN values found in target. Dropping those rows.")
            valid_mask = ~np.isnan(y)
            X = X[valid_mask]
            y = y[valid_mask]

        return X, y

    def tune_hyperparameters(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """
        Perform grid search for best hyperparameters (<=10 combinations).

        Args:
            X: Feature matrix.
            y: Target vector.

        Returns:
            Dictionary of best parameters.
        """
        logger.info("Starting hyperparameter tuning with GridSearchCV...")

        # Define parameter grid (max 10 combinations)
        # n_estimators: 2 values
        # max_depth: 2 values
        # learning_rate: 2 values
        # Total: 2 * 2 * 2 = 8 combinations (within limit of 10)
        param_grid = {
            'n_estimators': [50, 100],
            'max_depth': [3, 5],
            'learning_rate': [0.05, 0.1],
            'subsample': [0.8],
            'colsample_bytree': [0.8],
            'objective': ['reg:squarederror'],
            'random_state': [self.seed],
            'n_jobs': [-1],
            'verbosity': [0]
        }

        base_model = xgb.XGBRegressor()

        cv = KFold(n_splits=self.cv_folds, shuffle=True, random_state=self.seed)

        grid_search = GridSearchCV(
            estimator=base_model,
            param_grid=param_grid,
            cv=cv,
            scoring='r2',
            n_jobs=-1,
            verbose=1,
            refit=True
        )

        # Scale features for XGBoost (though not strictly necessary, helps some params)
        X_scaled = self.scaler.fit_transform(X)

        grid_search.fit(X_scaled, y)

        self.best_params = grid_search.best_params_
        logger.info(f"Best parameters: {self.best_params}")
        logger.info(f"Best CV R² score: {grid_search.best_score_:.4f}")

        # Log all results for transparency
        results_df = pd.DataFrame(grid_search.cv_results_)
        logger.debug(f"Grid search results:\n{results_df[['params', 'mean_test_score', 'rank_test_score']]}")

        return self.best_params

    def train_model(self, X: np.ndarray, y: np.ndarray, params: Dict[str, Any]) -> xgb.XGBRegressor:
        """
        Train the final XGBoost model with best parameters.

        Args:
            X: Feature matrix.
            y: Target vector.
            params: Best hyperparameters.

        Returns:
            Trained XGBRegressor model.
        """
        logger.info("Training final model with best parameters...")

        X_scaled = self.scaler.transform(X)

        self.model = xgb.XGBRegressor(**params)
        self.model.fit(X_scaled, y)

        # Training metrics
        y_pred_train = self.model.predict(X_scaled)
        train_r2 = r2_score(y, y_pred_train)
        train_rmse = np.sqrt(mean_squared_error(y, y_pred_train))

        logger.info(f"Training complete. Train R²: {train_r2:.4f}, RMSE: {train_rmse:.2f}")

        return self.model

    def evaluate_model(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance using cross-validation.

        Args:
            X: Feature matrix.
            y: Target vector.

        Returns:
            Dictionary of evaluation metrics.
        """
        if self.model is None:
            raise ModelTrainingError("No model trained. Call train_model first.")

        logger.info("Evaluating model with cross-validation...")

        X_scaled = self.scaler.transform(X)
        cv = KFold(n_splits=self.cv_folds, shuffle=True, random_state=self.seed)

        # Cross-validation scores
        cv_r2_scores = cross_val_score(
            self.model, X_scaled, y, cv=cv, scoring='r2', n_jobs=-1
        )
        cv_rmse_scores = cross_val_score(
            self.model, X_scaled, y, cv=cv, scoring='neg_mean_squared_error', n_jobs=-1
        )
        cv_rmse_scores = np.sqrt(-cv_rmse_scores)

        metrics = {
            'cv_r2_mean': float(np.mean(cv_r2_scores)),
            'cv_r2_std': float(np.std(cv_r2_scores)),
            'cv_rmse_mean': float(np.mean(cv_rmse_scores)),
            'cv_rmse_std': float(np.std(cv_rmse_scores)),
            'cv_folds': self.cv_folds,
            'n_samples': len(y)
        }

        logger.info(f"CV R²: {metrics['cv_r2_mean']:.4f} (+/- {metrics['cv_r2_std']:.4f})")
        logger.info(f"CV RMSE: {metrics['cv_rmse_mean']:.2f} (+/- {metrics['cv_rmse_std']:.2f})")

        return metrics

    def save_model(self, output_dir: Optional[Path] = None) -> Path:
        """
        Save the trained model and metadata.

        Args:
            output_dir: Directory to save artifacts. If None, uses config default.

        Returns:
            Path to the saved model directory.
        """
        if self.model is None:
            raise ModelTrainingError("No model to save. Train first.")

        if output_dir is None:
            output_dir = get_models_dir()

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        model_path = output_dir / "xgboost_hardness_model.json"
        metadata_path = output_dir / "xgboost_training_metadata.json"

        # Save model in XGBoost JSON format
        self.model.save_model(str(model_path))
        logger.info(f"Model saved to {model_path}")

        # Save metadata
        metadata = {
            'best_params': self.best_params,
            'feature_names': self.feature_names,
            'target_col': self.target_col,
            'seed': self.seed,
            'cv_folds': self.cv_folds,
            'scaler_mean': self.scaler.mean_.tolist(),
            'scaler_scale': self.scaler.scale_.tolist(),
            'metrics_history': self.metrics_history
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Metadata saved to {metadata_path}")
        return output_dir

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance from the trained model.

        Returns:
            DataFrame with feature names and importance scores.
        """
        if self.model is None:
            raise ModelTrainingError("No model trained. Cannot get importance.")

        importance_scores = self.model.feature_importances_
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance_scores
        }).sort_values('importance', ascending=False)

        return importance_df


def main():
    """
    Main entry point for XGBoost training pipeline.
    """
    logger.info("Starting XGBoost Training Pipeline")

    try:
        # Initialize trainer
        trainer = XGBoostTrainer(seed=42)

        # Load data
        df = trainer.load_data()

        # Prepare features
        X, y = trainer.prepare_features(df)

        # Tune hyperparameters
        best_params = trainer.tune_hyperparameters(X, y)

        # Train final model
        trainer.train_model(X, y, best_params)

        # Evaluate
        metrics = trainer.evaluate_model(X, y)
        trainer.metrics_history.append(metrics)

        # Get feature importance
        importance_df = trainer.get_feature_importance()
        logger.info(f"Top 5 features:\n{importance_df.head(5)}")

        # Save model
        output_dir = trainer.save_model()

        # Save feature importance
        importance_path = output_dir / "xgboost_feature_importance.csv"
        importance_df.to_csv(importance_path, index=False)
        logger.info(f"Feature importance saved to {importance_path}")

        logger.info("XGBoost training completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"XGBoost training failed: {e}", exc_info=True)
        raise ModelTrainingError(f"Training failed: {e}") from e


if __name__ == "__main__":
    sys.exit(main())
