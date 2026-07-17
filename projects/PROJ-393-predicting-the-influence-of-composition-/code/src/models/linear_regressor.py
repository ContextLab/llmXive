"""
Linear Regression Model for Heusler Alloy Hysteresis Prediction.

Implements baseline linear regression with hyperparameter tuning using GridSearchCV.
This module is part of User Story 2 (Feature Engineering and Model Training).
"""

import logging
import json
from pathlib import Path
from typing import Dict, Optional, Any, Tuple

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

from src.utils.logging_config import setup_logging

# Configure logging
logger = setup_logging(__name__)

# Default paths
DEFAULT_INPUT_PATH = Path("data/processed/alloys_features.csv")
DEFAULT_OUTPUT_DIR = Path("code/models")
DEFAULT_METRICS_PATH = Path("data/processed/model_metrics.json")
DEFAULT_MODEL_PATH = Path("code/models/linear_regressor.joblib")
DEFAULT_SCALER_PATH = Path("code/models/linear_scaler.joblib")


def load_features_data(input_path: Path) -> pd.DataFrame:
    """
    Load the feature-engineered dataset.

    Args:
        input_path: Path to the CSV file containing features.

    Returns:
        DataFrame with features and target variables.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")

    # Validate required columns
    required_cols = [
        'coercivity_normalized', 'saturation_magnetization_normalized',
        'average_electronegativity', 'valence_electron_concentration',
        'atomic_radii_variance', 'average_d_electrons', 'atomic_size_mismatch'
    ]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df


def prepare_data(df: pd.DataFrame, target_col: str = 'coercivity_normalized') -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare features (X) and target (y) for training.

    Args:
        df: DataFrame with features and target.
        target_col: Name of the target column.

    Returns:
        Tuple of (X, y) as numpy arrays.
    """
    feature_cols = [
        'average_electronegativity',
        'valence_electron_concentration',
        'atomic_radii_variance',
        'average_d_electrons',
        'atomic_size_mismatch'
    ]

    X = df[feature_cols].values
    y = df[target_col].values

    # Handle missing values if any
    if np.any(np.isnan(X)) or np.any(np.isnan(y)):
        logger.warning("NaN values detected. Dropping rows with missing values.")
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]

    logger.info(f"Prepared data: X shape {X.shape}, y shape {y.shape}")
    return X, y


def create_model_pipeline(regressor: str = 'linear') -> Pipeline:
    """
    Create a scikit-learn pipeline with scaling and regression.

    Args:
        regressor: Type of regressor ('linear', 'ridge', 'lasso').

    Returns:
        A scikit-learn Pipeline.
    """
    if regressor == 'linear':
        model = LinearRegression()
    elif regressor == 'ridge':
        model = Ridge()
    elif regressor == 'lasso':
        model = Lasso()
    else:
        raise ValueError(f"Unknown regressor type: {regressor}")

    return Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', model)
    ])


def tune_hyperparameters(X: np.ndarray, y: np.ndarray, model_type: str = 'ridge', cv: int = 5) -> Tuple[Any, Dict[str, Any]]:
    """
    Perform hyperparameter tuning using GridSearchCV.

    Args:
        X: Feature matrix.
        y: Target vector.
        model_type: Type of model to tune ('linear', 'ridge', 'lasso').
        cv: Number of cross-validation folds.

    Returns:
        Tuple of (best_model, best_params).
    """
    pipeline = create_model_pipeline(model_type)

    if model_type == 'linear':
        param_grid = {
            'regressor__fit_intercept': [True, False]
        }
    elif model_type == 'ridge':
        param_grid = {
            'regressor__alpha': [0.01, 0.1, 1.0, 10.0, 100.0]
        }
    elif model_type == 'lasso':
        param_grid = {
            'regressor__alpha': [0.01, 0.1, 1.0, 10.0, 100.0]
        }
    else:
        raise ValueError(f"Unsupported model type for tuning: {model_type}")

    logger.info(f"Starting GridSearchCV for {model_type} with {len(param_grid['regressor__alpha']) if 'alpha' in param_grid else 2} parameter combinations.")

    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=cv,
        scoring='r2',
        n_jobs=-1,
        verbose=1
    )

    grid_search.fit(X, y)

    logger.info(f"Best parameters: {grid_search.best_params_}")
    logger.info(f"Best CV R² score: {grid_search.best_score_:.4f}")

    return grid_search.best_estimator_, grid_search.best_params_


