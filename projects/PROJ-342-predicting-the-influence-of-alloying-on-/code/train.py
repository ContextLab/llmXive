import os
import sys
import logging
import json
import pickle
import time
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import LeaveOneGroupOut, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

# Import from local modules as per API surface
from resource_monitor import resource_monitor, ResourceLimitExceeded
from descriptors import get_project_root, setup_logging as setup_desc_logging

def setup_logging_custom():
    """Configure logging for the training module."""
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "train.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_prepared_data(data_path: str) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load cleaned data and descriptors, extract features (X), target (y), and families.
    """
    logger = logging.getLogger(__name__)
    df = pd.read_csv(data_path)
    
    # Ensure required columns exist
    required_cols = ['radius_mismatch', 'electronegativity_diff', 'VEC', 'Tg', 'family']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    X = df[['radius_mismatch', 'electronegativity_diff', 'VEC']].values
    y = df['Tg'].values
    families = df['family'].values

    logger.info(f"Loaded {len(df)} records. X shape: {X.shape}, y shape: {y.shape}")
    return df, X, y, families

def get_family_groups(families: np.ndarray) -> List[int]:
    """
    Map family names to integer group IDs for LOFO CV.
    """
    unique_families = np.unique(families)
    family_to_id = {f: i for i, f in enumerate(unique_families)}
    return np.array([family_to_id[f] for f in families])

def check_family_stratification(families: np.ndarray, logger: logging.Logger) -> bool:
    """
    Check if any family has < 50 samples. Logs a warning if so.
    Returns True if a warning was triggered.
    """
    unique, counts = np.unique(families, return_counts=True)
    warned = False
    for fam, count in zip(unique, counts):
        if count < 50:
            logger.warning(f"STRATIFICATION_WARNING: Family '{fam}' has only {count} samples (< 50). Proceeding with caution.")
            warned = True
    return warned

def generate_stratification_status_file(was_warned: bool, families: np.ndarray, logger: logging.Logger, project_root: Path):
    """
    Generate stratification_status.json based on whether a warning was triggered.
    """
    status_data = {}
    if was_warned:
        unique, counts = np.unique(families, return_counts=True)
        small_families = [{"family_name": str(f), "sample_count": int(c), "action_taken": "warned"} 
                          for f, c in zip(unique, counts) if c < 50]
        status_data = {"status": "warning_triggered", "families_below_threshold": small_families}
        logger.info(f"Generated stratification_status.json with {len(small_families)} small families.")
    else:
        status_data = {"status": "no_warning"}
        logger.info("Generated stratification_status.json: no warning triggered.")
    
    output_path = project_root / "data" / "processed" / "stratification_status.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(status_data, f, indent=2)

def lofo_cv_score(X: np.ndarray, y: np.ndarray, families: np.ndarray, max_depth: int = 3) -> float:
    """
    Perform Leave-One-Family-Out Cross-Validation and return mean R2 score.
    """
    logo = LeaveOneGroupOut()
    model = GradientBoostingRegressor(max_depth=max_depth, random_state=42)
    scores = cross_val_score(model, X, y, cv=logo, groups=families, scoring='r2')
    return np.mean(scores)

def calculate_null_model_r2(y: np.ndarray) -> float:
    """
    Calculate R2 of a null model (predicting mean of y).
    """
    y_mean = np.mean(y)
    ss_res = np.sum((y - y_mean) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    if ss_tot == 0:
        return 0.0
    return 1 - (ss_res / ss_tot)

@resource_monitor(runtime_limit_h=6.0, memory_limit_gb=7.0)
def train_and_evaluate(X: np.ndarray, y: np.ndarray, families: np.ndarray, logger: logging.Logger, project_root: Path):
    """
    Train the final model, evaluate, and save artifacts.
    """
    logger.info("Starting model training and evaluation...")
    
    # Hyperparameter search (limited to 10 combos as per FR-003)
    # Grid: max_depth in [3, 5, 7], n_estimators in [50, 100, 200]
    best_score = -np.inf
    best_params = {}
    best_model = None

    depths = [3, 5, 7]
    estimators = [50, 100, 200]
    
    logger.info("Performing grid search for hyperparameters...")
    for d in depths:
        for n in estimators:
            try:
                score = lofo_cv_score(X, y, families, max_depth=d)
                logger.info(f"Depth={d}, Estimators={n} -> LOFO R2: {score:.4f}")
                if score > best_score:
                    best_score = score
                    best_params = {'max_depth': d, 'n_estimators': n}
                    # Train the model on full data for this config to keep it as candidate
                    candidate_model = GradientBoostingRegressor(max_depth=d, n_estimators=n, random_state=42)
                    candidate_model.fit(X, y)
                    best_model = candidate_model
            except Exception as e:
                logger.warning(f"Failed to train with depth={d}, n_estimators={n}: {e}")
                continue

    if best_model is None:
        raise RuntimeError("No valid model could be trained during grid search.")

    logger.info(f"Best parameters: {best_params}, Best LOFO R2: {best_score:.4f}")

    # Retrain best model on full data (it was already trained in the loop, but ensure final state)
    final_model = GradientBoostingRegressor(**best_params, random_state=42)
    final_model.fit(X, y)

    # Calculate metrics
    y_pred = final_model.predict(X)
    mae = mean_absolute_error(y, y_pred)
    r2 = r2_score(y, y_pred)
    null_r2 = calculate_null_model_r2(y)
    
    # Feature importances
    feature_names = ['radius_mismatch', 'electronegativity_diff', 'VEC']
    importances = dict(zip(feature_names, final_model.feature_importances_.tolist()))

    logger.info(f"Final Model Metrics: R2={r2:.4f}, MAE={mae:.4f}, Null R2={null_r2:.4f}")

    # Save Model (T024a)
    model_path = project_root / "artifacts" / "models" / "best_model.pkl"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(final_model, f)
    logger.info(f"Model saved to {model_path}")

    # Save Metrics (T024b)
    metrics = {
        "R2": float(r2),
        "MAE": float(mae),
        "feature_importances": importances,
        "null_model_r2": float(null_r2),
        "best_params": best_params
    }
    metrics_path = project_root / "artifacts" / "metrics" / "metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

    return final_model, metrics

def save_artifacts(model, metrics, project_root: Path):
    """
    Placeholder for additional artifact saving if needed.
    """
    pass

def run_training_pipeline():
    """
    Main entry point for the training pipeline.
    """
    logger = setup_logging_custom()
    project_root = get_project_root()
    
    # Load data
    data_path = project_root / "data" / "processed" / "descriptors.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Input data file not found: {data_path}")
    
    df, X, y, families = load_prepared_data(str(data_path))
    
    # Stratification check
    was_warned = check_family_stratification(families, logger)
    generate_stratification_status_file(was_warned, families, logger, project_root)
    
    # Train and evaluate
    model, metrics = train_and_evaluate(X, y, families, logger, project_root)
    
    logger.info("Training pipeline completed successfully.")

def main():
    run_training_pipeline()

if __name__ == "__main__":
    main()
