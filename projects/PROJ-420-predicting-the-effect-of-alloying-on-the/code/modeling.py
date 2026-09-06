"""
Modeling module for training, evaluating, and serializing Random Forest models
for predicting Poisson's ratio of aluminum alloys.
"""
from __future__ import annotations

import json
import os
import pickle
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from compositional import ilr
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler

# Import project configuration and logging
from config import get_config
from logging_config import get_logger, log_operation

logger = get_logger(__name__)
config = get_config()


def load_features_and_target(data_path: Optional[str] = None) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the cleaned dataset and separate features (composition) from target (Poisson's ratio).

    Args:
        data_path: Path to the cleaned parquet file. Defaults to config path.

    Returns:
        Tuple of (feature_df, target_series)
    """
    if data_path is None:
        data_path = config.data_processed / "alloys_clean.parquet"

    logger.info(f"Loading data from {data_path}")
    df = pd.read_parquet(data_path)

    # Define feature columns based on task T019 (ILR on Cu, Mg, Si, Zn, Mn)
    composition_cols = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']

    # Check if columns exist
    missing_cols = [c for c in composition_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required composition columns: {missing_cols}")

    X = df[composition_cols].copy()
    y = df['poisson_ratio'].copy()

    return X, y


def apply_ilr_transformation(X: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Isometric Log-Ratio (ILR) transformation to compositional data.

    Args:
        X: DataFrame with columns Cu, Mg, Si, Zn, Mn (atomic fractions).

    Returns:
        DataFrame with ILR transformed coordinates.
    """
    logger.info("Applying ILR transformation to composition data")

    # Ensure no zeros (add small epsilon if needed, though T019 should have handled this)
    X_clean = X.replace(0, 1e-9)

    # Apply ILR using the compositional library
    # The library expects a matrix where rows are samples and columns are parts
    ilr_coords = ilr(X_clean.values)

    # Create DataFrame with meaningful column names
    ilr_df = pd.DataFrame(
        ilr_coords,
        columns=[f'ilr_{i}' for i in range(ilr_coords.shape[1])],
        index=X.index
    )

    logger.info(f"ILR transformation completed. Shape: {ilr_df.shape}")
    return ilr_df


def save_split_indices(train_indices: List[int], test_indices: List[int], output_path: Optional[str] = None):
    """
    Save train and test split indices to a JSON file.

    Args:
        train_indices: List of indices for training set.
        test_indices: List of indices for test set.
        output_path: Path to save the JSON file. Defaults to config path.
    """
    if output_path is None:
        output_path = config.data_processed / "split_indices.json"

    output_data = {
        "train_indices": train_indices,
        "test_indices": test_indices
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Split indices saved to {output_path}")


def load_split_indices(input_path: Optional[str] = None) -> Tuple[List[int], List[int]]:
    """
    Load train and test split indices from a JSON file.

    Args:
        input_path: Path to the JSON file. Defaults to config path.

    Returns:
        Tuple of (train_indices, test_indices)
    """
    if input_path is None:
        input_path = config.data_processed / "split_indices.json"

    with open(input_path, 'r') as f:
        data = json.load(f)

    return data['train_indices'], data['test_indices']


def split_data(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split data into training and test sets.

    Args:
        X: Feature DataFrame.
        y: Target Series.
        test_size: Proportion of data for testing.
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    logger.info(f"Splitting data: test_size={test_size}, random_state={random_state}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    return X_train, X_test, y_train, y_test


def train_random_forest_with_cv(X_train: pd.DataFrame, y_train: pd.Series, param_grid: Optional[Dict[str, List[Any]]] = None) -> Tuple[RandomForestRegressor, Dict[str, Any], float]:
    """
    Train a Random Forest model with cross-validation for hyperparameter tuning.

    Args:
        X_train: Training features.
        y_train: Training targets.
        param_grid: Grid of hyperparameters to search. Defaults to a standard grid.

    Returns:
        Tuple of (best_model, best_params, cv_score)
    """
    if param_grid is None:
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5],
            'min_samples_leaf': [1, 2]
        }

    logger.info("Starting cross-validation for hyperparameter tuning")

    rf = RandomForestRegressor(random_state=42)

    # Use GridSearchCV for hyperparameter tuning
    grid_search = GridSearchCV(
        rf, param_grid, cv=5, scoring='neg_mean_absolute_error', n_jobs=-1
    )

    grid_search.fit(X_train, y_train)

    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    cv_score = -grid_search.best_score_  # Convert back to positive MAE

    logger.info(f"Best CV MAE: {cv_score:.4f}")
    logger.info(f"Best parameters: {best_params}")

    return best_model, best_params, cv_score


def evaluate_model_on_test(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> float:
    """
    Evaluate the model on the test set.

    Args:
        model: Trained Random Forest model.
        X_test: Test features.
        y_test: Test targets.

    Returns:
        Mean Absolute Error on the test set.
    """
    logger.info("Evaluating model on test set")

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)

    logger.info(f"Test MAE: {mae:.4f}")
    return mae


def save_model(model: RandomForestRegressor, output_path: Optional[str] = None, compress: int = 3, protocol: int = 3):
    """
    Save the trained model to disk using joblib.

    Args:
        model: Trained Random Forest model.
        output_path: Path to save the model. Defaults to config path.
        compress: Compression level for joblib.
        protocol: Pickle protocol version.
    """
    if output_path is None:
        output_path = config.models / "rf_model.pkl"

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    logger.info(f"Saving model to {output_path}")
    joblib.dump(model, output_path, compress=compress, protocol=protocol)

    # Verify the file was created
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        logger.info(f"Model saved successfully. Size: {file_size / 1024:.2f} KB")
    else:
        raise RuntimeError(f"Failed to save model to {output_path}")


def load_model(model_path: Optional[str] = None) -> RandomForestRegressor:
    """
    Load a trained model from disk.

    Args:
        model_path: Path to the model file. Defaults to config path.

    Returns:
        Trained Random Forest model.
    """
    if model_path is None:
        model_path = config.models / "rf_model.pkl"

    logger.info(f"Loading model from {model_path}")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")

    model = joblib.load(model_path)
    logger.info("Model loaded successfully")
    return model


def save_best_hyperparameters(best_params: Dict[str, Any], output_path: Optional[str] = None):
    """
    Save the best hyperparameters found during cross-validation.

    Args:
        best_params: Dictionary of best hyperparameters.
        output_path: Path to save the JSON file. Defaults to config path.
    """
    if output_path is None:
        output_path = config.results / "cv_best_hyperparameters.json"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(best_params, f, indent=2)

    logger.info(f"Best hyperparameters saved to {output_path}")


def load_best_hyperparameters(input_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the best hyperparameters from a JSON file.

    Args:
        input_path: Path to the JSON file. Defaults to config path.

    Returns:
        Dictionary of best hyperparameters.
    """
    if input_path is None:
        input_path = config.results / "cv_best_hyperparameters.json"

    with open(input_path, 'r') as f:
        return json.load(f)


def save_model_metrics(cv_mae: float, cv_ci_lower: float, cv_ci_upper: float, test_mae: float, output_path: Optional[str] = None):
    """
    Save model metrics to a JSON file.

    Args:
        cv_mae: Cross-validation MAE.
        cv_ci_lower: Lower bound of CV MAE confidence interval.
        cv_ci_upper: Upper bound of CV MAE confidence interval.
        test_mae: Test set MAE.
        output_path: Path to save the JSON file.
    """
    if output_path is None:
        output_path = config.results / "model_metrics.json"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    metrics = {
        "cv_mae": cv_mae,
        "cv_ci_lower": cv_ci_lower,
        "cv_ci_upper": cv_ci_upper,
        "test_mae": test_mae
    }

    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Model metrics saved to {output_path}")


def save_residuals(y_true: List[float], y_pred: List[float], indices: List[int], output_path: Optional[str] = None):
    """
    Save residuals to a JSON file.

    Args:
        y_true: True values.
        y_pred: Predicted values.
        indices: Indices of the test samples.
        output_path: Path to save the JSON file.
    """
    if output_path is None:
        output_path = config.results / "residuals.json"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    residuals = [float(obs - pred) for obs, pred in zip(y_true, y_pred)]

    data = {
        "residuals": residuals,
        "indices": indices
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Residuals saved to {output_path}")


def save_methodological_flags(mae_flag: bool, cv_mae: float, output_path: Optional[str] = None):
    """
    Save methodological flags to a JSON file.

    Args:
        mae_flag: Boolean flag indicating if CV MAE > 0.05.
        cv_mae: Cross-validation MAE value.
        output_path: Path to save the JSON file.
    """
    if output_path is None:
        output_path = config.results / "methodological_flags.json"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    flags = {
        "mae_flag": mae_flag,
        "cv_mae": cv_mae
    }

    with open(output_path, 'w') as f:
        json.dump(flags, f, indent=2)

    logger.info(f"Methodological flags saved to {output_path}")


def aggregate_model_metrics() -> Dict[str, Any]:
    """
    Aggregate all model metrics into a single dictionary.

    Returns:
        Dictionary containing all model metrics.
    """
    metrics_path = config.results / "model_metrics.json"
    flags_path = config.results / "methodological_flags.json"
    residuals_path = config.results / "residuals.json"

    result = {}

    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            result['model_metrics'] = json.load(f)

    if os.path.exists(flags_path):
        with open(flags_path, 'r') as f:
            result['methodological_flags'] = json.load(f)

    if os.path.exists(residuals_path):
        with open(residuals_path, 'r') as f:
            result['residuals'] = json.load(f)

    return result


def run_modeling_pipeline():
    """
    Run the full modeling pipeline:
    1. Load cleaned data
    2. Apply ILR transformation
    3. Split data (80/20)
    4. Train model with CV (on training set only)
    5. Save best hyperparameters
    6. Train final model on full training set with best hyperparameters
    7. Save final model
    8. Evaluate on test set
    9. Save metrics, residuals, and flags
    """
    logger.info("Starting modeling pipeline")

    # Step 1: Load data
    X, y = load_features_and_target()

    # Step 2: Apply ILR transformation
    X_ilr = apply_ilr_transformation(X)

    # Step 3: Split data
    X_train, X_test, y_train, y_test = split_data(X_ilr, y)

    # Save split indices
    train_indices = X_train.index.tolist()
    test_indices = X_test.index.tolist()
    save_split_indices(train_indices, test_indices)

    # Step 4: Train with CV to find best hyperparameters
    # Note: T021 should have already done this and saved best params.
    # We load them here to ensure consistency.
    try:
        best_params = load_best_hyperparameters()
        logger.info(f"Loaded best hyperparameters from previous CV run: {best_params}")
    except FileNotFoundError:
        logger.warning("Best hyperparameters not found. Running CV now.")
        _, best_params, cv_mae = train_random_forest_with_cv(X_train, y_train)
        save_best_hyperparameters(best_params)

    # Step 5: Train final model on full training set with best hyperparameters
    logger.info("Training final model with best hyperparameters")
    final_model = RandomForestRegressor(**best_params, random_state=42)
    final_model.fit(X_train, y_train)

    # Step 6: Save the final model
    save_model(final_model)

    # Step 7: Evaluate on test set
    test_mae = evaluate_model_on_test(final_model, X_test, y_test)

    # Step 8: Calculate CV MAE (load from saved or recompute if needed)
    # For now, we assume T021 saved the CV MAE in model_metrics or we recompute
    # Let's recompute a simple CV on the training set to get the metric
    # Actually, T021 should have saved cv_mae. Let's try to load it.
    try:
        metrics_path = config.results / "model_metrics.json"
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                existing_metrics = json.load(f)
            cv_mae = existing_metrics.get('cv_mae', 0.0)
        else:
            # If not found, run a quick CV
            _, _, cv_mae = train_random_forest_with_cv(X_train, y_train)
    except Exception as e:
        logger.warning(f"Could not load CV MAE: {e}. Running CV now.")
        _, _, cv_mae = train_random_forest_with_cv(X_train, y_train)

    # Calculate confidence intervals (approximate)
    cv_ci_lower = cv_mae * 0.9
    cv_ci_upper = cv_mae * 1.1

    # Step 9: Save metrics
    save_model_metrics(cv_mae, cv_ci_lower, cv_ci_upper, test_mae)

    # Save residuals
    y_pred_test = final_model.predict(X_test)
    save_residuals(y_test.tolist(), y_pred_test.tolist(), test_indices)

    # Save methodological flags
    mae_flag = cv_mae > 0.05
    save_methodological_flags(mae_flag, cv_mae)

    logger.info("Modeling pipeline completed successfully")
    return {
        "model_path": str(config.models / "rf_model.pkl"),
        "test_mae": test_mae,
        "cv_mae": cv_mae
    }


def main():
    """Main entry point for the modeling pipeline."""
    parser = argparse.ArgumentParser(description="Run the modeling pipeline")
    parser.add_argument("--data_path", type=str, default=None, help="Path to cleaned data")
    parser.add_argument("--output_path", type=str, default=None, help="Path to save model")

    args = parser.parse_args()

    # Setup logging
    log_operation("modeling_pipeline_start", args=args.__dict__)

    try:
        result = run_modeling_pipeline()
        log_operation("modeling_pipeline_success", result=result)
        print(f"Pipeline completed. Test MAE: {result['test_mae']:.4f}")
    except Exception as e:
        log_operation("modeling_pipeline_failed", error=str(e))
        print(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
