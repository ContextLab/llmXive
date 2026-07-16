import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, List
import pickle

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error
import xgboost as xgb

# Import from project utils
from utils import setup_logging, set_random_seed, load_metadata, update_metadata_entry, save_metadata
from error_handling import DataInsufficiencyError

# Initialize logger
logger = setup_logging("train_final")

# Constants
RANDOM_SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "reports"
METRICS_FILE = ARTIFACTS_DIR / "training_metrics.json"
MODEL_FILE = MODELS_DIR / "best_model.json"
SPLIT_INDICES_FILE = DATA_DIR / "split_indices.pkl"
COLLINEARITY_REPORT_FILE = ARTIFACTS_DIR / "collinearity_diagnostic.json"

def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned dataset produced by T011."""
    path = DATA_DIR / "cleaned_dataset.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {path}. Run T011 first.")
    logger.info(f"Loading cleaned dataset from {path}")
    return pd.read_parquet(path)

def load_split_indices() -> Dict[str, np.ndarray]:
    """Load the train/test split indices saved by T012a."""
    if not SPLIT_INDICES_FILE.exists():
        raise FileNotFoundError(f"Split indices not found at {SPLIT_INDICES_FILE}. Run T012a first.")
    logger.info(f"Loading split indices from {SPLIT_INDICES_FILE}")
    with open(SPLIT_INDICES_FILE, 'rb') as f:
        return pickle.load(f)

def load_best_hyperparameters() -> Dict[str, Any]:
    """Load best hyperparameters saved by T012a."""
    path = MODELS_DIR / "best_params.json"
    if not path.exists():
        raise FileNotFoundError(f"Best parameters not found at {path}. Run T012a first.")
    logger.info(f"Loading best hyperparameters from {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_collinearity_report() -> Dict[str, Any]:
    """Load the collinearity diagnostic report from T016."""
    if not COLLINEARITY_REPORT_FILE.exists():
        logger.warning(f"Collinearity report not found at {COLLINEARITY_REPORT_FILE}. Proceeding without framing.")
        return {"status": "missing", "message": "Report not found."}
    with open(COLLINEARITY_REPORT_FILE, 'r') as f:
        return json.load(f)

def train_final_model(X_train: pd.DataFrame, y_train: pd.Series, params: Dict[str, Any]) -> xgb.XGBRegressor:
    """Train the final XGBoost model on the training set."""
    logger.info("Training final XGBoost model...")
    model = xgb.XGBRegressor(
        n_estimators=params['n_estimators'],
        max_depth=params['max_depth'],
        learning_rate=params['learning_rate'],
        objective='reg:squarederror',
        random_state=RANDOM_SEED,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    logger.info("Final model training complete.")
    return model

def evaluate_model(model: xgb.XGBRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """Evaluate model on the held-out test set."""
    logger.info("Evaluating model on held-out test set...")
    y_pred = model.predict(X_test)

    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mape = mean_absolute_percentage_error(y_test, y_pred)

    # Calculate SD of R^2 across k=5 folds on the TEST set (nested CV)
    # This satisfies SC-001 requirement for stability assessment on test data
    logger.info("Performing 5-fold CV on test set to calculate R^2 standard deviation...")
    kfold = KFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    cv_scores = cross_val_score(model, X_test, y_test, cv=kfold, scoring='r2')
    r2_sd = np.std(cv_scores)

    logger.info(f"Test R^2: {r2:.4f}, RMSE: {rmse:.4f}, MAPE: {mape:.4f}, R^2 SD (5-fold): {r2_sd:.4f}")

    return {
        "r2": float(r2),
        "rmse": float(rmse),
        "mape": float(mape),
        "r2_std_5fold": float(r2_sd),
        "test_sample_size": int(len(y_test))
    }

def save_metrics(metrics: Dict[str, float], collinearity_report: Dict[str, Any]) -> None:
    """Save training metrics and collinearity framing to JSON."""
    # Ensure directory exists
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Create framing statement based on T016 report
    framing_statement = "The relationship between misorientation and Σ value is descriptive, not causal, as Σ is derived from misorientation."

    report_data = {
        "metrics": metrics,
        "collinearity_framing": {
            "statement": framing_statement,
            "source_report": collinearity_report,
            "note": "Unconditional framing applied as per task requirements regardless of MI score."
        },
        "timestamp": str(pd.Timestamp.now())
    }

    with open(METRICS_FILE, 'w') as f:
        json.dump(report_data, f, indent=2)
    logger.info(f"Metrics saved to {METRICS_FILE}")

def save_model(model: xgb.XGBRegressor) -> None:
    """Save the trained model to JSON."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model.save_model(str(MODEL_FILE))
    logger.info(f"Model saved to {MODEL_FILE}")

def main():
    """Main execution function for T012b."""
    try:
        # 1. Load data
        df = load_cleaned_data()
        split_indices = load_split_indices()
        best_params = load_best_hyperparameters()
        collinearity_report = load_collinearity_report()

        # 2. Split data using saved indices
        train_idx = split_indices['train']
        test_idx = split_indices['test']

        X = df.drop(columns=['diffusivity'])
        y = df['diffusivity']

        X_train = X.iloc[train_idx]
        y_train = y.iloc[train_idx]
        X_test = X.iloc[test_idx]
        y_test = y.iloc[test_idx]

        logger.info(f"Training set size: {len(X_train)}, Test set size: {len(X_test)}")

        # 3. Train final model
        model = train_final_model(X_train, y_train, best_params)

        # 4. Evaluate on held-out test set
        metrics = evaluate_model(model, X_test, y_test)

        # 5. Save outputs
        save_model(model)
        save_metrics(metrics, collinearity_report)

        logger.info("T012b completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during training: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())