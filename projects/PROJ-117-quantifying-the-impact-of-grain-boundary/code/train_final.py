"""
T012b: Final Model Training and Evaluation

This script trains the final XGBoost model using the best hyperparameters found during tuning.
It evaluates the model on the held-out test set, calculates performance metrics including
standard deviation via k-fold cross-validation on the test set, and generates the training metrics report.

Dependencies:
- T012a: Must have produced models/best_params.json and data/processed/split_indices.pkl
- T016: Must have produced artifacts/reports/collinearity_diagnostic.json
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error
import pickle

# Import local utilities
from utils import setup_logging, set_random_seed
from error_handling import DataInsufficiencyError

# Configure logging
logger = setup_logging("train_final")

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
REPORTS_DIR = ARTIFACTS_DIR / "reports"

# File paths
CLEANED_DATA_PATH = PROCESSED_DIR / "cleaned_dataset.parquet"
SPLIT_INDICES_PATH = PROCESSED_DIR / "split_indices.pkl"
BEST_PARAMS_PATH = MODELS_DIR / "best_params.json"
COLLINEARITY_REPORT_PATH = REPORTS_DIR / "collinearity_diagnostic.json"
TRAINED_MODEL_PATH = MODELS_DIR / "best_model.json"
METRICS_OUTPUT_PATH = REPORTS_DIR / "training_metrics.json"

# Ensure output directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned dataset from parquet."""
    if not CLEANED_DATA_PATH.exists():
        raise FileNotFoundError(f"Cleaned data not found at {CLEANED_DATA_PATH}. Run preprocess.py first.")
    logger.info(f"Loading cleaned data from {CLEANED_DATA_PATH}")
    df = pd.read_parquet(CLEANED_DATA_PATH)
    logger.info(f"Loaded {len(df)} records")
    return df


def load_split_indices() -> Dict[str, List[int]]:
    """Load the train/validation/test split indices."""
    if not SPLIT_INDICES_PATH.exists():
        raise FileNotFoundError(f"Split indices not found at {SPLIT_INDICES_PATH}. Run train_tuning.py first.")
    with open(SPLIT_INDICES_PATH, 'rb') as f:
        indices = pickle.load(f)
    logger.info(f"Loaded split indices: train={len(indices['train'])}, val={len(indices['val'])}, test={len(indices['test'])}")
    return indices


def load_best_hyperparameters() -> Dict[str, Any]:
    """Load the best hyperparameters from tuning."""
    if not BEST_PARAMS_PATH.exists():
        raise FileNotFoundError(f"Best parameters not found at {BEST_PARAMS_PATH}. Run train_tuning.py first.")
    with open(BEST_PARAMS_PATH, 'r') as f:
        params = json.load(f)
    logger.info(f"Loaded best hyperparameters: {params}")
    return params


def load_collinearity_report() -> Dict[str, Any]:
    """Load the collinearity diagnostic report."""
    if not COLLINEARITY_REPORT_PATH.exists():
        logger.warning(f"Collinearity report not found at {COLLINEARITY_REPORT_PATH}. Proceeding without framing statement.")
        return {}
    with open(COLLINEARITY_REPORT_PATH, 'r') as f:
        report = json.load(f)
    logger.info("Loaded collinearity diagnostic report")
    return report


def train_final_model(X_train: pd.DataFrame, y_train: pd.Series, params: Dict[str, Any]) -> xgb.XGBRegressor:
    """Train the final XGBoost model."""
    logger.info("Training final model...")
    # Extract XGBoost specific params
    xgb_params = {
        'objective': 'reg:squarederror',
        'eval_metric': 'rmse',
        'random_state': params.get('random_state', 42),
        'n_jobs': -1
    }
    # Update with tuned hyperparameters
    xgb_params.update(params)

    model = xgb.XGBRegressor(**xgb_params)
    model.fit(X_train, y_train)
    logger.info("Final model training complete.")
    return model


def evaluate_model(model: xgb.XGBRegressor, X_test: pd.DataFrame, y_test: pd.Series, n_folds: int = 5) -> Dict[str, float]:
    """
    Evaluate the model on the test set.
    Calculates R2, RMSE, MAPE, and the standard deviation of R2 across k-folds on the test set.
    """
    logger.info("Evaluating model on held-out test set...")

    # Predictions
    y_pred = model.predict(X_test)

    # Standard Metrics
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    # MAPE handling for potential zeros in y_test
    if np.any(y_test == 0):
        logger.warning("Zero values detected in y_test. MAPE calculation may be unstable or infinite.")
        mape = mean_absolute_percentage_error(y_test, y_pred, multioutput='uniform_average')
    else:
        mape = mean_absolute_percentage_error(y_test, y_pred)

    # Standard Deviation of R2 via K-Fold on Test Set
    logger.info(f"Performing {n_folds}-fold cross-validation on test set to calculate R2 SD...")
    kfold = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_test, y_test, cv=kfold, scoring='r2')
    r2_sd = np.std(cv_scores)

    logger.info(f"Test Set Metrics -> R2: {r2:.4f}, RMSE: {rmse:.4f}, MAPE: {mape:.4f}, R2_SD: {r2_sd:.4f}")

    return {
        'r2': float(r2),
        'rmse': float(rmse),
        'mape': float(mape),
        'r2_sd': float(r2_sd),
        'n_folds_cv': n_folds,
        'cv_scores': cv_scores.tolist()
    }


def save_metrics(metrics: Dict[str, Any], collinearity_report: Dict[str, Any]) -> None:
    """Save the training metrics and framing statement to JSON."""
    # Construct the framing statement based on T016 report
    framing_statement = (
        "The relationship between misorientation and Σ value is descriptive, not causal, "
        "as Σ is derived from misorientation."
    )

    output_data = {
        'metrics': metrics,
        'framing_statement': framing_statement,
        'collinearity_diagnostic_status': collinearity_report.get('status', 'unknown'),
        'timestamp': str(pd.Timestamp.now())
    }

    with open(METRICS_OUTPUT_PATH, 'w') as f:
        json.dump(output_data, f, indent=2)
    logger.info(f"Metrics saved to {METRICS_OUTPUT_PATH}")


def save_model(model: xgb.XGBRegressor) -> None:
    """Save the trained model to JSON."""
  # XGBoost save_model expects a path, usually .json or .bst
  # We use .json as per task description
    model.save_model(TRAINED_MODEL_PATH)
    logger.info(f"Model saved to {TRAINED_MODEL_PATH}")


def main():
    """Main execution flow for T012b."""
    try:
        # 1. Load Data and Config
        df = load_cleaned_data()
        indices = load_split_indices()
        best_params = load_best_hyperparameters()
        collinearity_report = load_collinearity_report()

        # 2. Split Data
        train_idx = indices['train']
        test_idx = indices['test']

        X = df.drop(columns=['diffusivity']) # Assuming target is 'diffusivity'
        y = df['diffusivity']

        X_train = X.iloc[train_idx]
        y_train = y.iloc[train_idx]
        X_test = X.iloc[test_idx]
        y_test = y.iloc[test_idx]

        logger.info(f"Split data: Train {len(X_train)}, Test {len(X_test)}")

        # 3. Train Final Model
        model = train_final_model(X_train, y_train, best_params)

        # 4. Evaluate
        metrics = evaluate_model(model, X_test, y_test)

        # 5. Save Artifacts
        save_model(model)
        save_metrics(metrics, collinearity_report)

        logger.info("T012b execution completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Required file missing: {e}")
        sys.exit(1)
    except DataInsufficiencyError as e:
        logger.error(f"Data insufficiency error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during training: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()