def evaluate_model(model: Pipeline, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Evaluate the model using cross-validation and hold-out metrics.

    Args:
        model: Fitted scikit-learn pipeline.
        X: Feature matrix.
        y: Target vector.

    Returns:
        Dictionary of evaluation metrics.
    """
    # Cross-validation scores
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
    cv_r2_mean = cv_scores.mean()
    cv_r2_std = cv_scores.std()

    # Train-test split for detailed metrics
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    metrics = {
        'cv_r2_mean': float(cv_r2_mean),
        'cv_r2_std': float(cv_r2_std),
        'test_mse': float(mse),
        'test_rmse': float(rmse),
        'test_mae': float(mae),
        'test_r2': float(r2),
        'n_samples': int(len(X)),
        'n_test_samples': int(len(X_test))
    }

    logger.info(f"Evaluation Results: R²={r2:.4f}, RMSE={rmse:.4f}, MAE={mae:.4f}")
    return metrics


def save_model(model: Pipeline, output_path: Path) -> None:
    """
    Save the trained model to disk.

    Args:
        model: Fitted scikit-learn pipeline.
        output_path: Path to save the model.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    logger.info(f"Model saved to {output_path}")


def save_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Save evaluation metrics to a JSON file.

    Args:
        metrics: Dictionary of metrics.
        output_path: Path to save the metrics.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")


def run_linear_regression(
    input_path: Path = DEFAULT_INPUT_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    metrics_path: Path = DEFAULT_METRICS_PATH,
    model_type: str = 'ridge',
    target_col: str = 'coercivity_normalized',
    cv_folds: int = 5
) -> Dict[str, Any]:
    """
    Main function to run the linear regression pipeline with hyperparameter tuning.

    Args:
        input_path: Path to input features CSV.
        output_dir: Directory to save models.
        metrics_path: Path to save metrics JSON.
        model_type: Type of linear model ('linear', 'ridge', 'lasso').
        target_col: Target column name.
        cv_folds: Number of cross-validation folds.

    Returns:
        Dictionary containing model and metrics.
    """
    logger.info(f"Starting Linear Regression Pipeline for {model_type}")

    # Load data
    df = load_features_data(input_path)

    # Prepare data
    X, y = prepare_data(df, target_col)

    if len(X) < 10:
        raise ValueError(f"Insufficient data for training: {len(X)} samples. Need at least 10.")

    # Tune hyperparameters
    best_model, best_params = tune_hyperparameters(X, y, model_type, cv=cv_folds)

    # Evaluate model
    metrics = evaluate_model(best_model, X, y)
    metrics['model_type'] = model_type
    metrics['best_params'] = best_params

    # Save outputs
    model_path = output_dir / f"{model_type}_regressor.joblib"
    save_model(best_model, model_path)
    save_metrics(metrics, metrics_path)

    logger.info("Linear Regression pipeline completed successfully.")

    return {
        'model': best_model,
        'metrics': metrics,
        'model_path': str(model_path),
        'metrics_path': str(metrics_path)
    }


def main() -> None:
    """
    Entry point for running the linear regression model training.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Train Linear Regression model for Heusler alloys.")
    parser.add_argument('--input', type=str, default=str(DEFAULT_INPUT_PATH),
                        help='Path to input features CSV')
    parser.add_argument('--output-dir', type=str, default=str(DEFAULT_OUTPUT_DIR),
                        help='Directory to save models')
    parser.add_argument('--metrics-path', type=str, default=str(DEFAULT_METRICS_PATH),
                        help='Path to save metrics JSON')
    parser.add_argument('--model-type', type=str, default='ridge',
                        choices=['linear', 'ridge', 'lasso'],
                        help='Type of linear model to train')
    parser.add_argument('--target', type=str, default='coercivity_normalized',
                        help='Target column name')
    parser.add_argument('--cv-folds', type=int, default=5,
                        help='Number of cross-validation folds')

    args = parser.parse_args()

    run_linear_regression(
        input_path=Path(args.input),
        output_dir=Path(args.output_dir),
        metrics_path=Path(args.metrics_path),
        model_type=args.model_type,
        target_col=args.target,
        cv_folds=args.cv_folds
    )


if __name__ == "__main__":
    main()
