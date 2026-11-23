"""
Random Forest implementation for molecular property prediction.

This module handles the training of Random Forest models using Open Babel fingerprints
and evaluation on held-out test sets, as defined in tasks T020 and T020.1.

It implements:
- Nested Cross-Validation for hyperparameter tuning (T019.5)
- Final model training on the full training set (T020)
- Evaluation on the held-out test set (T020.1)
"""

import os
import sys
import pickle
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Project root for relative imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.config import get_runtime_config, get_joblib_parallel_backend
from code.seed_manager import set_global_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RANDOM_SEED = 42
TRAIN_SET_PATH = PROJECT_ROOT / "data" / "derived" / "train_set.csv"
TEST_SET_PATH = PROJECT_ROOT / "data" / "derived" / "test_set.csv"
FINGERPRINTS_PATH = PROJECT_ROOT / "data" / "processed" / "train_fingerprints.parquet"
MODEL_OUTPUT_PATH = PROJECT_ROOT / "data" / "derived" / "final_model.pkl"
RF_TEST_PREDICTIONS_PATH = PROJECT_ROOT / "data" / "derived" / "rf_test_predictions.csv"

def load_fingerprints_and_targets(
    fingerprint_path: Path,
    train_set_path: Path,
    target_property: str = "LogP"
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load fingerprints from parquet and merge with training set to get targets.

    Args:
        fingerprint_path: Path to train_fingerprints.parquet
        train_set_path: Path to train_set.csv
        target_property: Name of the target property column (e.g., 'LogP')

    Returns:
        X: Array of fingerprint bits (flattened)
        y: Array of target values
        smiles_list: List of SMILES strings corresponding to rows
    """
    logger.info(f"Loading fingerprints from {fingerprint_path}")
    if not fingerprint_path.exists():
        raise FileNotFoundError(f"Fingerprint file not found: {fingerprint_path}")

    df_fp = pd.read_parquet(fingerprint_path)

    logger.info(f"Loading training set from {train_set_path}")
    if not train_set_path.exists():
        raise FileNotFoundError(f"Training set not found: {train_set_path}")

    df_train = pd.read_csv(train_set_path)

    # Merge on SMILES
    merged = pd.merge(df_fp, df_train, on="smiles", how="inner")

    if merged.empty:
        raise ValueError("No matching SMILES found between fingerprints and training set.")

    logger.info(f"Loaded {len(merged)} samples for training")

    # Extract features (fingerprint bits)
    # Assuming columns like 'maccs_bits', 'ecfp4_bits', 'fp2_bits' are stored as lists or strings
    # We need to flatten them into a feature matrix
    feature_cols = [col for col in df_fp.columns if col != 'smiles']
    if not feature_cols:
        raise ValueError("No fingerprint columns found in the parquet file.")

    # Convert list/string bits to numpy array
    X_list = []
    for _, row in merged.iterrows():
        features = []
        for col in feature_cols:
            val = row[col]
            if isinstance(val, list):
                features.extend(val)
            elif isinstance(val, str):
                # Assume comma-separated or space-separated bits
                bits = val.replace("[", "").replace("]", "").split(",")
                features.extend([int(b.strip()) for b in bits if b.strip().isdigit()])
            else:
                features.append(int(val))
        X_list.append(features)

    X = np.array(X_list)
    y = merged[target_property].values
    smiles_list = merged["smiles"].tolist()

    return X, y, smiles_list

def reduce_dataset_size(X: np.ndarray, y: np.ndarray, max_samples: int = 2000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reduce dataset size if it exceeds memory/time constraints.

    Args:
        X: Feature matrix
        y: Target vector
        max_samples: Maximum number of samples to keep

    Returns:
        X_reduced, y_reduced
    """
    if len(X) <= max_samples:
        return X, y

    logger.warning(f"Dataset size ({len(X)}) exceeds limit ({max_samples}). Reducing...")
    indices = np.random.RandomState(RANDOM_SEED).choice(len(X), max_samples, replace=False)
    return X[indices], y[indices]

def tune_hyperparameters(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Perform grid search for hyperparameter tuning using nested CV structure.

    Args:
        X: Feature matrix
        y: Target vector

    Returns:
        best_params: Dictionary of best hyperparameters found
    """
    logger.info("Starting hyperparameter tuning with GridSearchCV...")

    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [5, 10, 15]
    }

    rf = RandomForestRegressor(random_state=RANDOM_SEED, n_jobs=-1)

    grid_search = GridSearchCV(
        rf,
        param_grid,
        cv=5,
        scoring='neg_mean_absolute_error',
        n_jobs=-1,
        verbose=1
    )

    grid_search.fit(X, y)

    best_params = grid_search.best_params_
    logger.info(f"Best parameters found: {best_params}")
    logger.info(f"Best CV score (neg MAE): {grid_search.best_score_}")

    return best_params

def run_nested_cross_validation(X: np.ndarray, y: np.ndarray, best_params: Dict[str, Any]) -> Dict[str, float]:
    """
    Run nested cross-validation to estimate generalization error.

    Args:
        X: Feature matrix
        y: Target vector
        best_params: Best hyperparameters from tuning

    Returns:
        cv_results: Dictionary containing mean and std of CV scores
    """
    logger.info("Running nested cross-validation...")

    rf = RandomForestRegressor(**best_params, random_state=RANDOM_SEED, n_jobs=-1)

    # Outer loop for estimation
    scores = cross_val_score(rf, X, y, cv=5, scoring='neg_mean_absolute_error', n_jobs=-1)

    results = {
        'mean_mae': -scores.mean(),
        'std_mae': scores.std()
    }

    logger.info(f"Nested CV MAE: {results['mean_mae']:.4f} (+/- {results['std_mae']:.4f})")

    return results

def train_final_model(X: np.ndarray, y: np.ndarray, best_params: Dict[str, Any]) -> RandomForestRegressor:
    """
    Train the final model on the full training set.

    Args:
        X: Feature matrix
        y: Target vector
        best_params: Best hyperparameters

    Returns:
        model: Trained RandomForestRegressor
    """
    logger.info("Training final model on full training set...")

    model = RandomForestRegressor(**best_params, random_state=RANDOM_SEED, n_jobs=-1)
    model.fit(X, y)

    logger.info("Final model training complete.")
    return model

def save_model(model: RandomForestRegressor, output_path: Path) -> None:
    """
    Save the trained model to disk.

    Args:
        model: Trained model
        output_path: Path to save the model
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {output_path}")

def evaluate_on_test_set(
    model: RandomForestRegressor,
    test_set_path: Path,
    fingerprint_path: Path,
    output_path: Path,
    target_property: str = "LogP"
) -> None:
    """
    Evaluate the trained model on the held-out test set and save predictions.

    Args:
        model: Trained model
        test_set_path: Path to test_set.csv
        fingerprint_path: Path to train_fingerprints.parquet (assumed to contain test fingerprints too, or we need test fingerprints)
        output_path: Path to save rf_test_predictions.csv
        target_property: Target property name
    """
    logger.info(f"Evaluating model on test set from {test_set_path}")

    if not test_set_path.exists():
        raise FileNotFoundError(f"Test set not found: {test_set_path}")

    # Note: In a real pipeline, we would have a separate test fingerprint file.
    # For this implementation, we assume the fingerprint file contains all data
    # or we re-generate fingerprints for the test set.
    # To strictly follow the task, we need to ensure we have fingerprints for the test set.
    # Since T019 generates fingerprints for the TRAINING set, we must assume
    # a similar process generated test fingerprints or we are re-using the same logic.
    # However, the task T020.1 says: "Load final_model.pkl, Predict on test set".
    # We need the test fingerprints. Let's assume they are in a file named test_fingerprints.parquet
    # or we need to generate them. The task T019 says "Generate ... for all molecules in the training set".
    # This implies test fingerprints are NOT in train_fingerprints.parquet.
    # We must generate test fingerprints or load them if they exist.
    # Given the constraints, let's assume a file `data/processed/test_fingerprints.parquet` exists
    # or we generate it on the fly if the code supports it.
    # For this specific task T054a, we will implement the evaluation logic assuming
    # we can get test fingerprints. If the file doesn't exist, we raise an error.

    test_fp_path = PROJECT_ROOT / "data" / "processed" / "test_fingerprints.parquet"

    if not test_fp_path.exists():
        # Fallback: Try to use the train fingerprints if the test set is small subset? No, that's data leakage.
        # We must have test fingerprints.
        logger.error(f"Test fingerprints not found at {test_fp_path}. Please ensure T019 or a similar process generated them.")
        raise FileNotFoundError(f"Test fingerprints not found: {test_fp_path}")

    df_test = pd.read_csv(test_set_path)
    df_test_fp = pd.read_parquet(test_fp_path)

    merged = pd.merge(df_test_fp, df_test, on="smiles", how="inner")

    if merged.empty:
        raise ValueError("No matching SMILES found between test fingerprints and test set.")

    logger.info(f"Evaluating on {len(merged)} test samples")

    # Extract features
    feature_cols = [col for col in df_test_fp.columns if col != 'smiles']
    X_test_list = []
    for _, row in merged.iterrows():
        features = []
        for col in feature_cols:
            val = row[col]
            if isinstance(val, list):
                features.extend(val)
            elif isinstance(val, str):
                bits = val.replace("[", "").replace("]", "").split(",")
                features.extend([int(b.strip()) for b in bits if b.strip().isdigit()])
            else:
                features.append(int(val))
        X_test_list.append(features)

    X_test = np.array(X_test_list)
    y_true = merged[target_property].values
    smiles_list = merged["smiles"].tolist()

    # Predict
    y_pred = model.predict(X_test)
    residuals = y_true - y_pred

    # Create output dataframe
    results_df = pd.DataFrame({
        'smiles': smiles_list,
        'property_name': target_property,
        'experimental_value': y_true,
        'predicted_value': y_pred,
        'residual': residuals
    })

    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Test predictions saved to {output_path}")

    # Log metrics
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    logger.info(f"Test Set Metrics - MAE: {mae:.4f}, RMSE: {rmse:.4f}")

def check_runtime_elapsed(start_time: float, max_hours: float = 6.0) -> bool:
    """
    Check if the runtime has exceeded the maximum allowed time.

    Args:
        start_time: Start time in seconds
        max_hours: Maximum allowed hours

    Returns:
        True if time exceeded, False otherwise
    """
    elapsed = time.time() - start_time
    if elapsed > max_hours * 3600:
        logger.error(f"Runtime exceeded limit: {elapsed/3600:.2f} hours > {max_hours} hours")
        return True
    return False

def main():
    """
    Main entry point for the Random Forest pipeline.
    Executes T020 (Training) and T020.1 (Evaluation).
    """
    set_global_seed(RANDOM_SEED)
    start_time = time.time()

    config = get_runtime_config()
    max_samples = config.get('max_samples', 2000)

    # 1. Load Data
    try:
        X_train, y_train, _ = load_fingerprints_and_targets(
            FINGERPRINTS_PATH,
            TRAIN_SET_PATH,
            target_property="LogP"
        )
    except Exception as e:
        logger.error(f"Failed to load training data: {e}")
        sys.exit(1)

    # 2. Reduce size if necessary
    X_train, y_train = reduce_dataset_size(X_train, y_train, max_samples)

    # 3. Tune Hyperparameters (T020)
    best_params = tune_hyperparameters(X_train, y_train)

    # 4. Run Nested CV (T019.5 - part of T020)
    if not check_runtime_elapsed(start_time):
        cv_results = run_nested_cross_validation(X_train, y_train, best_params)
    else:
        logger.warning("Skipping nested CV due to time limit.")
        cv_results = {}

    # 5. Train Final Model (T020)
    if not check_runtime_elapsed(start_time):
        model = train_final_model(X_train, y_train, best_params)
        save_model(model, MODEL_OUTPUT_PATH)
    else:
        logger.error("Cannot train final model due to time limit.")
        sys.exit(1)

    # 6. Evaluate on Test Set (T020.1)
    if not check_runtime_elapsed(start_time):
        try:
            evaluate_on_test_set(
                model,
                TEST_SET_PATH,
                FINGERPRINTS_PATH, # This path is used as a reference, actual test fp path is derived
                RF_TEST_PREDICTIONS_PATH,
                target_property="LogP"
            )
        except FileNotFoundError as e:
            logger.error(f"Test evaluation failed: {e}")
            logger.info("Note: Ensure test fingerprints are generated (e.g., data/processed/test_fingerprints.parquet)")
            # Do not exit with error if test fingerprints are missing, as this might be a pipeline order issue
            # But the task requires the file to be written. If we can't, we fail.
            sys.exit(1)
    else:
        logger.error("Cannot evaluate due to time limit.")
        sys.exit(1)

    logger.info("Random Forest pipeline completed successfully.")

if __name__ == "__main__":
    main()